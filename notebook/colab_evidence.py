"""Publish a run note only when the current release has a promoted Colab pass.

The historical record is retained for audit. It is not a verification claim
for a later revision; promotion requires a new successful real-Colab run.
"""

import json
from pathlib import Path


EVIDENCE = json.loads(Path(__file__).with_name("colab_verified.json").read_text())
CURRENT_EVIDENCE = EVIDENCE if EVIDENCE.get("publish",False) and EVIDENCE.get("passed") else None


def run_note():
    if CURRENT_EVIDENCE is None:
        return ""
    seconds = CURRENT_EVIDENCE["run_all_seconds_including_setup"]
    minutes = round(seconds/30)/2
    commit = CURRENT_EVIDENCE["commit"]
    return (f"Run all ≈ {minutes:g} min on free Colab including setup "
            f"({seconds:g} s; all {CURRENT_EVIDENCE['passed_code_cells']} code cells), verified at "
            f"commit [{commit[:7]}](https://github.com/PenguinEino/tritflow/commit/{commit}).")
