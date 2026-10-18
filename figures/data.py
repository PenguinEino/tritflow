"""Data access for figures.

Figures read the repository's published results. While streams are re-running, set
FIG_REF=<git ref> to draw from a committed snapshot instead of the working tree.
"""

import json
import os
import subprocess

from tritflow import ROOT  # noqa: F401


def text(relpath: str) -> str:
    ref = os.environ.get("FIG_REF")
    if ref:
        return subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:{relpath}"],
                              check=True, capture_output=True, text=True).stdout
    return (ROOT / relpath).read_text()


def load(relpath: str):
    return json.loads(text(relpath))
