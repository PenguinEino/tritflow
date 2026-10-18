"""Actual ngspice/PDK regression with self-contained source-schematic fixtures."""
import json
from pathlib import Path
import shutil
import pytest
from tritflow import PDK_ROOT
from tritflow.sim import (simulate, input_vectors, build_testbench, dc_transfer,
                          compare_layout, gate_spice)
from tritflow.sim.characterize import characterize_cell
from tritflow.netlist import GateNetlist, Port, Instance

FIXTURES = Path(__file__).parent/'fixtures'
pytestmark = pytest.mark.skipif(not shutil.which('ngspice') or not (PDK_ROOT/'libs.tech/spice/models/ip62_models').exists(), reason='ngspice and TR-1um PDK required')


@pytest.mark.parametrize('cell,top,inputs', [('INV','inverter',['vin']),('NANY','nany',['a','b'])])
def test_characterization_all_biases_loads_transitions(cell, top, inputs, tmp_path):
    destination = tmp_path/'cell.char.json'
    result = characterize_cell(cell, (FIXTURES/f'{top}.spice').read_text(), top=top,
                               inputs=inputs, output='vout', destination=destination, include_cascade=False)
    assert result['passed']
    assert json.loads(destination.read_text())['source_sha256'] == result['source_sha256']
    assert len(result['dc']) == 3**len(inputs)
    assert len(result['input_capacitance']['rows']) == len(inputs)*3**len(inputs)
    assert 0 < result['input_capacitance']['max_f'] < 1e-12
    assert result['max_static_current_a'] > 1e-4
    for transient in result['transient']:
        edges = [(tuple(r['previous_trits']),tuple(r['input_trits'])) for r in transient['rows'][1:]]
        assert len(set(edges)) == (3**len(inputs))*(3**len(inputs)-1)
        assert transient['unsettled'] == 0
    assert result['fanout']['suggested_max'] >= 1


def test_dc_and_pre_post_comparison():
    spice = (FIXTURES/'inverter.spice').read_text()
    data = dc_transfer(spice, 'inverter', ['vin'], ['vout'], 'vin', step_v=5)['data']
    assert data['v(vout)'].tolist() == pytest.approx([5, -.03954, -5], abs=.001)
    result = compare_layout(spice, spice, 'inverter', ['vin'], ['vout'],
                            input_vectors(1), lambda v: {'vout':-v[0]})
    assert result['passed']
    assert all(r['settling_difference_s']['vout'] == 0 for r in result['transitions'])


def test_testbench_validation_and_explicit_order():
    spice = (FIXTURES/'nany.spice').read_text()
    bench = build_testbench(spice,'nany',['a','b'],['vout'],[(-1,0),(1,-1)], loads_f={'vout':1e-13}, nodeset={'xdut.net1':5})
    assert 'Xdut a b vout VDD VSS VMID nany' in bench['netlist']
    assert '.nodeset v(xdut.net1)=5' in bench['netlist']
    with pytest.raises(ValueError): build_testbench(spice,'nany',['a'],['vout'],[(0,)])
    with pytest.raises(ValueError): build_testbench(spice,'nany',['a','b'],['vout'],[(2,0)])
    with pytest.raises(ValueError): build_testbench(spice,'nany',['a','b'],['vout'],[(0,0)],loads_f=-1)


def test_gate_reference_contract():
    netlist = GateNetlist('test', [Port('a[0]','input'),Port('y','output')],
                          [Instance('g1','INV',{'A':'a[0]','Y':'y'})])
    good = '.subckt INV A Y VDD VMID VSS\nR1 A Y 1k\n.ends INV\n'
    text = gate_spice(netlist,good)
    from tritflow.synth.writers import spice
    assert text.startswith(spice(netlist))
    with pytest.raises(ValueError):
        gate_spice(netlist, good.replace('A Y VDD VMID VSS','VDD VSS A Y'))


def test_bit_blasted_ports_survive_nutmeg_expressions():
    # Passive feedthrough tests literal square-bracket node names independently
    # of cell topology. Nutmeg otherwise mistakes them for vector indexing.
    spice = '.subckt bits a[0] y[0] VDD VMID VSS\nR1 a[0] y[0] 1k\n.ends bits\n'
    result = simulate(spice, 'bits', ['a[0]'], ['y[0]'], input_vectors(1),
                      lambda v: {'y[0]': v[0]})
    assert result['measurements']['passed']
    assert 'v(a[0])' in result['waveforms']
    assert 'v(y[0])' in result['waveforms']


def test_case_sensitive_hdl_names_round_trip_through_ngspice():
    """Nine independent states expose a/A shorts and mixed-case output aliases."""
    import numpy as np
    from tritflow.synth.writers import spice, spice_names
    from tritflow.sim.characterize import dc_operating_points
    net = GateNetlist('case_test', [Port('a','input'),Port('A','input'),
        Port('y','output'),Port('Y','output')], [
        Instance('g','INV',{'A':'a','Y':'y'}), Instance('G','INV',{'A':'A','Y':'Y'})])
    cells = '.subckt INV A Y VDD VMID VSS\nE1 Y 0 A 0 -1\n.ends INV\n'
    text = gate_spice(net, cells)
    assert text.startswith(spice(net))
    names = spice_names(net.nets(), ('VDD','VMID','VSS','0'))
    assert len({n.lower() for n in names.values()}) == len(names)
    expected = lambda v: {'y':-v[0], 'Y':-v[1]}
    run = simulate(text,net.top,['a','A'],['y','Y'],input_vectors(2),expected)
    assert run['measurements']['passed']
    assert not np.array_equal(run['waveforms']['v(a)'],run['waveforms']['v(A)'])
    assert not np.array_equal(run['waveforms']['v(y)'],run['waveforms']['v(Y)'])
    assert all(r['passed'] for r in dc_operating_points(text,net.top,['a','A'],['y','Y'],input_vectors(2),expected))
    assert all(set(r['outputs']) == {'y','Y'} for r in run['measurements']['rows'])
