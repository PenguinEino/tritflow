"""Programmable-dot4 wrapper in the unmodified 16-pad OpenSUSI OSS_FRAME.

ESD VDD is a separate +5 V terminal. ESD VSS, the common substrate and core
VSS are -5 V. Core VDD and VMID enter through ordinary ANA signal pads, as
in the author's AUDIO_OPAMP07 taped-out ternary circuit.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import time

import klayout.db as db

from tritflow import RAILS
from tritflow.netlist import GateNetlist
from .chip_frame_power import check_stock_currents, esd_leakage_check, stock_power
from .chip_router import ChipRouter
from .gds import DBU, box, wire_box
from .library import Library
from .signoff import _hash, _write
from .verify import PhysicalVerificationError, connectivity


def _pads(netlist):
    """Use the package's actual counterclockwise numbering and stock pad types."""
    inputs = [p.name for p in netlist.ports if p.dir == "input"]
    outputs = [p.name for p in netlist.ports if p.dir == "output"]
    if len(inputs) != 8 or len(outputs) != 2:
        raise ValueError(
            "OSS_FRAME dot4 allocation requires eight inputs and two outputs"
        )
    # Input names follow the synthesized HDL's port order: w0..w3, x0..x3.
    names = [
        "VDD",
        "VDD",
        inputs[5],
        inputs[4],
        inputs[3],
        inputs[2],
        inputs[0],
        "VSS",
        inputs[7],
        inputs[1],
        outputs[0],
        outputs[1],
        "VMID",
        inputs[6],
        "VDD",
        "ESD_VDD",
    ]
    centers = [
        (-200, 1040),
        (-600, 1040),
        (-1040, 600),
        (-1040, 200),
        (-1040, -200),
        (-1040, -600),
        (-600, -1040),
        (-200, -1040),
        (200, -1040),
        (600, -1040),
        (1040, -600),
        (1040, -200),
        (1040, 200),
        (1040, 600),
        (600, 1040),
        (200, 1040),
    ]
    pads = []
    for number, (net, (x, y)) in enumerate(zip(names, centers), 1):
        kind = "VSS" if number == 8 else "VDD" if number == 16 else "ANA"
        pads.append(
            {
                "pad": f"P{number:02d}",
                "frame_pin": kind if kind != "ANA" else f"P{number}",
                "net": net,
                "center_um": [float(x), float(y)],
                "type": "power" if net in (*RAILS, "ESD_VDD") else "signal",
                "master": f"OSS_ESD_5V_{kind}",
                "opening_um": [x - 40, y - 40, x + 40, y + 40],
            }
        )
    return pads


def frame_integrity(gds, frame_source):
    """Compare every stock-frame layer and text after hierarchy import."""
    source, actual = db.Layout(), db.Layout()
    source.read(str(frame_source))
    actual.read(str(gds))
    a, b = source.cell("OSS_FRAME"), actual.cell("OSS_FRAME")
    if a is None or b is None:
        return {"clean": False, "reason": "Missing OSS_FRAME"}
    differences, text_differences = {}, []
    for info in set(source.layer_infos()) | set(actual.layer_infos()):
        ar = db.Region(a.begin_shapes_rec(source.layer(info)))
        br = db.Region(b.begin_shapes_rec(actual.layer(info)))
        area = (ar ^ br).area() * source.dbu**2
        if area:
            differences[str(info)] = area

        def texts(cell, layer):
            items, it = [], cell.begin_shapes_rec(layer)
            while not it.at_end():
                if it.shape().is_text():
                    items.append(str(it.shape().text.transformed(it.trans())))
                it.next()
            return sorted(items)

        if texts(a, source.layer(info)) != texts(b, actual.layer(info)):
            text_differences.append(str(info))
    return {
        "clean": not differences and not text_differences,
        "xor_area_um2": differences,
        "text_differences": text_differences,
        "method": "Every layer and transformed text of the complete stock OSS_FRAME hierarchy",
    }


