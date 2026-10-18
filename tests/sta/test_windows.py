"""Measured slew, local-class consistency and symbolic history compatibility."""
from itertools import product
import math
import pytest

from tritflow.netlist import GateNetlist,Instance,Port
from tritflow.sta import analyze,ModelDomainError
from tritflow.sta.window import analyze_windows
from test_propagation import midpoint_library


def chain():
    return GateNetlist('chain',[Port('a','input'),Port('y','output')],
        [Instance('i','INV',{'A':'a','Y':'m'}),Instance('j','INV',{'A':'m','Y':'y'})])


def test_default_follows_measured_slew_instead_of_arbitrary_slow_ramp(library):
    models=midpoint_library(library)
    for arc in models['INV'].arcs:arc['propagation_s']=[[2e-9]*2,[100e-9]*2]
    r=analyze(chain(),library=models)
    # The measured output slew is 8 ns: the next full ramp is 10 ns,
    # rather than the unused 100 ns end of this synthetic timing table.
    second=2e-9+9/99*98e-9
    assert r.arrival['y']==pytest.approx(.5e-9+2e-9+second+7e-9)
    assert r.critical_path[1].input_transition_s==pytest.approx(10e-9)
    assert r.critical_path[0].arrival_s==pytest.approx(.5e-9+2e-9)
    assert r.arrival['y']==pytest.approx(.5e-9+sum(s.delay_s for s in r.critical_path)+r.critical_path[-1].settling_tail_s)
    assert r.provenance['metric']=='conditioned_slew_windows'
    assert r.sensitizing_pattern['before'] is None
    assert 'compatible_primary_endpoints' in r.sensitizing_pattern


def test_every_composed_single_input_class_is_bounded_by_independent_oracle(library):
    models=midpoint_library(library);model=models['INV']
    for k,arc in enumerate(model.arcs):
        arc['propagation_s']=[[(k+1)*1e-9]*2,[(k+3)*1e-9]*2]
        arc['output_slew_10_90_s']=[[(k+2)*1e-9]*2,[(k+8)*1e-9]*2]
    report=analyze(chain(),library=models,bin_s=.5e-9)
    oracle=[]
    for a,b in product((-1,0,1),repeat=2):
        if a==b:continue
        first=next(x for x in model.arcs if x['from_inputs']=={'A':a} and x['to_inputs']=={'A':b})
        second=next(x for x in model.arcs if x['from_inputs']=={'A':-a} and x['to_inputs']=={'A':-b})
        r=model.sample(first,report.loads['m']['total_f'],1e-9,field='output_slew_10_90_s')/.8
        expected=.5e-9+model.sample(first,report.loads['m']['total_f'],1e-9)
        expected+=model.sample(second,report.loads['y']['total_f'],r)+model.sample(second,report.loads['y']['total_f'],r,field='tail_s')
        oracle.append(expected)
    assert report.arrival['y']>=max(oracle)-1e-18
    assert report.arrival['y']<max(oracle)+.1e-9


def test_endpoint_and_reachable_pulse_classes_are_separate(library):
    models=midpoint_library(library)
    net=GateNetlist('pulse',[Port('a','input'),Port('y','output')],
        [Instance('i','INV',{'A':'a','Y':'na'}),Instance('n','NANY',{'A':'a','B':'na','Y':'m'}),
         Instance('b','BUF',{'A':'m','Y':'y'})])
    endpoint=analyze_windows(net,library=models,side_states='endpoint')
    reachable=analyze(net,library=models)
    assert endpoint.arrival['y']==0  # Endpoint-stable local recovery is not a logical edge.
    assert reachable.arrival['y']>0
    assert reachable.statistics['unmodeled_analog_recovery_propagation']
    assert not reachable.statistics['joint_temporal_witness']
    assert any('time alignment' in x for x in reachable.assumptions)


def test_slew_domain_and_search_budgets_fail_without_partial_success(library):
    models=midpoint_library(library)
    for arc in models['INV'].arcs:arc['output_slew_10_90_s']=[[200e-9]*2]*2
    with pytest.raises(ModelDomainError,match='Label full-ramp interval'):
        analyze(chain(),library=models)
    for arc in models['INV'].arcs:arc['output_slew_10_90_s']=[[8e-9]*2]*2
    with pytest.raises(RuntimeError,match='budget'):
        analyze(chain(),library=models,max_labels=1)
    with pytest.raises(ValueError):analyze(chain(),library=models,bin_s=math.nan)


def test_tied_pins_do_not_acquire_independent_transient_values(library):
    models=midpoint_library(library)
    n=GateNetlist('tied',[Port('a','input'),Port('y','output')],
        [Instance('n','NANY',{'A':'a','B':'a','Y':'y'})])
    r=analyze(n,library=models)
    assert r.arrival['y']>0
    for stage in r.critical_path:
        assert stage.from_inputs['A']==stage.from_inputs['B']
        assert stage.to_inputs['A']==stage.to_inputs['B']
