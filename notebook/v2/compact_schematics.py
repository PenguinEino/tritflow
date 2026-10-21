"""Export the four hand-drawn, electrically checked chapter 3 schematics.

The editable sources are assets/schematics/src/{inv,nand,nor,nany}.sch.
No source geometry is generated or compacted here. Each figure uses the same
640-unit drafting width and the same print scale. Embedded PDK symbols retain
all native geometry, pins and netlisting properties; only their annotations
have been moved for legibility. Chapter 2's inv_compact.sch is independent.

    python3 notebook/v2/compact_schematics.py
"""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile

PDK_XSCHEM = Path(os.environ.get("TR1UM_PDK", Path.home()/"pdk/TR-1um-pinned"))/"libs.tech/xschem"
SYSTEM = Path("/usr/local/share/xschem/xschem_library")
HERE = Path(__file__).resolve().parent
OUT = HERE.parent/"assets/schematics"
# Exact, reviewed print boxes. Common horizontal bounds preserve device scale
# in cell_tables' equal-width columns; spare height is never filled by zooming.
BOXES = {"INV": (0, 0, 640, 590), "NAND": (0, 0, 640, 740),
         "NOR": (0, 0, 640, 800), "NANY": (0, 0, 640, 830)}
SERIF = "Times New Roman, Times, Nimbus Roman, Liberation Serif, serif"


def export(sch, svg, box, scale=1.6):
    """Print native Xschem geometry in an exact box, with the notebook palette."""
    sys.path.insert(0, str(HERE.parent))
    from export_schematics import _theme_svg
    with tempfile.TemporaryDirectory(prefix="tritflow-compact-") as directory:
        work = Path(directory)
        rc, raw = work/"xschemrc", work/"out.svg"
        rc.write_text(f"set XSCHEM_LIBRARY_PATH {{{PDK_XSCHEM}:{SYSTEM}}}\n"
                      "set dark_colorscheme 0\nset transparent_svg 0\nset color_ps 1\n")
        x0, y0, x1, y1 = box
        w, h = round((x1-x0)*scale), round((y1-y0)*scale)
        command = (f"xschem set text_svg 1; xschem print svg {{{raw}}} {w} {h} "
                   f"{x0} {y0} {x1} {y1}; exit")
        process = subprocess.run(["xschem", "-r", "-x", "--rcfile", str(rc),
                                  "--command", command, str(sch.resolve())],
                                 check=True, capture_output=True, text=True, timeout=60, cwd=work)
        log = process.stdout+process.stderr
        if re.search(r"(?i)IS MISSING|not found|SKIPPING|error:", log):
            raise RuntimeError(f"Xschem could not export {sch}: {log}")
        source = raw.read_text()
    themed = _theme_svg(source, f"{sch.stem.upper()}: hand-drawn taped-out circuit", "light")
    # The shared theme also relocates old RR annotations. These sources already
    # place every annotation explicitly, so restore their native print positions.
    original_text = iter(re.findall(r'<text\b[^>]*>[^<]*</text>', source))
    def native_position(match):
        original = next(original_text)
        position = re.search(r'transform="[^"]+"', original)[0]
        return re.sub(r'transform="[^"]+"', position, match[0])
    themed = re.sub(r'<text\b[^>]*>[^<]*</text>', native_position, themed)
    themed = re.sub(r'<desc id="schematic-description">.*?</desc>',
                    '<desc id="schematic-description">Hand-drawn Xschem schematic of the taped-out '
                    'circuit. Device values, pin order and connectivity are preserved; '
                    'PDK symbol annotations are repositioned without hiding labels.</desc>', themed)
    # These SVGs are inlined together: title/description IDs must be unique.
    for kind in ("title", "description"):
        themed = themed.replace(f"schematic-{kind}", f"compact-{sch.stem}-{kind}")
    svg.write_text(themed.replace("DejaVu Sans,sans-serif", SERIF))


def main():
    for cell, box in BOXES.items():
        sch = OUT/"src"/f"{cell.lower()}.sch"
        export(sch, OUT/f"{cell}.compact.svg", box)
        print(f"{sch.relative_to(OUT)} → {cell}.compact.svg")


if __name__ == "__main__":
    main()
