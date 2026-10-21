"""Compact copies of the taped-out Xschem schematics for side-by-side figures.

The taped-out drawings space wires generously, which reads well alone but wastes room when four
of them sit in a grid. This copies each drawing and closes the empty gaps: on each axis, every
stretch between neighbouring wire ends or pins that no symbol spans is shortened to at most
``GAP_X``/``GAP_Y`` units, while each symbol keeps its own geometry. Devices, connections, pins and labels
are unchanged; only free text notes (the old sizing sidebars) are left out. The reference
repository is read, never written.

    python3 notebook/v2/compact_schematics.py   # writes notebook/assets/schematics/src/*_compact.sch
                                                #    and notebook/assets/schematics/<CELL>.compact.svg
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

REFERENCE = Path.home()/"balanced-ternary-logic"
PDK_XSCHEM = Path.home()/"pdk/TR-1um-pinned/libs.tech/xschem"
SYSTEM = Path("/usr/local/share/xschem/xschem_library")
HERE = Path(__file__).resolve().parent
OUT = HERE.parent/"assets/schematics"
CELLS = {"INV": "inverter.sch", "NAND": "mul_nand.sch", "NOR": "mul_nor.sch", "NANY": "nany.sch"}
# Longest allowed empty stretch: wider across, where device and pin labels sit.
GAP_X, GAP_Y = 90, 50
SERIF = "Times New Roman, Times, Nimbus Roman, Liberation Serif, serif"


def _records(text):
    """Split a .sch into records; a record's braces may span lines."""
    records, current, depth = [], "", 0
    for line in text.splitlines(keepends=True):
        current += line
        depth += line.count("{")-line.count("}")
        if depth <= 0:
            records.append(current)
            current, depth = "", 0
    return records


def _pins(symbol):
    """Pin centres of a symbol, from its ``B 5`` boxes."""
    for root in (REFERENCE, PDK_XSCHEM, SYSTEM):
        path = root/symbol
        if path.is_file():
            boxes = re.findall(r"(?m)^B 5 (\S+) (\S+) (\S+) (\S+)", path.read_text())
            return [((float(a)+float(c))/2, (float(b)+float(d))/2) for a, b, c, d in boxes] or [(0., 0.)]
    raise FileNotFoundError(symbol)


def _place(points, x, y, rot, flip):
    out = []
    for px, py in points:
        if flip:
            px = -px
        for _ in range(rot % 4):
            px, py = -py, px
        out.append((x+px, y+py))
    return out


def _mapping(coords, rigid, gap):
    """A monotone map that keeps distances inside rigid intervals and caps the others at ``gap``."""
    rigid = sorted(rigid)
    merged = []
    for lo, hi in rigid:
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    inside = lambda a, b: any(lo <= a and b <= hi for lo, hi in merged)
    points = sorted(set(coords) | {v for pair in merged for v in pair})
    new, position = {points[0]: points[0]}, points[0]
    for a, b in zip(points, points[1:]):
        position += (b-a) if inside(a, b) else min(b-a, gap)
        new[b] = position
    return new


def compact(text):
    records = [r for r in _records(text) if not r.startswith("T ")]
    xs, ys, rx, ry = [], [], [], []
    for r in records:
        if r.startswith("N "):
            x1, y1, x2, y2 = map(float, r.split()[1:5])
            xs += [x1, x2]
            ys += [y1, y2]
        elif r.startswith("C "):
            symbol, rest = re.match(r"C \{([^}]+)\} (.*)", r, re.S).groups()
            x, y, rot, flip = (float(v) for v in rest.split()[:4])
            pins = _place(_pins(symbol), x, y, int(rot), int(flip))
            px, py = [p[0] for p in pins]+[x], [p[1] for p in pins]+[y]
            xs += px
            ys += py
            rx.append((min(px), max(px)))
            ry.append((min(py), max(py)))
    fx, fy = _mapping(xs, rx, GAP_X), _mapping(ys, ry, GAP_Y)
    out = []
    for r in records:
        if r.startswith("N "):
            parts = r.split(" ", 5)
            x1, y1, x2, y2 = map(float, parts[1:5])
            out.append(f"N {fx[x1]:g} {fy[y1]:g} {fx[x2]:g} {fy[y2]:g} {parts[5]}")
        elif r.startswith("C "):
            match = re.match(r"(C \{[^}]+\}) (\S+) (\S+) (.*)", r, re.S)
            out.append(f"{match[1]} {fx[float(match[2])]:g} {fy[float(match[3])]:g} {match[4]}")
        else:
            out.append(r)
    box = (min(fx.values()), min(fy.values()), max(fx.values()), max(fy.values()))
    return "".join(out), box


def export(sch, svg, box, margin=(110, 40), scale=1.6):
    """Xschem's own SVG, themed like the other notebook schematics, in the serif face."""
    sys.path.insert(0, str(HERE.parent))
    from export_schematics import _theme_svg
    with tempfile.TemporaryDirectory() as work:
        rc, raw = Path(work)/"xschemrc", Path(work)/"out.svg"
        rc.write_text(f"set XSCHEM_LIBRARY_PATH {{{REFERENCE}:{PDK_XSCHEM}:{SYSTEM}}}\n"
                      "set dark_colorscheme 0\nset transparent_svg 0\nset color_ps 1\n")
        # Print exactly the drawing's extent plus room for the labels beside devices and pins.
        x0, y0, x1, y1 = box[0]-margin[0], box[1]-margin[1], box[2]+margin[0], box[3]+margin[1]
        w, h = round((x1-x0)*scale), round((y1-y0)*scale)
        subprocess.run(["xschem", "-r", "-x", "--rcfile", str(rc), "--command",
                        f"xschem set text_svg 1; xschem print svg {{{raw}}} {w} {h} {x0} {y0} {x1} {y1}; exit", str(sch)],
                       check=True, capture_output=True, timeout=60, cwd=work)
        text = raw.read_text()
    svg.write_text(_theme_svg(text, sch.stem, "light").replace("DejaVu Sans,sans-serif", SERIF))


if __name__ == "__main__":
    (OUT/"src").mkdir(parents=True, exist_ok=True)
    for cell, name in CELLS.items():
        sch = OUT/"src"/f"{Path(name).stem}_compact.sch"
        text = (REFERENCE/name).read_text()
        # Symbols are referenced relative to the reference repository; keep them resolvable.
        drawing, box = compact(text)
        sch.write_text(drawing)
        export(sch, OUT/f"{cell}.compact.svg", box)
        print(sch, OUT/f"{cell}.compact.svg")
