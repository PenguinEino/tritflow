"""Publish the named real-Colab run with its actual retry and timing scope.

The historical record is retained for audit. It is not a verification claim
for a later revision; promotion requires a new successful real-Colab run.
"""

import json
from pathlib import Path


EVIDENCE = json.loads(Path(__file__).with_name("colab_verified.json").read_text())
CURRENT_EVIDENCE = EVIDENCE if EVIDENCE.get("publish",False) and EVIDENCE.get("passed") else None


def narrative_values():
    """Expose the single published run as language-neutral narrative tokens."""
    if CURRENT_EVIDENCE is None:
        return {}
    record = CURRENT_EVIDENCE
    return {f"colab.{key}": value for key, value in {
        "commit": record["commit"], "short_commit": record["commit"][:7],
        "date_utc": record.get("date_utc", ""),
        "seconds": record["run_all_seconds_including_setup"],
        "minutes": max(1, round(record["run_all_seconds_including_setup"]/60)),
        "code_cells": record["passed_code_cells"],
        "attempts": record.get("run_all_attempts", 1),
    }.items()}


def run_note(language="en"):
    if CURRENT_EVIDENCE is None:
        return ""
    if language == "ja":
        # Text lives with the Japanese narrative; all run quantities are tokens.
        from editorial import render
        labels = json.loads(Path(__file__).with_name("narrative_ja").joinpath("labels.json").read_text())
        key = "colab_retry" if CURRENT_EVIDENCE.get("run_all_attempts") == 2 else "colab_note"
        return render(labels["ui"][key], narrative_values())
    seconds = CURRENT_EVIDENCE["run_all_seconds_including_setup"]
    commit = CURRENT_EVIDENCE["commit"]
    scope = ("on the successful second Run all (initial setup attempt excluded)"
             if CURRENT_EVIDENCE.get('run_all_attempts') == 2 else 'including setup')
    return (f"Free Colab verification at [{commit[:7]}](https://github.com/PenguinEino/tritflow/commit/{commit}): "
            f"all {CURRENT_EVIDENCE['passed_code_cells']} code cells completed in {seconds:g} s {scope}.\n\n"
            "If Run all stops after setup, choose Run all again.")
