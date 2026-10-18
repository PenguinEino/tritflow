"""Notebook and CLI entry point for the complete physical-design flow."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from tritflow.netlist import GateNetlist
from .gds import write_gds
from .library import Library
from .placement import pin_location, place
from .power import draw_power, power_plan
from .router import RoutingFailure, floorplan, route
from .verify import PhysicalVerificationError, connectivity, pdk_drc, routing_drc


@dataclass
class PnrResult:
    """Exported artifacts plus the full placement/routing record for animation."""

    gds_path: Path
    json_path: Path
    stats: dict
    data: dict


def place_and_route(netlist, library=None, *, output_dir=None, rows=None, seed=0,
                    anneal_steps=600, history_every=25, channel_tracks=None,
                    max_expansions=5, ripup_passes=3, run_pdk_drc=True,
                    current_density_a_per_um=.00025, default_cell_current_a=.0001,
                    sheet_resistance_ohm=.05, pdk_root=None, klayout_binary=None):
    """Place, route, export and verify a combinational GateNetlist.

    The default library is re-discovered on every call, so a newly published real
    library replaces provisional mocks automatically. A mock result is identified
    in both JSON and stats; it is never evidence of transistor-level correctness.
    DRC failures retain GDS, JSON and reports for inspection, then raise.
    """
    if isinstance(netlist, (str, Path)):
        netlist = GateNetlist.load(netlist)
    elif isinstance(netlist, dict):
        netlist = GateNetlist.from_dict(netlist)
    if not netlist.top or netlist.top in {i.cell for i in netlist.instances} or any(c in netlist.top for c in "/\\"):
        raise ValueError("Top name must be a safe GDS name distinct from cell masters")
    if max_expansions < 0 or ripup_passes < 1:
        raise ValueError("Invalid routing retry limits")
    if library is None:
        library = Library.automatic()
    elif isinstance(library, (str, Path)):
        library = Library.load(library)
    library.validate()
    relative, history, row_count = place(netlist, library, rows, seed, anneal_steps, history_every)
    while True:
        try:
            plan = power_plan(relative, library, current_density_a_per_um=current_density_a_per_um,
                              default_cell_current_a=default_cell_current_a,
                              sheet_resistance_ohm=sheet_resistance_ohm)
            break
        except ValueError as error:
            # A fixed template cannot widen its internal rails. Add rows to
            # reduce current per row, unless the caller fixed the row count.
            if rows is not None or "wider cell rail" not in str(error) or row_count >= len(netlist.instances):
                raise
            relative, history, row_count = place(netlist, library, row_count+1, seed,
                                                  anneal_steps, history_every)
    ports = max((sum(port.dir == direction for port in netlist.ports) for direction in ("input", "output")), default=0)
    min_tracks = 2*math.ceil(ports/(row_count+1))+2
    tracks = channel_tracks or max(12, min_tracks, math.ceil(len(netlist.nets())/(row_count+1)*.4))
    if tracks < min_tracks:
        raise ValueError(f"At least {min_tracks} channel tracks are needed for boundary pins")
    compact_metal = any(cell.obstructions.get("M2") or cell.obstructions.get("V1") or cell.free_tracks
                        for cell in library.cells.values())
    bypass_tracks = 8 if compact_metal else 0
    attempts = []
    for expansion in range(max_expansions+1):
        data, terminals = floorplan(netlist, library, relative, row_count,
                                    plan["margin"]+bypass_tracks*library.template["grid"], tracks)
        data["routing_corridors"] = {"bypass_tracks_per_side": bypass_tracks}
        data.update({"top": netlist.top, "schema": "tritflow.pnr.v1", "seed": seed,
                     "library": {"source": library.source, "mock": library.mock,
                         "cells": {name: {"width": cell.width, "height": cell.height,
                                          "free_tracks": cell.free_tracks, "routing": cell.routing}
                                   for name, cell in library.cells.items()}}})
        draw_power(data, data["placements"], library, plan)
        try:
            log = route(data, terminals, library, seed+expansion, ripup_passes)
            attempts.append({"channel_tracks": tracks, "bypass_tracks_per_side": bypass_tracks,
                             "ripped_up": log, "success": True})
            break
        except RoutingFailure as error:
            attempts.append({"channel_tracks": tracks, "bypass_tracks_per_side": bypass_tracks, "failed_net": error.net, "reason": str(error),
                             "ripped_up": getattr(error, "ripup_log", []), "success": False})
            if expansion == max_expansions or "access conflicts" in str(error):
                raise RoutingFailure(error.net, f"{error}; channel attempts={attempts}") from error
            # Expansion of all channels gives the blocked net alternative paths
            # through neighboring rows, rather than only increasing one cut.
            tracks = math.ceil(tracks*1.6)+4
            if compact_metal:
                bypass_tracks = math.ceil(bypass_tracks*1.6)+4
    data["routing_attempts"] = attempts
    # Animation coordinates must match the final floorplan, including expansion.
    for snapshot in history:
        snapshot["placements"] = [{**pl, "x": pl["x"]+plan["margin"]+bypass_tracks*library.template["grid"],
            "y": data["rows"][pl["row"]]["y"]} for pl in snapshot["placements"]]
        positions = {}
        by_name = {i.name: i for i in netlist.instances}
        for pl in snapshot["placements"]:
            for pin, net in by_name[pl["inst"]].pins.items():
                positions.setdefault(net, []).append(pin_location(library.cells[pl["cell"]], pin, pl))
        snapshot["hpwl"] = sum(max(x for x, y in pts)-min(x for x, y in pts)+
            max(y for x, y in pts)-min(y for x, y in pts) for pts in positions.values())
    data["history"] = history
    area = sum(library.cells[pl["cell"]].width*library.cells[pl["cell"]].height for pl in data["placements"])
    wirelength = {m: sum(sum(abs(b-a) for a, b in zip(w["points"][0], w["points"][-1]))
                         for w in data["wires"] if w["layer"] == m) for m in ("M1", "M2")}
    data["stats"] = {"die_size_um": data["die"], "die_area_um2": math.prod(data["die"]),
        "wirelength_um": wirelength, "via_count": len(data["vias"]),
        "power_via_count": len(data["power"]["vias"]), "utilization": area/math.prod(data["die"]),
        "instance_count": len(netlist.instances), "net_count": len(netlist.nets()),
        "routed_nets": len(terminals), "library_mock": library.mock,
        "max_supply_drop_v": data["power"]["ir_drop"]["max_drop_v"],
        "bypass_tracks_per_side": bypass_tracks,
        "hpwl_before_um": history[0]["hpwl"], "hpwl_after_um": history[-1]["hpwl"],
        "hpwl_improvement_pct": (100*(1-history[-1]["hpwl"]/history[0]["hpwl"])
                                 if history[0]["hpwl"] else 0.)}
    out = Path(output_dir or Path("build")/netlist.top)
    out.mkdir(parents=True, exist_ok=True)
    gds_path, json_path = out/f"{netlist.top}.gds", out/f"{netlist.top}.pnr.json"
    write_gds(data, library, gds_path)
    data["checks"] = {"connectivity": connectivity(gds_path, data, netlist, library),
                      "routing_drc": routing_drc(gds_path, data, library)}
    own_clean = all(c["clean"] for c in data["checks"].values())
    json_path.write_text(json.dumps(data, indent=2)+"\n")
    if not own_clean:
        raise PhysicalVerificationError(f"Physical self-check failed: {data['checks']}; artifacts in {out}")
    if run_pdk_drc:
        options = {"binary": klayout_binary}
        if pdk_root is not None:
            options["pdk_root"] = pdk_root
        data["checks"]["pdk_drc"] = pdk_drc(gds_path, netlist.top, **options)
    else:
        data["checks"]["pdk_drc"] = {"clean": None, "skipped": True}
    json_path.write_text(json.dumps(data, indent=2)+"\n")
    if data["checks"]["pdk_drc"]["clean"] is False:
        raise PhysicalVerificationError(f"PDK DRC has {data['checks']['pdk_drc']['violations']} violations; see {json_path}")
    return PnrResult(gds_path, json_path, data["stats"], data)
