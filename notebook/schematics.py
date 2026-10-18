"""Display bundled SVG themes in a portable notebook gallery, checking hashes."""

from base64 import b64encode
from hashlib import sha256
from html import escape
import json
from pathlib import Path


def schematic_gallery(directory):
    """Return HTML for all exported drawings; no Xschem install needed to view.

    Explicit opaque backgrounds make either variant legible on the host theme.
    Details elements permit comparison of light/dark versions and expose source
    filenames/hashes. Data URLs work in Colab without serving local asset paths.
    """
    directory = Path(directory)
    manifest = json.loads((directory/"manifest.json").read_text())
    parts = []
    for label, entry in manifest["schematics"].items():
        variants = {}
        for theme, image in entry["themes"].items():
            raw = (directory/image["file"]).read_bytes()
            assert sha256(raw).hexdigest() == image["sha256"], f"schematic asset changed: {image['file']}"
            variants[theme] = "data:image/svg+xml;base64,"+b64encode(raw).decode()
        parts.append(f'<details open><summary><strong>{escape(label)}</strong> — {escape(entry["source"])}</summary>'
                     f'<picture><source media="(prefers-color-scheme: dark)" srcset="{variants["dark"]}">'
                     f'<img src="{variants["light"]}" alt="{escape(label)} taped-out schematic" '
                     'style="display:block;width:100%;max-width:1000px;height:auto;border:1px solid #94a3b8">'
                     '</picture><details><summary>Both themes / source provenance</summary>'
                     f'<p>Source SHA-256: <code>{entry["source_sha256"]}</code></p>')
        for theme, uri in variants.items():
            parts.append(f'<img src="{uri}" alt="{escape(label)} {theme}" '
                         'style="width:48%;height:auto;vertical-align:top;border:1px solid #94a3b8">')
        parts.append('</details></details>')
    return "".join(parts)
