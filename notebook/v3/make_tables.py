"""Draw the narrative's small truth tables as SVG.

Colab's Markdown drops inline styles, so an HTML table in a text cell renders at the default
small size. An SVG keeps its size, scales cleanly and shows before any cell runs. It is served
through jsDelivr, since raw.githubusercontent.com sends SVG as plain text.

    python3 notebook/v3/make_tables.py    # writes notebook/assets/tables/*.svg
"""
from html import escape
import re
import unicodedata
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]/"assets/tables"
# Same palette and face as notebook/style.py and the paper figures.
INK, COLOR = "#0b0b0b", {"−1": "#2a78d6", "0": "#6f6e69", "+1": "#e34948"}
SERIF = "Times New Roman, Times, Nimbus Roman, Liberation Serif, Noto Serif JP, Noto Serif CJK JP, Hiragino Mincho ProN, serif"
CELL_W, CELL_H, FONT = 88, 34, 18


MONO = "Menlo, Consolas, DejaVu Sans Mono, monospace"


def _lines(text, available, font):
    """Wrap a column conservatively, counting Japanese glyphs as one full em."""
    lines, line, used = [], "", 0.0
    for token in re.findall(r"[A-Za-z0-9_]+|.", text):
        advance = font*sum(1 if unicodedata.east_asian_width(c) in ("W", "F") else .62 for c in token)
        if line and used + advance > available:
            lines.append(line)
            line, used = "", 0.0
        line += token
        used += advance
    return [*lines, line]


def table(rows, *, header_rows=1, header_cols=0, widths=None, left=(), font=FONT, wrap=False):
    """rows: list of lists of strings, drawn booktabs-style: a rule above and below the table and
    a thin one under the header, no vertical lines; trit values in their colours. Cells written
    `like this` are set in a monospace face; columns listed in ``left`` are left-aligned."""
    columns = len(rows[0])
    widths = widths or [CELL_W]*columns
    laid_out = [[_lines(text.strip("*`"), widths[c]-20, font-3 if text.startswith("`") else font)
                 if wrap else [text.strip("*`")]
                 for c, text in enumerate(row)] for row in rows]
    leading = font*1.45
    heights = [max(CELL_H, max(map(len, row))*leading+14) if wrap else CELL_H for row in laid_out]
    width, height = sum(widths), sum(heights)+4
    parts = [f'<path d="M0,1 H{width} M0,{height-1} H{width}" stroke="{INK}" stroke-width="1.4"/>',
             f'<path d="M0,{2+sum(heights[:header_rows])} H{width}" stroke="{INK}" stroke-width=".8"/>']
    y = 2
    for r, row in enumerate(rows):
        x = 0
        for c, text in enumerate(row):
            header = r < header_rows or c < header_cols
            bold = header or text.startswith("**")
            text = text.strip("*")
            color = INK if header else COLOR.get(text, INK)
            code = text.startswith("`") and text.endswith("`")
            text = text.strip("`") if code else text
            anchor, tx = ("start", x+10) if c in left else ("middle", x+widths[c]/2)
            face = f' font-family="{MONO}" font-size="{font-3}"' if code else f' font-size="{font}"'
            lines = laid_out[r][c]
            top = y+heights[r]/2-(len(lines)-1)*leading/2+font*.35
            spans = "".join(f'<tspan x="{tx}" y="{top+i*leading:g}">{escape(line)}</tspan>'
                            for i, line in enumerate(lines))
            weight_attr = ' font-weight="700"' if bold and not code else ''
            parts.append(f'<text{face} xml:space="preserve" '
                         f'text-anchor="{anchor}" fill="{color}"{weight_attr}>{spans}</text>')
            x += widths[c]
        y += heights[r]
    return "".join(parts), width, height


def svg(*tables, gap=48):
    """Tables side by side in one SVG, so the page lays them out the same everywhere."""
    x, parts, height = 0, [], 0
    for inner, w, h in tables:
        parts.append(f'<g transform="translate({x},0)">{inner}</g>')
        x, height = x+w+gap, max(height, h)
    width = x-gap
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'font-family="{SERIF}">{"".join(parts)}</svg>\n')


