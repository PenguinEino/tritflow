"""Named-device DC sweeps preserve baseline connectivity and cache real results."""
import hashlib
from pathlib import Path

import pytest
from tritflow.sim import sizing
from tritflow.sim.runner import SimulationError
from tritflow import CELLS_DIR


@pytest.mark.parametrize('candidate',[{'unknown':{'w_um':1}}, {'MP':{'width':1}},
    {'MP':{'w_um':0}}, {'RP':{'l_um':-1}}, {'MN':{'l_um':float('nan')}}, {'MN':{'w_um':True}}])
def test_invalid_dimensions(candidate,tmp_path,monkeypatch):
    monkeypatch.setattr(sizing,'CACHE',tmp_path/'cache')
    with pytest.raises(ValueError): sizing.sweep_dimensions('INV',[candidate])
    assert not (tmp_path/'cache').exists()


@pytest.mark.parametrize('kwargs',[{'fixed_trits':{'Z':0}}, {'fixed_trits':{'B':2}},
    {'fixed_trits':{'A':0}}, {'fixed_trits':{'B':True}}, {'step_v':0}, {'sweep_pin':'Y'}])
def test_invalid_sweep(kwargs):
    with pytest.raises(ValueError): sizing.sweep_dimensions('NANY',[],**kwargs)


def test_real_sizing_baseline_and_sparse_inheritance(tmp_path,monkeypatch):
    monkeypatch.setattr(sizing,'CACHE',tmp_path/'cache')
    source = CELLS_DIR/'out/INV/INV.spice';before = source.read_bytes()
    result = sizing.sweep_dimensions('INV',[{}, {'MN':{'l_um':1.5},'RP':{'l_um':20}},{}],
                                     workdir=tmp_path/'raw')
    assert len(result['rows'])==2 and result['adopted_index']==0
    baseline,changed = result['rows']
    assert baseline['passed'] and baseline['is_adopted'] and not changed['is_adopted']
    assert len(baseline['dc'])==3 and len(changed['dc'])==3
    assert changed['dimensions']['MP']==baseline['dimensions']['MP']
    assert changed['dimensions']['MN']['w_um']==baseline['dimensions']['MN']['w_um']
    assert changed['dimensions']['RN']==baseline['dimensions']['RN']
    assert changed['dimensions']['RP']['l_um']==20
    assert result['source_sha256']==hashlib.sha256(before).hexdigest()
    assert source.read_bytes()==before
    deck=(tmp_path/'raw/candidate_001/transfer/tb.spice').read_text()
    assert 'XMN n A VSS VSS NMOS W=5u L=1.5u' in deck
    assert (tmp_path/'raw/candidate_001/dc/state_002/ngspice.log').is_file()
    assert len(changed['transfer']['data']['v(a)'])==101
    def reject(*args,**kwargs): raise AssertionError('cache should avoid solver')
    monkeypatch.setattr(sizing,'dc_transfer',reject)
    cached=sizing.sweep_dimensions('INV',[{'MN':{'l_um':1.5},'RP':{'l_um':20}}])
    assert cached['rows']==result['rows']


def test_failed_solver_remains_failed_row(tmp_path,monkeypatch):
    monkeypatch.setattr(sizing,'CACHE',tmp_path)
    def fail(*args,**kwargs): raise SimulationError('deliberate nonconvergence')
    monkeypatch.setattr(sizing,'dc_transfer',fail)
    result=sizing.sweep_dimensions('NANY',[])
    row=result['rows'][0]
    assert row['passed'] is False and row['max_error_v'] is None
    assert row['max_static_current_a'] is None and row['dc']==[]
    assert 'deliberate nonconvergence' in row['error']
    assert not list(tmp_path.rglob('*.json'))


def test_finite_nonphysical_solver_root_is_not_a_design_measurement(tmp_path,monkeypatch):
    monkeypatch.setattr(sizing,'CACHE',tmp_path)
    monkeypatch.setattr(sizing,'dc_transfer',lambda *a,**k:{'data':{'v(y)':[333.]},'log':'raw root','deck':'raw deck'})
    monkeypatch.setattr(sizing,'dc_operating_points',lambda *a,**k:[{
        'output_v':{'Y':0},'error_v':{'Y':0},'rail_current_a':{'VDD':-.001},'passed':True}])
    row=sizing.sweep_dimensions('NANY',[])['rows'][0]
    assert row['max_error_v'] is None and row['max_static_current_a'] is None
    assert not row['passed'] and 'Nonphysical DC output' in row['error']
    assert row['transfer']['data']['v(y)']==[333.]  # preserve the rejected evidence


def test_dc_nodeset_callable_is_only_an_initial_guess():
    from tritflow.sim.characterize import dc_operating_points
    source,_=sizing.published_dimensions('INV')
    vectors=[(-1,),(0,),(1,)]
    rows=dc_operating_points(source,'INV',['A'],['Y'],vectors,lambda v:{'Y':-v[0]},
                             nodeset=lambda v:{'Y':3.2})
    assert all(r['passed'] for r in rows)
    assert rows[0]['output_v']['Y']>4.5 and rows[2]['output_v']['Y']< -4.5
    assert abs(rows[1]['output_v']['Y'])<.5
