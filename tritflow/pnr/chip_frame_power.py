"""Stock-frame supply paths, including the slotted VSS ring and bond pads.

The resistor network retains the macro's existing current-envelope assumptions.
Imported metal is marked ``existing`` so a model never fills a frame's slots.
"""

from __future__ import annotations

from pathlib import Path

import klayout.db as db

from tritflow import RAILS
from .chip_power import _power_header, _via_array
from .gds import box, wire_box
from .power import dc_current_check
from .signoff import _hash, _write


def esd_leakage_check(output_dir, pdk):
    """Check every ANA bias with the pinned ESD MPE/MNE models at 27 C.

    Clamps have no inter-pad signal path, so the three independent pad biases
    bound any combination of ternary inputs/outputs. Supply-only clamps are
    included. A 1 uA minimum budget covers numerical leakage in the DC rail
    checks; this does not assert surge, sequencing or transient qualification.
    """
    from tritflow.sim.runner import run_ngspice
    from tritflow.sim.spice import model_includes
    from tritflow.sim.tools import ngspice_binary

    out = Path(output_dir)
    lines = [
        "Stock OSS_FRAME nominal DC leakage",
        model_includes(pdk),
        ".temp 27",
        "VESD esd 0 5",
        "VDD core 0 5",
        "VSS vss 0 -5",
        "VMID mid 0 0",
        "VPATTERN pattern 0 -5",
    ]
    # Ten signal ANA pads, three core-VDD ANA pads and one VMID ANA pad.
    for i, node in enumerate(["pattern"] * 10 + ["core"] * 3 + ["mid"]):
        lines += [
            f"XP{i} {node} esd esd esd MPE w=500u l=2u",
            f"XN{i} {node} vss vss vss MNE w=500u l=2u",
        ]
    for i in range(2):
        lines += [
            f"XRP{i} vss esd esd esd MPE w=500u l=2u",
            f"XRN{i} esd vss vss vss MNE w=500u l=2u",
        ]
    vectors = ["i(VESD)", "i(VDD)", "i(VSS)", "i(VMID)", "i(VPATTERN)"]
    run = run_ngspice("\n".join(lines), "dc VPATTERN -5 5 5", vectors, workdir=out)
    measured = {name: [float(v) for v in run["data"][name.lower()]] for name in vectors}
    peak_sum = max(sum(abs(measured[n][i]) for n in vectors) for i in range(3))
    budget = max(1e-6, 10 * peak_sum)
    if peak_sum > 1e-6:
        raise ValueError(
            f"Stock ESD frame has unexpectedly high nominal leakage: {peak_sum:g} A"
        )
    report = {
        "passed": True,
        "biases_v": [-5, 0, 5],
        "temperature_c": 27,
        "measured_supply_a": measured,
        "max_total_absolute_current_a": peak_sum,
        "conservative_budget_a_per_supply": budget,
        "scope": "Independent ESD clamps at all three pad levels; three VDD ANA pads and VMID included. No core current, package or transient model.",
        "models": "Pinned ESD MPE/MNE, W/L=500/2 um, from stock frame schematics",
        "ngspice_sha256": _hash(ngspice_binary()),
        "model_sha256": {
            p.name: _hash(p)
            for p in (Path(pdk) / "libs.tech/spice/models").iterdir()
            if p.is_file()
        },
    }
    _write(out / "summary.json", report)
    return report