SCHEMATIC = Path(__file__).resolve().parents[1]/"assets/schematics/src/inv_compact.sch"
KEEP = re.compile(r"^(w=|l=|VDD$|VSS$|A$|Y$)")


def compact_schematic(sch=SCHEMATIC, crop=(20, -130, 360, 290), width=330):
    """Export a small Xschem drawing to SVG, keeping wires, devices, W/L and the port names.

    Pin names, instance names, m=1, model names and the RR value are dropped, and the pin marker
    squares (Xschem layer 5) removed; sizes read 13.5u, not 13.5e-06.
    """
    import subprocess, sys, tempfile
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from export_schematics import _theme_svg
    x0, y0, x1, y1 = crop
    height = round(width*(y1-y0)/(x1-x0))
    try:
        with tempfile.TemporaryDirectory() as work:
            rc, raw = Path(work)/"xschemrc", Path(work)/"out.svg"
            rc.write_text(f"set XSCHEM_LIBRARY_PATH {{{Path.home()}/pdk/TR-1um-pinned/libs.tech/xschem:"
                          "/usr/local/share/xschem/xschem_library}\nset dark_colorscheme 0\nset transparent_svg 0\n"
                          "set color_ps 1\n")
            subprocess.run(["xschem", "-r", "-x", "--rcfile", str(rc), "--command",
                            f"xschem set text_svg 1; xschem print svg {{{raw}}} {width*2} {height*2} {x0} {y0} {x1} {y1}; exit",
                            str(sch)], check=True, capture_output=True, timeout=45)
            svg = raw.read_text()
    except (FileNotFoundError, subprocess.SubprocessError):
        cached = OUT/"inv.svg"
        if cached.is_file():
            return cached.read_text(), width, height
        raise
    def text(match):
        content = match[2]
        if not KEEP.match(content):
            return ""
        content = re.sub(r"(\d(?:\.\d+)?)e-06", r"\1u", content)
        opening = match[1]
        if content.startswith(("w=", "l=")):
            # Keep the dimensions readable at the 330 px display width. Separate W and L
            # baselines so the larger labels cannot collide.
            opening = re.sub(r'font-size="[^"]+"', 'font-size="24.8"', opening)
            if content.startswith("l="):
                opening = re.sub(r'translate\(([^,]+),\s*([\d.]+)\)',
                                 lambda m: f'translate({m[1]}, {float(m[2])+10:g})', opening)
        return opening+content+"</text>"
    svg = re.sub(r"(<text\b[^>]*>)([^<]*)</text>", text, svg)
    svg = re.sub(r'<(?:path|rect)\b[^>]*class="l5"[^>]*/>', "", svg)
    svg = _theme_svg(svg, "INV", "light").replace("DejaVu Sans,sans-serif", SERIF)
    return re.sub(r'width="[^"]+" height="[^"]+"', f'width="{width}" height="{height}"', svg, count=1), width, height


def beside(table_parts, schematic, gap=40):
    """A table and a schematic side by side in one SVG, vertically centred."""
    inner, tw, th = table_parts
    svg, sw, sh = schematic
    height = max(th, sh)
    body = svg[svg.index(">", svg.index("<svg"))+1:svg.rindex("</svg>")]
    # Xschem's stylesheet styles every <text>; scope it to the schematic so the table keeps its colours.
    body = re.sub(r"<style>(.*?)</style>", lambda m: "<style>" + re.sub(r"(^|\})\s*([^{}]+)\{",
                  lambda r: f"{r[1]}#schematic {r[2].strip()}{{", m[1]) + "</style>", body, flags=re.S)
    view = re.search(r'viewBox="([^"]+)"', svg)[1]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{tw+gap+sw}" height="{height}" '
            f'viewBox="0 0 {tw+gap+sw} {height}" font-family="{SERIF}">'
            f'<g transform="translate(0,{(height-th)/2})">{inner}</g>'
            f'<svg id="schematic" x="{tw+gap}" y="{(height-sh)/2}" width="{sw}" height="{sh}" viewBox="{view}">{body}</svg></svg>\n')


