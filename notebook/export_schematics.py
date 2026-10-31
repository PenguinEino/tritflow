"""Apply the notebook palette to native Xschem SVG geometry.

The v3 table and compact-schematic exporters use the same theme. Geometry,
connections and device-value text remain native Xschem output.
"""

from html import escape
import re
import xml.etree.ElementTree as ET

THEMES = {"light": ("#ffffff", "#172033"), "dark": ("#111827", "#e5edf7")}


def _theme_svg(source, label, theme):
    """Recolor native Xschem paths and device text without changing connections."""
    background, foreground = THEMES[theme]
    classes = sorted(set(re.findall(r'class="(l\d+)"', source)))
    styles = []
    for name in classes:
        color = background if name == "l0" else foreground
        styles.append(f".{name}{{fill:{color};stroke:{color};stroke-width:1.3;"
                      "stroke-linecap:round;stroke-linejoin:round}")
    styles.append(f"text{{font-family:DejaVu Sans,sans-serif;fill:{foreground};fill-opacity:1}}")
    source = re.sub(r"<style\b[^>]*>.*?</style>", "<style>"+"\n".join(styles)+"</style>", source, flags=re.S)
    source = re.sub(r'(<text\b[^>]*\bfill=")#[0-9A-Fa-f]+(")', rf'\g<1>{foreground}\2', source)
    # Xschem's RR symbol puts its property block over its zigzag/terminal
    # annotations. Move text only into the empty space on the left. Original
    # values, device labels and every path/connection remain unchanged.
    blocks = list(re.finditer(r'<text\b[^>]*>[^<]*</text>', source))
    labels = []
    for match in blocks:
        element = ET.fromstring(match[0])
        position = re.fullmatch(r'translate\(([\d.eE+\-]+),\s*([\d.eE+\-]+)\)',element.get('transform',''))
        if position:
            labels.append((match[0],element.text or '',float(position[1]),float(position[2])))
    for _, text, x, y in labels:
        if text != 'RR':
            continue
        for raw, content, tx, ty in labels:
            model = content == 'RR' and tx == x and ty == y
            prop = abs(tx-(x-13.637)) < 2 and -2 <= ty-y <= 38 and re.match(r'^[wlmR]=',content)
            if model or prop:
                changed = re.sub(r'transform="[^"]+"',
                    f'transform="translate({tx-80:g}, {ty-15 if model else ty:g})"',raw)
                source = source.replace(raw,changed,1)
    root = ET.fromstring(source)
    width, height = root.attrib["width"], root.attrib["height"]
    source = source.replace('<svg ', f'<svg role="img" aria-labelledby="schematic-title schematic-description" '
                            f'viewBox="0 0 {width} {height}" ', 1)
    end = source.index(">")+1
    description = ("Batch Xschem export of the taped-out source; device properties are retained. "
                   "Primitive crops omit obsolete sizing sidebars. Geometry is not a new layout or verification result.")
    source = (source[:end] + f'<title id="schematic-title">{escape(label)}</title>'
              f'<desc id="schematic-description">{escape(description)}</desc>' + source[end:])
    ET.fromstring(source)
    return source