def stock_power(data, macro_pins, core, margin):
    """Feed VDD through three ANA pads and VSS through the common ESD ring.

    The three 40 um M1 VDD feeders are separate until the M2 distribution bar.
    VSS has six banks of four M1 fingers into M2 tongues on the inner ring.
    A pad's existing 70 um TC remains untouched; new small cuts are outside
    its opening. The model omits the parallel pad-TC path conservatively.
    """
    _, header = _power_header(data, macro_pins, core, margin, distribution_only=True)
    power = data["power"]
    bars = header["bar_y_um"]
    for cx in (-600.0, -200.0, 600.0):
        power["rails"].append(
            {
                "net": "VDD",
                "layer": "M1",
                "width": 40.0,
                "points": [
                    [cx, bars["VDD"] - header["M2_width_um"]["VDD"] / 2 + 1.7],
                    [cx, 983.0],
                ],
                "rect": [
                    cx - 20,
                    bars["VDD"] - header["M2_width_um"]["VDD"] / 2,
                    cx + 20,
                    1040.0,
                ],
                "path": "ANA_pad_feeder",
            }
        )
        _via_array(
            power["vias"], "VDD", cx, bars["VDD"], 40, header["M2_width_um"]["VDD"]
        )
        _via_array(power["vias"], "VDD", cx, 975, 40, 16)
        power["straps"].append(
            {
                "net": "VDD",
                "layer": "M2",
                "width": 16.0,
                "points": [[cx - 20, 975.0], [cx + 20, 975.0]],
                "rect": [cx - 20, 967, cx + 20, 983],
                "path": "ANA_pad_neck",
            }
        )
        for offset in (-16.0, -8.0, 0.0, 8.0, 16.0):
            power["straps"].append(
                {
                    "net": "VDD",
                    "layer": "M2",
                    "width": 8.0,
                    "points": [[cx + offset, 975.0], [cx + offset, 1040.0]],
                    "path": "ANA_pad_neck",
                }
            )
    for wire in power["straps"]:
        if wire["net"] == "VSS" and wire["points"][0][1] == bars["VSS"]:
            wire["points"][0][0], wire["points"][1][0] = -890.0, 890.0
    for center in (-860.0, -660.0, -300.0, 300.0, 660.0, 860.0):
        for column in range(4):
            cx = center + (column - 1.5) * 11.8
            power["rails"].append(
                {
                    "net": "VSS",
                    "layer": "M1",
                    "width": 9.4,
                    "points": [[cx, 803.8], [cx, 932.3]],
                    "rect": [cx - 4.7, 802.1, cx + 4.7, 934.0],
                    "path": "VSS_ring_tap",
                }
            )
            power["straps"].append(
                {
                    "net": "VSS",
                    "layer": "M2",
                    "width": 9.4,
                    "points": [[cx, bars["VSS"]], [cx, 839.9]],
                    "path": "VSS_ring_tap",
                }
            )
            _via_array(power["vias"], "VSS", cx, 820.0, 9.4, 32.4)
            power["straps"].append(
                {
                    "net": "VSS",
                    "layer": "M2",
                    "width": 9.4,
                    "points": [[cx, 879.7], [cx, 932.3]],
                    "rect": [cx - 4.7, 878, cx + 4.7, 934],
                    "path": "VSS_ring_tap",
                }
            )
            _via_array(power["vias"], "VSS", cx, 899.8, 9.4, 32.4)
    # Two continuous lanes, with the actual 2 um slot left open. Periodic
    # crosslinks are modeled from the actual stock geometry, not as a solid
    # 30 um conductor that would overrate the slotted metal.
    for radius in (927.0, 943.0):
        corners = [
            (-radius, -radius),
            (radius, -radius),
            (radius, radius),
            (-radius, radius),
            (-radius, -radius),
        ]
        for a, b in zip(corners, corners[1:]):
            power["straps"].append(
                {
                    "net": "VSS",
                    "layer": "M2",
                    "width": 14.0,
                    "points": [list(a), list(b)],
                    "existing": True,
                    "path": "stock_VSS_ring",
                }
            )
    for tangent in range(-780, 781, 40):
        for sign in (-1, 1):
            for vertical in (False, True):
                a, b = ([tangent, sign * 927], [tangent, sign * 943])
                if vertical:
                    a, b = a[::-1], b[::-1]
                rect = [
                    min(a[0], b[0]) - 10,
                    min(a[1], b[1]) - 10,
                    max(a[0], b[0]) + 10,
                    max(a[1], b[1]) + 10,
                ]
                # Clip radial ends to the real 30 um ring band.
                radial = 0 if vertical else 1
                rect[radial], rect[radial + 2] = sorted((sign * 920, sign * 950))
                power["straps"].append(
                    {
                        "net": "VSS",
                        "layer": "M2",
                        "width": 20.0,
                        "points": [a, b],
                        "rect": rect,
                        "existing": True,
                        "path": "stock_VSS_ring_bridge",
                    }
                )
    # The VSS pad's two 40 um M2 fingers meet the outer lane. The crosslinks
    # above include x=-220/-180, connecting to the inner lane at the pad.
    for x in (-230.0, -170.0):
        power["straps"].append(
            {
                "net": "VSS",
                "layer": "M2",
                "width": 40.0,
                "points": [[x, -1040.0], [x, -943.0]],
                "rect": [x - 20, -1040.0, x + 20, -950.0],
                "existing": True,
                "path": "stock_VSS_pad",
            }
        )
    power["pins"] = [
        {"name": "VDD", "layer": "M2", "rect": [x + o - 1, 1039, x + o + 1, 1041]}
        for x in (-600.0, -200.0, 600.0)
        for o in (-16, -8, 0, 8, 16)
    ] + [
        {"name": "VSS", "layer": "M2", "rect": [x - 1, -1041, x + 1, -1039]}
        for x in (-230.0, -170.0)
    ]
    return header


