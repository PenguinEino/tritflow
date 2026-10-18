"""Three separate supplies, current-based sizing, and a resistive rail estimate."""
from __future__ import annotations

import math

import numpy as np

from tritflow import RAILS


def cell_current(cell, default):
    """Read explicit ampere quantities; never infer units from an unlabelled number."""
    char = cell.characterization
    for key in ("static_current_a", "static_current_A", "max_static_current_a"):
        if key in char:
            value = char[key]
            if isinstance(value, list):
                return max(abs(float(v)) for v in value), key
            if isinstance(value, dict):
                return max(abs(float(v)) for v in value.values()), key
            return abs(float(value)), key
    # SIM's vector-by-vector schema can publish supply current measurements.
    vectors = char.get("dc", char.get("vectors", []))
    if isinstance(vectors, list):
        currents = [abs(float(v[k])) for v in vectors if isinstance(v, dict)
                    for k in ("static_current_a", "supply_current_a") if k in v]
        currents += [abs(float(i)) for v in vectors if isinstance(v, dict)
                     for i in v.get("rail_current_a", {}).values()]
        if currents:
            return max(currents), "vector maximum"
    return default, "default"


def power_plan(placements, library, *, current_density_a_per_um=.00025,
               default_cell_current_a=.0001, sheet_resistance_ohm=.05):
    """Plan split M2 trunks; template rail bands are immutable cell geometry.

    Width scaling is an assumption; the conservative default uses the manual's
    500 µA stepped-M1 rating at 2 µm. Sheet resistance is also an assumption. Conservative constant current is sunk at every cell.
    """
    if (not all(math.isfinite(v) for v in (current_density_a_per_um, default_cell_current_a, sheet_resistance_ohm))
            or current_density_a_per_um <= 0 or default_cell_current_a < 0 or sheet_resistance_ohm <= 0):
        raise ValueError("Power assumptions must be positive (default current may be zero)")
    currents, sources, rail_currents = {}, {}, {}
    for pl in placements:
        cell = library.cells[pl["cell"]]
        fallback = 0. if cell.name in ("FILL", "TIEP", "TIEZ", "TIEN") else default_cell_current_a
        currents[pl["inst"]], sources[pl["inst"]] = cell_current(cell, fallback)
        value = currents[pl["inst"]]
        if not math.isfinite(value):
            raise ValueError(f"{cell.name}: non-finite static current")
        rail_currents[pl["inst"]] = {}
        for rail in RAILS:
            measured = [abs(float(row["rail_current_a"][rail]))
                        for row in cell.characterization.get("dc", [])
                        if rail in row.get("rail_current_a", {})]
            rail_currents[pl["inst"]][rail] = max(measured) if measured else (
                value if rail != "VMID" or cell.name == "NANY" else 0.)
    if not all(math.isfinite(v) for values in rail_currents.values() for v in values.values()):
        raise ValueError("Non-finite characterized rail current")
    total = sum(currents.values())
    # Each side supplies half the worst-case total current.
    required = max(6., total / (2 * current_density_a_per_um))
    count = math.ceil(required / 42.)
    width = math.ceil(max(6., required/count) * 10) / 10
    pitch = library.template["grid"]
    stride = math.ceil((width + 3.) / pitch) * pitch
    bank = 3 * count * stride
    margin = math.ceil((bank + 4*pitch) / pitch) * pitch
    for row in {pl["row"] for pl in placements}:
        load = sum(currents[pl["inst"]] for pl in placements if pl["row"] == row)
        for name, band in library.template["rails"].items():
            if load / (2 * current_density_a_per_um) > band[1]-band[0] + 1e-9:
                raise ValueError(f"Row {row} {name}: current requires a wider cell rail; "
                                 "increase rows or the assumed current density")
            if band[1]-band[0] > 45:
                raise ValueError("Cell rail exceeds the PDK unslotted 45 µm limit")
    return {"margin": margin, "trunk_width": width, "trunks_per_supply_per_side": count,
            "stride": stride, "currents_a": currents, "rail_currents_a": rail_currents, "current_sources": sources,
            "assumptions": {"default_cell_current_a": default_cell_current_a,
                "allowed_current_a_per_um": current_density_a_per_um,
                "sheet_resistance_ohm_per_square": sheet_resistance_ohm,
                "qualification": "linear width scaling and constant-current assumptions; not EM sign-off",
                "current_reference": "OS00 rev1.1 I.3.1/I.3.2: M1(2um) 900uA flat / 500uA stepped; M2(3um) 3.7mA; V1 780uA/cut"}}


