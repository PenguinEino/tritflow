"""Notebook views of physical GDS, net routes, placement and routing progress.

All Plotly functions return ordinary Figures: use ``.show()`` in a notebook or
``.write_html(...)`` for a standalone interactive artifact. Coordinates are µm.
The GDS raster is rendered by KLayout's LayoutView, not redrawn from abstracts.
"""
from __future__ import annotations

import json
from pathlib import Path

# A small, fixed drawing palette keeps raster and vector layer names consistent.
LAYERS = (
    ("N-well", (140, 0), "#b7d6e8"),
    ("P diffusion", (3, 1), "#ed9ab0"),
    ("N diffusion", (3, 2), "#9acc88"),
    ("Diffusion resistor", (3, 3), "#bd9cdb"),
    ("Gate poly", (8, 1), "#b94456"),
    ("Resistor poly", (8, 2), "#b17c49"),
    ("Contact", (11, 0), "#42464c"),
    ("M1", (13, 0), "#2869ae"),
    ("V1", (19, 0), "#da9a22"),
    ("M2", (20, 0), "#b43d8a"),
    ("Boundary", (235, 0), "#778493"),
)
METAL_COLORS = {"M1": "#2869ae", "M2": "#b43d8a", "V1": "#da9a22"}
CELL_COLORS = {"INV": "#d2e5f1", "NANY": "#d8d2eb", "NAND": "#d5e8d2", "NOR": "#f2dec1"}


def _data(pnr):
    if hasattr(pnr, "data"):
        return pnr.data
    return json.loads(Path(pnr).read_text()) if isinstance(pnr, (str, Path)) else pnr


def render_gds(gds_path, output_path=None, *, top=None, width=1400, height=950):
    """Save a KLayout raster with an embedded layer legend and return its Path.

    Uses the headless pip ``klayout.lay`` renderer; no display server or Qt app
    is required. The legend lists only layers present in this GDS hierarchy.
    Device layers retain their actual PDK drawing-layer numbers.
    """
    import tempfile
    import klayout.db as db
    import klayout.lay as lay
    from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

    gds_path = Path(gds_path)
    output = Path(output_path or gds_path.with_suffix(".png"))
    output.parent.mkdir(parents=True, exist_ok=True)
    if width < 500 or height < 300:
        raise ValueError("Raster must be at least 500 × 300 pixels to fit the legend")
    view = lay.LayoutView()
    try:
        view.load_layout(str(gds_path), 0)
        cv = view.cellview(0)
        cell = cv.layout().cell(top) if top else cv.layout().top_cell()
        if cell is None:
            raise ValueError(f"No GDS top cell {top}")
        cv.cell = cell
        view.clear_layers()
        active = []
        for name, pair, color in LAYERS:
            index = cv.layout().find_layer(*pair)
            if index is None or db.Region(cell.begin_shapes_rec(index)).is_empty():
                continue
            node = lay.LayerPropertiesNode()
            node.source = f"{pair[0]}/{pair[1]}@1"
            node.name = name
            node.fill_color = int(color[1:], 16)
            node.frame_color = int(color[1:], 16)
            node.dither_pattern = 1 if name in ("Boundary", "N-well") else 0
            view.insert_layer(view.end_layers(), node)
            active.append((name, pair, color))
        view.max_hier_levels = 100
        view.min_hier_levels = 0
        for key, value in (("background-color", "#ffffff"), ("grid-visible", "false"),
                           ("text-visible", "false"), ("cell-box-visible", "false")):
            view.set_config(key, value)
        view.zoom_fit()
        with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
            raw = Path(temporary)/"klayout.png"
            legend_width, header = 225, 54
            view.save_image(str(raw), width-legend_width, height-header)
            canvas = Image.new("RGB", (width, height), "white")
            with Image.open(raw) as image:
                canvas.paste(image.convert("RGB"), (0, header))
        draw = ImageDraw.Draw(canvas)
        # Pillow's bundled font is portable; installed DejaVu improves notebook text.
        try:
            from matplotlib.font_manager import findfont
            font_path = findfont("DejaVu Sans")
            font = ImageFont.truetype(font_path, 15)
            title_font = ImageFont.truetype(font_path, 20)
        except (ImportError, OSError):
            font = title_font = ImageFont.load_default()
        bbox = cell.dbbox()
        draw.text((18, 13), f"{cell.name}  |  {bbox.width():g} × {bbox.height():g} µm", fill="#223044", font=title_font)
        x = width-legend_width+16
        draw.line((x-12, header, x-12, height-15), fill="#d8dee8", width=1)
        draw.text((x, header+12), "Drawing layers", fill="#223044", font=font)
        for i, (name, (layer, datatype), color) in enumerate(active):
            y = header+48+i*34
            draw.rectangle((x, y, x+17, y+17), fill=color)
            draw.text((x+26, y-1), f"{name}  {layer}/{datatype}", fill="#344054", font=font)
        draw.text((x, height-50), "KLayout raster", fill="#667085", font=font)
        draw.text((x, height-29), "Coordinates in µm", fill="#667085", font=font)
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Renderer", "KLayout LayoutView")
        metadata.add_text("Layer legend", json.dumps([{ "name": n, "layer": list(p)} for n, p, _ in active]))
        canvas.save(output, pnginfo=metadata)
    finally:
        view.destroy()
    return output


