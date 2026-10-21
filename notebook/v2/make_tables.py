"""Draw the narrative's small truth tables as PNG images.

Colab's Markdown drops inline styles, so an HTML table in a text cell renders at the default
small size. An image keeps its size and shows before any cell runs. PNG at twice the size, since
raw.githubusercontent.com serves SVG as plain text; the narrative sets the display width.

    python3 notebook/v2/make_tables.py    # writes notebook/assets/tables/*.png
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


def width(svg):
    """Display width in CSS pixels (the PNG is twice this)."""
    return int(svg.split('width="', 1)[1].split('"', 1)[0])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in TABLES.items():
        (OUT/f"{name}.svg").write_text(svg)
        print(OUT/f"{name}.svg", width(svg))
