"""Portable edited includes and publication provenance, without ignored builds."""

from hashlib import sha256
import importlib.util
from pathlib import Path

import pytest

from examples.curated import DESIGNS


spec = importlib.util.spec_from_file_location("notebook_experiments", Path(__file__).resolve().parents[1]/"experiments.py")
experiments = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiments)


def test_edit_included_multiplier_without_changing_published_example(tmp_path):
    example = DESIGNS["mul2"]
    before = example.path.read_bytes()
    edited = before.decode()+"\n// My notebook edit\n"
    circuit = experiments.load_edited(example, edited, tmp_path)
    table = circuit.truth_table()
    oracle = example.oracle(circuit.design.inputs)
    for i, vector in enumerate(zip(*(table[p] for p in circuit.design.inputs))):
        assert {p:int(table[p][i]) for p in circuit.design.outputs} == oracle(vector)
    assert circuit.synthesize().report()["equivalence"]["passed"]
    assert example.path.read_bytes() == before
    assert (tmp_path/"mul2.tv").read_text() == edited


def test_published_sources_relocate_without_recorded_build_directory(tmp_path):
    root, pdk = tmp_path/"clone", tmp_path/"pdk"
    source = root/"tritflow/sim/model.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"source")
    model = pdk/"libs.tech/spice/models/model"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"model")
    manual = pdk/"openIP62/IP62/Technology/doc/reference.pdf"
    manual.parent.mkdir(parents=True)
    manual.write_bytes(b"PDK reference")
    cell = root/"cells/out/INV/INV.spice"
    cell.parent.mkdir(parents=True)
    cell.write_bytes(b"cell")
    record = {"sources_sha256": {
        "/old/tritflow/tritflow/sim/model.py":sha256(source.read_bytes()).hexdigest(),
        "/old/tritflow/cells/out/INV/INV.spice":sha256(cell.read_bytes()).hexdigest(),
        "/old/PDK/libs.tech/spice/models/model":sha256(model.read_bytes()).hexdigest(),
        "/old/PDK/openIP62/IP62/Technology/doc/reference.pdf":sha256(manual.read_bytes()).hexdigest(),
        "/old/repo/build/adder4/adder4.gds":"not-a-runtime-input"}}
    experiments.verify_publication_sources(record,root,pdk)
    source.write_bytes(b"new source")
    with pytest.raises(RuntimeError,match="stale"):
        experiments.verify_publication_sources(record,root,pdk)
    with pytest.raises(RuntimeError,match="fingerprints"):
        experiments.verify_publication_sources({},root,pdk)


def test_opening_sequence_exercises_all_outputs_and_carry_assert_release():
    from tritflow import flow
    circuit = flow.load("examples/adder.tv", "adder", {"N":2})
    inputs = circuit.design.inputs
    vectors, labels = experiments.adder_demo_vectors(inputs)
    assert len(vectors) == len(labels) and all(a != b for a,b in zip(vectors,vectors[1:]))
    values = [circuit.design.evaluate(dict(zip(inputs,v,strict=True))) for v in vectors]
    for output in circuit.design.outputs:
        assert {int(v[output]) for v in values} == {-1,0,1}
        assert any(a[output] != b[output] for a,b in zip(values,values[1:]))
    for sign,label in ((1,"positive"),(-1,"negative")):
        assert int(values[labels.index(label+"_carry_assert")]["cout"]) == sign
        assert int(values[labels.index(label+"_carry_release")]["cout"]) == 0
