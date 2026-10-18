"""Midpoint composition, signed delays and measured-slew transport."""
from copy import deepcopy

import pytest

from tritflow.netlist import GateNetlist,Instance,Port
from tritflow.sta import analyze
from tritflow.sta.propagation import PropagationCell


def midpoint_library(library):
    library.metric='midpoint'
    for name,model in list(library.cells.items()):
        data=deepcopy(model.data)
        for arc in data['arcs']+data['simultaneous']:
            arc['propagation_s']=[[2e-9,2e-9],[2e-9,2e-9]]
            arc['tail_s']=[[7e-9,7e-9],[7e-9,7e-9]]
            arc['output_slew_10_90_s']=[[8e-9,8e-9],[8e-9,8e-9]]
            arc['recovery_s']=[[3e-9,3e-9],[3e-9,3e-9]]
        library.cells[name]=PropagationCell(data)
    return library


def test_endpoint_tail_once_and_slew_transport(library):
    models=midpoint_library(library)
    n=GateNetlist('chain',[Port('a','input'),Port('y','output')],
        [Instance('i1','INV',{'A':'a','Y':'m'}),Instance('i2','INV',{'A':'m','Y':'y'})])
    r=analyze(n,library=models,vector_pairs=[({'a':0},{'a':1})])
    assert r.arrival['y']==pytest.approx(.5e-9+2*2e-9+7e-9)
    assert r.critical_path[0].arrival_s==pytest.approx(2.5e-9)
    assert r.critical_path[-1].arrival_s==pytest.approx(r.arrival['y'])
    assert r.critical_path[1].input_transition_s==pytest.approx(10e-9)
    graph=analyze(n,library=models)
    assert graph.arrival['y']==pytest.approx(r.arrival['y'])
    fixed=analyze(n,library=models,vector_pairs=[({'a':0},{'a':1})],propagate_slew=False)
    assert fixed.critical_path[1].input_transition_s==1e-9


def test_signed_midpoint_delay_is_not_clamped(library):
    models=midpoint_library(library);model=models['INV'];arc=model.arcs[0]
    arc['propagation_s']=[[-2e-9,-2e-9],[-2e-9,-2e-9]]
    assert model.sample(arc,1e-14,field='propagation_s')==pytest.approx(-2e-9)


def test_midpoint_pattern_is_jointly_sensitizable(library):
    models=midpoint_library(library)
    n=GateNetlist('constant',[Port('a','input'),Port('y','output')],
        [Instance('i','INV',{'A':'a','Y':'na'}),Instance('n','NANY',{'A':'a','B':'na','Y':'y'})])
    r=analyze(n,library=models)
    assert set(r.transition_arrival['y'])=={'0->0'}
    assert r.critical_path[-1].metric=='local_recovery'


def test_ordered_reconvergence_propagates_logical_pulse(library):
    models=midpoint_library(library)
    n=GateNetlist('pulse',[Port('a','input'),Port('y','output')],
        [Instance('i','INV',{'A':'a','Y':'na'}),Instance('n','NANY',{'A':'a','B':'na','Y':'m'}),
         Instance('b','BUF',{'A':'m','Y':'y'})])
    r=analyze(n,library=models,vector_pairs=[({'a':-1},{'a':1})])
    assert r.arrival['y']==pytest.approx(13.5e-9)
    assert r.critical_path[-1].output_transition==(-1,0)
    assert r.statistics['event_model']
