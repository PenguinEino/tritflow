import pytest

from tritflow import hdl, synth
from tritflow.seq.simulator import Simulator


@pytest.mark.parametrize('mapped',[False,True])
def test_edges_and_hold(mapped):
    circuit = hdl.load('examples/shift3.tv')
    if mapped:
        circuit = synth.synthesize(circuit)
    sim = Simulator(circuit,initial={'q[0]':-1,'q[1]':0,'q[2]':1})
    for d in (-1,0,1):
        assert sim.drive({'clk':-1,'d':d}) == {'q[2]':1,'q[1]':0,'q[0]':-1}
    assert sim.drive({'clk':1,'d':1}) == {'q[2]':0,'q[1]':-1,'q[0]':1}
    for d in (-1,0,1):
        assert sim.drive({'clk':1,'d':d}) == {'q[2]':0,'q[1]':-1,'q[0]':1}
    assert sim.drive({'clk':-1,'d':-1}) == {'q[2]':0,'q[1]':-1,'q[0]':1}
    assert sim.drive({'clk':1,'d':-1}) == {'q[2]':-1,'q[1]':1,'q[0]':-1}
    assert sim.edges == 2
    with pytest.raises(ValueError,match='zero'):
        sim.drive({'clk':0,'d':0})
