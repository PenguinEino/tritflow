"""Check the hand-drawn schematics against the taped-out Xschem circuits.

Xschem netlists both drawings, so this checks connectivity rather than trusting
wire labels or a coordinate parser. Each device's ordered terminals must match
under one bijection of internal nets; external port names and order are fixed.
Native embedded symbols are separately checked: only text positions and sizes
may differ from the pinned PDK, and every text label must remain present.

    python3 notebook/assets/schematics/verify_compact.py
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REFERENCES = {"INV": "inverter.sch", "NAND": "mul_nand.sch",
              "NOR": "mul_nor.sch", "NANY": "nany.sch"}
SYSTEM = Path("/usr/local/share/xschem/xschem_library")
DEVICES = {"MP", "MN", "RR"}


def records(text):
    """Read Xschem records, including multiline properties and Tcl text."""
    current, depth = "", 0
    for line in text.splitlines(keepends=True):
        current += line
        depth += line.count("{")-line.count("}")
        if depth == 0:
            yield current
            current = ""
    if current or depth:
        raise ValueError("unbalanced schematic record")


def components(text):
    """Return outer instances and embedded symbols, without interpreting wires."""
    instances, symbols = {}, {}
    embedded, symbol, last = None, [], None
    for record in records(text):
        if record.strip() == "[":
            embedded, symbol = last, []
        elif record.strip() == "]":
            symbols[embedded] = symbol
            embedded = None
        elif embedded is not None:
            symbol.append(record)
        elif record.startswith("C "):
            match = re.fullmatch(r'C \{([^}]+)\} \S+ \S+ \d \d \{(.*)\}\s*', record, re.S)
            path, attributes = match.groups()
            props = dict(re.findall(r'(\w+)=([^\s}]+)', attributes))
            name = props["name"]
            if name in instances:
                raise ValueError(f"duplicate instance {name}")
            props.pop("embed", None)
            instances[name] = {"symbol": path, "properties": props}
            last = path
    return instances, symbols


def text_content(record):
    """Annotation text independently of its drawing position, size and colour."""
    return re.fullmatch(r'T \{(.*)\} \S+ \S+ \d \d \S+ \S+ \{.*\}\s*', record, re.S)[1]


def check_sources(original, redrawn, pdk):
    """Preserve source parameters, original port/label instances and PDK pins."""
    before, _ = components(original.read_text())
    after, embedded = components(redrawn.read_text())
    for name, instance in before.items():
        if after.get(name) != instance:
            raise ValueError(f"changed/missing source instance {name}: {after.get(name)} != {instance}")
    native = {i["symbol"] for i in after.values() if Path(i["symbol"]).stem in DEVICES}
    if set(embedded) != native:
        raise ValueError("every native device symbol must have its reviewed embedded definition")
    for path, actual in embedded.items():
        expected = list(records((pdk/"libs.tech/xschem"/path).read_text()))
        if [r for r in actual if not r.startswith("T ")] != [r for r in expected if not r.startswith("T ")]:
            raise ValueError(f"changed native symbol geometry, pins or netlisting contract: {path}")
        if Counter(text_content(r) for r in actual if r.startswith("T ")) != Counter(
                text_content(r) for r in expected if r.startswith("T ")):
            raise ValueError(f"changed or missing native annotation: {path}")
    return {name: i for name, i in before.items() if Path(i["symbol"]).stem in DEVICES}


def netlist(source, destination, cell, reference, pdk):
    """Netlist a temporary copy; Xschem never writes into either reference root."""
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tritflow-netlist-") as directory:
        work = Path(directory)
        sch, rc = work/f"{cell}.sch", work/"xschemrc"
        sch.write_text(source.read_text())
        rc.write_text(f"set XSCHEM_LIBRARY_PATH {{{reference}:{pdk}/libs.tech/xschem:{SYSTEM}}}\n"
                      f"set netlist_dir {{{destination}}}\n")
        process = subprocess.run(["xschem", "-n", "-s", "-q", "-x", "--rcfile", str(rc),
                                  "-o", str(destination), str(sch)], cwd=work,
                                 capture_output=True, text=True, check=True, timeout=60)
        log = process.stdout+process.stderr
        (destination/f"{cell}.log").write_text(log)
        if re.search(r"(?i)IS MISSING|not found|SKIPPING|error:|unconnected|shorted", log):
            raise ValueError(f"Xschem netlisting diagnostic for {source}: {log}")
    return destination/f"{cell}.spice"


def parse_netlist(path):
    """Read native PDK MOS (D,G,S,BG) and RR (PLUS,MINUS,SUB) terminals."""
    text = path.read_text()
    ports = re.search(r'^\*\*\.subckt \S+ (.*)$', text, re.M)[1].split()
    directions = re.findall(r'^\*\.(iopin|ipin|opin) (\S+)$', text, re.M)
    devices = {}
    for line in text.splitlines():
        if not line.startswith("X"):
            continue
        fields = line.split()
        count = 3 if fields[4] == "F_RR" else 4
        model = fields[count+1]
        if model not in {"PMOS", "NMOS", "F_RR"}:
            raise ValueError(f"unexpected device record: {line}")
        devices[fields[0]] = {"model": model, "nodes": fields[1:count+1],
                              "parameters": dict(f.split("=", 1) for f in fields[count+2:])}
    if not devices:
        raise ValueError(f"empty device netlist: {path}")
    return ports, directions, devices


def compare(original, redrawn):
    """One terminal-preserving bijection catches opens, shorts and swapped pins."""
    ports, directions, before = parse_netlist(original)
    new_ports, new_directions, after = parse_netlist(redrawn)
    if ports != new_ports or directions != new_directions or before.keys() != after.keys():
        raise ValueError("changed external ports/directions or device inventory")
    forward, reverse = {p: p for p in ports}, {p: p for p in ports}
    for name, device in before.items():
        other = after[name]
        if device["model"] != other["model"] or device["parameters"] != other["parameters"]:
            raise ValueError(f"changed model/parameters: {name}")
        for old, new in zip(device["nodes"], other["nodes"], strict=True):
            if forward.setdefault(old, new) != new or reverse.setdefault(new, old) != old:
                raise ValueError(f"inconsistent terminal net mapping at {name}: {old} → {new}")
    return {"ports": ports, "port_directions": directions,
            "device_count": len(before), "terminal_count": sum(len(d["nodes"]) for d in before.values()),
            "net_count": len(forward), "net_mapping": dict(sorted(forward.items())),
            "devices": {name: {**before[name], "redrawn_nodes": after[name]["nodes"]} for name in sorted(before)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=Path.home()/"balanced-ternary-logic")
    parser.add_argument("--pdk", type=Path, default=Path(os.environ.get("TR1UM_PDK", Path.home()/"pdk/TR-1um-pinned")))
    parser.add_argument("--out", type=Path, default=ROOT/"build/schem-compact/verification")
    args = parser.parse_args()
    out, reference, pdk = args.out.resolve(), args.reference.expanduser().resolve(), args.pdk.expanduser().resolve()
    if out.is_relative_to(reference) or out.is_relative_to(pdk):
        raise ValueError("verification output must be outside read-only reference roots")
    report = {"passed": True, "method": "Xschem SPICE; ordered device terminals under bijective net renaming",
              "cells": {}}
    for cell, filename in REFERENCES.items():
        original, redrawn = reference/filename, HERE/"src"/f"{cell.lower()}.sch"
        sources = check_sources(original, redrawn, pdk)
        old = netlist(original, out/"original", cell, reference, pdk)
        new = netlist(redrawn, out/"redrawn", cell, reference, pdk)
        result = compare(old, new)
        result["source_devices"] = sources
        result["sha256"] = {"original_schematic": sha256(original.read_bytes()).hexdigest(),
                            "redrawn_schematic": sha256(redrawn.read_bytes()).hexdigest()}
        result["embedded_symbols"] = "all native geometry/pins/netlisting data and annotation text unchanged"
        report["cells"][cell] = result
        print(f"{cell}: PASS — {result['device_count']} devices, {result['terminal_count']} ordered terminals, "
              f"{result['net_count']} nets; source properties, ports and embedded symbols preserved")
    (out/"equivalence.json").write_text(json.dumps(report, indent=2)+"\n")
    print(out/"equivalence.json")


if __name__ == "__main__":
    main()
