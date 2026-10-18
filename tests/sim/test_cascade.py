from pathlib import Path
import hashlib
import pytest
from tritflow.sim.cascade import cascade_bench,characterize_cascade,replay_reference,attach_cascade
from tritflow.sim import simulate


def test_chain_oracle_and_actual_gate_loading():
    source=(Path(__file__).parent/'fixtures/inverter.spice').read_text()
    # Characterize a custom-port schematic through its declared-pin adapter.
    r=characterize_cascade('INV',source,top='inverter',inputs=['vin'],output='vout',fanouts=(1,2))
    assert r['chains_passed'] and r['suggested_max']==2
    assert len(r['cases'])==3
    base={'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'passed':True,'fanout':{'suggested_max':4}}
    attach_cascade(base,r)
    assert base['fanout']['suggested_max']==2
    assert base['fanout']['capacitance_estimate_max']==4
    with pytest.raises(ValueError):attach_cascade({'source_sha256':'wrong'},r)


def test_binary_chain_neutral_and_receiver_pin():
    source=(Path(__file__).parent/'fixtures/nany.spice').read_text()
    wrapper='.subckt NANY A B Y VDD VMID VSS\nX1 A B Y VDD VSS VMID nany\n.ends NANY\n'+source
    circuit,inputs,outputs,expected,loads=cascade_bench('NANY',wrapper,driven_pin='B',fanout=2,bias=-1)
    values=expected((1,0))
    assert values=={'y0':-1,'y1':1,'y2':1}
    assert loads['y0']==0 and loads['y1']==10e-15
    assert 'Xstage1 bias y0 y1' in circuit


def test_saved_cascade_reference_replay(tmp_path):
    folder=Path.home()/'balanced-ternary-logic/simulation/cascade'
    if not folder.exists(): pytest.skip('Optional saved source cascade checkout unavailable')
    r=replay_reference(folder,workdir=tmp_path)
    assert r['passed'] and r['saved_waveform_max_checkpoint_difference_v']<.01
