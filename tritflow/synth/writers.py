"""Portable gate TritVerilog, cell-level SPICE and reviewable synthesis reports."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tritflow.netlist import GateNetlist
from .simulate import CELL_INPUTS, ordered_instances


def tv_identifier(name: str) -> str:
    """Verilog escaped identifiers retain bit and hierarchy names verbatim."""
    if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9$]*", name):
        return name
    return "\\" + name + " "


def tritverilog(net: GateNetlist) -> str:
    """Write scalar gate primitives in the same parseable TritVerilog language."""
    if any(i.cell == "TDFF" for i in net.instances):
        from tritflow.seq import writers
        return writers.tritverilog(net)
    instances = ordered_instances(net)
    ports = ", ".join(f"{p.dir} trit {tv_identifier(p.name)}" for p in net.ports)
    lines = ["// Generated combinational TritVerilog; trits are -1/0/+1.",
             f"module {tv_identifier(net.top)}({ports});"]
    internal = sorted(net.nets() - {p.name for p in net.ports})
    for name in internal:
        lines.append(f"  wire trit {tv_identifier(name)};")
    for inst in instances:
        output = tv_identifier(inst.pins["Y"])
        if inst.cell.startswith("TIE"):
            digit = {"TIEN": "T", "TIEZ": "0", "TIEP": "1"}[inst.cell]
            lines.append(f"  assign {output} = 1't{digit};")
        else:
            pins = [inst.pins["Y"], *(inst.pins[p] for p in CELL_INPUTS[inst.cell])]
            connection = ", ".join(tv_identifier(n) for n in pins)
            lines.append(f"  {inst.cell.lower()} {tv_identifier(inst.name)}({connection});")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"


def spice_names(names, reserved=()):
    """Shared HDL→SPICE boundary for writers, SIM and physical comparison.

    Deterministic case-insensitive unique names encode punctuation, rail-name
    reservations and case collisions. ``spice`` emits inverse ``* net safe =
    logical`` annotations for every changed name; consumers must restore exact
    logical spelling before comparing oracle/waveform or physical-label keys.
    """
    used = {name.lower() for name in reserved}
    result = {}
    for name in sorted(names):
        candidate = name if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name) else "tf_" + name.encode().hex()
        if candidate.lower() in used:
            candidate = "tf_" + name.encode().hex()
        while candidate.lower() in used:
            candidate = "_" + candidate
        used.add(candidate.lower())
        result[name] = candidate
    return result


def spice(net: GateNetlist) -> str:
    """Write a top subckt; include cells/out/all.spice from the calling testbench.

    Each instance uses signal pins A[, B], Y followed by VDD VMID VSS, exactly
    matching the shared cell contract. Node renaming is recorded in comments.
    """
    if any(i.cell == "TDFF" for i in net.instances):
        from tritflow.seq import writers
        return writers.spice(net)
    instances = ordered_instances(net)
    names = spice_names(net.nets(), ("VDD", "VMID", "VSS", "0"))
    inst_names = spice_names([inst.name for inst in instances])
    top = spice_names([net.top])[net.top]
    lines = ["* TritFlow cell netlist: trits -1/0/+1 at -5/0/+5 V."]
    for original, encoded in names.items():
        if original != encoded:
            lines.append(f"* net {encoded} = {original}")
    ports = [names[p.name] for p in net.ports]
    lines.append(f".subckt {top} {' '.join([*ports, 'VDD', 'VMID', 'VSS'])}")
    for inst in instances:
        pins = [names[inst.pins[p]] for p in (*CELL_INPUTS[inst.cell], "Y")]
        lines.append(f"X{inst_names[inst.name]} {' '.join(pins)} VDD VMID VSS {inst.cell}")
    lines.append(f".ends {top}")
    return "\n".join(lines) + "\n"


def report_text(report: dict) -> str:
    lines = [f"TritFlow synthesis: {report['top']}", f"Total cells: {report['total_cells']}",
             "Cells: " + ", ".join(f"{cell}={count}" for cell, count in report["cells"].items()),
             f"Logic depth: {report['logic_depth']}",
             f"Maximum cell-pin fanout: {report['max_fanout']} (limit {report['fanout_limit']})",
             "Hierarchy (exclusive cell counts):"]
    for path, cells in report["hierarchy"].items():
        lines.append(f"  {path}: " + ", ".join(f"{cell}={n}" for cell, n in cells.items()))
    check = report["equivalence"]
    lines.append(f"Equivalence: PASS ({check['mode']}, {check['vectors']} vectors)" if check else "Equivalence: not checked")
    return "\n".join(lines) + "\n"


def write_artifacts(net, directory: str | Path, *, name: str | None = None) -> dict[str, Path]:
    """Write the shared JSON plus gate source, SPICE, JSON and text reports."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stem = name or net.top
    if Path(stem).name != stem or stem in {".", ".."}:
        raise ValueError("artifact name must be a filename without directory components")
    report = net.report()
    contents = {"json": net.to_json(), "gate.tv": tritverilog(net), "spice": spice(net),
                "report.json": json.dumps(report, indent=2) + "\n", "report.txt": report_text(report)}
    paths = {}
    for suffix, content in contents.items():
        paths[suffix] = directory / f"{stem}.{suffix}"
        paths[suffix].write_text(content)
    return paths
