"""Optional 2.5 mm OpenSUSI chip wrappers with native qualification.

The legacy TEG allocation supports the existing full-adder callers and recorded
snapshots. ``frame="OSS_FRAME"`` selects the unchanged 16-pad ESD frame for the
eight-input/two-output dot4 allocation. Only the organizer's unmodified stock
frame waivers and independently reproduced frame-only MDP delta are accepted.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import klayout.db as db

from tritflow import PDK_ROOT, RAILS
from tritflow.netlist import GateNetlist
from .chip_router import ChipRouter
from .chip_power import _power_header
from .gds import DBU, box, wire_box
from .library import Library
from .power import dc_current_check
from .signoff import _drc, _hash, _layout_audit, _metal_preservation, _run, _write
from .verify import PhysicalVerificationError, connectivity


@dataclass
class ChipResult:
    """Separate full-chip artifacts; the original macro and SIM JSON stay intact."""

    gds_path: Path
    json_path: Path
    data: dict
    report: dict

    @property
    def stats(self):
        return self.data["stats"]

    def signoff(self, **options):
        """Revalidate the full-chip drawing, LVS, MDP, mask and MPW checks."""
        options = {**self.data.get("signoff_options", {}), **options}
        self.report = chip_signoff(self, **options)
        return self.report


def _shift_wire(wire, dx, dy):
    return {**wire, "points": [[x + dx, y + dy] for x, y in wire["points"]]}


def _shift_pin(pin, dx, dy):
    x0, y0, x1, y1 = pin["rect"]
    return {**pin, "rect": [x0 + dx, y0 + dy, x1 + dx, y1 + dy]}


def chip(
    result,
    *,
    output_dir=None,
    top=None,
    library=None,
    pdk_root=PDK_ROOT,
    klayout_binary=None,
    mpw_template=None,
    current_margin=0.2,
    timeout=180,
    force_signoff=False,
    frame="OSS_FRAME_TEG",
):
    """Wrap a verified macro in a custom, passive OpenSUSI TEG allocation.

    Every signal and each of VDD/VMID/VSS gets an independent real PDK pad.
    The 2500 x 2500 um centered frame uses the pinned PDK seal ring and pad
    primitive. The peripheral probe/bond map needs organizer/package approval;
    this API performs physical signoff, not submission or ESD qualification.
    A failed connectivity/DRC/LVS/mask check never publishes a canonical GDS.
    Use ``frame="OSS_FRAME"`` for the stock ESD frame's dot4 allocation; its
    ESD VDD is separate from core VDD and its ESD VSS is the common substrate.
    """
    if frame == "OSS_FRAME":
        from .chip_frame import stock_chip

        return stock_chip(
            result,
            output_dir=output_dir,
            top=top,
            library=library,
            pdk_root=pdk_root,
            klayout_binary=klayout_binary,
            mpw_template=mpw_template,
            current_margin=current_margin,
            timeout=timeout,
            force_signoff=force_signoff,
        )
    if frame != "OSS_FRAME_TEG":
        raise ValueError("frame must be OSS_FRAME or OSS_FRAME_TEG")
    started = time.perf_counter()
    if not 0 <= current_margin < 1:
        raise ValueError("current_margin must be in [0, 1)")
    if result.data.get("library", {}).get("mock"):
        raise ValueError("Full-chip signoff requires real device cells")
    netlist = getattr(result, "netlist", None)
    if netlist is None:
        netlist = GateNetlist.load(Path(result.gds_path).with_suffix(".json"))
    library = library or Library.load(result.data["library"]["source"])
    if isinstance(library, (str, Path)):
        library = Library.load(library)
    pdk = Path(pdk_root).expanduser().resolve()
    frame_path = pdk / "libs.tech/klayout/libraries/TR-1um_frame_25x25.gds"
    top = top or f"tr_1um_{netlist.top}"
    if not top or any(c in top for c in "/\\") or top == netlist.top:
        raise ValueError("Chip top must be a safe name distinct from the macro")
    w, h = result.data["die"]
    if w > 1850 or h > 1602:
        raise ValueError(
            f"Macro {w:g} x {h:g} um does not fit the TEG power/pad channels; try fewer rows, another seed or more annealing"
        )
    dx, dy = -w / 2, -h / 2
    core = [dx, dy, dx + w, dy + h]
    out = Path(output_dir or Path(result.gds_path).parent / "chip").resolve()
    out.mkdir(parents=True, exist_ok=True)
    data = copy.deepcopy(result.data)
    data.update(
        top=top,
        schema="tritflow.chip.v1",
        die=[2500.0, 2500.0],
        die_origin=[-1250.0, -1250.0],
    )
    data["placements"] = [
        {**p, "x": p["x"] + dx, "y": p["y"] + dy} for p in data["placements"]
    ]
    data["wires"] = [_shift_wire(v, dx, dy) for v in data["wires"]]
    data["vias"] = [{**v, "x": v["x"] + dx, "y": v["y"] + dy} for v in data["vias"]]
    macro_pins = [_shift_pin(v, dx, dy) for v in data["power"]["pins"]]
    for key in ("rails", "straps"):
        data["power"][key] = [_shift_wire(v, dx, dy) for v in data["power"][key]]
    data["power"]["vias"] = [
        {**v, "x": v["x"] + dx, "y": v["y"] + dy} for v in data["power"]["vias"]
    ]
    data["power"]["assumptions"]["reserved_current_margin"] = current_margin
    pads, power_header = _power_header(data, macro_pins, core, current_margin)
    # The circuit model and integer GDS must use the same 1 nm coordinates.
    for wire in data["power"]["rails"] + data["power"]["straps"]:
        wire["points"] = [[round(x, 3), round(y, 3)] for x, y in wire["points"]]
        if "rect" in wire:
            wire["rect"] = [round(v, 3) for v in wire["rect"]]
    for via in data["power"]["vias"]:
        via["x"], via["y"] = round(via["x"], 3), round(via["y"], 3)
    layout = db.Layout()
    layout.dbu = DBU
    parent = layout.create_cell(top)
    source = db.Layout()
    source.read(str(result.gds_path))
    macro = layout.create_cell(netlist.top)
    macro.copy_tree(source.cell(netlist.top))
    parent.insert(
        db.CellInstArray(macro.cell_index(), db.Trans(round(dx / DBU), round(dy / DBU)))
    )
    ref = db.Layout()
    ref.read(str(frame_path))
    frame = layout.create_cell("OSS_FRAME_TEG")
    frame.copy_tree(ref.cell("OSS_FRAME_TEG"))
    # Only the copied pad bank changes; the pinned seal-ring tree is preserved.
    for inst in list(frame.each_inst()):
        if layout.cell(inst.cell_index).name.startswith("OSS_PAD16"):
            inst.delete()
    pad = layout.create_cell("TRITFLOW_PROBE_PAD")
    pad.copy_tree(ref.cell("OSS_PAD_TEG"))
    parent.insert(db.CellInstArray(frame.cell_index(), db.Trans()))
    route_cell = layout.create_cell(top + "__chip_wiring")
    parent.insert(db.CellInstArray(route_cell.cell_index(), db.Trans()))
    shapes, terminals = [], {}
    macro_signal = {p["name"]: _shift_pin(p, dx, dy) for p in result.data["pins"]}
    wrapper_wires, wrapper_vias = [], []
    pads.append(("VMID", 0.0, -1100.0))
    data["power"]["straps"].append(
        {
            "net": "VMID",
            "layer": "M2",
            "width": 40.0,
            "points": [[0.0, -1050.0], [0.0, -1030.0]],
            "rect": [-20.0, -1050.0, 20.0, -1030.0],
        }
    )
    for offset in (-16.0, -8.0, 0.0, 8.0, 16.0):
        data["power"]["straps"].append(
            {
                "net": "VMID",
                "layer": "M2",
                "width": 8.0,
                "points": [[offset, -1100.0], [offset, -1032.0]],
            }
        )
    vx, vy = power_header["vmid_escape_um"]
    exit_y = round(core[3] + 30, 3)
    data["power"]["rails"].append(
        {"net": "VMID", "layer": "M1", "width": 3.4, "points": [[vx, vy], [vx, exit_y]]}
    )
    data["power"]["rails"].append(
        {
            "net": "VMID",
            "layer": "M1",
            "width": 3.4,
            "points": [[vx, exit_y], [-936.0, exit_y]],
        }
    )
    data["power"]["vias"] += [
        {"net": "VMID", "x": vx, "y": vy},
        {"net": "VMID", "x": -936.0, "y": exit_y},
    ]
    terminals["VMID"] = [(1, -936.0, exit_y), (1, 0.0, -1032.0)]
    for direction, px in (("input", -1020.0), ("output", 1020.0)):
        ports = [p for p in netlist.ports if p.dir == direction]
        if len(ports) > 13:
            raise ValueError(
                "TEG side supports at most 13 ports; use a multi-side pad assignment"
            )
        # Align each pad's vertical order with its macro access to avoid crossings.
        ports.sort(key=lambda p: sum(macro_signal[p.name]["rect"][1::2]) / 2)
        ys = []
        for port in ports:
            p = macro_signal[port.name]
            desired = (p["rect"][1] + p["rect"][3]) / 2
            ys.append(max(desired, ys[-1] + 150 if ys else -1000.0))
        ceiling = min(900.0, core[3] - 45.0)
        if ys and ys[-1] > ceiling:
            ys = [y - (ys[-1] - ceiling) for y in ys]
        if ys and ys[0] < -1000.0:
            raise ValueError(
                "Macro needs more vertical pad-access space; use more rows"
            )
        for port, py in zip(ports, ys):
            py = round(float(py), 3)
            pads.append((port.name, px, py))
            p = macro_signal[port.name]
            a, b, c, d = p["rect"]
            x = dx + 3 if direction == "input" else dx + w - 3
            y = (b + d) / 2
            ex = dx - 12 if direction == "input" else dx + w + 12
            wrapper_wires.append(
                {
                    "net": port.name,
                    "layer": "M1",
                    "width": 3.4,
                    "points": [[x, y], [ex, y]],
                }
            )
            wrapper_vias.append({"net": port.name, "x": x, "y": y})
            sign = 1 if px < 0 else -1
            neck = [px + sign * 50, py - 20, px + sign * 70, py + 20]
            neck = [min(neck[0], neck[2]), neck[1], max(neck[0], neck[2]), neck[3]]
            wrapper_wires.append(
                {
                    "net": port.name,
                    "layer": "M1",
                    "width": 40.0,
                    "points": [[px + sign * 50, py], [px + sign * 70, py]],
                    "rect": neck,
                }
            )
            terminals[port.name] = [(0, ex, y), (0, px + sign * 68, py)]
    for name, x, y in pads:
        frame.insert(
            db.CellInstArray(pad.cell_index(), db.Trans(round(x / DBU), round(y / DBU)))
        )
        for layer in (0, 1):
            shapes.append((layer, name, [x - 50, y - 50, x + 50, y + 50]))
    data["pins"] = [
        {"name": n, "layer": "M2", "rect": [x - 50, y - 50, x + 50, y + 50]}
        for n, x, y in pads
        if n not in RAILS
    ]
    data["power"]["pins"] = [
        {
            "name": n,
            "layer": "M2",
            "rect": [x + offset - 2, y - 2, x + offset + 2, y + 2],
        }
        for n, x, y in pads
        if n in RAILS
        for offset in (-16.0, -8.0, 0.0, 8.0, 16.0)
    ]
    for wire in wrapper_wires + data["power"]["rails"] + data["power"]["straps"]:
        rect = wire.get("rect", wire_box(wire))
        if (
            rect[0] < core[0]
            or rect[2] > core[2]
            or rect[1] < core[1]
            or rect[3] > core[3]
        ):
            shapes.append((0 if wire["layer"] == "M1" else 1, wire["net"], rect))
    router = ChipRouter(shapes, terminals, core, pads, {n: 3.4 for n in terminals})
    for name in sorted(
        terminals,
        key=lambda n: abs(terminals[n][0][2] - terminals[n][1][2]),
        reverse=True,
    ):
        wires, vias = router.route(name)
        if name == "VMID":
            data["power"]["rails"] += [w for w in wires if w["layer"] == "M1"]
            data["power"]["straps"] += [w for w in wires if w["layer"] == "M2"]
            data["power"]["vias"] += vias
        else:
            wrapper_wires += wires
            wrapper_vias += vias
    data["wires"] += wrapper_wires
    data["vias"] += wrapper_vias
    for wire in (
        wrapper_wires
        + data["power"]["rails"][len(result.data["power"]["rails"]) :]
        + data["power"]["straps"][len(result.data["power"]["straps"]) :]
    ):
        route_cell.shapes(layout.layer(13 if wire["layer"] == "M1" else 20, 0)).insert(
            box(wire.get("rect", wire_box(wire)))
        )
    # Power cuts were appended after the translated original macro cuts.
    new_power_vias = data["power"]["vias"][len(result.data["power"]["vias"]) :]
    for via in wrapper_vias + new_power_vias:
        x, y = via["x"], via["y"]
        route_cell.shapes(layout.layer(19, 0)).insert(
            box([x - 0.7, y - 0.7, x + 0.7, y + 0.7])
        )
        for layer in (13, 20):
            route_cell.shapes(layout.layer(layer, 0)).insert(
                box([x - 1.7, y - 1.7, x + 1.7, y + 1.7])
            )
    for n, x, y in pads:
        parent.shapes(layout.layer(49, 0)).insert(
            db.Text(n, db.Trans(round(x / DBU), round(y / DBU)))
        )
    for unused in [
        c.cell_index()
        for c in layout.top_cells()
        if c.cell_index() != parent.cell_index()
    ]:
        if layout.is_valid_cell_index(unused):
            layout.prune_cell(unused, -1)
    candidate = out / (top + ".candidate.gds")
    options = db.SaveLayoutOptions()
    options.gds2_write_timestamps = False
    layout.write(str(candidate), options)
    data["macro"] = {
        "top": netlist.top,
        "netlist": json.loads(netlist.to_json()),
        "gds_path": str(Path(result.gds_path).resolve()),
        "gds_sha256": _hash(result.gds_path),
        "pnr_json": str(Path(result.json_path).resolve()),
        "origin_um": [dx, dy],
        "bbox_um": core,
    }
    data["frame"] = {
        "source": str(frame_path),
        "sha256": _hash(frame_path),
        "cell": "OSS_FRAME_TEG",
        "modification": "Peripheral OSS_PAD_TEG instances replace the copied OSS_PAD16 bank; unchanged pinned seal ring",
        "pad_master": "OSS_PAD_TEG",
        "pad_count": len(pads),
        "ESD": False,
        "stock_16_pin_package": False,
    }
    data["pad_map"] = [
        {
            "pad": f"P{i:02d}",
            "net": n,
            "center_um": [x, y],
            "type": "power" if n in RAILS else "signal",
            "opening_um": [x - 40, y - 40, x + 40, y + 40],
        }
        for i, (n, x, y) in enumerate(pads, 1)
    ]
    data["power_header"] = power_header
    data["signoff_options"] = {
        "pdk_root": str(pdk),
        "klayout_binary": str(klayout_binary) if klayout_binary else None,
        "mpw_template": str(Path(mpw_template).resolve()) if mpw_template else None,
    }
    data["checks"] = {"connectivity": connectivity(candidate, data, netlist, library)}
    try:
        data["power"]["dc_current_check"] = dc_current_check(data, library)
    except Exception as error:
        failed = out / (top + ".failed.gds")
        candidate.replace(failed)
        failure = out / (top + ".chip.failure.json")
        _write(failure, {"top": top, "error": str(error), "failed_gds": str(failed)})
        raise PhysicalVerificationError(
            f"Chip power-network check failed; inspect {failure}"
        ) from error
    data["stats"] = {
        "die_size_um": [2500.0, 2500.0],
        "macro_size_um": [w, h],
        "pad_count": len(pads),
        "build_runtime_s": time.perf_counter() - started,
    }
    json_path = out / (top + ".chip.json")
    reference_path = out / (top + ".cir")
    previous_exports = {
        path: path.read_bytes() if path.exists() else None
        for path in (json_path, reference_path)
    }
    _write(json_path, data)
    _reference(netlist, library, reference_path, top)
    wrapped = ChipResult(candidate, json_path, data, {})
    try:
        report = chip_signoff(
            wrapped,
            pdk_root=pdk,
            klayout_binary=klayout_binary,
            mpw_template=mpw_template,
            timeout=timeout,
            force=force_signoff,
        )
        wrapped.report = report
        if not report["clean"]:
            raise PhysicalVerificationError(
                f'Chip qualification failed; inspect {report["summary_path"]}'
            )
    except Exception:
        failed = out / (top + ".failed.gds")
        candidate.replace(failed)
        for path, previous in previous_exports.items():
            if path.exists():
                shutil.copy2(path, path.with_name(path.name + ".failed"))
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(previous)
        raise
    published = out / (top + ".gds")
    candidate.replace(published)
    wrapped.gds_path = published
    report["gds_path"] = str(published)
    _write(Path(report["summary_path"]), report)
    data["stats"].update(
        signoff_runtime_s=report["runtime_s"],
        total_runtime_s=time.perf_counter() - started,
    )
    _write(json_path, data)
    _submission_notes(wrapped)
    return wrapped


def _reference(netlist, library, path, top):
    from tritflow.sim.spice import gate_spice
    from tritflow.synth.writers import spice_names

    # Preserve synthesis's reversible encoding annotations on all wrapper ports.
    mapping = spice_names(netlist.nets(), (*RAILS, "0"))
    encoded = [mapping[p.name] for p in netlist.ports] + list(RAILS)
    reference = gate_spice(
        netlist, (Path(library.source) / "out/all.spice").read_text()
    )
    reference += (
        "\n.subckt "
        + top
        + " "
        + " ".join(encoded)
        + "\nXmacro "
        + " ".join(encoded)
        + " "
        + netlist.top
        + "\n.ends "
        + top
        + "\n"
    )
    path.write_text(reference)


def chip_signoff(
    result,
    *,
    pdk_root=PDK_ROOT,
    klayout_binary=None,
    mpw_template=None,
    timeout=180,
    force=False,
):
    """Unmodified pinned drawing/LVS, MDP and mask decks, all items counted."""
    from tritflow.extract import extract_layout

    started = time.perf_counter()
    source = Path(result.gds_path).resolve()
    top = result.data["top"]
    out = source.parent / "signoff"
    out.mkdir(exist_ok=True)
    pdk = Path(pdk_root).expanduser().resolve()
    binary = Path(
        klayout_binary
        or os.environ.get("KLAYOUT_BINARY")
        or shutil.which("klayout")
        or Path.home() / "bin/klayout/klayout"
    ).resolve()
    files = [
        source.parent / (top + ".cir"),
        binary,
        Path(__file__),
        Path(__file__).with_name("chip_router.py"),
    ]
    files += [
        Path(__file__).with_name(name)
        for name in ("chip_power.py", "signoff.py", "power.py", "verify.py")
    ]
    stock = result.data["frame"]["cell"] == "OSS_FRAME"
    if stock:
        files += [
            Path(__file__).with_name(name)
            for name in ("chip_frame.py", "chip_frame_power.py", "chip_frame_audit.py")
        ]
        files += [Path(result.data["frame"]["source"])]
        files += list((pdk / "libs.tech/xschem/TR-1um_frame").glob("*.sch"))
        files += list((pdk / "libs.tech/spice/models").glob("*"))
        files += list((source.parent / "esd_dc").glob("*"))
    files += [
        p
        for group in ("drc", "lvs")
        for p in (pdk / "libs.tech/klayout/tech" / group).rglob("*")
        if p.is_file()
    ]
    cells = Path(result.data["library"]["source"])
    files += [cells / "template.json", cells / "out/all.spice"]
    files += list((cells / "out").glob("*/*.abstract.json")) + list(
        (cells / "out").glob("*/*.char.json")
    )
    if mpw_template:
        files += [
            Path(mpw_template) / p
            for p in (
                "scripts/pre_check.py",
                ".github/workflows/check.yml",
                "info.yaml",
            )
        ]
    inputs = {str(p.resolve()): _hash(p) for p in files}
    model = {k: v for k, v in result.data.items() if k != "stats"}
    fingerprint = hashlib.sha256(
        json.dumps(
            {"source": _hash(source), "inputs": inputs, "model": model}, sort_keys=True
        ).encode()
    ).hexdigest()
    summary = out / "signoff.summary.json"
    if summary.exists() and not force:
        previous = json.loads(summary.read_text())
        if previous.get("fingerprint") == fingerprint and previous.get("artifacts"):
            try:
                if all(_hash(p) == h for p, h in previous["artifacts"].items()):
                    return {**previous, "cache_hit": True, "gds_path": str(source)}
            except FileNotFoundError:
                pass
    # A new source gets a new proof directory. A failed requalification cannot
    # erase the previous mask/LVS evidence or the published canonical chip.
    out = out / "runs" / fingerprint[:16]
    out.mkdir(parents=True, exist_ok=True)
    if (out / "pdk").exists():
        shutil.rmtree(out / "pdk")
    for group in ("drc", "lvs"):
        shutil.copytree(
            pdk / "libs.tech/klayout/tech" / group,
            out / "pdk/libs.tech/klayout/tech" / group,
            dirs_exist_ok=True,
        )
    drawing = out / (top + ".drawing.gds")
    shutil.copy2(source, drawing)
    deck = out / "pdk/libs.tech/klayout/tech/drc"
    drc = _drc(binary, deck / "run.drc", drawing, top, out, "drawing_drc", timeout)
    lvs = extract_layout(
        drawing,
        top,
        out / "lvs",
        reference=source.parent / (top + ".cir"),
        pdk=out / "pdk",
        executable=binary,
        timeout=timeout,
    )
    lvs.pop("log", None)
    mask = out / (top + ".ip62.gds")
    mask.unlink(missing_ok=True)
    mdp = _run(
        [
            binary,
            "-b",
            "-r",
            deck / "run_mdp.drc",
            "-rd",
            f"input={drawing}",
            "-rd",
            f"cellname={top}",
            "-rd",
            f"output={mask}",
        ],
        out,
        "mdp",
        timeout,
    )
    if mdp["exit_code"] or not mask.exists():
        raise RuntimeError(f'MDP failed; inspect {mdp["log_path"]}')
    mdp.update(
        output_path=str(mask),
        metal_preservation=_metal_preservation(drawing, mask, top),
    )
    mask_drc = _drc(binary, deck / "run_IP62.drc", mask, top, out, "mask_drc", timeout)
    audit = _layout_audit(drawing, top)
    stock_policy = None
    if stock:
        from .chip_frame_audit import stock_frame_policy

        # Run the same pinned MDP on the stock hierarchy alone. A matching
        # frame delta is recorded; any extra change or any owned waiver fails.
        original_frame = db.Layout()
        original_frame.read(result.data["frame"]["source"])
        isolated = db.Layout()
        isolated.dbu = original_frame.dbu
        isolated.create_cell("OSS_FRAME").copy_tree(original_frame.cell("OSS_FRAME"))
        frame_drawing, frame_mask = (
            out / "stock_frame.gds",
            out / "stock_frame.ip62.gds",
        )
        isolated.write(str(frame_drawing))
        frame_run = _run(
            [
                binary,
                "-b",
                "-r",
                deck / "run_mdp.drc",
                "-rd",
                f"input={frame_drawing}",
                "-rd",
                "cellname=OSS_FRAME",
                "-rd",
                f"output={frame_mask}",
            ],
            out,
            "stock_frame_mdp",
            timeout,
        )
        if frame_run["exit_code"] or not frame_mask.exists():
            raise RuntimeError(
                f"Stock frame MDP failed; inspect {frame_run['log_path']}"
            )
        stock_policy = stock_frame_policy(drawing, mask, top, frame_drawing, frame_mask)
        mdp["full_die_metal_preservation"] = mdp["metal_preservation"]
        mdp["metal_preservation"] = stock_policy["metal_preservation"]
        mdp["stock_frame_mdp"] = frame_run
        audit["stock_waivers"] = stock_policy["stock_waivers"]
    library = Library.load(result.data["library"]["source"])
    netlist = GateNetlist.from_dict(result.data["macro"]["netlist"])
    own = {"connectivity": connectivity(drawing, result.data, netlist, library)}
    if stock:
        from .chip_frame import frame_integrity
        from .chip_frame_power import check_stock_currents

        own["stock_frame"] = frame_integrity(drawing, result.data["frame"]["source"])
        dc = check_stock_currents(result.data, library, drawing)
    else:
        dc = dc_current_check(result.data, library)
    precheck = {
        "clean": audit["bbox_um"] == [-1250.0, -1250.0, 1250.0, 1250.0]
        and audit["top_cells"] == [top]
        and audit["dbu_um"] == 0.001
        and bool(audit["frame_cells"]),
        "method": "MPW fixed 2.5 mm centered die, DBU and frame checks",
    }
    if mpw_template:
        directory = out
        if stock:
            directory = out / "mpw_template"
            shutil.copytree(
                Path(mpw_template).expanduser(),
                directory,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
                dirs_exist_ok=True,
            )
            copied = directory / "scripts/pre_check.py"
            local_drawing = directory / "src" / (top + ".gds")
            shutil.copy2(drawing, local_drawing)
        else:
            copied = out / "pre_check.py"
            shutil.copy2(Path(mpw_template) / "scripts/pre_check.py", copied)
            local_drawing = drawing
        precheck = _run(
            [sys.executable, copied, "--top", top, local_drawing],
            directory,
            "mpw_precheck",
            timeout,
        )
        precheck["clean"] = precheck["exit_code"] == 0
        if stock:
            precheck["template_copy"] = str(directory)
            precheck["drawing_sha256"] = _hash(local_drawing)
    physical = (
        drc["clean"]
        and lvs["matched"]
        and mask_drc["clean"]
        and precheck["clean"]
        and own["connectivity"]["clean"]
        and own.get("stock_frame", {"clean": True})["clean"]
        and (
            stock_policy["stock_waivers"]["clean"]
            if stock
            else not audit["waiver_polygon_count"]
        )
        and mdp["metal_preservation"]["clean"]
    )
    clean = physical and dc.get("reserved_margin_met", False)
    commit = subprocess.run(
        ["git", "-C", str(pdk), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    report = {
        "schema": "tritflow.chip.signoff.v1",
        "clean": bool(clean),
        "physical_checks_passed": bool(physical),
        "cache_hit": False,
        "fingerprint": fingerprint,
        "inputs": inputs,
        "submission_ready": False,
        "reason": (
            "Organizer allocation of a full 2500 um slot, final bond diagram and final CI remain"
            if stock
            else "Custom TEG pad/bond allocation and ESD/power/package approval still required"
        ),
        "top": top,
        "gds_path": str(source),
        "drawing_drc": drc,
        "drawing_lvs": lvs,
        "mdp": mdp,
        "mask_drc": mask_drc,
        "stock_frame_policy": stock_policy,
        "drawing_audit": audit,
        "mpw_precheck": precheck,
        "self_checks": own,
        "dc_current_check": dc,
        "mask_lvs": {
            "defined": False,
            "matched": None,
            "reason": "Inspected MPW workflow defines drawing LVS before MDP; no post-MDP LVS stage",
        },
        "provenance": {
            "pdk_root": str(pdk),
            "pdk_commit": commit.stdout.strip() if commit.returncode == 0 else None,
            "frame": result.data["frame"],
            "rule_sha256": {
                str(p.relative_to(out / "pdk")): _hash(p)
                for p in (out / "pdk").rglob("*")
                if p.is_file()
            },
            "binary_sha256": _hash(binary),
            "source_sha256": _hash(source),
        },
        "runtime_s": time.perf_counter() - started,
        "summary_path": str(summary),
    }
    if stock and not physical:
        report["reason"] = (
            "Stock-frame qualification failed; inspect native reports, frame integrity, owned-waiver and owned-metal audits"
        )
    if any(_hash(p) != h for p, h in inputs.items()):
        raise RuntimeError(
            "Chip signoff inputs changed during qualification; rerun after publication settles"
        )
    report["artifacts"] = {
        str(p): _hash(p) for p in out.rglob("*") if p.is_file() and p != summary
    }
    _write(summary, report)
    return report


def _submission_notes(result):
    """Give a chip reviewer its actual terminals and the remaining shuttle work."""
    lines = [
        f"# {result.data['top']}",
        "",
        "Centered 2500 × 2500 µm OpenSUSI TEG allocation. The pinned seal ring is unchanged;",
        "the copied pad bank is replaced by genuine OSS_PAD_TEG peripheral pads.",
        "Drawing DRC, strict LVS, MDP and mask DRC reports are in signoff/.",
        "",
        "VDD = +5 V; VMID = 0 V; VSS/common substrate = −5 V.",
        "Bond or probe **every supply pad** in its domain; the current reserve assumes all are powered.",
        "The original macro and its power JSON are unchanged.",
        "",
        "| Pad | Net | X (µm) | Y (µm) |",
        "|---|---|---:|---:|",
    ]
    for pad in result.data["pad_map"]:
        x, y = pad["center_um"]
        lines.append(f"| {pad['pad']} | {pad['net']} | {x:g} | {y:g} |")
    lines += [
        "",
        "Before a real submission:",
        "",
        "- Obtain the organizer's allocation and approval for this custom pad/probe map; it is not the stock 16-pin package.",
        "- Agree the bond diagram, die attach/common substrate at VSS, all supply bonds and external VMID reference.",
        "- Obtain process/ESD approval for the accepted ±5 V operating condition. These passive TEG pads add no ESD network.",
        "- Simulate the full chip with package/probe loading and supply impedances; DC width/cut reserve is not lifetime EM signoff.",
        "- Complete the shuttle info.yaml, project licence/metadata and schematic/reference package, using this top name and final PDK revision; run the organizer's final CI.",
        "- Review the complete mask GDS and electrical results with the shuttle owner. No submission/upload is performed by TritFlow.",
        "",
        "The inspected MPW flow specifies drawing LVS before MDP, and no post-MDP LVS stage.",
        "",
    ]
    result.json_path.with_name("README.md").write_text("\n".join(lines))
