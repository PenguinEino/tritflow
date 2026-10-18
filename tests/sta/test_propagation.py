"""Midpoint composition, signed delays and measured-slew transport."""
from copy import deepcopy
import json

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


def test_small_measured_local_recovery_is_not_discarded(library):
    models=midpoint_library(library)
    for arc in models['NANY'].arcs:
        arc['recovery_s']=[[.25e-9,.25e-9],[.25e-9,.25e-9]]
    n=GateNetlist('recovery',[Port('a','input'),Port('b','input'),Port('y','output')],
        [Instance('n','NANY',{'A':'a','B':'b','Y':'y'})])
    r=analyze(n,library=models,vector_pairs=[({'a':-1,'b':-1},{'a':0,'b':-1})])
    assert r.arrival['y']==pytest.approx(.75e-9)


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
    with pytest.raises(RuntimeError,match='event budget'):
        analyze(n,library=models,vector_pairs=[({'a':-1},{'a':1})],max_events=1)


def test_published_metrics_reconstruct_band_entry():
    from tritflow import ROOT
    folder=ROOT/'results/sta/propagation/tables'
    if not folder.exists():pytest.skip('Run STA characterization to generate midpoint tables')
    count=0
    for path in folder.glob('*.propagation.json'):
        data=json.loads(path.read_text())
        assert data['passed'] and data['complete']
        assert data['coverage']['measured_grid_points']==30
        for arc in data['arcs']+data['simultaneous']:
            if arc['output_from']==arc['output_to']:continue
            for i,ramp in enumerate(data['axes']['input_transition_s']):
                for j,_ in enumerate(data['axes']['load_f']):
                    assert arc['propagation_s'][i][j]+ramp/2+arc['tail_s'][i][j]==pytest.approx(arc['settling_s'][i][j],abs=1e-18)
                    count+=1
    assert count>3000


def test_real_default_midpoint_report_and_source_pattern():
    from tritflow import ROOT
    from tritflow.synth import evaluate_netlist
    path=ROOT/'build/adder_scaling/adder6/adder6.json'
    if not path.exists() or not (ROOT/'results/sta/propagation/tables/NANY.propagation.json').exists():
        pytest.skip('Real layout/timing publication is not present')
    report=analyze(path)
    assert report.provenance['metric']=='midpoint_with_endpoint_tail'
    n=GateNetlist.load(path);pattern=report.sensitizing_pattern
    old=evaluate_netlist(n,pattern['before'],return_all=True)
    new=evaluate_netlist(n,pattern['after'],return_all=True)
    for stage in report.critical_path:
        assert (int(old[stage.output_net]),int(new[stage.output_net]))==stage.output_transition
    assert report.arrival[report.critical_output]==pytest.approx(
        .5e-9+sum(s.delay_s for s in report.critical_path)+report.critical_path[-1].settling_tail_s)
