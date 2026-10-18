"""Notebook and CLI entry point for the complete physical-design flow."""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

from tritflow.netlist import GateNetlist
from .gds import write_gds
from .library import Library
from .placement import RowCapacityError, pin_location, place
from .power import cell_current, draw_power, power_plan
from .router import RoutingFailure, floorplan, route
from .verify import PhysicalVerificationError, connectivity, pdk_drc, routing_drc


@dataclass
class PnrResult:
    """Exported artifacts plus the full placement/routing record for animation."""

    gds_path: Path
    json_path: Path
    stats: dict
    data: dict
    netlist: GateNetlist | None = None

    def signoff(self, **options):
        """Run optional cached MDP/IP62 qualification; inspect clean/submission_ready."""
        from .signoff import signoff
        return signoff(self, **options)


def _floorplan_choice(netlist, library, rows, channel_tracks, currents, capacity, power_options):
    """Choose a small, nearly square grid of independently powered row spans."""
    n = max(1, len(netlist.instances))
    ports = max((sum(port.dir == direction for port in netlist.ports)
                 for direction in ("input", "output")), default=0)
    p, h = library.template["grid"], library.template["height"]
    candidates = []
    for count in ([rows] if rows is not None else range(1, min(n, 48)+1)):
        minimum = 2*math.ceil(ports/(count+1))+2
        tracks = channel_tracks if channel_tracks is not None else max(
            8 if n > 32 else 4, minimum, math.ceil(len(netlist.nets())/(count+1)*.4))
        if count < 1 or tracks < minimum:
            continue
        required = max(1, math.ceil(sum(currents.values())/(capacity*count)-1e-9))
        for spans in range(required, required+3):
            if count*spans > n and n > 1:
                continue
            try:
                initial, _, _ = place(netlist, library, count, steps=0,
                    instance_currents=currents, max_row_current_a=capacity, spans=spans,
                    channel_tracks=tracks)
            except RowCapacityError:
                continue
            widths = {}
            for pl in initial:
                key = pl["row"], pl["span"]
                widths[key] = widths.get(key, 0.)+pl["width"]
            span_loads = [sum(currents[pl["inst"]] for pl in initial if pl["span"] == span)
                          for span in range(spans)]
            plan = power_plan(initial, library, **power_options,
                              span_current_limit_a=max(span_loads))
            plan["span_width"] = max(widths.values(), default=6*p)
            core_width = spans*plan["span_width"]+(spans-1)*plan["span_gap"]
            w = core_width+2*plan["margin"]
            height = count*(h+p)+(count+1)*(tracks+1)*p
            aspect = max(w/height, height/w)
            area = w*height
            candidates.append(((max(0., aspect-1.5), area, aspect, count, spans),
                               count, spans, tracks, plan, core_width))
    if not candidates:
        raise ValueError("No legal floorplan: check rows, channel tracks and cell current capacity")
    _, count, spans, tracks, plan, core_width = min(candidates, key=lambda c: c[0])
    return count, spans, tracks, plan, core_width


