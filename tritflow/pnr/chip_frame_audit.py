"""Separate the organizer's immutable frame exceptions from all TritFlow geometry."""

from __future__ import annotations

import klayout.db as db

LAYERS = {"CO": 11, "M1": 13, "V1": 19, "M2": 20}


def _owned_regions(layout, top):
    """Flatten our hierarchy while skipping only the actual OSS_FRAME instance.

    Checking provenance as well as region subtraction rejects an added waiver
    even when it is placed exactly on top of a legitimate stock logo waiver.
    A stock leaf cell instantiated outside OSS_FRAME is also our geometry.
    """
    regions = {name: db.Region() for name in (*LAYERS, "waiver")}
    frame_transforms, waiver_sources = [], []

    def visit(cell, transform):
        for name, number in {**LAYERS, "waiver": 63}.items():
            layer = layout.layer(number, 0)
            shapes = [s for s in cell.shapes(layer).each() if not s.is_text()]
            if not shapes:
                continue
            region = db.Region(cell.shapes(layer)).transformed(transform)
            regions[name] += region
            if name == "waiver":
                waiver_sources.append(
                    {
                        "cell": cell.name,
                        "count": len(shapes),
                        "area_um2": region.area() * layout.dbu**2,
                    }
                )
        for instance in cell.each_inst():
            child = layout.cell(instance.cell_index)
            for placement in instance.cell_inst.each_cplx_trans():
                absolute = transform * placement
                if child.name == "OSS_FRAME":
                    frame_transforms.append(str(absolute))
                else:
                    visit(child, absolute)

    visit(layout.cell(top), db.ICplxTrans())
    return regions, frame_transforms, waiver_sources


def stock_frame_policy(drawing, mask, top, isolated_frame, frame_mask):
    """Accept only stock waivers and a delta reproduced by frame-only MDP.

    This implements the integrator's binding 2026-10-23 decision. It does not
    relax DRC item counting or permit exceptions in macro/routing/power/pads.
    All such geometry must retain an exact zero-area MDP XOR.
    """
    before, after, stock_before, stock_after = (db.Layout() for _ in range(4))
    for layout, path in (
        (before, drawing),
        (after, mask),
        (stock_before, isolated_frame),
        (stock_after, frame_mask),
    ):
        layout.read(str(path))
    if len({layout.dbu for layout in (before, after, stock_before, stock_after)}) != 1:
        raise ValueError("Stock-frame audit requires identical database units")
    unit = before.dbu**2
    owned, transforms, own_waivers = _owned_regions(before, top)
    stock_cell = stock_before.cell("OSS_FRAME")
    stock_waivers = db.Region(stock_cell.begin_shapes_rec(stock_before.layer(63, 0)))
    source_cells = []
    indices = {stock_cell.cell_index(), *stock_cell.called_cells()}
    for index in sorted(indices):
        cell = stock_before.cell(index)
        shapes = [
            s for s in cell.shapes(stock_before.layer(63, 0)).each() if not s.is_text()
        ]
        if shapes:
            source_cells.append({"cell": cell.name, "polygon_count": len(shapes)})
    waiver_report = {
        "clean": not own_waivers and transforms == [str(db.ICplxTrans())],
        "policy": "Organizer stock 63/0 polygons accepted only in the unmodified OSS_FRAME hierarchy; no TritFlow waiver geometry",
        "stock_polygon_count": sum(item["polygon_count"] for item in source_cells),
        "stock_union_area_um2": stock_waivers.merged().area() * unit,
        "stock_source_cells": source_cells,
        "frame_instances": transforms,
        "own_polygon_count": sum(item["count"] for item in own_waivers),
        "own_union_area_um2": owned["waiver"].merged().area() * unit,
        "own_sources": own_waivers,
    }
    full, stock, outside, own_overlap, remainder_counts = {}, {}, {}, {}, {}
    for name, number in LAYERS.items():

        def region(layout, cell):
            return db.Region(
                layout.cell(cell).begin_shapes_rec(layout.layer(number, 0))
            )

        delta = region(before, top) ^ region(after, top)
        frame_delta = region(stock_before, "OSS_FRAME") ^ region(
            stock_after, "OSS_FRAME"
        )
        remainder = delta - frame_delta
        full[name], stock[name] = delta.area() * unit, frame_delta.area() * unit
        outside[name], own_overlap[name] = (
            remainder.area() * unit,
            (delta & owned[name]).area() * unit,
        )
        remainder_counts[name] = sum(1 for _ in remainder.each())
    mdp_report = {
        "clean": all(v == 0 for v in (*outside.values(), *own_overlap.values())),
        "xor_area_um2": full,
        "outside_stock_frame_xor_area_um2": outside,
        "stock_frame_only_xor_area_um2": stock,
        "delta_over_own_geometry_um2": own_overlap,
        "outside_stock_frame_polygon_count": remainder_counts,
        "method": "Full-chip Region XOR minus the independently reproduced stock-frame-only MDP XOR; exact zero outside it and on owned geometry",
        "policy": "Binding integrator decision: record organizer stock-logo MDP delta; no changes to TritFlow metal",
    }
    return {
        "stock_waivers": waiver_report,
        "metal_preservation": mdp_report,
        "clean": waiver_report["clean"] and mdp_report["clean"],
    }
