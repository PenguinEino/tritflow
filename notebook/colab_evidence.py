"""Publish the named real-Colab run with its actual retry and timing scope.

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
    commit = CURRENT_EVIDENCE["commit"]
    scope = ("on the successful second Run all (initial setup attempt excluded)"
             if CURRENT_EVIDENCE.get('run_all_attempts') == 2 else 'including setup')
    return (f"Free Colab verification at [{commit[:7]}](https://github.com/PenguinEino/tritflow/commit/{commit}): "
            f"all {CURRENT_EVIDENCE['passed_code_cells']} code cells completed in {seconds:g} s {scope}.\n\n"
            "If Run all stops after setup, choose Run all again.")
