"""Draw TR-1um GDS layers with matplotlib in a print-friendly palette."""

import klayout.db as db
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch

# (layer, datatype): (label, face, edge, alpha, z)
LAYERS = {
    (140, 0): ("N-well", "#f1ecdc", "#c9bf9a", 1.0, 1),
    (3, 1): ("P diffusion", "#f6c7a6", "#d98b57", 0.9, 2),
    (3, 2): ("N diffusion", "#b5dfc6", "#5aa77c", 0.9, 2),
    (3, 3): ("Diffusion resistor", "#f3e2a0", "#c4a33c", 0.95, 2),
    (8, 1): ("Poly", "#e34948", "#b52d2c", 0.75, 4),
    (13, 0): ("Metal 1", "#2a78d6", "#1c5cab", 0.38, 5),
    (11, 0): ("Contact", "#0b0b0b", "#0b0b0b", 0.9, 6),
    (20, 0): ("Metal 2", "#6250d6", "#3f31a6", 0.38, 7),
    (19, 0): ("Via 1", "#26215c", "#26215c", 0.95, 8),
}


def polygons(path, top=None):
    """Return {(layer, datatype): [ [(x,y),...], ...]} in µm, hierarchy flattened."""
    layout = db.Layout()
    layout.read(str(path))
    cell = layout.cell(top) if top else layout.top_cells()[0]
    out = {}
    for li in layout.layer_indexes():
        info = layout.get_info(li)
        key = (info.layer, info.datatype)
        if key not in LAYERS:
            continue
        region = db.Region(cell.begin_shapes_rec(li)).merged()
        polys = []
        for p in region.each():
            pts = p.to_simple_polygon().each_point() if p.holes() else p.each_point_hull()
            polys.append([(pt.x * layout.dbu, pt.y * layout.dbu) for pt in pts])
        if polys:
            out[key] = polys
    return out, cell.dbbox()


def draw(ax, path, top=None, *, dx=0.0, dy=0.0, rasterized=False, skip=(), lw=0.25):
    polys, bbox = polygons(path, top)
    for key, (label, face, edge, alpha, z) in LAYERS.items():
        if key not in polys or key in skip:
            continue
        shifted = [[(x + dx, y + dy) for x, y in p] for p in polys[key]]
        pc = PolyCollection(shifted, facecolors=face, edgecolors=edge, linewidths=lw,
                            alpha=alpha, zorder=z, rasterized=rasterized)
        ax.add_collection(pc)
    return bbox


def legend_handles(keys=None):
    keys = keys or list(LAYERS)
    return [Patch(facecolor=LAYERS[k][1], edgecolor=LAYERS[k][2], alpha=LAYERS[k][3],
                  linewidth=0.5, label=LAYERS[k][0]) for k in keys]


def frame(ax, bbox, pad=2.0):
    ax.set_xlim(bbox.left - pad, bbox.right + pad)
    ax.set_ylim(bbox.bottom - pad, bbox.top + pad)
    ax.set_aspect("equal")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
