"""Export taped-out Xschem drawings from isolated temporary copies.

Only paths in temporary .sch/.sym copies are relocated. Circuit/device data is
unchanged. Primitive crops omit stale free-text sizing sidebars; instance W/L
properties remain visible. Both themes are native Xschem SVG geometry with an
opaque high-contrast backing, so embedding on either notebook background works.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET


EXPORTS = {
    "INV": ("inverter.sch", (0, 0, 930, 880)),
    "NAND": ("mul_nand.sch", (100, 0, 930, 1040)),
    "NOR": ("mul_nor.sch", (100, 0, 930, 1140)),
    "NANY": ("nany.sch", (-340, -520, 980, 640)),
    "half_adder": ("half_adder.sch", (-20, -240, 1530, 1270)),
    "full_adder": ("full_adder.sch", (-20, -220, 1750, 1090)),
}
THEMES = {"light": ("#ffffff", "#172033"), "dark": ("#111827", "#e5edf7")}
NS = "{http://www.w3.org/2000/svg}"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _copy_dependencies(roots, work):
    """Resolve every C{} symbol, allowing only copied reference/PDK/system roots."""
    copied, records = {}, {}

    def relocate(text):
        for root in roots.values():
            text = text.replace(str(root)+"/", "")
        return text

    def copy(path, group, relative):
        path = path.resolve()
        if path in copied:
            return
        destination = work/group/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        text = path.read_text()
        destination.write_text(relocate(text))
        copied[path] = destination
        records[f"{group}/{relative}"] = {"source_sha256": digest(path)}
        for symbol in re.findall(r"(?m)^C \{([^}\n]+)\}", text):
            candidates = ([Path(symbol)] if Path(symbol).is_absolute() else
                          [path.parent/symbol, *(r/symbol for r in roots.values())])
            found = next((p for p in candidates if p.is_file()), None)
            if found is None:
                raise FileNotFoundError(f"missing symbol {symbol!r} in {path.name}")
            for label, root in roots.items():
                if found.absolute().is_relative_to(root):
                    copy(found, label, found.absolute().relative_to(root))
                    break
            else:
                raise ValueError(f"symbol outside allowed read-only roots: {found}")

    for filename, _ in EXPORTS.values():
        copy(roots["reference"]/filename, "reference", Path(filename))
    return copied, records


def _theme_svg(source, label, theme):
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


def export(reference, pdk, system_library, output, *, executable="xschem"):
    roots = {"reference": Path(reference).expanduser().resolve(),
             "pdk": Path(pdk).expanduser().resolve()/"libs.tech/xschem",
             "system": Path(system_library).expanduser().resolve()}
    output = Path(output).resolve()
    for root in roots.values():
        if output.is_relative_to(root):
            raise ValueError("exports must not be written inside a read-only source root")
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    with tempfile.TemporaryDirectory(prefix="tritflow-schematics-") as directory:
        work = Path(directory)
        copied, dependencies = _copy_dependencies(roots, work)
        hashes = {path: digest(path) for path in copied}
        rc = work/"xschemrc"
        library_path = ":".join(str(work/name) for name in roots)
        rc.write_text(f"set XSCHEM_LIBRARY_PATH {{{library_path}}}\n"
                      "set dark_colorscheme 0\nset transparent_svg 0\nset color_ps 1\n")
        for label, (filename, bounds) in EXPORTS.items():
            raw = work/f"{label}.svg"
            x0, y0, x1, y1 = bounds
            width = 1200
            height = round(width*(y1-y0)/(x1-x0))
            command = (f"xschem set text_svg 1; xschem print svg {{{raw}}} {width} {height} "
                       f"{x0} {y0} {x1} {y1}; exit")
            process = subprocess.run([executable, "-r", "-x", "--rcfile", str(rc), "--command", command,
                                      str(work/"reference"/filename)], cwd=work,
                                     capture_output=True, text=True, timeout=45)
            log = process.stdout+process.stderr
            if process.returncode or not raw.is_file() or re.search(r"(?i)IS MISSING|not found|SKIPPING|error:", log):
                raise RuntimeError(f"Xschem export failed for {label}: {log}")
            image = raw.read_text()
            root = ET.fromstring(image)
            if len(list(root.iter(NS+"path"))) < 10 or not list(root.iter(NS+"text")):
                raise ValueError(f"incomplete schematic SVG for {label}")
            outputs = {}
            for theme in THEMES:
                name = f"{label}{'.dark' if theme == 'dark' else ''}.svg"
                path = output/name
                path.write_text(_theme_svg(image, f"{label}: {filename}", theme))
                outputs[theme] = {"file": name, "sha256": digest(path)}
            symbols = re.findall(r"(?m)^C \{([^}\n]+)\}", (roots["reference"]/filename).read_text())
            records[label] = {"source": filename, "source_sha256": hashes[roots["reference"]/filename],
                              "instances_by_symbol": dict(sorted(Counter(Path(s).stem for s in symbols).items())),
                              "crop": bounds, "themes": outputs}
        assert all(digest(path) == value for path, value in hashes.items()), "read-only source changed during export"
    binary = Path(shutil.which(executable) or executable)
    manifest = {"schema_version": 1, "renderer": "batch xschem -r -x; text_svg=1",
                "renderer_sha256": digest(binary), "dependencies": dependencies, "schematics": records,
                "presentation": "Opaque light/dark themes; visual-only stroke/color normalization; no circuit edits"}
    (output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=Path.home()/"balanced-ternary-logic")
    parser.add_argument("--pdk", type=Path, default=Path.home()/"pdk/TR-1um-pinned")
    parser.add_argument("--system-library", type=Path, default=Path("/usr/local/share/xschem/xschem_library"))
    parser.add_argument("--output", type=Path, default=Path(__file__).parent/"assets/schematics")
    args = parser.parse_args()
    result = export(args.reference, args.pdk, args.system_library, args.output)
    print(f"Exported {len(result['schematics'])} schematics with light/dark variants to {args.output}")


if __name__ == "__main__":
    main()