def _cell_traces(data, placements=None, highlight=None):
    import plotly.graph_objects as go
    traces = []
    for pl in placements if placements is not None else data["placements"]:
        cell_info = data.get("library", {}).get("cells", {}).get(pl["cell"], {})
        w, h = pl.get("width", cell_info.get("width")), pl.get("height", cell_info.get("height"))
        if w is None or h is None:
            raise ValueError("Cell dimensions missing: rebuild PNR JSON with the current exporter")
        x, y = pl["x"], pl["y"]
        selected = pl["inst"] == highlight or (highlight is not None and pl.get("hier") == highlight)
        text = f"{pl['inst']} · {pl['cell']}<br>Hierarchy: {pl.get('hier') or '(top)'}<br>{pl['orient']} · {w:g} × {h:g} µm"
        traces.append(go.Scatter(x=[x, x+w, x+w, x, x], y=[y, y, y+h, y+h, y],
            mode="lines", fill="toself", fillcolor="#ffe3a3" if selected else CELL_COLORS.get(pl["cell"], "#e3e7ed"),
            line={"color": "#e58b12" if selected else "#8c98aa", "width": 3 if selected else 1},
            text=text, hovertemplate="%{text}<extra></extra>", name=pl["inst"], showlegend=False,
            meta={"kind": "cell", "inst": pl["inst"], "hier": pl.get("hier", ""), "cell": pl["cell"]}))
    return traces


def _route_trace(net, layer, wires, vias=(), *, selected=False, faded=False):
    import plotly.graph_objects as go
    xs, ys = [], []
    for wire in wires:
        for x, y in wire["points"]:
            xs.append(x); ys.append(y)
        xs.append(None); ys.append(None)
    if layer == "V1":
        xs, ys = [v["x"] for v in vias], [v["y"] for v in vias]
    color = "#e47712" if selected else METAL_COLORS[layer]
    return go.Scatter(x=xs, y=ys, mode="markers" if layer == "V1" else "lines",
        line={"color": color, "width": 4 if selected else 1.5},
        marker={"color": color, "size": 5 if selected else 3, "symbol": "square"},
        opacity=.12 if faded else 1., name=f"{net} · {layer}", legendgroup=net, showlegend=False,
        hovertemplate=f"{net} · {layer}<br>x=%{{x:g}} µm · y=%{{y:g}} µm<extra></extra>",
        meta={"kind": "route", "net": net, "layer": layer})


def _axes(fig, data, title):
    w, h = data["die"]
    fig.update_layout(title=title, template="plotly_white", height=720,
        margin={"l": 55, "r": 25, "t": 105, "b": 55}, hovermode="closest",
        xaxis={"title": "x (µm)", "range": [-w*.02, w*1.02]},
        yaxis={"title": "y (µm)", "range": [-h*.02, h*1.02], "scaleanchor": "x", "scaleratio": 1})
    return fig


