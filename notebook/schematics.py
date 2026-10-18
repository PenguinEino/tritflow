"""Display bundled SVG themes in a portable notebook gallery, checking hashes."""

from base64 import b64encode
from hashlib import sha256
from html import escape
import json
from pathlib import Path


def schematic_gallery(directory, *, names=None, selected="NANY", max_width=620):
    """Return HTML for all exported drawings; no Xschem install needed to view.

    Explicit opaque backgrounds make either variant legible on the host theme.
    Details elements permit comparison of light/dark versions and expose source
    filenames/hashes. Data URLs work in Colab without serving local asset paths.
    """
    directory = Path(directory)
    manifest = json.loads((directory/"manifest.json").read_text())
    entries = manifest["schematics"]
    names = list(entries) if names is None else list(names)
    if any(name not in entries for name in names) or selected not in names:
        raise ValueError("choose a selected schematic from the displayed names")
    parts = [f'<div data-schematic-selected="{escape(selected)}">']
    for label in [selected, *(name for name in names if name != selected)]:
        entry = entries[label]
        variants = {}
        for theme, image in entry["themes"].items():
            raw = (directory/image["file"]).read_bytes()
            assert sha256(raw).hexdigest() == image["sha256"], f"schematic asset changed: {image['file']}"
            variants[theme] = "data:image/svg+xml;base64,"+b64encode(raw).decode()
        opened = " open" if label == selected else ""
        parts.append(f'<details{opened}><summary><strong>{escape(label)}</strong> — {escape(entry["source"])}</summary>'
                     f'<picture><source media="(prefers-color-scheme: dark)" srcset="{variants["dark"]}">'
                     f'<img src="{variants["light"]}" alt="{escape(label)} taped-out schematic" '
                     f'style="display:block;width:100%;max-width:{int(max_width)}px;height:auto;border:1px solid #94a3b8">'
                     '</picture><details><summary>Both themes / source provenance</summary>'
                     f'<p>Source SHA-256: <code>{entry["source_sha256"]}</code></p>')
        for theme, uri in variants.items():
            parts.append(f'<img src="{uri}" alt="{escape(label)} {theme}" '
                         'style="width:48%;height:auto;vertical-align:top;border:1px solid #94a3b8">')
        parts.append('</details></details>')
    return "".join(parts)+"</div>"