def stock_reference(netlist, library, path, top, pads):
    """Reference the stock frame's ESD MOS devices, following the PDK schematic.

    Port order and the 500/2 um PMOS/NMOSE clamps match OSS_FRAME.sch and
    OSS_ESD_5V_{ANA,VDD,VSS}.sch, also used in the organizer's Sanken .cir.
    This reference is independent of the extracted drawing netlist.
    """
    from tritflow.sim.spice import gate_spice
    from tritflow.synth.writers import spice_names

    mapping = spice_names(netlist.nets(), (*RAILS, "ESD_VDD", "0"))
    encoded = [mapping[p.name] for p in netlist.ports] + list(RAILS)
    by_pin = {p["frame_pin"]: mapping.get(p["net"], p["net"]) for p in pads}
    order = "P1 VDD P2 P15 P14 P3 P4 P13 P5 P12 P6 P11 P10 P7 P9 VSS".split()
    lines = [
        gate_spice(netlist, (Path(library.source) / "out/all.spice").read_text()),
        f".subckt {top} {' '.join(encoded)} ESD_VDD",
        f"Xmacro {' '.join(encoded)} {netlist.top}",
        f"Xframe {' '.join(by_pin[p] for p in order)} OSS_FRAME",
        f".ends {top}",
        "",
        "* Independent stock-frame reference: pinned TR-1um_frame Xschem schematics.",
        f".subckt OSS_FRAME {' '.join(order)}",
    ]
    for index, pin in enumerate(p for p in order if p not in ("VDD", "VSS")):
        lines.append(f"Xana{index+1} VDD {pin} VSS OSS_ESD_5V_ANA")
    lines += [
        "Xvdd VDD VSS OSS_ESD_5V_VDD",
        "Xvss VDD VSS OSS_ESD_5V_VSS",
        ".ends OSS_FRAME",
        ".subckt OSS_ESD_5V_ANA VDD PAD VSS",
        "M1 PAD VDD VDD VDD PMOS w=500u l=2u",
        "M2 PAD VSS VSS VSS NMOSE w=500u l=2u",
        ".ends OSS_ESD_5V_ANA",
        ".subckt OSS_ESD_5V_VDD VDD VSS",
        "M1 VSS VDD VDD VDD PMOS w=500u l=2u",
        "M2 VDD VSS VSS VSS NMOSE w=500u l=2u",
        ".ends OSS_ESD_5V_VDD",
        ".subckt OSS_ESD_5V_VSS VDD VSS",
        "M1 VSS VDD VDD VDD PMOS w=500u l=2u",
        "M2 VDD VSS VSS VSS NMOSE w=500u l=2u",
        ".ends OSS_ESD_5V_VSS",
        "",
    ]
    path.write_text("\n".join(lines))


def _notes(result):
    lines = [
        f"# {result.data['top']}",
        "",
        "Centered 2500 × 2500 µm die in the unmodified pinned PDK `OSS_FRAME`.",
        "The 16 stock pads include 14 `OSS_ESD_5V_ANA`, one ESD VDD and one ESD VSS.",
        "",
        "Core VDD = +5 V; VMID = 0 V; **ESD VSS = core VSS = substrate = −5 V**.",
        "**ESD VDD is a separate +5 V terminal: apply it before or together with core VDD.**",
        "Bond or probe all three core VDD pads; they join inside the die.",
        "ESD VDD and core VDD are electrically separate inside the chip.",
        "",
        "| Pad | Frame pin | Net | Pad cell | X (µm) | Y (µm) |",
        "|---|---|---|---|---:|---:|",
    ]
    for pad in result.data["pad_map"]:
        x, y = pad["center_um"]
        lines.append(
            f"| {pad['pad']} | {pad['frame_pin']} | {pad['net']} | {pad['master']} | {x:g} | {y:g} |"
        )
    lines += [
        "",
        "Remaining organizer steps:",
        "",
        "- Allocate a complete 2500 × 2500 µm slot for this top.",
        "- Agree the final bond diagram, including every supply bond and the VSS substrate.",
        "- Complete the submission metadata/reference package and run the organizer's final CI.",
        "",
        "Drawing DRC, strict device/port LVS including the ESD devices, MDP, mask DRC,",
        "the copied organizer precheck and the DC width/cut reserve are recorded separately.",
        "No post-MDP LVS stage is defined by the inspected organizer workflow.",
        "Current limits use conservative engineering width scaling; this is not lifetime EM qualification.",
        "",
    ]
    result.json_path.with_name("README.md").write_text("\n".join(lines))