def check_stock_currents(data, library, gds):
    """Run the existing DC solver and report its worst branch per supply.

    Every imported model rectangle must lie in the actual GDS. The pad's
    continuous 70 um TC receives a separate full-pad-current upper bound:
    the published 1.4 um TC limit is conservatively scaled by minimum width,
    not area. This is the same engineering width-scaling interpretation as
    the metal check, not a published pad-specific or lifetime EM rating.
    """
    from tritflow.extract.ir import _rail_graph, solve_resistive_network
    from tritflow.extract.technology import DEFAULT_SHEET_OHM, DEFAULT_VIA_OHM

    layout = db.Layout()
    layout.read(str(gds))
    top = layout.cell(data["top"])
    regions = {
        name: db.Region(top.begin_shapes_rec(layout.layer(layer, 0))).merged()
        for name, layer in (("M1", 13), ("M2", 20), ("V1", 19))
    }
    missing = []
    for wire in data["power"]["rails"] + data["power"]["straps"]:
        if not (
            db.Region(box(wire.get("rect", wire_box(wire)))) - regions[wire["layer"]]
        ).is_empty():
            missing.append(wire)
    for via in data["power"]["vias"]:
        if not (
            db.Region(
                box([via["x"] - 0.7, via["y"] - 0.7, via["x"] + 0.7, via["y"] + 0.7])
            )
            - regions["V1"]
        ).is_empty():
            missing.append(via)
    if missing:
        raise ValueError(
            f"Stock current model includes {len(missing)} absent conductors"
        )
    report = dc_current_check(data, library)
    leakage = data["frame"]["dc_leakage"]
    auxiliary_budget = leakage["conservative_budget_a_per_supply"]
    per_supply = {}
    all_rows = []
    for rail in RAILS:
        band = library.template["rails"][rail]
        taps = {
            p["inst"]: (
                p["x"] + library.cells[p["cell"]].width / 2,
                p["y"] + sum(band) / 2,
            )
            for p in data["placements"]
        }
        edges, fixed, nodes, details = _rail_graph(
            data, rail, taps, DEFAULT_SHEET_OHM, DEFAULT_VIA_OHM
        )
        currents = {
            p["inst"]: max(
                (
                    v["rail_current_a"][rail]
                    for v in library.cells[p["cell"]].characterization["dc"]
                ),
                key=abs,
            )
            for p in data["placements"]
        }
        injection = {}
        for name, node in nodes.items():
            injection[node] = injection.get(node, 0.0) + currents[name]
        solved = solve_resistive_network(edges, fixed, injection)
        rows = []
        for (a, b, resistance), detail in zip(edges, details):
            current = abs(
                (solved["voltage_v"][a] - solved["voltage_v"][b]) / resistance
            )
            rows.append(
                {
                    **detail,
                    "current_a": current,
                    "upper_bound_a": current + auxiliary_budget,
                    "utilization": (current + auxiliary_budget) / detail["limit_a"],
                    "endpoints": [list(a), list(b)],
                }
            )
        worst = max(rows, key=lambda row: row["utilization"])
        per_supply[rail] = {
            "current_envelope_a": sum(abs(v) for v in currents.values()),
            "auxiliary_leakage_budget_a": auxiliary_budget,
            "max_utilization": worst["utilization"],
            "reserve": 1 - worst["utilization"],
            "worst_branch": worst,
            "worst_by_kind": {
                kind: max(
                    (r for r in rows if r["kind"] == kind),
                    key=lambda r: r["utilization"],
                    default=None,
                )
                for kind in ("M1_step", "M2_field", "TC")
            },
            "pad_injection_a": [
                {"node": list(n), "current_a": v}
                for n, v in solved["pad_injection_a"].items()
            ],
        }
        all_rows.extend(rows)
    # ESD clamps are off at the specified nominal biases. Their leakage is
    # checked separately with the PDK models by the snapshot build script.
    esd_rows = [
        {
            "kind": kind,
            "net": "ESD_VDD",
            "upper_bound_a": auxiliary_budget,
            "limit_a": limit,
            "utilization": auxiliary_budget / limit,
        }
        for kind, limit in (
            ("M1_step", 1.8 * 0.00025),
            ("M2_field", 14 * 0.0037 / 3),
            ("TC", 0.00078),
        )
    ]
    esd_max = max(row["utilization"] for row in esd_rows)
    per_supply["ESD_VDD"] = {
        "current_envelope_a": auxiliary_budget,
        "max_utilization": esd_max,
        "reserve": 1 - esd_max,
        "worst_by_kind": {row["kind"]: row for row in esd_rows},
        "scope": "Entire measured-leakage budget on each minimum-width M1 path, each 14 um ESD ring lane and every standard TC; no core load",
    }
    all_rows.extend(esd_rows)
    pad_checks = []
    for pad in data["pad_map"]:
        if pad["net"] not in per_supply:
            continue
        rail = pad["net"]
        # Use the full rail envelope on EACH supply pad, a conservative upper
        # bound that also covers current sharing in unmodeled parallel metal.
        current = per_supply[rail]["current_envelope_a"] + (
            auxiliary_budget if rail != "ESD_VDD" else 0
        )
        limit = 780e-6 * (70.0 / 1.4)
        x, y = pad["center_um"]
        cut = db.Region(box([x - 35, y - 35, x + 35, y + 35]))
        if not (cut - regions["V1"]).is_empty():
            raise ValueError(f"{pad['pad']}: missing 70 um stock pad TC")
        pad_checks.append(
            {
                "pad": pad["pad"],
                "net": rail,
                "cut_um": 70.0,
                "upper_bound_current_a": current,
                "limit_a": limit,
                "utilization": current / limit,
                "reserve": 1 - current / limit,
            }
        )
    worst_pad = max((p["utilization"] for p in pad_checks), default=0)
    maximum = max(max(r["utilization"] for r in all_rows), worst_pad)
    target = 1 - data["power"]["assumptions"]["reserved_current_margin"]
    report.update(
        max_utilization=maximum,
        margin_to_limit=1 - maximum,
        reserved_margin_met=maximum <= target + 1e-7,
        passed=maximum <= 1 + 1e-9,
        per_supply=per_supply,
        pad_cut_checks=pad_checks,
        imported_model_geometry_verified=True,
        worst_by_kind={
            kind: max(
                (r for r in all_rows if r["kind"] == kind),
                key=lambda r: r["utilization"],
            )
            for kind in ("M1_step", "M2_field", "TC")
        },
        esd_leakage=leakage,
        pad_cut_rating="780 uA * (minimum cut width / 1.4 um); conservative linear-width engineering interpretation, no published 70 um pad rating",
        frame_scope="Unchanged slotted VSS M2 ring, its two M2 pad fingers, every added feeder and TC, and existing macro distribution; no package/contact/transient EM qualification",
    )
    return report