def layout_figure(pnr, *, highlight_net=None, highlight_instance=None, show_power=False, controls=True):
    """Vector route view with net/instance selectors, hierarchy hover and equal axes.

    Any named signal or supply can be selected programmatically. Dropdowns work
    in exported HTML without a Python kernel. Cell highlight accepts an instance
    name or its source hierarchy path. Wire thickness is schematic in pixels;
    physical widths and the actual polygons are in the PNR record/GDS raster.
    """
    import plotly.graph_objects as go
    data = _data(pnr)
    fig = go.Figure(_cell_traces(data, highlight=highlight_instance))
    wires, vias = list(data["wires"]), list(data["vias"])
    power = data.get("power", {})
    if show_power or highlight_net in ("VDD", "VMID", "VSS"):
        wires += power.get("rails", [])+power.get("straps", [])
        vias += power.get("vias", [])
    nets = sorted({w["net"] for w in wires} | {v["net"] for v in vias} | {p["name"] for p in data["pins"]})
    if highlight_net is not None and highlight_net not in nets:
        raise ValueError(f"Unknown net: {highlight_net}")
    if highlight_instance is not None and not any(highlight_instance in (p["inst"], p.get("hier")) for p in data["placements"]):
        raise ValueError(f"Unknown cell instance/hierarchy: {highlight_instance}")
    for net in nets:
        for layer in ("M1", "M2", "V1"):
            selected_wires = [w for w in wires if w["net"] == net and w["layer"] == layer]
            selected_vias = [v for v in vias if v["net"] == net]
            fig.add_trace(_route_trace(net, layer, selected_wires, selected_vias,
                selected=net == highlight_net, faded=highlight_net is not None and net != highlight_net))
    # External terminal markers include otherwise unused input ports.
    for pin in data["pins"]:
        x0, y0, x1, y1 = pin["rect"]
        fig.add_trace(go.Scatter(x=[(x0+x1)/2], y=[(y0+y1)/2], mode="markers", name=pin["name"],
            marker={"size": 7, "symbol": "diamond", "color": "#273d57"}, showlegend=False,
            hovertemplate=f"Port {pin['name']}<extra></extra>", meta={"kind": "port", "net": pin["name"]}))
    # Legend has one entry per physical routing layer rather than hundreds of nets.
    for layer, color in METAL_COLORS.items():
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line={"color": color},
                                name=layer, showlegend=True, meta={"kind": "legend"}))
    _axes(fig, data, f"{data['top']} · physical routing")
    if controls:
        route_indices = [i for i, trace in enumerate(fig.data)
                         if (trace.meta or {}).get("kind") in ("route", "port")]
        def net_style(chosen):
            opacity, colors, widths, sizes = [], [], [], []
            for i in route_indices:
                meta = fig.data[i].meta
                selected = chosen is not None and meta.get("net") == chosen
                opacity.append(.12 if chosen and not selected else 1.)
                colors.append("#e47712" if selected else METAL_COLORS.get(meta.get("layer"), "#273d57"))
                widths.append(4 if selected else 1.5)
                sizes.append(7 if meta["kind"] == "port" else 5 if selected else 3)
            return {"opacity": opacity, "line.color": colors, "line.width": widths,
                    "marker.color": colors, "marker.size": sizes}
        net_buttons = [{"label": "All nets", "method": "restyle", "args": [net_style(None), route_indices]}]
        net_buttons += [{"label": n, "method": "restyle", "args": [net_style(n), route_indices]} for n in nets]
        cell_buttons = []
        for chosen in [None]+[p["inst"] for p in data["placements"]]:
            fills, colors, widths = [], [], []
            for pl in data["placements"]:
                selected = pl["inst"] == chosen
                fills.append("#ffe3a3" if selected else CELL_COLORS.get(pl["cell"], "#e3e7ed"))
                colors.append("#e58b12" if selected else "#8c98aa")
                widths.append(3 if selected else 1)
            label = "All cells" if chosen is None else next(
                f"{p['inst']} · {p.get('hier') or '(top)'}" for p in data["placements"] if p["inst"] == chosen)
            cell_buttons.append({"label": label, "method": "restyle",
                "args": [{"fillcolor": fills, "line.color": colors, "line.width": widths}, list(range(len(fills)))]})
        fig.update_layout(updatemenus=[
            {"buttons": net_buttons, "x": 0., "y": 1.12, "xanchor": "left", "active": 0},
            {"buttons": cell_buttons, "x": .45, "y": 1.12, "xanchor": "left", "active": 0}])
    return fig


def _animation_controls(names, prefix):
    return {"updatemenus": [{"type": "buttons", "direction": "left", "x": 0., "y": 1.15,
        "buttons": [{"label": "Play", "method": "animate", "args": [None,
            {"frame": {"duration": 180, "redraw": True}, "fromcurrent": True}]},
                    {"label": "Pause", "method": "animate", "args": [[None],
            {"frame": {"duration": 0}, "mode": "immediate"}]}]}],
        "sliders": [{"currentvalue": {"prefix": prefix}, "steps": [
            {"label": n, "method": "animate", "args": [[n],
             {"mode": "immediate", "frame": {"duration": 0, "redraw": True}, "transition": {"duration": 0}}]}
            for n in names]}]}


