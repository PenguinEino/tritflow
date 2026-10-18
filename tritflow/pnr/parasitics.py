"""Logical-net loads from routed metal and characterized receiving cell pins.

Wire C uses SIM's merged-polygon estimator. It is an assumed substrate model,
not calibrated PEX. Characterized input C is a conservative per-pin bias
envelope; summing those maxima need not represent one realizable logic vector.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from tritflow.netlist import GateNetlist
from .gds import DBU, wire_box
from .library import Library


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _pin_capacitance(cell, pin):
    """Use this pin's largest measured AC capacitance, never another pin's max."""
    rows = cell.characterization.get("input_capacitance", {}).get("rows", [])
    values = [
        r["capacitance_f"]
        for r in rows
        if r.get("pin") == pin and r.get("capacitance_f") is not None
    ]
    if not values:
        return None
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError(f"Invalid characterized input capacitance: {cell.name}.{pin}")
    return max(values)


def estimate_net_parasitics(data, netlist, library):
    """Return every signal net, including unused ports and unrouted singleton nets.

    Supply geometry is excluded. Rectangles exactly match the GDS exporter's
    square-ended wires, boundary pads and metal landings around V1 cuts. SIM's
    estimator unions overlaps before applying its shared area/fringe model.
    """
    from tritflow.extract import DEFAULT_CAP_COEFFICIENTS, wire_capacitance

    rules = library.template["rules"]
    metal = [
        {"name": w["net"], "layer": w["layer"], "rect": wire_box(w)}
        for w in data["wires"]
    ]
    metal += list(data["pins"])
    for via in data["vias"]:
        for layer in ("M1", "M2"):
            half = (rules["V1"] + 2 * rules[f"V1_enc_{layer}"]) / 2
            x, y = via["x"], via["y"]
            metal.append(
                {
                    "name": via["net"],
                    "layer": layer,
                    "rect": [x - half, y - half, x + half, y + half],
                }
            )
    wire = wire_capacitance(
        {"pins": metal}, coefficients=DEFAULT_CAP_COEFFICIENTS, dbu_um=DBU
    )
    nets = {}
    for name in sorted(netlist.nets()):
        cap = wire["nets"].get(name, {"capacitance_f": 0.0, "layers": {}})
        nets[name] = {
            "wirelength_um": {
                layer: sum(
                    sum(
                        abs(b[0] - a[0]) + abs(b[1] - a[1])
                        for a, b in zip(w["points"], w["points"][1:])
                    )
                    for w in data["wires"]
                    if w["net"] == name and w["layer"] == layer
                )
                for layer in ("M1", "M2")
            },
            "via_count": sum(v["net"] == name for v in data["vias"]),
            "wire_capacitance_f": cap["capacitance_f"],
            "layers": cap["layers"],
            "pins": [],
            "ports": [],
        }
    for port in netlist.ports:
        nets[port.name]["ports"].append({"name": port.name, "direction": port.dir})
    for inst in netlist.instances:
        cell = library.cells[inst.cell]
        for pin, name in inst.pins.items():
            direction = cell.pins[pin]["dir"]
            nets[name]["pins"].append(
                {
                    "instance": inst.name,
                    "cell": inst.cell,
                    "pin": pin,
                    "hier": inst.hier,
                    "direction": direction,
                    "input_capacitance_f": (
                        _pin_capacitance(cell, pin) if direction == "input" else None
                    ),
                }
            )
    for row in nets.values():
        sinks = [p for p in row["pins"] if p["direction"] == "input"]
        missing = [
            f"{p['instance']}.{p['pin']}"
            for p in sinks
            if p["input_capacitance_f"] is None
        ]
        known = sum(
            p["input_capacitance_f"]
            for p in sinks
            if p["input_capacitance_f"] is not None
        )
        row.update(
            {
                "pin_count": len(row["pins"]) + len(row["ports"]),
                "cell_pin_count": len(row["pins"]),
                "port_count": len(row["ports"]),
                "fanout": len(sinks),
                "missing_pin_capacitance": missing,
                "known_cell_input_capacitance_f": known,
                "cell_input_capacitance_f": None if missing else known,
                "total_load_f": None if missing else row["wire_capacitance_f"] + known,
                "external_load_included": False,
            }
        )
    char_sources = {}
    if not library.mock:
        for name in sorted({i.cell for i in netlist.instances}):
            path = Path(library.source) / "out" / name / f"{name}.char.json"
            if path.is_file():
                char_sources[str(path.resolve())] = _sha(path)
    complete = all(n["total_load_f"] is not None for n in nets.values())
    return {
        "schema": "tritflow.net_parasitics.v1",
        "top": netlist.top,
        "nets": nets,
        "coefficients": deepcopy(wire["coefficients"]),
        "parameter_origin": wire["parameter_origin"],
        "assumptions": wire["assumptions"],
        "wire_scope": "Routed M1/M2 including square ends, boundary pins and V1 metal landings; excludes cell-internal metal and supplies. Via cuts have no modeled capacitance.",
        "pin_count_definition": "Cell signal terminals plus top-level ports; fanout counts receiving cell input pins, including two pins of one cell tied to the same net.",
        "load_scope": "On-chip routed wire C plus sum of per-input-pin maximum characterized AC C across biases. External output loads, driver intrinsic C and connected cell metal are excluded. Missing characterization gives null load, not zero.",
        "characterization_sha256": char_sources,
        "totals": {
            "wirelength_um": {
                m: sum(n["wirelength_um"][m] for n in nets.values())
                for m in ("M1", "M2")
            },
            "via_count": sum(n["via_count"] for n in nets.values()),
            "wire_capacitance_f": sum(n["wire_capacitance_f"] for n in nets.values()),
            "known_cell_input_capacitance_f": sum(
                n["known_cell_input_capacitance_f"] for n in nets.values()
            ),
            "total_load_f": (
                sum(n["total_load_f"] for n in nets.values()) if complete else None
            ),
            "complete_pin_characterization": complete,
        },
    }


def compare_extracted_capacitance(report, gds_path, lvs_report, capacitance_path=None):
    """Map SIM's actual connected-metal C through strict LVS correspondence.

    Route-only C and connected-metal C have different scopes: their difference
    includes connected cell metal and merging at pin contacts. A like-for-like
    check recomputes the actual GDS model and compares every mapped node with a
    retained SIM capacitance.json. No SPICE names are guessed by string casing.
    """
    from tritflow.extract import gds_wire_capacitance, reference_net_map

    mapping = reference_net_map(lvs_report, report["top"])
    measured = gds_wire_capacitance(gds_path, lvs_report, top=report["top"])
    comparison = {
        "lvs_report": str(Path(lvs_report).resolve()),
        "gds_sha256": _sha(gds_path),
        "lvs_sha256": _sha(lvs_report),
        "scope": measured["scope"],
        "nets": {},
        "unmapped_signal_nets": [],
        "route_only_comparison": "Different scope: connected metal includes cell-pin metal; routed C and connected-metal C are alternatives, never additive.",
    }
    retained = None
    if capacitance_path is not None:
        path = Path(capacitance_path)
        retained = json.loads(path.read_text())
        if retained["coefficients"] != measured["coefficients"]:
            raise ValueError(
                "SIM capacitance coefficients differ from the current shared model"
            )
        comparison.update(
            {"capacitance_path": str(path.resolve()), "capacitance_sha256": _sha(path)}
        )
        # SIM retains the exact GDS consumed next to capacitance.json. Reject a
        # stale physical revision even if its extracted node names happen to match.
        snapshot = path.parent / "inputs" / f"{report['top']}.gds"
        if snapshot.is_file() and _sha(snapshot) != comparison["gds_sha256"]:
            raise ValueError(f"SIM capacitance refers to a different GDS: {snapshot}")
    for logical, routed in report["nets"].items():
        physical = mapping.get(logical)
        if physical is None or physical not in measured["nets"]:
            comparison["unmapped_signal_nets"].append(logical)
            continue
        cap = measured["nets"][physical]["capacitance_f"]
        row = {
            "extracted_net": physical,
            "connected_metal_capacitance_f": cap,
            "routed_wire_capacitance_f": routed["wire_capacitance_f"],
            "connected_minus_routed_f": cap - routed["wire_capacitance_f"],
            "connected_metal_total_load_f": (
                cap + routed["cell_input_capacitance_f"]
                if routed["cell_input_capacitance_f"] is not None
                else None
            ),
            "layers": measured["nets"][physical]["layers"],
        }
        if retained is not None:
            saved = retained["nets"].get(physical)
            row["sim_capacitance_f"] = saved["capacitance_f"] if saved else None
            row["difference_f"] = cap - saved["capacitance_f"] if saved else None
            row["agrees"] = bool(
                saved is not None
                and math.isclose(
                    cap, saved["capacitance_f"], rel_tol=1e-12, abs_tol=1e-24
                )
            )
        comparison["nets"][logical] = row
    physical_nodes = {r["extracted_net"] for r in comparison["nets"].values()}
    comparison["mapped_signal_net_count"] = len(comparison["nets"])
    comparison["connected_signal_capacitance_f"] = sum(
        measured["nets"][n]["capacitance_f"] for n in physical_nodes
    )
    comparison["connected_all_net_capacitance_f"] = sum(
        n["capacitance_f"] for n in measured["nets"].values()
    )
    comparison["non_signal_capacitance_f"] = sum(
        r["capacitance_f"]
        for n, r in measured["nets"].items()
        if n not in physical_nodes
    )
    if retained is not None:
        comparison["all_mapped_signals_agree"] = not comparison[
            "unmapped_signal_nets"
        ] and all(n["agrees"] for n in comparison["nets"].values())
        # Also check supplies and other retained nodes, beyond the signal subset.
        comparison["all_extracted_nodes_agree"] = set(retained["nets"]) == set(
            measured["nets"]
        ) and all(
            math.isclose(
                r["capacitance_f"],
                retained["nets"][n]["capacitance_f"],
                rel_tol=1e-12,
                abs_tol=1e-24,
            )
            for n, r in measured["nets"].items()
        )
        comparison["sim_all_net_capacitance_f"] = sum(
            n["capacitance_f"] for n in retained["nets"].values()
        )
    return comparison


def result_net_parasitics(
    result, *, library=None, lvs_report=None, capacitance_path=None
):
    """Write a logical-net sidecar; older PNR results can be upgraded in place.

    New PNR JSON embeds a portable snapshot. Reuse it without consulting mutable
    library files, unless a library is explicitly supplied to refresh the data.
    Optional LVS/SIM comparisons live in the sidecar, leaving the PNR power
    section and SIM's retained outputs unchanged.
    """
    if capacitance_path is not None and lvs_report is None:
        raise ValueError("capacitance_path requires its matching lvs_report")
    if library is None and "net_parasitics" in result.data:
        report = deepcopy(result.data["net_parasitics"])
    else:
        netlist = result.netlist
        if netlist is None:
            path = result.json_path.with_name(f"{result.data['top']}.json")
            if not path.is_file():
                raise ValueError(
                    "Net parasitics require the GateNetlist or a current PNR snapshot; rebuild this older result"
                )
            netlist = GateNetlist.load(path)
        library = library or Library.load(result.data["library"]["source"])
        report = estimate_net_parasitics(result.data, netlist, library)
    if lvs_report is not None:
        report["extracted_comparison"] = compare_extracted_capacitance(
            report, result.gds_path, lvs_report, capacitance_path
        )
    path = result.json_path.with_name(f"{result.data['top']}.net_parasitics.json")
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)
    return report
