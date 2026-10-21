"""Draw the narrative's small truth tables and the chapter 1 flow map as SVG.

Colab's Markdown drops inline styles, so an HTML table in a text cell renders at the default
small size. An SVG keeps its size, scales cleanly and shows before any cell runs. It is served
through jsDelivr, since raw.githubusercontent.com sends SVG as plain text.

    python3 notebook/v2/make_tables.py    # writes notebook/assets/tables/*.svg
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]/"assets/tables"
COLOR = {"−1": "#2f6fbf", "0": "#6b7280", "+1": "#c8423b"}
CELL_W, CELL_H, FONT = 92, 40, 19


def table(rows, *, header_rows=1, header_cols=0, widths=None):
    """rows: list of lists of strings. Header cells are shaded; trit values are coloured."""
    columns = len(rows[0])
    widths = widths or [CELL_W]*columns
    width, height = sum(widths)+2, CELL_H*len(rows)+2
    parts = []
    for r, row in enumerate(rows):
        x = 1
        for c, text in enumerate(row):
            header = r < header_rows or c < header_cols
            bold = header or text.startswith("**")
            text = text.strip("*")
            fill = "#f3f4f6" if header else "#ffffff"
            color = "#30353b" if header else COLOR.get(text, "#30353b")
            parts.append(f'<rect x="{x}" y="{1+r*CELL_H}" width="{widths[c]}" height="{CELL_H}" '
                         f'fill="{fill}" stroke="#c9ccd1"/>')
            parts.append(f'<text x="{x+widths[c]/2}" y="{1+r*CELL_H+CELL_H/2+FONT*.35}" font-size="{FONT}" '
                         f'text-anchor="middle" fill="{color}"{" font-weight=\"700\"" if bold else ""}>{escape(text)}</text>')
            x += widths[c]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'font-family="Noto Sans CJK JP, Noto Sans, sans-serif">{"".join(parts)}</svg>\n')


TABLES = {
    "and_not": table([["a", "~a", "a & ~a"], ["−1", "+1", "−1"], ["0", "0", "**0"], ["+1", "−1", "−1"]]),
    "and": table([["a & b", "b = −1", "b = 0", "b = +1"], ["a = −1", "−1", "−1", "−1"],
                  ["a = 0", "−1", "0", "0"], ["a = +1", "−1", "0", "+1"]], header_cols=1),
    "inv": table([["A", "Y"], ["−1（−5 V）", "+1（+5 V）"], ["0（0 V）", "0（0 V）"], ["+1（+5 V）", "−1（−5 V）"]],
                 widths=[150, 150]),
}



TRITFLOW, OSS = "#e8782a", "#7d8794"


def flow_map():
    """The flow of chapter 1 in two rows: what TritFlow implements and what open-source tools do."""
    rows = [[("三値のHDL", "TritFlow", TRITFLOW), ("論理合成", "TritFlow", TRITFLOW),
             ("スタンダードセル", "TritFlow", TRITFLOW), ("配置配線", "TritFlow", TRITFLOW)],
            [("DRC・LVS", "KLayout＋PDKのデッキ", OSS), ("抽出", "KLayout", OSS),
             ("配線容量の見積もり", "TritFlow", TRITFLOW), ("回路シミュレーション", "ngspice＋PDKのモデル", OSS),
             ("三値の判定", "TritFlow", TRITFLOW)]]
    box_w, box_h, gap, arrow = 166, 58, 26, 26
    width = 5*box_w+4*gap+20
    height = 10+2*box_h+70+40
    parts = []
    def box(x, y, title, owner, color):
        parts.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="7" fill="{color}1f" stroke="{color}" stroke-width="1.6"/>'
                     f'<text x="{x+box_w/2}" y="{y+25}" font-size="15" font-weight="700" text-anchor="middle" fill="#30353b">{escape(title)}</text>'
                     f'<text x="{x+box_w/2}" y="{y+45}" font-size="12" text-anchor="middle" fill="{color}">{escape(owner)}</text>')
    def right(x, y):
        parts.append(f'<path d="M{x},{y} h{gap-8}" stroke="#59606b" stroke-width="1.6"/>'
                     f'<path d="M{x+gap-2},{y} l-8,-4 v8 z" fill="#59606b"/>')
    for r, row in enumerate(rows):
        y = 10+r*(box_h+70)
        for k, (title, owner, color) in enumerate(row):
            x = 10+k*(box_w+gap)
            box(x, y, title, owner, color)
            if k < len(row)-1:
                right(x+box_w, y+box_h/2)
    # From the end of the first row down and back to the start of the second.
    x_end, y_mid = 10+3*(box_w+gap)+box_w/2, 10+box_h
    parts.append(f'<path d="M{x_end},{y_mid} v{arrow} H{10+box_w/2} v{70-arrow-8}" fill="none" stroke="#59606b" stroke-width="1.6"/>'
                 f'<path d="M{10+box_w/2},{10+box_h+70-2} l-4,-8 h8 z" fill="#59606b"/>')
    legend_y = 10+2*box_h+70+28
    parts.append(f'<rect x="10" y="{legend_y-11}" width="12" height="12" fill="{TRITFLOW}"/>'
                 f'<text x="28" y="{legend_y}" font-size="13" fill="#30353b">TritFlow</text>'
                 f'<rect x="110" y="{legend_y-11}" width="12" height="12" fill="{OSS}"/>'
                 f'<text x="128" y="{legend_y}" font-size="13" fill="#30353b">OSS</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'font-family="Noto Sans CJK JP, Noto Sans, sans-serif">{"".join(parts)}</svg>\n')


TABLES["flow_map"] = flow_map()

def width(svg):
    """Display width in CSS pixels."""
    return int(svg.split('width="', 1)[1].split('"', 1)[0])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in TABLES.items():
        (OUT/f"{name}.svg").write_text(svg)
        print(OUT/f"{name}.svg", width(svg))
