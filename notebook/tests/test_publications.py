"""V3 sizing grids and cell qualification retain their source checks."""

from hashlib import sha256
import json

import pytest

from tritflow import CELLS_DIR, PDK_ROOT
from tritflow.sim.sizing import load_grid


@pytest.mark.parametrize("cell", ["INV","NANY"])
def test_required_sizing_campaign_is_current(cell):
    result = load_grid(cell)
    assert result["rows"] and result["rows"][result["adopted_index"]]["passed"]


def test_cell_qualification_consumed_the_pinned_decks_and_current_views():
    report = json.loads((CELLS_DIR/"out/verify_report.json").read_text())
    assert report["passed"]
    for relative, expected in report["deck_sha256"].items():
        assert sha256((PDK_ROOT/relative).read_bytes()).hexdigest() == expected, relative
    for cell, artifacts in report["artifact_sha256"].items():
        for suffix, expected in artifacts.items():
            assert sha256((CELLS_DIR/f"out/{cell}/{cell}.{suffix}").read_bytes()).hexdigest() == expected
