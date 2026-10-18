"""Final notebook campaigns must be current on the distributed public PDK."""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

from tritflow import CELLS_DIR, PDK_ROOT, ROOT
from tritflow.sim.sizing import load_grid
from tritflow.sim.scaling import load_scaling
from tritflow.sim.load_sweep import load_sweep_results


spec = importlib.util.spec_from_file_location("publication_checks", ROOT/"notebook/experiments.py")
experiments = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiments)


@pytest.mark.parametrize("cell", ["INV","NANY"])
def test_required_sizing_campaign_is_current(cell):
    result = load_grid(cell)
    assert result["rows"] and result["rows"][result["adopted_index"]]["passed"]


@pytest.mark.parametrize("filename,loader", [
    ("adder_scaling.json",load_scaling), ("full_add_load_sweep.json",load_sweep_results)])
def test_required_scaling_and_load_campaigns_are_current(filename, loader):
    result = loader(ROOT/"results"/filename)
    records = result["rows"] if filename == "adder_scaling.json" else [result]
    assert records
    for record in records:
        experiments.verify_publication_sources(record, ROOT, PDK_ROOT)


def test_cell_qualification_consumed_the_pinned_decks_and_current_views():
    report = json.loads((CELLS_DIR/"out/verify_report.json").read_text())
    assert report["passed"]
    for relative, expected in report["deck_sha256"].items():
        assert sha256((PDK_ROOT/relative).read_bytes()).hexdigest() == expected, relative
    for cell, artifacts in report["artifact_sha256"].items():
        for suffix, expected in artifacts.items():
            assert sha256((CELLS_DIR/f"out/{cell}/{cell}.{suffix}").read_bytes()).hexdigest() == expected
