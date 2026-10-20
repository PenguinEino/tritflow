"""Shifter implementation boundaries and showcase ALU coverage."""

from itertools import product

import numpy as np
import pytest

from examples.alu9_reference import check_truth_table, decode, expected, representative_vectors, result
from tritflow.hdl import load, loads
from tritflow.synth import check_equivalence, synthesize, tritverilog


@pytest.mark.parametrize('expression,wiring', [('a<<1',"{1't0,a,1't0}"),
                                             ('a>>1',"{3't000,a[1]}"),
                                             ('a<<-1',"{3't000,a[1]}"),
                                             ('a>>-1',"{1't0,a,1't0}")])
def test_fixed_shifts_are_identical_to_authored_wiring(expression,wiring):
    def net(rhs):
        return synthesize(loads(f'''module m(input trit [1:0] a,output trit [3:0] y);
            assign y={rhs}; endmodule'''))
    assert net(expression).to_json()==net(wiring).to_json()


@pytest.mark.parametrize('operator',['<<','>>'])
def test_signal_shift_without_optimization_and_writer_round_trip(operator):
    design=loads(f'''module m(input trit [1:0] a,k,output trit [3:0] y);
        assign y=a {operator} k; endmodule''')
    check_equivalence(design,synthesize(design,optimize_logic=False))
    check_equivalence(design,synthesize(loads(tritverilog(synthesize(design)))))


def test_large_amount_bus_prunes_overshifts_without_enumerating_its_states():
    design=loads('''module m(input trit [1:0] a,input trit [41:0] k,output trit [2:0] y);
        assign y=a << k; endmodule''')
    net=synthesize(design)
    assert net.equivalence['passed']
    assert len(net.instances)<2000  # Bounded wiring-choice network, not 3**42 states.
    assert not any('shift' in inst.cell.lower() for inst in net.instances)


def test_showcase_alu_every_state_source_and_cells_against_integer_oracle():
    design=load('examples/alu9.tv')
    net=synthesize(design)
    assert net.equivalence['vectors']==729
    assert check_truth_table(design,net)==729
    for a,b in product(range(-4,5),repeat=2):
        assert result(a,b,2)==round(a/3)
        assert result(a,b,4)==a*b
    # Digit minimum differs from integer minimum, e.g. -2 = T1 and +2 = 1T.
    assert result(-2,2,-1)==-4
    assert result(-2,2,0)==4


def test_representative_spice_sequence_covers_every_opcode_and_output_level():
    vectors=representative_vectors()
    assert vectors==representative_vectors()
    assert {decode(v[4:]) for v in vectors}==set(range(-4,5))
    for key in expected(vectors[0]):
        assert {expected(v)[key] for v in vectors}=={-1,0,1}
    assert len(vectors)<30