def draw_power(data, placements, library, plan):
    """Connect each row at both ends; crossings between unlike metals have no via."""
    t, rules = library.template, library.template["rules"]
    w, h = data["die"]
    p, width, stride = t["grid"], plan["trunk_width"], plan["stride"]
    count = plan["trunks_per_supply_per_side"]
    straps, rail_wires, vias, pins = [], [], [], []
    row_ys = {i: row["y"] for i, row in enumerate(data["rows"])}
    for k, rail in enumerate(RAILS):
        xs = []
        for side in ("left", "right"):
            for j in range(count):
                # Signal I/O sits outside these banks and crosses them on M1.
                xleft = 2*p + (k*count+j)*stride
                x = xleft + width/2 if side == "left" else w-xleft-width/2
                xs.append(x)
                straps.append({"net": rail, "layer": "M2", "width": width,
                               "points": [[x, p+width/2], [x, h-width/2]], "side": side})
                pins.append({"name": rail, "layer": "M2", "rect": [x-width/2, h-p, x+width/2, h]})
        y0, y1 = t["rails"][rail]
        railwidth = y1-y0
        for row, y in sorted(row_ys.items()):
            cy = y+(y0+y1)/2
            rail_wires.append({"net": rail, "layer": "M1", "width": railwidth,
                               "points": [[min(xs)-width/2, cy], [max(xs)+width/2, cy]]})
            cut = rules["V1"]
            enclosure = max(rules["V1_enc_M1"], rules["V1_enc_M2"])
            spacing = math.ceil((cut + 1.5)*20)/20
            nx = max(1, math.floor((width-2*enclosure-cut)/spacing)+1)
            ny = max(1, math.floor((railwidth-2*enclosure-cut)/spacing)+1)
            for x in xs:
                for i in range(nx):
                    for j in range(ny):
                        vias.append({"net": rail, "x": round(x+(i-(nx-1)/2)*spacing, 6),
                                     "y": round(cy+(j-(ny-1)/2)*spacing, 6)})
    data["power"] = {**plan, "straps": straps, "rails": rail_wires,
                     "vias": vias, "pins": pins}
    data["power"]["ir_drop"] = solve_rails(placements, library, plan, straps, row_ys, h)


def solve_rails(placements, library, plan, straps, row_ys, die_height):
    """Solve coupled row/trunk resistor graphs, with top supply pins held ideal.

    Every cell is represented by its worst-case current. VMID is evaluated in
    both current directions because clamp current depends on the input vector.
    Divider-cell midpoint shift uses equal pull-up/pull-down conductance at
    ternary zero. NANY instead reports its local VMID deviation envelope.
    """
    rho = plan["assumptions"]["sheet_resistance_ohm_per_square"]
    results = {pl["inst"]: {} for pl in placements}
    rows = sorted(row_ys)
    for rail, nominal, sign in (("VDD", 5., -1), ("VMID", 0., 1), ("VSS", -5., 1)):
        selected = [s for s in straps if s["net"] == rail]
        xl = np.mean([s["points"][0][0] for s in selected if s["side"] == "left"])
        xr = np.mean([s["points"][0][0] for s in selected if s["side"] == "right"])
        railwidth = library.template["rails"][rail][1]-library.template["rails"][rail][0]
        yc = sum(library.template["rails"][rail])/2
        nodes = {}
        edges, loads = [], {}
        def node(key):
            if key not in nodes:
                nodes[key] = len(nodes)
            return nodes[key]
        for row in rows:
            cells = sorted((pl for pl in placements if pl["row"] == row), key=lambda pl: pl["x"])
            ordered = [(node((row, "left")), xl)]
            for pl in cells:
                index = node((row, pl["inst"]))
                loads[index] = plan["rail_currents_a"][pl["inst"]][rail]
                ordered.append((index, pl["x"]+library.cells[pl["cell"]].width/2))
            ordered.append((node((row, "right")), xr))
            for (a, x0), (b, x1) in zip(ordered, ordered[1:]):
                edges.append((a, b, rho*max(x1-x0, .05)/railwidth))
        fixed = []
        trunkwidth = plan["trunk_width"] * plan["trunks_per_supply_per_side"]
        for side in ("left", "right"):
            for low, high in zip(rows, rows[1:]):
                edges.append((node((low, side)), node((high, side)),
                              rho*(row_ys[high]-row_ys[low])/trunkwidth))
            if rows:
                last = rows[-1]
                fixed.append((node((last, side)), rho*max(die_height-row_ys[last]-yc, .05)/trunkwidth))
        size = len(nodes)
        matrix, rhs = np.zeros((size, size)), np.zeros(size)
        for a, b, resistance in edges:
            g = 1/resistance
            matrix[a, a] += g
            matrix[b, b] += g
            matrix[a, b] -= g
            matrix[b, a] -= g
        for index, resistance in fixed:
            matrix[index, index] += 1/resistance
        for index, current in loads.items():
            rhs[index] = current
        drop = np.linalg.solve(matrix, rhs) if size else []
        for pl in placements:
            d = float(drop[nodes[(pl["row"], pl["inst"])]])
            results[pl["inst"]][f"{rail}_v"] = nominal + sign*d
            results[pl["inst"]][f"{rail}_drop_v"] = d
            if rail == "VMID":
                results[pl["inst"]]["VMID_range_v"] = [-d, d]
    for pl in placements:
        values = results[pl["inst"]]
        if pl["cell"] in ("INV", "NAND", "NOR", "BUF"):
            values["zero_level_shift_v"] = (values["VDD_v"] + values["VSS_v"])/2
        elif pl["cell"] == "NANY":
            values["zero_level_shift_range_v"] = values["VMID_range_v"]
    return {"cells": results, "max_drop_v": max((v[f"{r}_drop_v"] for v in results.values() for r in RAILS), default=0),
            "midpoint_model": "equal pull-up/down conductance; not a transistor DC simulation"}
