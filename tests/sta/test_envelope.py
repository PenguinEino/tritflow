"""Conservative timing must cover modeled slow classes and downstream hazards."""
import pytest

from tritflow.netlist import GateNetlist,Instance,Port
from tritflow.sta import analyze,ModelDomainError
from tritflow.sta.envelope import analyze_envelope
from tritflow.sta.validate import case_coverage,pessimism
from test_propagation import midpoint_library


def chain():
    return GateNetlist('chain',[Port('a','input'),Port('y','output')],
        [Instance('i','INV',{'A':'a','Y':'m'}),Instance('j','INV',{'A':'m','Y':'y'})])


def test_default_envelope_includes_slow_internal_ramp_without_stacking_tails(library):
    models=midpoint_library(library)
    for arc in models['INV'].arcs:
        arc['propagation_s']=[[2e-9,2e-9],[100e-9,100e-9]]
    report=analyze(chain(),library=models,global_mode="envelope")
    assert report.arrival['y']==pytest.approx(.5e-9+2e-9+100e-9+7e-9)
    assert [s.input_transition_s for s in report.critical_path]==[1e-9,100e-9]
    assert report.critical_path[0].settling_tail_s==0
    assert report.provenance['metric']=='local_class_ramp_envelope'
    assert report.sensitizing_pattern['before'] is None
    assert not report.statistics['joint_endpoint_witness']
    assert analyze(chain(),library=models,global_mode='endpoint').arrival['y']<report.arrival['y']
    models['INV'].arcs[0]['passed'][1][0]=False
    with pytest.raises(ModelDomainError):analyze(chain(),library=models,global_mode="envelope")


def test_recovery_clock_can_launch_downstream_activity_on_stable_endpoint(library):
    models=midpoint_library(library)
    for arc in models['NANY'].arcs:
        arc['recovery_s']=[[30e-9,30e-9],[30e-9,30e-9]]
    net=GateNetlist('hazard',[Port('a','input'),Port('b','input'),Port('y','output')],
        [Instance('g','NANY',{'A':'a','B':'b','Y':'m'}),Instance('h','BUF',{'A':'m','Y':'y'})])
    r=analyze(net,library=models,global_mode="envelope")
    assert r.arrival['y']==pytest.approx(.5e-9+30e-9+2e-9+7e-9)
    assert r.critical_path[0].output_transition[0]==r.critical_path[0].output_transition[1]
    assert r.critical_path[0].metric=='recovery_guard'
    assert analyze_envelope(net,library=models,include_recovery=False).arrival['y']<r.arrival['y']


def test_non_closed_slew_domain_is_reported_without_clipping(library):
    models=midpoint_library(library)
    for arc in models['INV'].arcs:arc['output_slew_10_90_s']=[[200e-9]*2]*2
    r=analyze(chain(),library=models,global_mode="envelope")
    assert not r.statistics['slew_domain_closed']
    assert r.statistics['slew_domain_violations'][0]['full_ramp_upper_s']==pytest.approx(250e-9)
    assert any('not closed' in w for w in r.warnings)
    # The envelope has not used a clipped 250 ns point disguised as a valid ramp.
    assert all(s.input_transition_s<=100e-9 for s in r.critical_path)
    with pytest.raises(ModelDomainError):analyze(chain(),library=models,input_transition_s=101e-9,global_mode="envelope")


def test_constant_cone_has_no_fictitious_activity(library):
    models=midpoint_library(library)
    n=GateNetlist('constant',[Port('y','output')],
        [Instance('t','TIEZ',{'Y':'z'}),Instance('i','INV',{'A':'z','Y':'y'})])
    assert analyze(n,library=models,global_mode="envelope").arrival['y']==0


def test_every_recorded_case_includes_initial_and_unchanged_endpoint_hazards():
    measured={'rows':[{'previous_trits':None,'outputs':{'y':{'settling_s':0.}}},
        {'previous_trits':[0],'input_trits':[0],'outputs':{'y':{'settling_s':20e-9}}}]}
    fail=case_coverage(measured,{'y':19e-9})
    assert fail['case_count']==2 and fail['initial_state_case_count']==1
    assert not fail['passed'] and fail['underprediction_count']==1
    assert fail['violations'][0]['row']==1
    assert case_coverage(measured,{'y':20e-9})['passed']
    measured['rows'][1]['outputs']['y']['settling_s']=None
    assert not case_coverage(measured,{'y':100e-9})['passed']
    assert pessimism([{'predicted_s':30e-9,'simulated_s':20e-9}])['mean_factor']==pytest.approx(1.5)
