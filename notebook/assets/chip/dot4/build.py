"""Rebuild the recorded programmable dot4 MPW-frame top with pinned PDK decks.

Run from any directory with the published real cells and the project installed:
``TR1UM_PDK=~/pdk/TR-1um-pinned python3 notebook/assets/chip/dot4/build.py``.
The optional ``--mpw-template`` executes the organizer's actual precheck on a
local copy. All generated files stay beneath this script's directory.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "notebook")]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def build(mpw_template=None, seed=0):
    """Use the existing verified chip API; publish only after every check passes."""
    from reuse import DEFAULT_SOURCE, DOT4_SOURCE
    from tritflow import PDK_ROOT, flow

    work = HERE / ".work"
    for folder in (work / "macro", work / "chip"):
        if folder.exists():
            shutil.rmtree(folder)
    circuit = flow.loads(DOT4_SOURCE)
    net = circuit.synthesize()
    print(f"Synthesis: {net.report()['total_cells']} cells", flush=True)
    layout = net.place_and_route(output_dir=work / "macro", seed=seed)
    print(f"Macro: {layout.stats['die_size_um']} um", flush=True)
    full = layout.result.to_chip(pdk_root=PDK_ROOT, klayout_binary=circuit.settings.klayout,
                                 output_dir=work / "chip", mpw_template=mpw_template,
                                 force_signoff=True)
    report = full.report
    if not (report["clean"] and report["drawing_lvs"]["strict_ports"]):
        raise RuntimeError("Dot4 chip did not pass strict physical qualification")
    print("Drawing DRC / strict LVS / MDP / mask DRC / MPW: PASS", flush=True)
    (HERE / "dot4.tv").write_text(DOT4_SOURCE)
    (HERE / "dot4_fixed.tv").write_text(DEFAULT_SOURCE)
    (HERE / "dot4.json").write_text(net.to_json() + "\n")
    for source, name in ((full.gds_path, "tr_1um_dot4.gds"),
                         (full.gds_path.with_suffix(".cir"), "tr_1um_dot4.cir"),
                         (Path(report["mdp"]["output_path"]), "tr_1um_dot4.ip62.gds")):
        shutil.copy2(source, HERE / name)
    pad_map = full.data["pad_map"]
    save("pad_map.json", pad_map)
    snapshot = {
        "schema": "tritflow.notebook.chip_snapshot.v1", "note": "Recorded programmable dot4; not re-executed in Colab.",
        "top": full.data["top"], "macro_seed": seed, "macro_cells": net.report()["total_cells"],
        "macro_die_um": layout.stats["die_size_um"], "pdk_commit": report["provenance"]["pdk_commit"],
        "die_um": [2500.0, 2500.0], "pad_count": len(pad_map), "pad_map": pad_map,
        "port_directions": {p.name: p.dir for p in net.ports},
        "drawing_drc": {k: report["drawing_drc"][k] for k in ("clean", "violations", "categories")},
        "drawing_lvs": {k: report["drawing_lvs"][k] for k in ("matched", "strict_ports")},
        "mdp": {k: report["mdp"][k] for k in ("exit_code", "metal_preservation")},
        "mask_drc": {k: report["mask_drc"][k] for k in ("clean", "violations", "categories")},
        "mask_lvs": report["mask_lvs"],
        "mpw_precheck": {k: v for k, v in report["mpw_precheck"].items() if k not in ("log_path",)},
        "drawing_audit": report["drawing_audit"],
        "dc_current_max_utilization": report["dc_current_check"]["max_utilization"],
        "dc_current_reserved_margin_met": report["dc_current_check"]["reserved_margin_met"],
        "physical_checks_passed": report["physical_checks_passed"], "clean": report["clean"],
        "submission_ready": report["submission_ready"], "reason": report["reason"],
        "gds_sha256": digest(HERE / "tr_1um_dot4.gds"), "mask_gds_sha256": digest(HERE / "tr_1um_dot4.ip62.gds"),
    }
    save("signoff.json", snapshot)
    # Keep the original paths in the native record: the archive contains the
    # corresponding .work tree, so each report can be traced without rerunning.
    with ZipFile(HERE / "evidence.zip", "w", ZIP_DEFLATED) as archive:
        for folder in (work / "macro", work / "chip"):
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(HERE))
    save("provenance.json", {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "project_commit": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                          check=True, capture_output=True, text=True).stdout.strip(),
        "pdk_commit": snapshot["pdk_commit"], "frame": full.data["frame"],
        "build_options": {"seed": seed, "anneal_steps": 600, "rows": None, "current_margin": 0.2,
                          "mpw_template": str(mpw_template) if mpw_template else None},
        "qualification_inputs_sha256": report["inputs"], "pdk_rule_sha256": report["provenance"]["rule_sha256"],
        "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in
                          [HERE / "build.py", HERE / "verify.py", ROOT / "notebook/reuse.py", HERE / "dot4.tv", HERE / "dot4_fixed.tv"]},
        "published_artifacts_sha256": {p.name: digest(p) for p in
                                       [HERE / n for n in ("dot4.json", "pad_map.json", "signoff.json", "evidence.zip",
                                                           "tr_1um_dot4.gds", "tr_1um_dot4.cir", "tr_1um_dot4.ip62.gds")]},
        "scope": "Device/port LVS on drawing; unmodified pinned drawing and mask decks; no mask LVS stage defined.",
    })
    readme = (work / "chip/README.md").read_text()
    readme += ("\n## Recorded notebook snapshot\n\n"
               "The macro is the programmable chapter 3–5 dot4 (46 cells), with eight independent input trits and two output trits. "
               "The editable fixed-weight example is separate (`dot4_fixed.tv`, 31 cells).\n\n"
               "`signoff.json` and `provenance.json` describe this snapshot; `evidence.zip` contains the original macro, "
               "chip JSON/reference, copied rule decks, native reports/logs, extracted SPICE, drawing and mask GDS. "
               "The frame is an unchanged pinned seal ring with genuine peripheral OSS_PAD_TEG probe pads.\n\n"
               "Rebuild with `TR1UM_PDK=~/pdk/TR-1um-pinned python3 notebook/assets/chip/dot4/build.py "
               "--mpw-template ~/TR-1um_MPW_Sanken`. All generated files remain in this directory.\n\n"
               "Notebook view: `from reuse import shuttle_view; shuttle_view()`. This opens the recorded GDS and "
               "the pad table without rerunning qualification.\n")
    (HERE / "README.md").write_text(readme)
    print(f"Snapshot: {len(pad_map)} pads, DC reserve {100 * (1 - snapshot['dc_current_max_utilization']):.2f}%", flush=True)
    return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mpw-template", type=Path)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    build(args.mpw_template, args.seed)
