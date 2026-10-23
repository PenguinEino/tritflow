"""Rebuild and publish the programmable dot4 in the pinned stock OSS_FRAME.

Use the brief's TR1UM_PDK and NGSPICE_BINARY environment. Only the organizer's
unchanged stock waivers/frame-only MDP delta are accepted. Native DRC items,
our waiver geometry, our MDP changes or insufficient current reserve fail.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
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
    """Qualify the real drawing and then replace the notebook's canonical snapshot."""
    from reuse import DEFAULT_SOURCE, DOT4_SOURCE
    from tritflow import PDK_ROOT, flow
    from tritflow.viz.layout import render_gds
    from frame_verify import verify

    if seed != 0:
        raise ValueError("The recorded programmable-dot4 macro uses seed 0")
    mpw_template = (
        Path(mpw_template or Path.home() / "TR-1um_MPW_Sanken").expanduser().resolve()
    )
    prior = json.loads((HERE / "provenance.json").read_text())
    with ZipFile(HERE / "evidence.zip") as archive:
        previous_macro_hash = sha256(archive.read(".work/macro/dot4.gds")).hexdigest()
    work = HERE / ".work"
    for folder in (work / "macro", work / "chip"):
        if folder.exists():
            shutil.rmtree(folder)
    circuit = flow.loads(DOT4_SOURCE)
    net = circuit.synthesize()
    assert net.report()["total_cells"] == 46
    layout = net.place_and_route(output_dir=work / "macro", seed=0, anneal_steps=600)
    assert digest(layout.gds_path) == previous_macro_hash, "Programmable macro changed"
    print(f"Same 46-cell seed-0 macro: {layout.stats['die_size_um']} um", flush=True)
    full = layout.result.to_chip(
        frame="OSS_FRAME",
        pdk_root=PDK_ROOT,
        klayout_binary=circuit.settings.klayout,
        output_dir=work / "chip",
        mpw_template=mpw_template,
        force_signoff=True,
    )
    report = full.report
    assert report["clean"] and report["drawing_lvs"]["strict_ports"]
    assert report["stock_frame_policy"]["clean"]
    print(
        "Stock drawing DRC / strict ESD LVS / owned-metal MDP / mask DRC / MPW / DC: PASS",
        flush=True,
    )
    (HERE / "dot4.tv").write_text(DOT4_SOURCE)
    (HERE / "dot4_fixed.tv").write_text(DEFAULT_SOURCE)
    (HERE / "dot4.json").write_text(net.to_json() + "\n")
    for source, name in (
        (full.gds_path, "tr_1um_dot4.gds"),
        (full.gds_path.with_suffix(".cir"), "tr_1um_dot4.cir"),
        (Path(report["mdp"]["output_path"]), "tr_1um_dot4.ip62.gds"),
    ):
        shutil.copy2(source, HERE / name)
    snapshot = {
        "schema": "tritflow.notebook.chip_snapshot.v1",
        "note": "Recorded programmable dot4; not re-executed in Colab.",
        "top": full.data["top"],
        "macro_seed": 0,
        "macro_cells": 46,
        "macro_die_um": layout.stats["die_size_um"],
        "macro_gds_sha256": previous_macro_hash,
        "pdk_commit": report["provenance"]["pdk_commit"],
        "frame": full.data["frame"],
        "die_um": [2500.0, 2500.0],
        "pad_count": 16,
        "pad_map": full.data["pad_map"],
        "port_directions": {p.name: p.dir for p in net.ports},
        "drawing_drc": {
            k: report["drawing_drc"][k] for k in ("clean", "violations", "categories")
        },
        "drawing_lvs": {
            k: report["drawing_lvs"][k] for k in ("matched", "strict_ports")
        },
        "mdp": {
            k: report["mdp"][k]
            for k in ("exit_code", "metal_preservation", "full_die_metal_preservation")
        },
        "mask_drc": {
            k: report["mask_drc"][k] for k in ("clean", "violations", "categories")
        },
        "mask_lvs": report["mask_lvs"],
        "stock_frame_policy": report["stock_frame_policy"],
        "drawing_audit": report["drawing_audit"],
        "mpw_precheck": {
            k: v for k, v in report["mpw_precheck"].items() if k != "log_path"
        },
        "dc_current_check": report["dc_current_check"],
        "dc_current_max_utilization": report["dc_current_check"]["max_utilization"],
        "dc_current_reserved_margin_met": report["dc_current_check"][
            "reserved_margin_met"
        ],
        "physical_checks_passed": report["physical_checks_passed"],
        "clean": report["clean"],
        "submission_ready": False,
        "reason": report["reason"],
        "gds_sha256": digest(HERE / "tr_1um_dot4.gds"),
        "mask_gds_sha256": digest(HERE / "tr_1um_dot4.ip62.gds"),
    }
    save("signoff.json", snapshot)
    save("native_signoff.json", report)
    save("pad_map.json", full.data["pad_map"])
    with ZipFile(HERE / "evidence.zip", "w", ZIP_DEFLATED) as archive:
        for folder in (work / "macro", work / "chip"):
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(HERE))
    render_gds(HERE / "tr_1um_dot4.gds", HERE / "tr_1um_dot4.png", top="tr_1um_dot4")
    verify(HERE)
    readme = (work / "chip/README.md").read_text()
    readme += "\n## Qualification scope\n\n"
    readme += (
        "The organizer's two stock 63/0 waiver polygons in `OSS_LOGO_TR` and `OSS_FRAME_CNR0` "
        "are preserved (union **63400 µm²**). There is **no TritFlow waiver geometry**, including inside the stock waiver area. "
        "The unchanged stock drawing and mask decks report **zero items**.\n\n"
        "An independent frame-only MDP run reproduces the stock logo's **0.001508 µm² M2 XOR**. "
        "CO/M1/V1 XOR is zero everywhere; M2 XOR is **exactly zero outside that stock delta and on all macro/routing/pad/power geometry**. "
        "This applies the integrator's binding stock-frame policy; the full-die XOR is recorded, not hidden.\n\n"
        "The programmable chapter 3–5 macro is byte-identical to the prior seed-0 GDS: **46 cells, 1692 × 1206 µm**. "
        "The fixed-weight edit (`dot4_fixed.tv`, 31 cells) remains a separate example.\n\n"
    )
    readme += "| Supply | Core current envelope (mA) | Minimum DC reserve |\n|---|---:|---:|\n"
    for rail, values in report["dc_current_check"]["per_supply"].items():
        readme += f"| {rail} | {1000*values['current_envelope_a']:.6g} | {100*values['reserve']:.4f}% |\n"
    readme += (
        "\nEvery supply path includes a 1 µA auxiliary leakage budget. The pinned ESD MPE/MNE three-bias "
        "ngspice check at 27 °C measures at most 0.542608 nA summed absolute current. The DC model "
        "includes the actual 14 µm slotted-ring lanes/bridges, stock pad fingers, every added feeder/TC and macro rails. "
        "All modeled rectangles/cuts are checked against the GDS. A stock 70 µm pad TC uses conservative "
        "minimum-width scaling from the published 1.4 µm rating; this is an explicit engineering interpretation.\n\n"
        "`native_signoff.json` and `evidence.zip` retain the native reports, independent stock-frame MDP, copied "
        "pinned decks and Sanken precheck/template, extracted device netlist, macro/chip metadata and reference. "
        "`provenance.json` hashes published artifacts, consumed qualification inputs and source files. "
        "The original Japanese helper archive remains for language-parity checking; its historical producer hashes "
        "are distinguished from the current sources.\n\n"
        "Rebuild with `python3 -B notebook/assets/chip/dot4/build.py --mpw-template ~/TR-1um_MPW_Sanken` "
        "using the brief's PDK/ngspice environment. `frame_verify.py` renders the KLayout PNG/legend and "
        "`shuttle_view()` in headless Chrome. Notebook call: `from reuse import shuttle_view; shuttle_view()`.\n"
    )
    (HERE / "README.md").write_text(readme)
    sources = [
        HERE / name
        for name in (
            "build.py",
            "verify.py",
            "frame_verify.py",
            "dot4.tv",
            "dot4_fixed.tv",
            "reuse_before_english.py",
        )
    ]
    sources += [ROOT / "notebook/reuse.py"] + list(
        (ROOT / "tritflow/pnr").glob("chip*.py")
    )
    artifacts = [
        p
        for p in HERE.iterdir()
        if p.is_file() and p.name != "provenance.json" and not p.name.startswith(".")
    ]
    save(
        "provenance.json",
        {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "project_commit": subprocess.run(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "pdk_commit": snapshot["pdk_commit"],
            "frame": full.data["frame"],
            "build_options": {
                "seed": 0,
                "anneal_steps": 600,
                "rows": None,
                "current_margin": 0.2,
                "frame": "OSS_FRAME",
                "mpw_template": str(mpw_template),
            },
            "stock_frame_policy": report["stock_frame_policy"],
            "qualification_inputs_sha256": report["inputs"],
            "pdk_rule_sha256": report["provenance"]["rule_sha256"],
            "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sources},
            "producer_source_sha256": prior.get("producer_source_sha256", {}),
            "producer_source_sha256_scope": "Historical pre-English helper archive only; current build sources are in source_sha256",
            "published_artifacts_sha256": {p.name: digest(p) for p in artifacts},
            "scope": "Stock-deck zero-item drawing/mask DRC; strict device/port LVS including frame ESD; own-waiver absence; exact MDP preservation outside independent stock-frame delta; DC envelope reserve. No mask LVS stage defined.",
        },
    )
    print(
        f"Published stock OSS_FRAME: 16 pads, DC reserve {100*(1-snapshot['dc_current_max_utilization']):.4f}%",
        flush=True,
    )
    return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mpw-template", type=Path, default=Path.home() / "TR-1um_MPW_Sanken"
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    build(args.mpw_template, args.seed)
