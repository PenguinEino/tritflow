"""Chapter 3 views: the closure of one-input functions per cell basis, the library's truth tables,
and the standard cells drawn side by side at one scale.

Truth tables come from each cell's published ``*.truth.json``; geometry from its GDS. Nothing
here runs a tool; the chapter's own cells run the closure and the PDK checks.
"""

from html import escape
from itertools import product
import json
import re

from IPython.display import HTML, display

from live import _layer_paths, _patterns, LayoutView, layer_legend
from style import MUTED, RULE, SERIF, TRIT_COLOR as COLOR, TRIT_TEXT, figure_css, table_css
_VIEWS = 0


def _key(prefix):
    global _VIEWS
    _VIEWS += 1
    return f"{prefix}{_VIEWS}"


def closure_view(found):
    """Booktabs table of the construction, one row per round: the one-input functions that first
    appear in it, each written as its outputs at a = −1, 0, +1, and the running count out of 27."""
    names = {(-1, 0, 1): "a", (1, 0, -1): "−a", (1, 1, 1): "定数 +1", (0, 0, 0): "定数 0", (-1, -1, -1): "定数 −1"}

    def function(f):
        digits = ", ".join(f'<span style="color:{COLOR[v]}">{TRIT_TEXT[v]}</span>' for v in f)
        name = f' <span class="n">{names[f]}</span>' if f in names else ""
        return f'<span class="f">({digits}){name}</span>'

    rounds = sorted(set(found.values()))
    total, rows = 0, []
    for r in rounds:
        new = sorted((f for f, g in found.items() if g == r), key=lambda f: (f not in names, f))
        total += len(new)
        rows.append(f'<tr><td>{r}</td><td class="l">{" ".join(function(f) for f in new)}</td><td>{total} / 27</td></tr>')
    display(HTML(f'<style>{figure_css(".tfclosure")}{table_css(".tfclosure")}'
                 f'.tfclosure td.l{{text-align:left;line-height:1.9}} .tfclosure .f{{white-space:nowrap;margin-right:1.1em}}'
                 f'.tfclosure .n{{color:{MUTED};font-size:12.5px}}</style><div class="tfclosure"><table>'
                 f'<tr><th>段</th><th>新しく作れた1入力関数<small>a = −1, 0, +1 のときの出力</small></th><th>累計</th></tr>'
                 f'{"".join(rows)}</table></div>'))


FORMULA = {"INV": "Y = −A", "BUF": "Y = A", "NAND": "Y = −min(A, B)", "NOR": "Y = −max(A, B)",
           "NANY": "Y = −sat(A + B)", "TIEP": "Y = +1", "TIEZ": "Y = 0", "TIEN": "Y = −1"}


def _truth_grid(rows):
    """3×3 for two inputs (A down, B across), one row for one input, one cell for a tie."""
    def cell(v):
        return f'<td class="t{v+1}">{TRIT_TEXT[v]}</td>'
    inputs = list(rows[0]["inputs"]) if rows else []
    if len(inputs) == 2:
        table = {(r["inputs"]["A"], r["inputs"]["B"]): r["Y"] for r in rows}
        head = "<tr><th>A＼B</th>" + "".join(f"<th>{TRIT_TEXT[b]}</th>" for b in (-1, 0, 1)) + "</tr>"
        body = "".join(f"<tr><th>{TRIT_TEXT[a]}</th>" + "".join(cell(table[a, b]) for b in (-1, 0, 1)) + "</tr>"
                       for a in (-1, 0, 1))
        return f'<table >{head}{body}</table>'
    if len(inputs) == 1:
        head = "<tr><th>A</th>" + "".join(f"<th>{TRIT_TEXT[r['inputs']['A']]}</th>" for r in rows) + "</tr>"
        return f'<table >{head}<tr><th>Y</th>{"".join(cell(r["Y"]) for r in rows)}</tr></table>'
    return f'<table ><tr><th>Y</th>{cell(rows[0]["Y"])}</tr></table>'


