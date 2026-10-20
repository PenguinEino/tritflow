"""Shuttle ALU integer specification and analog stimulus coverage."""

from itertools import product

from examples import alu_reference as reference
from tritflow.hdl import load
from tritflow.synth import synthesize


def test_shuttle_alu_all_243_states_and_bounded_cell_count():
    design = load('examples/alu.tv')
    net = synthesize(design)
    assert net.equivalence['vectors'] == 243
    assert reference.check_truth_table(design,net) == 243
    assert net.report()['total_cells'] <= 64
    assert net.report()['max_fanout'] <= 4
    for a,b in product(range(-4,5),repeat=2):
        assert reference.result(a,b,-1) == a-b
        assert reference.result(a,b,0) == round(a/3)
        assert reference.result(a,b,1) == a+b


def test_shuttle_spice_vectors_cover_instructions_and_every_output_level():
    vectors = reference.representative_vectors()
    assert vectors == reference.representative_vectors()
    assert {v[4] for v in vectors} == {-1,0,1}
    for key in reference.expected(vectors[0]):
        assert {reference.expected(v)[key] for v in vectors} == {-1,0,1}
    assert len(vectors) < 15
