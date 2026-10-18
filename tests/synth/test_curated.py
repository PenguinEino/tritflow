"""Every chapter-8 choice: exhaustive integer oracle through real DRC and LVS."""

import os
from pathlib import Path
import shutil

import pytest

from examples.curated import DESIGNS
from tritflow import flow, PDK_ROOT
from tritflow.synth import evaluate_netlist


@pytest.mark.parametrize("name", DESIGNS)
def test_curated_exhaustive_arithmetic(name):
    example = DESIGNS[name]
    circuit = flow.load(example.path, example.top)
    net = circuit.synthesize()
    table = circuit.truth_table()
    inputs = circuit.design.inputs
    vectors = list(zip(*(table[p] for p in inputs)))
    actual = evaluate_netlist(net, {p: table[p] for p in inputs})
    for index, vector in enumerate(vectors):
        expected = example.oracle(inputs)(vector)
        assert set(expected) == set(circuit.design.outputs)
        assert {p: int(table[p][index]) for p in expected} == expected
        assert {p: int(actual[p][index]) for p in expected} == expected
    assert len(vectors) == 3**len(inputs)
    assert net.report()["equivalence"]["passed"]


BINARY = Path(os.environ.get("KLAYOUT_BINARY") or shutil.which("klayout")
              or Path.home()/"bin/klayout/klayout")


@pytest.mark.skipif(not BINARY.is_file() or not PDK_ROOT.is_dir(), reason="real PDK/KLayout required")
@pytest.mark.parametrize("name", DESIGNS)
def test_curated_physical_end_to_end(name, tmp_path):
    example = DESIGNS[name]
    net = flow.load(example.path, example.top, klayout_binary=BINARY).synthesize()
    layout = net.place_and_route(output_dir=tmp_path/name, rows=None, anneal_steps=600, seed=0)
    assert not layout.stats["library_mock"]
    assert layout.stats["routed_nets"] == len(net.nets())
    assert all(check["clean"] for check in layout.data["checks"].values())
    assert layout.drc()["clean"]
    assert layout.lvs()["matched"]
