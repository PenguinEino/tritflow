"""Band references, available process data and controlled wire-C comparisons."""
import numpy as np
import pytest
from tritflow import CELLS_DIR, TRIT_VOLTS
from tritflow.sim import simulate, input_vectors, measure_sequence
from tritflow.sim.corners import available_corners
from tritflow.sim.diagnose import device_fingerprint, reverse_negative_resistors
from tritflow.viz.scaling import corners_figure


def test_only_distributed_process_is_advertised():
    inventory=available_corners()
    assert inventory['available']==['TYP'] and inventory['lib_sections']=={}
    assert inventory['pdk_provenance']['qualified_commit'].startswith('5d963db')


def test_publication_rejects_dev_deck_even_with_a_pinned_commit_label():
    from tritflow.sim.publication import qualified_pdk
    expected=available_corners()['pdk_provenance']
    assert qualified_pdk({'pdk_provenance':expected},expected)
    modified={**expected,'consumed_sha256':{**expected['consumed_sha256'],
        'libs.tech/klayout/tech/lvs/01_Extract.lvs':'old-dev-deck'}}
    assert not qualified_pdk({'pdk_provenance':modified},expected)
    assert not qualified_pdk({},expected)


def test_publication_rejects_missing_historical_evidence_instead_of_null_deltas(tmp_path,monkeypatch):
    from tritflow.sim import publication
    monkeypatch.setattr(publication,'ROOT',tmp_path)
    with pytest.raises(FileNotFoundError,match='Historical baseline is incomplete'):
        publication.publish_audit(tmp_path/'report.json')
    assert not (tmp_path/'report.json').exists()


def test_supply_tracking_and_project_bands_are_separate():
    text=(CELLS_DIR/'out/INV/INV.ext.spice').read_text()
    run=simulate(text,'INV',['A'],['Y'],input_vectors(1),lambda v:{'Y':-v[0]},
        temperature_c=85,supplies_v={'VDD':4.5,'VMID':0.,'VSS':-4.5})
    assert run['measurements']['passed']
    nominal=measure_sequence(run['waveforms'],run['stimulus'],lambda v:{'Y':-v[0]},ideal_volts=TRIT_VOLTS)
    assert not nominal['passed'] and nominal['max_error_v']>.5
    assert np.isfinite(run['waveforms']['v(Y)']).all()
    from tritflow.viz.waves import waveform_figure
    figure=waveform_figure(run)
    assert list(figure.layout.yaxis.tickvals)==[-4.5,0.,4.5]
    assert any(shape.y0==4.0 and shape.y1==5.0 for shape in figure.layout.shapes)


def test_intrinsic_device_changes_cannot_be_hidden_as_wire_capacitance():
    source='.subckt A a y VDD VMID VSS\nXRN y n VDD F_RR W=2.8u L=30u\n.ends A\n'
    wire=source.replace('.ends A','Ctfwire0 y 0 1e-14\n.ends A')
    assert device_fingerprint(source)==device_fingerprint(wire)
    assert device_fingerprint(source)!=device_fingerprint(reverse_negative_resistors(source))


def test_delay_control_seeds_internal_bus_nets_without_forcing_the_transient():
    from tritflow.netlist import GateNetlist
    from tritflow.sim import build_testbench
    from tritflow.sim.diagnose import schematic_nodeset
    from tritflow.sim.spice import gate_spice
    net=GateNetlist.from_dict({'top':'chain','ports':[{'name':'a','dir':'input'},{'name':'y','dir':'output'}],
        'instances':[{'name':'g0','cell':'INV','pins':{'A':'a','Y':'n[0]'}},
                     {'name':'g1','cell':'INV','pins':{'A':'n[0]','Y':'y'}}]})
    seeds=schematic_nodeset(net,['a'],(1,))
    assert seeds == {'xdut.tf_6e5b305d':-5.}
    source=gate_spice(net,(CELLS_DIR/'out/all.spice').read_text())
    bench=build_testbench(source,'chain',['a'],['y'],[(1,)],nodeset=seeds)
    assert '.nodeset v(xdut.tf_6e5b305d)=-5' in bench['netlist']
    assert '.ic ' not in bench['netlist'] and 'uic' not in bench['commands'].lower()


def test_corner_figure_keeps_unsettled_delays_missing():
    case={'dut':'full_add','state':'complete','conditions':{'temperature_c':27.,'supply_scale':1.},
          'dc':{'max_static_current_a':.001},'transient':{
              name:{'max_error_v':1.,'max_settling_s':None,'passed':False} for name in ['nominal','tracking']}}
    fig=corners_figure({'temperatures_c':[27.],'supply_scales':[1.],'rows':[case]})
    assert fig.data[3].z[0][0] is None
    assert 'FAIL' in fig.data[0].text[0][0]
