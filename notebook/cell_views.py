"""Chapter 3 views: the closure of one-input functions per cell basis, the library's truth tables,
and the standard cells drawn side by side at one scale.

Truth tables come from each cell's published ``*.truth.json``; geometry from its GDS. Nothing
here runs a tool; the chapter's own cells run the closure and the PDK checks.
"""

from html import escape
from itertools import product
import json

from IPython.display import HTML, display

from live import _layer_paths, _patterns, LayoutView
from style import MUTED, RULE, SERIF, TRIT_COLOR as COLOR, TRIT_TEXT, figure_css, table_css
_VIEWS = 0


def _key(prefix):
    global _VIEWS
    _VIEWS += 1
    return f"{prefix}{_VIEWS}"


def closure_view(found):
    """All 27 one-input functions as columns (output at a = −1, 0, +1, top to bottom), each with
    the round of the construction in which it first appears; unreached ones are left blank."""
    functions = list(product((-1, 0, 1), repeat=3))
    size = 14

    def column(function):
        reached = function in found
        cells = "".join(f'<rect x="0" y="{k*size}" width="{size}" height="{size-1.5}" rx="2" '
                        f'fill="{COLOR[v] if reached else "#efeee9"}"/>' for k, v in enumerate(function))
        return f'<svg width="{size}" height="{3*size}">{cells}</svg>'

    cells = "".join(f'<td>{column(f)}<div class="g">{found.get(f, "")}</div></td>' for f in functions)
    legend = " ".join(f'<span style="color:{COLOR[v]}">■</span> {TRIT_TEXT[v]}' for v in (-1, 0, 1))
    display(HTML(f'<style>{figure_css(".tfclosure")}.tfclosure td{{padding:2px 2px;text-align:center}}'
                 f'.tfclosure .g{{font-size:12px;color:{MUTED}}}</style><div class="tfclosure">'
                 f'<table style="border-collapse:collapse"><tr>{cells}</tr></table>'
                 f'<div style="color:{MUTED};font-size:13px;margin-top:.4em">各列が1入力関数（上から a = −1, 0, +1 での出力）。'
                 f'下の数字は、その関数が初めて現れた段（0は入力そのものと定数）。{legend}</div></div>'))


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
    return svg[svg.index("<svg"):]


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
             ".tfcells .sym svg{width:110px;height:auto;display:block;margin:.1em 0 .3em}"
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
    pictures = []
    for group in groups:
        row = []
        for name in group:
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
                 f'<div style="font-size:13px;margin-top:.3em">' + "　".join(
                     f'<span style="display:inline-block;width:14px;height:9px;border:1.5px dashed {c};background:{c}1a;'
                     f'vertical-align:middle;margin-right:4px"></span>{label}' for c, label in DEVICE.values()) +
                 f'</div><div style="color:{MUTED};font-size:13px;margin-top:.2em">同じ縮尺。高さはすべて {height:g} µm、幅は '
                 f'{template["grid"]:g} µm の倍数。</div></div>'))