def placement_animation(pnr):
    """Linked cell-placement animation and HPWL trajectory using saved snapshots."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    data = _data(pnr)
    history = data.get("history", [])
    if not history:
        raise ValueError("PNR record has no placement history")
    fig = make_subplots(rows=1, cols=2, column_widths=[.68, .32],
                        subplot_titles=("Placement", "Cell-terminal HPWL"))
    for trace in _cell_traces(data, history[0]["placements"]):
        fig.add_trace(trace, row=1, col=1)
    steps, hpwl = [s["step"] for s in history], [s["hpwl"] for s in history]
    fig.add_trace(go.Scatter(x=steps, y=hpwl, mode="lines", line={"color": "#2869ae"}, name="HPWL"), row=1, col=2)
    fig.add_trace(go.Scatter(x=[steps[0]], y=[hpwl[0]], mode="markers", marker={"color": "#e47712", "size": 10}, name="Current step"), row=1, col=2)
    count = len(data["placements"])
    frames = []
    for snapshot in history:
        traces = _cell_traces(data, snapshot["placements"])
        traces.append(go.Scatter(x=[snapshot["step"]], y=[snapshot["hpwl"]], mode="markers"))
        frames.append(go.Frame(name=str(snapshot["step"]), data=traces,
                               traces=list(range(count))+[count+1]))
    fig.frames = frames
    w, h = data["die"]
    fig.update_xaxes(title_text="x (µm)", range=[-w*.02, w*1.02], row=1, col=1)
    fig.update_yaxes(title_text="y (µm)", range=[-h*.02, h*1.02], scaleanchor="x", scaleratio=1, row=1, col=1)
    fig.update_xaxes(title_text="Annealing step", row=1, col=2)
    fig.update_yaxes(title_text="HPWL (µm)", row=1, col=2)
    fig.update_layout(title=f"{data['top']} · placement annealing", template="plotly_white", height=700,
                      showlegend=False, margin={"t": 120}, **_animation_controls([f.name for f in frames], "Step "))
    return fig


def routing_progress(pnr):
    """Replay cumulative nets from the successful maze-routing pass.

    Frames use the recorded routing order, rather than pretending sorted JSON
    wire order is the route chronology. Failed/ripped-up passes remain available
    in ``routing_attempts``; the animation explicitly shows the successful pass.
    """
    import plotly.graph_objects as go
    data = _data(pnr)
    if "routing_order" not in data:
        raise ValueError("PNR record lacks routing_order; rebuild to record routing progress")
    fig = layout_figure(data, controls=False)
    order = data["routing_order"]
    rank = {net: i+1 for i, net in enumerate(order)}
    frames = []
    for step in range(len(order)+1):
        updates, indices = [], []
        for i, trace in enumerate(fig.data):
            meta = trace.meta or {}
            if meta.get("kind") == "route":
                indices.append(i)
                updates.append(go.Scatter(visible=rank.get(meta["net"], 0) <= step))
        frames.append(go.Frame(name=str(step), data=updates, traces=indices,
            layout={"title": f"{data['top']} · successful routing pass · {step}/{len(order)} nets"}))
    fig.frames = frames
    for trace in fig.data:
        if (trace.meta or {}).get("kind") == "route":
            trace.visible = False
    fig.update_layout(title=f"{data['top']} · successful routing pass · 0/{len(order)} nets",
                      **_animation_controls([f.name for f in frames], "Routed nets "))
    return fig


def save_layout_views(pnr, gds_path=None, output_dir=None):
    """Write the raster and three notebook figures beside a PNR result."""
    data = _data(pnr)
    if gds_path is None and hasattr(pnr, "gds_path"):
        gds_path = pnr.gds_path
    if gds_path is None:
        raise ValueError("gds_path is required for a plain PNR dictionary/path")
    out = Path(output_dir or Path(gds_path).parent)
    out.mkdir(parents=True, exist_ok=True)
    stem = data["top"]
    paths = {"png": render_gds(gds_path, out/f"{stem}.layout.png", top=stem)}
    for suffix, figure in (("layout", layout_figure(data, show_power=True)),
                           ("placement", placement_animation(data)),
                           ("routing", routing_progress(data))):
        path = out/f"{stem}.{suffix}.html"
        figure.write_html(path, include_plotlyjs=True, full_html=True)
        paths[suffix] = path
    return paths
