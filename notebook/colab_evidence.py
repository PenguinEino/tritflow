"""A scoped factual run note from the retained round-2 Colab evidence."""

import json
from pathlib import Path


EVIDENCE = json.loads(Path(__file__).with_name("colab_verified.json").read_text())


def run_note():
    seconds = EVIDENCE["run_all_seconds_including_setup"]
    minutes = round(seconds/30)/2
    commit = EVIDENCE["commit"]
    return (f"Run all ≈ {minutes:g} min on free Colab including setup "
            f"({seconds:g} s; all {EVIDENCE['passed_code_cells']} code cells), verified at "
            f"commit [{commit[:7]}](https://github.com/PenguinEino/tritflow/commit/{commit}).")
