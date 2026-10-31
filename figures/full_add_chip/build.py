"""Wrap Fig. 1's existing full-adder GDS in the unchanged stock OSS_FRAME.

Only this directory is writable. Runtime adapters specialize the dot4 pad map,
include spare ESD-loaded pads in the LVS reference, and extend the small macro's
VDD bar to the stock feeders. Native qualification functions remain unchanged.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOP = "tr_1um_full_add"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
os.environ.setdefault("TR1UM_PDK", str(Path.home() / "pdk/TR-1um-pinned"))
os.environ.setdefault(
    "NGSPICE_BINARY", str(Path.home() / ".local/opt/tritflow-ubuntu-24.04/bin/ngspice")
)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def full_adder_pads(netlist):
    """Keep three stock core-VDD pads and five independently unbonded ANA pads."""
    assert [(p.name, p.dir) for p in netlist.ports] == [
        ("a", "input"), ("b", "input"), ("cin", "input"),
        ("sum", "output"), ("cout", "output"),
    ]
    names = [
        "VDD", "VDD", "NC03", "cin", "b", "a", "NC07", "VSS",
        "NC09", "NC10", "sum", "cout", "VMID", "NC14", "VDD", "ESD_VDD",
    ]
    centers = [
        (-200, 1040), (-600, 1040), (-1040, 600), (-1040, 200),
        (-1040, -200), (-1040, -600), (-600, -1040), (-200, -1040),
        (200, -1040), (600, -1040), (1040, -600), (1040, -200),
        (1040, 200), (1040, 600), (600, 1040), (200, 1040),
    ]
    pads = []
    for number, (net, (x, y)) in enumerate(zip(names, centers), 1):
        kind = "VSS" if number == 8 else "VDD" if number == 16 else "ANA"
        pads.append({
            "pad": f"P{number:02d}",
            "frame_pin": kind if kind != "ANA" else f"P{number}",
            "net": net,
            "center_um": [float(x), float(y)],
            "type": ("unused" if net.startswith("NC") else "power"
                     if net in ("VDD", "VMID", "VSS", "ESD_VDD") else "signal"),
            "master": f"OSS_ESD_5V_{kind}",
            "opening_um": [x - 40, y - 40, x + 40, y + 40],
        })
    return pads


def adapters(frame):
    """Temporarily adapt allocation and wrapper geometry, never verification."""
    original_power = frame.stock_power
    original_reference = frame.stock_reference
    original_leakage = frame.esd_leakage_check

    def power(data, macro_pins, core, margin):
        header = original_power(data, macro_pins, core, margin)
        for wire in data["power"]["straps"]:
            if (wire["net"] == "VDD" and wire["points"][0][1] == header["bar_y_um"]["VDD"]
                    and wire["points"][1][1] == header["bar_y_um"]["VDD"]):
                wire["points"][0][0] = min(wire["points"][0][0], -620.0)
                wire["points"][1][0] = max(wire["points"][1][0], 620.0)
            if (wire["net"] == "VMID" and wire["points"][0][1] == header["bar_y_um"]["VMID"]
                    and wire["points"][1][1] == header["bar_y_um"]["VMID"]):
                # Escape on M2 beyond the VDD bar/feeder before turning down.
                wire["points"][1][0] = max(wire["points"][1][0], 654.0)
        return header

    def reference(netlist, library, path, top, pads):
        original_reference(netlist, library, path, top, pads)
        # Each spare pad is still a real terminal with two ESD MOS devices.
        # Expose it on the wrapper only; the five-port macro stays unchanged.
        spare = " ".join(p["net"] for p in pads if p["type"] == "unused")
        lines = path.read_text().splitlines()
        lines = [line + " " + spare if line.startswith(f".subckt {top} ") else line
                 for line in lines]
        path.write_text("\n".join(lines) + "\n")

    def leakage(output_dir, pdk):
        report = original_leakage(output_dir, pdk)
        report["scope"] = (
            "Ten non-supply ANA pads (five signals and five unbonded terminals) "
            "swept at -5/0/+5 V, three core-VDD ANA pads, one VMID ANA pad, and "
            "both rail clamps. No core current, package or transient model. "
            "This bounds spare-pad bias; it does not solve floating-pad voltage."
        )
        save(Path(output_dir) / "summary.json", report)
        return report

    stack = ExitStack()
    for name, value in (("_pads", full_adder_pads), ("stock_power", power),
                        ("stock_reference", reference), ("esd_leakage_check", leakage)):
        stack.enter_context(patch.object(frame, name, value))
    return stack


def macro_integrity(source_path, chip_path):
    """Compare every macro layer and label before and after hierarchy import."""
    import klayout.db as db

    source, chip = db.Layout(), db.Layout()
    source.read(str(source_path))
    chip.read(str(chip_path))
    differences, text_differences = {}, []
    for info in set(source.layer_infos()) | set(chip.layer_infos()):
        cells = [(layout.cell("full_add"), layout.layer(info)) for layout in (source, chip)]
        regions = [db.Region(cell.begin_shapes_rec(layer)) for cell, layer in cells]
        area = (regions[0] ^ regions[1]).area() * source.dbu**2
        if area:
            differences[str(info)] = area
        texts = []
        for cell, layer in cells:
            labels, iterator = [], cell.begin_shapes_rec(layer)
            while not iterator.at_end():
                if iterator.shape().is_text():
                    labels.append(str(iterator.shape().text.transformed(iterator.trans())))
                iterator.next()
            texts.append(sorted(labels))
        if texts[0] != texts[1]:
            text_differences.append(str(info))
    return {"clean": not differences and not text_differences,
            "xor_area_um2": differences, "text_differences": text_differences,
            "method": "Every layer and transformed text of the full_add hierarchy"}


def build(mpw_template):
    """Keep the source macro bytes intact and retain complete native evidence."""
    from tritflow import CELLS_DIR, PDK_ROOT
    from tritflow.netlist import GateNetlist
    from tritflow.pnr import PnrResult
    from tritflow.pnr import chip_frame

    pdk_commit = subprocess.check_output(
        ["git", "-C", str(PDK_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    pins = json.loads((ROOT / "notebook/setup_pins.json").read_text())
    if pdk_commit != pins["pdk_commit"]:
        raise ValueError("TR1UM_PDK must be the notebook's pinned public PDK")
    work = HERE / ".work"
    macro_dir, chip_dir = work / "macro", work / "chip"
    macro_dir.mkdir(parents=True, exist_ok=True)
    source_hashes = {}
    for suffix in ("gds", "json", "pnr.json"):
        source = ROOT / "build/full_add" / f"full_add.{suffix}"
        source_hashes[str(source.relative_to(ROOT))] = digest(source)
        shutil.copy2(source, macro_dir / source.name)
    data = json.loads((macro_dir / "full_add.pnr.json").read_text())
    # The copied P&R record names the old main worktree. Rebase only this local
    # record's library path; the original record and all macro geometry stay intact.
    original_library = data["library"]["source"]
    shutil.copy2(macro_dir / "full_add.pnr.json", macro_dir / "full_add.pnr.original.json")
    data["library"]["source"] = str(CELLS_DIR)
    save(macro_dir / "full_add.pnr.json", data)
    netlist = GateNetlist.load(macro_dir / "full_add.json")
    macro = PnrResult(macro_dir / "full_add.gds", macro_dir / "full_add.pnr.json",
                      data["stats"], data, netlist)
    save(HERE / "pad_map.json", full_adder_pads(netlist))
    print(f"Reusing {len(netlist.instances)} cells, {data['die']} um macro", flush=True)
    try:
        with adapters(chip_frame):
            full = macro.to_chip(
                frame="OSS_FRAME", output_dir=chip_dir, top=TOP,
                library=CELLS_DIR, pdk_root=PDK_ROOT,
                mpw_template=mpw_template, current_margin=0.2, force_signoff=True,
            )
    except Exception as error:
        # Even a failed qualification leaves the requested reviewable drawing.
        failed = chip_dir / f"{TOP}.failed.gds"
        if failed.exists():
            shutil.copy2(failed, HERE / f"{TOP}.gds")
        report_path = chip_dir / "signoff/signoff.summary.json"
        report = json.loads(report_path.read_text()) if report_path.exists() else None
        save(HERE / "summary.json", {
            "top": TOP, "clean": False, "error": str(error),
            "die_um": [2500, 2500], "pad_count": 16,
            "source_sha256": source_hashes, "native_report": report,
        })
        raise
    report = full.report
    same_macro = macro_integrity(macro.gds_path, full.gds_path)
    assert same_macro["clean"], same_macro
    for name, expected in source_hashes.items():
        assert digest(ROOT / name) == expected, f"Input changed: {name}"
    for path, name in (
        (full.gds_path, f"{TOP}.gds"),
        (full.gds_path.with_suffix(".cir"), f"{TOP}.cir"),
        (Path(report["mdp"]["output_path"]), f"{TOP}.ip62.gds"),
    ):
        shutil.copy2(path, HERE / name)
    save(HERE / "native_signoff.json", report)
    with ZipFile(HERE / "evidence.zip", "w", ZIP_DEFLATED) as archive:
        archive.write(__file__, "build.py")
        for folder in (macro_dir, chip_dir):
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(HERE))
    dc = report["dc_current_check"]
    summary = {
        "schema": "tritflow.figures.full_add_chip.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "top": TOP, "die_um": full.data["die"], "pad_count": 16,
        "ana_pad_count": 14, "macro_cells": len(netlist.instances),
        "macro_die_um": data["die"], "macro_rebuilt": False,
        "source_sha256": source_hashes, "build_script_sha256": digest(__file__),
        "original_library_path": original_library, "library_path": str(CELLS_DIR),
        "pdk_commit": pdk_commit, "pad_map": full.data["pad_map"],
        "macro_integrity": same_macro,
        "spare_pad_policy": "Unbonded, mutually isolated ANA terminals with stock ESD devices; all included in strict LVS",
        "drawing_drc": {k: report["drawing_drc"][k] for k in ("clean", "violations", "categories")},
        "drawing_lvs": {k: report["drawing_lvs"][k] for k in ("matched", "strict_ports", "errors", "unused_power_formals_restored")},
        "mask_drc": {k: report["mask_drc"][k] for k in ("clean", "violations", "categories")},
        "mdp": {k: report["mdp"][k] for k in ("exit_code", "metal_preservation", "full_die_metal_preservation")},
        "stock_frame_policy": report["stock_frame_policy"],
        "mpw_precheck": {k: report["mpw_precheck"][k] for k in ("clean", "exit_code")},
        "self_checks": report["self_checks"],
        "dc_current_check": {
            **{k: dc[k] for k in ("passed", "reserved_margin_met", "max_utilization", "margin_to_limit")},
            "required_reserve": 0.2,
            "per_supply": {rail: {k: values[k] for k in
                ("current_envelope_a", "max_utilization", "reserve")}
                for rail, values in dc["per_supply"].items()},
            "esd_leakage": {k: dc["esd_leakage"][k] for k in
                ("passed", "biases_v", "temperature_c", "max_total_absolute_current_a",
                 "conservative_budget_a_per_supply", "scope")},
        },
        "mask_lvs": report["mask_lvs"],
        "physical_checks_passed": report["physical_checks_passed"], "clean": report["clean"],
        "submission_ready": False, "reason": report["reason"],
        "gds_sha256": digest(HERE / f"{TOP}.gds"),
        "mask_gds_sha256": digest(HERE / f"{TOP}.ip62.gds"),
        "evidence_zip_sha256": digest(HERE / "evidence.zip"),
        "signoff_runtime_s": report["runtime_s"],
    }
    save(HERE / "summary.json", summary)
    print(json.dumps({k: summary[k] for k in ("clean", "drawing_drc", "drawing_lvs", "mask_drc", "mpw_precheck")}), flush=True)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mpw-template", type=Path, default=Path.home() / "TR-1um_MPW_Sanken")
    args = parser.parse_args()
    build(args.mpw_template.expanduser().resolve())