def place_and_route(netlist, library=None, *, output_dir=None, rows=None, seed=0,
                    anneal_steps=600, history_every=25, channel_tracks=None,
                    max_expansions=5, ripup_passes=8, run_pdk_drc=True,
                    current_density_a_per_um=.00025, default_cell_current_a=.0001,
                    sheet_resistance_ohm=.05, pdk_root=None, klayout_binary=None):
    """Place, route, export and verify a combinational GateNetlist.

    The default library is re-discovered on every call, so a newly published real
    library replaces provisional mocks automatically. A mock result is identified
    in both JSON and stats; it is never evidence of transistor-level correctness.
    DRC failures retain GDS, JSON and reports for inspection, then raise.

    ``rows=None`` chooses a near-square die including power feed banks and
    routing channels. An explicit positive ``rows`` fixes the physical row
    count; more internal feeds are added if its rails require them.
    ``anneal_steps=600`` is a bounded placement effort; zero shows the initial
    signal-flow placement. Both knobs are suitable for notebook comparisons.
    """
    started = time.perf_counter()
    if isinstance(netlist, (str, Path)):
        netlist = GateNetlist.load(netlist)
    elif isinstance(netlist, dict):
        netlist = GateNetlist.from_dict(netlist)
    if not netlist.top or netlist.top in {i.cell for i in netlist.instances} or any(c in netlist.top for c in "/\\"):
        raise ValueError("Top name must be a safe GDS name distinct from cell masters")
    if max_expansions < 0 or ripup_passes < 1:
        raise ValueError("Invalid routing retry limits")
    if rows is not None and (not isinstance(rows, int) or rows < 1):
        raise ValueError("rows must be a positive integer or None")
    out = Path(output_dir or Path("build")/netlist.top)
    out.mkdir(parents=True, exist_ok=True)
    failure_path = out/f"{netlist.top}.pnr.failure.json"
    if library is None:
        library = Library.automatic()
    elif isinstance(library, (str, Path)):
        library = Library.load(library)
    library.validate()
    currents = {inst.name: cell_current(library.cells[inst.cell],
        0. if inst.cell in ("FILL", "TIEP", "TIEZ", "TIEN") else default_cell_current_a)[0]
                for inst in netlist.instances}
    capacity = 2*current_density_a_per_um*min(y1-y0 for y0, y1 in library.template["rails"].values())
    power_options = dict(current_density_a_per_um=current_density_a_per_um,
                         default_cell_current_a=default_cell_current_a,
                         sheet_resistance_ohm=sheet_resistance_ohm)
    power_plan([], library, **power_options)  # Validate assumptions before sizing rows.
    row_count, spans, tracks, plan, core_width = _floorplan_choice(
        netlist, library, rows, channel_tracks, currents, capacity, power_options)
    relative, history, _ = place(netlist, library, row_count, seed, anneal_steps, history_every,
        instance_currents=currents, max_row_current_a=capacity, spans=spans,
        span_width=plan["span_width"], span_gap=plan["span_gap"], channel_tracks=tracks,
        span_current_limit_a=plan["span_current_limit_a"])
    placed_at = time.perf_counter()
    compact_metal = any(cell.obstructions.get("M2") or cell.obstructions.get("V1") or cell.free_tracks
                        for cell in library.cells.values())
    bypass_tracks = 0
    attempts = []
    for expansion in range(max_expansions+1):
        data, terminals = floorplan(netlist, library, relative, row_count,
                                    plan["margin"]+bypass_tracks*library.template["grid"], tracks,
                                    core_width=core_width)
        data["routing_corridors"] = {"bypass_tracks_per_side": bypass_tracks}
        data.update({"top": netlist.top, "schema": "tritflow.pnr.v1", "seed": seed,
                     "library": {"source": library.source, "mock": library.mock,
                         "cells": {name: {"width": cell.width, "height": cell.height,
                                          "free_tracks": cell.free_tracks, "routing": cell.routing}
                                   for name, cell in library.cells.items()}}})
        draw_power(data, data["placements"], library,
                   {**plan, "margin": plan["margin"]+bypass_tracks*library.template["grid"]})
        try:
            log = route(data, terminals, library, seed+expansion, ripup_passes)
            attempts.append({"channel_tracks": tracks, "bypass_tracks_per_side": bypass_tracks,
                             "ripped_up": log, "success": True})
            break
        except RoutingFailure as error:
            attempts.append({"channel_tracks": tracks, "bypass_tracks_per_side": bypass_tracks, "failed_net": error.net, "reason": str(error),
                             "ripped_up": getattr(error, "ripup_log", []), "success": False})
            if expansion == max_expansions or "access conflicts" in str(error):
                failure = RoutingFailure(error.net,
                    f"{error.reason}; exhausted {len(attempts)} floorplan attempts",
                    region=error.region_um, blocking_nets=error.blocking_nets,
                    failed_nets=[a["failed_net"] for a in attempts])
                failure_path.write_text(json.dumps({"status": "failed", "top": netlist.top,
                    "error": str(failure), "failed_nets": failure.failed_nets,
                    "region_um": failure.region_um, "blocking_nets": failure.blocking_nets,
                    "routing_attempts": attempts}, indent=2)+"\n")
                raise failure from error
            # Expansion of all channels gives the blocked net alternative paths
            # through neighboring rows, rather than only increasing one cut.
            tracks += 2 if compact_metal else max(2, math.ceil(tracks*.3))
            if compact_metal:
                bypass_tracks += 1
    routed_at = time.perf_counter()
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
        "instance_count": len(netlist.instances), "row_count": len(data["rows"]), "net_count": len(netlist.nets()),
        "spans_per_row": spans, "channel_tracks": tracks,
        "aspect_ratio": max(data["die"])/min(data["die"]),
        "anneal_steps": anneal_steps,
        "routed_nets": len(terminals), "library_mock": library.mock,
        "max_supply_drop_v": data["power"]["ir_drop"]["max_drop_v"],
        "bypass_tracks_per_side": bypass_tracks,
        "hpwl_before_um": history[0]["hpwl"], "hpwl_after_um": history[-1]["hpwl"],
        "hpwl_improvement_pct": (100*(1-history[-1]["hpwl"]/history[0]["hpwl"])
                                 if history[0]["hpwl"] else 0.)}
    gds_path, json_path = out/f"{netlist.top}.gds", out/f"{netlist.top}.pnr.json"
    candidate = out/f"{netlist.top}.candidate.gds"
    write_gds(data, library, candidate)
    data["checks"] = {"connectivity": connectivity(candidate, data, netlist, library),
                      "routing_drc": routing_drc(candidate, data, library)}
    own_clean = all(c["clean"] for c in data["checks"].values())
    if not own_clean:
        failed = out/f"{netlist.top}.failed.gds"
        candidate.replace(failed)
        failure_path.write_text(json.dumps({**data, "status": "failed", "gds_path": str(failed)}, indent=2)+"\n")
        raise PhysicalVerificationError(f"Physical self-check failed: {data['checks']}; inspect {failure_path} and {failed}; canonical GDS was not published")
    if run_pdk_drc:
        options = {"binary": klayout_binary}
        if pdk_root is not None:
            options["pdk_root"] = pdk_root
        try:
            data["checks"]["pdk_drc"] = pdk_drc(candidate, netlist.top,
                report_path=out/f"{netlist.top}.drc.lyrdb", **options)
        except Exception:
            candidate.replace(out/f"{netlist.top}.failed.gds")
            failure_path.write_text(json.dumps({**data, "status": "verification_failed"}, indent=2)+"\n")
            raise
    else:
        data["checks"]["pdk_drc"] = {"clean": None, "skipped": True}
    if data["checks"]["pdk_drc"]["clean"] is False:
        failed = out/f"{netlist.top}.failed.gds"
        candidate.replace(failed)
        failure_path.write_text(json.dumps({**data, "status": "failed", "gds_path": str(failed)}, indent=2)+"\n")
        raise PhysicalVerificationError(f"PDK DRC has {data['checks']['pdk_drc']['violations']} violations; inspect {failure_path} and {failed}; canonical GDS was not published")
    candidate.replace(gds_path)
    if run_pdk_drc:
        data["checks"]["pdk_drc"]["command"] = [s.replace(str(candidate.resolve()), str(gds_path.resolve()))
                                                for s in data["checks"]["pdk_drc"]["command"]]
    finished = time.perf_counter()
    data["stats"]["runtime_s"] = {"placement": placed_at-started,
        "routing": routed_at-placed_at, "export_and_verification": finished-routed_at,
        "total": finished-started}
    json_path.write_text(json.dumps(data, indent=2)+"\n")
    failure_path.unlink(missing_ok=True)
    return PnrResult(gds_path, json_path, data["stats"], data, netlist)
