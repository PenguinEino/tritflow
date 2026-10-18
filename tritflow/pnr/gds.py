"""Hierarchical GDS assembly with explicit via landings and drawing-layer labels."""
from __future__ import annotations

from pathlib import Path

import klayout.db as db

DBU = .001


def box(rect):
    return db.Box(*(round(v/DBU) for v in rect))


def wire_box(wire):
    """Square-ended Manhattan conductor, including enclosure at endpoints."""
    points, w = wire["points"], wire["width"]
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return [min(xs)-w/2, min(ys)-w/2, max(xs)+w/2, max(ys)+w/2]


def write_gds(data, library, path: str | Path):
    layout = db.Layout()
    layout.dbu = DBU
    layers = {name: layout.layer(*pair) for name, pair in library.template["layers"].items()}
    top = layout.create_cell(data["top"])
    # Reading into separate layouts avoids merging same-named helper cells from
    # independently generated GDS files. copy_tree handles hierarchy and DBU.
    masters = {}
    for name in sorted({p["cell"] for p in data["placements"]}):
        physical = library.cells[name]
        master = layout.create_cell(name)
        if physical.gds:
            source = db.Layout()
            source.read(str(physical.gds))
            source_cell = source.cell(name)
            if source_cell is None:
                raise ValueError(f"GDS has no cell {name}: {physical.gds}")
            master.copy_tree(source_cell)
        else:
            if not library.mock:
                raise ValueError(f"Real library missing GDS: {name}")
            master.shapes(layers["prBoundary"]).insert(box([0, 0, physical.width, physical.height]))
            for pin in physical.pins.values():
                for rect in pin["rects"]:
                    master.shapes(layers["M1"]).insert(box(rect))
        masters[name] = master
    for pl in data["placements"]:
        physical = library.cells[pl["cell"]]
        # KLayout M90 is reflection in the Y axis: x -> -x.
        trans = (db.Trans(db.Trans.M90, round((pl["x"]+physical.width)/DBU), round(pl["y"]/DBU))
                 if pl["orient"] == "MY" else
                 db.Trans(round(pl["x"]/DBU), round(pl["y"]/DBU)))
        top.insert(db.CellInstArray(masters[pl["cell"]].cell_index(), trans))
    routing = layout.create_cell(f"{data['top']}__routing")
    top.insert(db.CellInstArray(routing.cell_index(), db.Trans()))
    power = data["power"]
    for wire in data["wires"]+power["rails"]+power["straps"]:
        routing.shapes(layers[wire["layer"]]).insert(box(wire_box(wire)))
    rules = library.template["rules"]
    cut = rules["V1"]
    for via in data["vias"]+power["vias"]:
        x, y = via["x"], via["y"]
        routing.shapes(layers["V1"]).insert(box([x-cut/2, y-cut/2, x+cut/2, y+cut/2]))
        for metal in ("M1", "M2"):
            pad = cut + 2*rules[f"V1_enc_{metal}"]
            routing.shapes(layers[metal]).insert(box([x-pad/2, y-pad/2, x+pad/2, y+pad/2]))
    for pin in data["pins"]+power["pins"]:
        x0, y0, x1, y1 = pin["rect"]
        routing.shapes(layers["M2"]).insert(box(pin["rect"]))
        top.shapes(layers["TXM2"]).insert(db.Text(pin["name"], db.Trans(round((x0+x1)/2/DBU), round((y0+y1)/2/DBU))))
    # Rail text lies on the actual M1 rail, including on mock cells without labels.
    for rail in power["rails"]:
        x, y = rail["points"][0]
        top.shapes(layers["TXM1"]).insert(db.Text(rail["net"], db.Trans(round(x/DBU), round(y/DBU))))
    # Electrical extraction decks may recognize alternate pin-text datatypes too;
    # TXM1/TXM2 drawing labels above are the contract's authoritative port labels.
    top.shapes(layers["prBoundary"]).insert(box([0, 0, *data["die"]]))
    options = db.SaveLayoutOptions()
    options.gds2_write_timestamps = False
    layout.write(str(path), options)
    return layout
