"""Chapter 3 views: the closure of one-input functions per cell basis, the library's truth tables,
and the standard cells drawn side by side at one scale.

Truth tables come from each cell's published ``*.truth.json``; geometry from its GDS. Nothing
here runs a tool; the chapter's own cells run the closure and the PDK checks.
"""

from html import escape
from itertools import product
import json

from IPython.display import HTML, display

from live import FONT, DIM, _layer_paths, _patterns, LayoutView

COLOR = {-1: "#2f6fbf", 0: "#9aa1ab", 1: "#c8423b"}
TRIT_TEXT = {-1: "−1", 0: "0", 1: "+1"}
_VIEWS = 0


def _key(prefix):
    global _VIEWS
    _VIEWS += 1
    return f"{prefix}{_VIEWS}"


def closure_view(bases, closures):
    """All 27 one-input functions as columns (output at a = −1, 0, +1, top to bottom); each
    basis is a row, and the functions it reaches are drawn in colour."""
    functions = list(product((-1, 0, 1), repeat=3))
    size = 10

    def column(function, reached):
        cells = "".join(f'<rect x="0" y="{k*size}" width="{size}" height="{size-1}" rx="1.5" '
                        f'fill="{COLOR[v] if reached else "#eef0f3"}"/>' for k, v in enumerate(function))
        return f'<svg width="{size}" height="{3*size}">{cells}</svg>'

    rows = []
    for (name, _), reached in zip(bases, closures):
        cells = "".join(f'<td>{column(f, f in reached)}</td>' for f in functions)
        rows.append(f'<tr><th>{escape(name)}</th>{cells}<td class="n"><b>{len(reached)}</b> / 27</td></tr>')
    legend = " ".join(f'<span style="color:{COLOR[v]}">■</span> {TRIT_TEXT[v]}' for v in (-1, 0, 1))
    display(HTML(f'<div style="{FONT};font-size:13px"><table style="border-collapse:collapse">{"".join(rows)}</table>'
                 f'<div style="color:{DIM};margin-top:.4em">各列が1入力関数（上から a = −1, 0, +1 での出力）。'
                 f'色のついた列が、その組で作れる関数。{legend}</div></div>'
                 '<style>th{text-align:left;padding-right:1em;font-weight:600;white-space:nowrap}'
                 'td{padding:2px 1px} td.n{padding-left:1em;white-space:nowrap}</style>'))


FORMULA = {"INV": "Y = −A", "BUF": "Y = A", "NAND": "Y = −min(A, B)", "NOR": "Y = −max(A, B)",
           "NANY": "Y = −sat(A + B)", "TIEP": "Y = +1", "TIEZ": "Y = 0", "TIEN": "Y = −1"}


def _truth_grid(rows):
    """3×3 for two inputs (A down, B across), one row for one input, one cell for a tie."""
    def cell(v):
        return f'<td style="background:{COLOR[v]}26;color:{COLOR[v]};font-weight:700">{TRIT_TEXT[v]}</td>'
    inputs = list(rows[0]["inputs"]) if rows else []
    if len(inputs) == 2:
        table = {(r["inputs"]["A"], r["inputs"]["B"]): r["Y"] for r in rows}
        head = "<tr><th>A＼B</th>" + "".join(f"<th>{TRIT_TEXT[b]}</th>" for b in (-1, 0, 1)) + "</tr>"
        body = "".join(f"<tr><th>{TRIT_TEXT[a]}</th>" + "".join(cell(table[a, b]) for b in (-1, 0, 1)) + "</tr>"
                       for a in (-1, 0, 1))
        return f'<table class="g">{head}{body}</table>'
    if len(inputs) == 1:
        head = "<tr><th>A</th>" + "".join(f"<th>{TRIT_TEXT[r['inputs']['A']]}</th>" for r in rows) + "</tr>"
        return f'<table class="g">{head}<tr><th>Y</th>{"".join(cell(r["Y"]) for r in rows)}</tr></table>'
    return f'<table class="g"><tr><th>Y</th>{cell(rows[0]["Y"])}</tr></table>'