# The same layout as the cell tables of chapter 3: one input across the top (A, then −1 0 +1),
# two inputs as A＼B with B across and A down.
TABLES = {
    "and": svg(table([["a", "−1", "0", "+1"], ["~a", "+1", "0", "−1"], ["a & ~a", "−1", "**0", "−1"]],
                     header_cols=1, widths=[96, 70, 70, 70]),
               table([["a＼b", "−1", "0", "+1"], ["−1", "−1", "−1", "−1"], ["0", "−1", "0", "0"], ["+1", "−1", "0", "+1"]],
                     header_cols=1, widths=[96, 70, 70, 70])),
    "numbers": svg(table([["値", "−4", "−3", "−2", "−1", "0", "+1", "+2", "+3", "+4"],
                          ["3¹ 3⁰", "TT", "T0", "T1", "0T", "00", "01", "1T", "10", "11"]],
                         header_cols=1, widths=[80]+[54]*9)),
    "syntax": svg(table([
        ["書き方", "意味", "合成される回路"],
        ["`~a  a & b  a | b`", "符号反転、小さいほう（min）、大きいほう（max）", "INV、NAND＋INV、NOR＋INV"],
        ["`nany(a, b)`", "−sat(a + b)", "NANY"],
        ["`a + b  a - b  -a`", "整数の加算、減算、符号反転", "全加算器の連鎖、各桁のINV"],
        ["`a * b`", "整数の乗算", "1トリットの乗算器と加算器"],
        ["`a << 1  a >> 1`", "3倍、3で割って最も近い整数に丸める", "配線のつなぎ替え（セルなし）"],
        ["`a == b  a < b`", "比較。真は +1、偽は −1", "各桁の差と符号の判定"],
        ["`c ? x : y`", "c = +1 で x、−1 で y、0 では一致する桁を残し他は 0", "三値の選択回路"],
        ["`always @*  if  case`", "手続き的に書く組合せ回路", "条件ごとの値を選ぶ回路"],
        ["`inv g (y, a);`", "セルを直接置く", "そのセル"],
    ], left=(0, 1, 2), widths=[190, 260, 190], font=16, wrap=True)),
    "inv": beside(table([["A", "−1", "0", "+1"], ["Y", "+1", "0", "−1"]], header_cols=1, widths=[70, 70, 70, 70]),
                  compact_schematic()),
}

# English variants retain the Japanese tables' values and drawing rules.
TABLES_EN = {
    **TABLES,
    "numbers": svg(table([["Value", "−4", "−3", "−2", "−1", "0", "+1", "+2", "+3", "+4"],
                          ["3¹ 3⁰", "TT", "T0", "T1", "0T", "00", "01", "1T", "10", "11"]],
                         header_cols=1, widths=[80]+[54]*9)),
    "syntax": svg(table([
        ["Syntax", "Meaning", "Synthesized circuit"],
        ["`~a  a & b  a | b`", "Negation, minimum (min), maximum (max)", "INV, NAND + INV, NOR + INV"],
        ["`nany(a, b)`", "−sat(a + b)", "NANY"],
        ["`a + b  a - b  -a`", "Integer addition, subtraction, negation", "Full-adder chain; INV per digit"],
        ["`a * b`", "Integer multiplication", "One-trit multipliers and adders"],
        ["`a << 1  a >> 1`", "Multiply by 3; divide by 3 and round to the nearest integer", "Rewiring (no cells)"],
        ["`a == b  a < b`", "Comparison: true +1, false −1", "Per-digit differences and sign detection"],
        ["`c ? x : y`", "x for c = +1, y for −1; at 0, retain matching digits and set others to 0", "Ternary selector"],
        ["`always @*  if  case`", "Procedural combinational logic", "Conditional value selectors"],
        ["`inv g (y, a);`", "Direct cell instantiation", "The specified cell"],
    ], left=(0, 1, 2), widths=[190, 260, 190], font=16, wrap=True)),
}



def width(svg):
    """Display width in CSS pixels."""
    return int(svg.split('width="', 1)[1].split('"', 1)[0])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in TABLES.items():
        (OUT/f"{name}.svg").write_text(svg)
        print(OUT/f"{name}.svg", width(svg))
    for name, svg in TABLES_EN.items():
        (OUT/f"{name}_en.svg").write_text(svg)
        print(OUT/f"{name}_en.svg", width(svg))