def _symbol(kind):
    """The cell's symbol exactly as the gate-level schematics draw it, small, with pin names."""
    from tritflow.schematic.model import Symbol
    from tritflow.schematic.placement import anchors
    from tritflow.schematic.render import _symbol as draw
    from tritflow.schematic.vector import Vector
    v = Vector(150, 120, font_min=12)
    node = Symbol(kind, kind, "", x=35, y=12, width=80, height=96)
    if kind.startswith("TIE"):
        node.outputs = {"Y": "y"}
    else:
        node.inputs = {"A": "a"} if kind in {"INV", "BUF"} else {"A": "a", "B": "b"}
        node.outputs = {"Y": "y"}
    anchors(node)
    draw(v, node)
    svg = v.svg(kind)
    svg = svg[svg.index("<svg"):]
    # Crop the canvas to the drawn strokes (and any label above them), so the symbol has no margin.
    points = [tuple(map(float, xy)) for d in re.findall(r' d="([^"]+)"', svg)
              for xy in re.findall(r"(-?[\d.]+) (-?[\d.]+)", d)]
    points += [(float(x)+dx, float(y)+dy) for x, y, r in re.findall(r'cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', svg)
               for dx in (-float(r), float(r)) for dy in (-float(r), float(r))]
    points += [(float(x), float(y)-12) for x, y, t in re.findall(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*>([^<]+)</text>', svg)]
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    x0, y0, w, h = min(xs)-6, min(ys)-6, max(xs)-min(xs)+12, max(ys)-min(ys)+12
    svg = re.sub(r'width="[\d.]+" height="[\d.]+" viewBox="[^"]+"', f'width="{w*.8:g}" height="{h*.8:g}" viewBox="{x0:g} {y0:g} {w:g} {h:g}"', svg, count=1)
    return svg.replace('<rect width="100%" height="100%" fill="white"/>',
                       f'<rect x="{x0-4:g}" y="{y0-4:g}" width="{w+8:g}" height="{h+8:g}" fill="white"/>')


def cell_tables(cells_dir, schematics_dir):
    """Every logic cell's truth table in colour; the taped-out schematics folded underneath as one
    grid of equal-width figures, so opening them does not reflow the tables."""
    cards, figures = [], []
    for name, formula in FORMULA.items():
        rows = json.loads((cells_dir/name/f"{name}.truth.json").read_text())
        cards.append(f'<div class="card"><div class="t"><b>{name}</b> <span>{escape(formula)}</span></div>'
                     f'<div class="sym">{_symbol(name)}</div>{_truth_grid(rows)}</div>')
        schematic = schematics_dir/f"{name}.compact.svg"
        if schematic.is_file():
            figures.append(f'<figure><figcaption>{name}</figcaption>{schematic.read_text()}</figure>')
    style = (figure_css(".tfcells") + table_css(".tfcells") +
             ".tfcells{max-width:1100px} .tfcells .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,180px),1fr));gap:1.4em;align-items:start}"
             f".tfcells .card{{min-width:0}} .tfcells .t{{margin-bottom:.3em}} .tfcells .t span{{color:{MUTED}}}"
             ".tfcells .sym{height:56px;display:flex;align-items:center;margin:.3em 0 .4em} .tfcells .sym svg{display:block}"
             ".tfcells details{margin-top:1em} .tfcells summary{cursor:pointer}"
             ".tfcells .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:1.4em 1.5em;margin-top:.6em;align-items:start}"
             ".tfcells figure{margin:0;min-width:0} .tfcells figcaption{font-weight:600;margin-bottom:.2em}"
             ".tfcells figure svg{width:100%;max-width:540px;height:auto;display:block;margin:0 auto}")
    display(HTML(f'<style>{style}</style><div class="tfcells"><div class="cards">{"".join(cards)}</div>'
                 f'<details><summary>テープアウトした回路図（Xschem）</summary><div class="grid">{"".join(figures)}</div>'
                 f'</details></div>'))


# Device outlines on the cell drawings: one colour per device kind, named once in the caption.
DEVICE = {"PMOS": ("#c2185b", "PMOS"), "NMOS": ("#1565c0", "NMOS"), "F_RR": ("#2e7d32", "RR")}


def _device_marks(name, x, unit, margin=3.0):
    """Dashed outlines around each transistor and resistor of cell ``name`` placed at ``x``, from
    the LVS device pairs and the actual GDS geometry (``tritflow.viz.cell.device_locations``)."""
    from tritflow.viz.cell import device_locations
    marks = []
    for row in device_locations(name):
        color, _ = DEVICE[row["model"]]
        left, bottom, right, top = row["bbox_um"]
        marks.append(f'<rect x="{x+left-margin:g}" y="{-(top+margin):g}" width="{right-left+2*margin:g}" '
                     f'height="{top-bottom+2*margin:g}" fill="{color}" fill-opacity=".10" stroke="{color}" '
                     f'stroke-width="{1.6*unit:g}" stroke-dasharray="{4*unit:g} {2.5*unit:g}"/>')
    return "".join(marks)


def cell_row(library, cells_dir, *, groups=(("INV", "NAND", "NOR", "NANY"), ("BUF", "TIEP", "TIEZ", "TIEN", "FILL")),
             gap=8.0):
    """Every standard cell from its GDS, wrapping at one common scale, with the template's rails
    named and every PMOS, NMOS and RR outlined. The layout is drawn a little faded so the outlines
    read first."""
    view = LayoutView(cells_dir.parent)
    template = json.loads((cells_dir.parent/"template.json").read_text())
    widths = {cell["name"]: cell["width"] for cell in library}
    height = template["height"]
    # A fixed drawing scale lets narrow outputs wrap cells without shrinking their labels.
    unit = .75
    pad = 46*unit
    rails = template["rails"]
    rail_labels = (f'<text x="{-6*unit:g}" y="{-sum(rails["VDD"])/2+3*unit:g}" font-size="{11*unit:g}" text-anchor="end">VDD</text>'
                   f'<text x="{-6*unit:g}" y="{-rails["VMID"][1]+2*unit:g}" font-size="{11*unit:g}" text-anchor="end">VMID</text>'
                   f'<text x="{-6*unit:g}" y="{-rails["VSS"][0]+7*unit:g}" font-size="{11*unit:g}" text-anchor="end">VSS</text>')
    pictures, drawn = [], []
    for group in groups:
        row = []
        for name in group:
            drawn += view._cell(name)
            cx = widths[name]/2
            label = (f'<text x="{cx:g}" y="{20*unit:g}" font-size="{14*unit:g}" text-anchor="middle" '
                         f'font-weight="700">{name}</text><text x="{cx:g}" y="{38*unit:g}" font-size="{12*unit:g}" '
                         f'text-anchor="middle" fill="{MUTED}">{widths[name]:g} µm</text>')
            span = widths[name]+pad+8*unit
            row.append(
                f'<svg viewBox="{-pad:g} {-height-8*unit:g} {span:g} {height+48*unit:g}" '
                f'style="width:{span/unit:g}px;max-width:100%;height:auto;display:block;font-family:{SERIF}" fill="#0b0b0b">'
                f'<defs>{_patterns(unit)}</defs><g transform="scale(1,-1)" opacity=".55">{_layer_paths(view._cell(name), unit)}</g>'
                f'{_device_marks(name, 0, unit)}{rail_labels}{label}</svg>')
        pictures.append(f'<div class="group">{"".join(row)}</div>')
    style = figure_css(".tfrow") + f'.tfrow .group{{display:flex;flex-wrap:wrap;gap:1em {gap/unit:g}px;align-items:start}}'
    display(HTML(f'<style>{style}</style><div class="tfrow" style="max-width:1100px">'
                 f'<div style="border-top:1.4px solid #0b0b0b;border-bottom:1.4px solid #0b0b0b;padding:6px 0">{"".join(pictures)}</div>'
                 f'<div style="font-size:13px;margin-top:.4em;line-height:1.9">{layer_legend(drawn, unit, opacity=.55)}</div>'
                 f'<div style="font-size:13px;margin-top:.1em">' + "　".join(
                     f'<span style="display:inline-block;width:14px;height:9px;border:1.5px dashed {c};background:{c}1a;'
                     f'vertical-align:middle;margin-right:4px"></span>{label}' for c, label in DEVICE.values()) +
                 f'</div><div style="color:{MUTED};font-size:13px;margin-top:.2em">同じ縮尺。高さはすべて {height:g} µm、幅は '
                 f'{template["grid"]:g} µm の倍数。</div></div>'))