def cell_tables(cells_dir, schematics_dir):
    """Every logic cell's truth table in colour; the taped-out schematic folded underneath."""
    cards = []
    for name, formula in FORMULA.items():
        rows = json.loads((cells_dir/name/f"{name}.truth.json").read_text())
        schematic = schematics_dir/f"{name}.svg"
        folded = (f'<details><summary>回路図（Xschem）</summary><div class="sch">{schematic.read_text()}</div></details>'
                  if schematic.is_file() else "")
        cards.append(f'<div class="card"><div class="t"><b>{name}</b> <span>{escape(formula)}</span></div>'
                     f'{_truth_grid(rows)}{folded}</div>')
    style = ('.tfcells{display:flex;flex-wrap:wrap;gap:1em 1.6em;align-items:flex-start;max-width:1100px}'
             '.tfcells .card{min-width:150px} .tfcells .t{margin-bottom:.3em} .tfcells .t span{color:#59606b}'
             '.tfcells .g{border-collapse:collapse;font-size:13px}'
             '.tfcells .g td,.tfcells .g th{border:1px solid #d5d7db;padding:.15em .55em;text-align:center}'
             '.tfcells .g th{background:#f3f4f6;font-weight:600}'
             '.tfcells .sch svg{max-width:520px;height:auto;background:#fff}')
    display(HTML(f'<style>{style}</style><div class="tfcells" style="{FONT}">{"".join(cards)}</div>'))


def cell_row(library, cells_dir, *, groups=(("INV", "NAND", "NOR", "NANY"), ("BUF", "TIEP", "TIEZ", "TIEN", "FILL")),
             gap=24.0):
    """Every standard cell from its GDS, in rows at one common scale, with the template's rails
    named."""
    view = LayoutView(cells_dir.parent)
    template = json.loads((cells_dir.parent/"template.json").read_text())
    widths = {cell["name"]: cell["width"] for cell in library}
    height = template["height"]
    span = max(sum(widths[n] for n in group)+gap*(len(group)-1) for group in groups)
    unit = span/700
    pad = 46*unit
    rails = template["rails"]
    rail_labels = (f'<text x="{-6*unit:g}" y="{-sum(rails["VDD"])/2+3*unit:g}" font-size="{9*unit:g}" text-anchor="end">VDD</text>'
                   f'<text x="{-6*unit:g}" y="{-rails["VMID"][1]+2*unit:g}" font-size="{9*unit:g}" text-anchor="end">VMID</text>'
                   f'<text x="{-6*unit:g}" y="{-rails["VSS"][0]+7*unit:g}" font-size="{9*unit:g}" text-anchor="end">VSS</text>')
    pictures = []
    for group in groups:
        x, uses, names = 0.0, [], []
        for name in group:
            uses.append(f'<use href="#tfc-{name}" transform="translate({x:g},0)"/>')
            cx = x+widths[name]/2
            names.append(f'<text x="{cx:g}" y="{18*unit:g}" font-size="{10*unit:g}" text-anchor="middle" '
                         f'font-weight="700">{name}</text><text x="{cx:g}" y="{30*unit:g}" font-size="{8*unit:g}" '
                         f'text-anchor="middle" fill="{DIM}">{widths[name]:g} µm</text>')
            x += widths[name]+gap
        symbols = "".join(f'<g id="tfc-{n}">{_layer_paths(view._cell(n), unit)}</g>' for n in group)
        pictures.append(
            f'<svg viewBox="{-pad:g} {-height-8*unit:g} {span+pad+8*unit:g} {height+40*unit:g}" '
            f'style="width:100%;height:auto;display:block" fill="#30353b">'
            f'<defs>{_patterns(unit)}{symbols}</defs><g transform="scale(1,-1)">{"".join(uses)}</g>'
            f'{rail_labels}{"".join(names)}</svg>')
    display(HTML(f'<div style="{FONT};max-width:1000px"><div style="background:#fff;border:1px solid #d5d7db;'
                 f'border-radius:6px;padding:6px">{"".join(pictures)}</div>'
                 f'<div style="color:{DIM};font-size:12px">同じ縮尺。高さはすべて {height:g} µm、幅は '
                 f'{template["grid"]:g} µm の倍数。</div></div>'))