def stock_chip(
    result,
    *,
    output_dir,
    top,
    library,
    pdk_root,
    klayout_binary,
    mpw_template,
    current_margin,
    timeout,
    force_signoff,
):
    """Build the fixed 8-input/2-output allocation and publish only a clean top."""
    from .chip import ChipResult, _shift_pin, _shift_wire, chip_signoff

    started = time.perf_counter()
    if not 0 <= current_margin < 1:
        raise ValueError("current_margin must be in [0, 1)")
    if result.data.get("library", {}).get("mock"):
        raise ValueError("Full-chip signoff requires real device cells")
    netlist = result.netlist or GateNetlist.load(
        Path(result.gds_path).with_suffix(".json")
    )
    library = library or Library.load(result.data["library"]["source"])
    if isinstance(library, (str, Path)):
        library = Library.load(library)
    pdk = Path(pdk_root).expanduser().resolve()
    frame_path = pdk / "libs.tech/klayout/libraries/TR-1um_frame_25x25.gds"
    top = top or f"tr_1um_{netlist.top}"
    if not top or any(c in top for c in "/\\") or top == netlist.top:
        raise ValueError("Chip top must be a safe name distinct from the macro")
    w, h = result.data["die"]
    if w > 1752 or h > 1206:
        raise ValueError(
            f"Macro {w:g} x {h:g} um does not fit the stock-frame channels"
        )
    pads = _pads(netlist)
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
        pad_map=pads,
    )
    for pl in data["placements"]:
        pl["x"] += dx
        pl["y"] += dy
    data["wires"] = [_shift_wire(v, dx, dy) for v in data["wires"]]
    data["vias"] = [{**v, "x": v["x"] + dx, "y": v["y"] + dy} for v in data["vias"]]
    for key in ("rails", "straps"):
        data["power"][key] = [_shift_wire(v, dx, dy) for v in data["power"][key]]
    data["power"]["vias"] = [
        {**v, "x": v["x"] + dx, "y": v["y"] + dy} for v in data["power"]["vias"]
    ]
    macro_pins = [_shift_pin(v, dx, dy) for v in result.data["power"]["pins"]]
    data["power"]["assumptions"]["reserved_current_margin"] = current_margin
    header = stock_power(data, macro_pins, core, current_margin)
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
    reference = db.Layout()
    reference.read(str(frame_path))
    frame = layout.create_cell("OSS_FRAME")
    frame.copy_tree(reference.cell("OSS_FRAME"))
    parent.insert(db.CellInstArray(frame.cell_index(), db.Trans()))
    routes = layout.create_cell(top + "__chip_wiring")
    parent.insert(db.CellInstArray(routes.cell_index(), db.Trans()))
    wires, vias, terminals = [], [], {}
    macro_signals = {p["name"]: _shift_pin(p, dx, dy) for p in result.data["pins"]}
    for pad in pads:
        net = pad["net"]
        if pad["type"] != "signal" and net != "VMID":
            continue
        px, py = pad["center_um"]
        # Every ANA pad has the stock 20 um M1 lead to the inner ring edge.
        # Extend that lead 30 um inward; no new cut is near its PRO opening.
        if abs(px) > abs(py):
            ex, ey = (900.0 if px > 0 else -900.0), py
            start = (930.0 if px > 0 else -930.0, py)
        else:
            ex, ey = px, (900.0 if py > 0 else -900.0)
            start = (px, 930.0 if py > 0 else -930.0)
        escape = {
            "net": net,
            "layer": "M1",
            "width": 3.4,
            "points": [list(start), [ex, ey]],
        }
        if net == "VMID":
            data["power"]["rails"].append(escape)
            data["power"]["rails"].append(
                {
                    "net": net,
                    "layer": "M1",
                    "width": 20.0,
                    "points": [[px, py], list(start)],
                    "existing": True,
                    "path": "stock_ANA_lead",
                }
            )
            data["power"]["straps"].append(
                {
                    "net": net,
                    "layer": "M2",
                    "width": 40.0,
                    "points": [[px - 20, py], [px + 20, py]],
                    "existing": True,
                    "path": "stock_ANA_pad",
                }
            )
            data["power"]["vias"].append(
                {"net": net, "x": px, "y": py, "existing": True}
            )
            data["power"]["pins"].append(
                {"name": net, "layer": "M2", "rect": [px - 1, py - 1, px + 1, py + 1]}
            )
            # Reach the right end of the VMID distribution bar on its own M2.
            by = header["bar_y_um"][net]
            bx = max(
                w["points"][1][0]
                for w in data["power"]["straps"]
                if w["net"] == net and not w.get("existing")
            )
            terminals[net] = [(1, bx, by), (0, ex, ey)]
        else:
            wires.append(escape)
            pin = macro_signals[net]
            a, b, c, d = pin["rect"]
            is_input = next(p.dir for p in netlist.ports if p.name == net) == "input"
            x, y = (dx + 3 if is_input else dx + w - 3), (b + d) / 2
            sx = dx - 12 if is_input else dx + w + 12
            wires.append(
                {"net": net, "layer": "M1", "width": 3.4, "points": [[x, y], [sx, y]]}
            )
            vias.append({"net": net, "x": x, "y": y})
            terminals[net] = [(0, sx, y), (0, ex, ey)]
    data["pins"] = [
        {
            "name": p["net"],
            "layer": "M2",
            "rect": [
                p["center_um"][0] - 1,
                p["center_um"][1] - 1,
                p["center_um"][0] + 1,
                p["center_um"][1] + 1,
            ],
        }
        for p in pads
        if p["type"] == "signal" or p["net"] == "ESD_VDD"
    ]
    shapes = []
    for wire in wires + data["power"]["rails"] + data["power"]["straps"]:
        rect = wire.get("rect", wire_box(wire))
        if (
            rect[0] < core[0]
            or rect[2] > core[2]
            or rect[1] < core[1]
            or rect[3] > core[3]
        ):
            shapes.append((0 if wire["layer"] == "M1" else 1, wire["net"], rect))
    router = ChipRouter(
        shapes,
        terminals,
        core,
        [],
        {n: 3.4 for n in terminals},
        bound=912.0,
        x_bound=912.0,
    )
    for name in sorted(
        terminals,
        key=lambda n: abs(terminals[n][0][1] - terminals[n][1][1])
        + abs(terminals[n][0][2] - terminals[n][1][2]),
        reverse=True,
    ):
        new_wires, new_vias = router.route(name)
        if name == "VMID":
            data["power"]["rails"] += [v for v in new_wires if v["layer"] == "M1"]
            data["power"]["straps"] += [v for v in new_wires if v["layer"] == "M2"]
            data["power"]["vias"] += new_vias
        else:
            wires += new_wires
            vias += new_vias
    data["wires"] += wires
    data["vias"] += vias
    for wire in (
        wires
        + data["power"]["rails"][len(result.data["power"]["rails"]) :]
        + data["power"]["straps"][len(result.data["power"]["straps"]) :]
    ):
        if not wire.get("existing"):
            routes.shapes(layout.layer(13 if wire["layer"] == "M1" else 20, 0)).insert(
                box(wire.get("rect", wire_box(wire)))
            )
    for via in vias + data["power"]["vias"][len(result.data["power"]["vias"]) :]:
        if via.get("existing"):
            continue
        x, y = round(via["x"], 3), round(via["y"], 3)
        via.update(x=x, y=y)
        routes.shapes(layout.layer(19, 0)).insert(
            box([x - 0.7, y - 0.7, x + 0.7, y + 0.7])
        )
        for layer in (13, 20):
            routes.shapes(layout.layer(layer, 0)).insert(
                box([x - 1.7, y - 1.7, x + 1.7, y + 1.7])
            )
    for pad in pads:
        x, y = pad["center_um"]
        parent.shapes(layout.layer(49, 0)).insert(
            db.Text(pad["net"], db.Trans(round(x / DBU), round(y / DBU)))
        )
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
        "cell": "OSS_FRAME",
        "modification": None,
        "pad_master": "OSS_ESD_5V_ANA",
        "pad_count": 16,
        "ESD": True,
        "stock_16_pin_package": True,
        "unmodified": True,
        "ESD_VDD_separate": True,
        "ESD_VDD_v": 5.0,
        "VSS_substrate_v": -5.0,
    }
    data["frame"]["dc_leakage"] = esd_leakage_check(out / "esd_dc", pdk)
    data["power_header"] = header
    data["signoff_options"] = {
        "pdk_root": str(pdk),
        "klayout_binary": str(klayout_binary) if klayout_binary else None,
        "mpw_template": (
            str(Path(mpw_template).expanduser().resolve()) if mpw_template else None
        ),
    }
    data["checks"] = {
        "connectivity": connectivity(candidate, data, netlist, library),
        "stock_frame": frame_integrity(candidate, frame_path),
    }
    try:
        data["power"]["dc_current_check"] = check_stock_currents(
            data, library, candidate
        )
    except Exception as error:
        candidate.replace(out / (top + ".failed.gds"))
        _write(out / (top + ".chip.failure.json"), {"top": top, "error": str(error)})
        _write(out / (top + ".chip.failed.json"), data)
        raise PhysicalVerificationError(
            f"Stock-frame current model failed: {error}"
        ) from error
    data["stats"] = {
        "die_size_um": [2500.0, 2500.0],
        "macro_size_um": [w, h],
        "pad_count": 16,
        "build_runtime_s": time.perf_counter() - started,
    }
    json_path, ref_path = out / (top + ".chip.json"), out / (top + ".cir")
    previous = {
        p: p.read_bytes() if p.exists() else None for p in (json_path, ref_path)
    }
    _write(json_path, data)
    stock_reference(netlist, library, ref_path, top, pads)
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
        if not report["clean"]:
            raise PhysicalVerificationError(
                f"Stock-frame qualification failed; inspect {report['summary_path']}"
            )
    except Exception:
        candidate.replace(out / (top + ".failed.gds"))
        for path, content in previous.items():
            if path.exists():
                path.with_name(path.name + ".failed").write_bytes(path.read_bytes())
            (
                path.unlink(missing_ok=True)
                if content is None
                else path.write_bytes(content)
            )
        raise
    published = out / (top + ".gds")
    candidate.replace(published)
    wrapped.gds_path = published
    wrapped.report = report
    report["gds_path"] = str(published)
    _write(Path(report["summary_path"]), report)
    data["stats"].update(
        signoff_runtime_s=report["runtime_s"],
        total_runtime_s=time.perf_counter() - started,
    )
    _write(json_path, data)
    _notes(wrapped)
    return wrapped
