"""Band references, available process data and controlled wire-C comparisons."""
import numpy as np
from tritflow import CELLS_DIR, TRIT_VOLTS
from tritflow.sim import simulate, input_vectors, measure_sequence
from tritflow.sim.corners import available_corners
from tritflow.sim.diagnose import device_fingerprint, reverse_negative_resistors
from tritflow.viz.scaling import corners_figure


def test_only_distributed_process_is_advertised():
    inventory=available_corners()
    assert inventory['available']==['TYP'] and inventory['lib_sections']=={}
    assert inventory['pdk_provenance']['qualified_commit'].startswith('5d963db')


def test_supply_tracking_and_project_bands_are_separate():
    text=(CELLS_DIR/'out/INV/INV.ext.spice').read_text()
    run=simulate(text,'INV',['A'],['Y'],input_vectors(1),lambda v:{'Y':-v[0]},
        temperature_c=85,supplies_v={'VDD':4.5,'VMID':0.,'VSS':-4.5})
    assert run['measurements']['passed']
    nominal=measure_sequence(run['waveforms'],run['stimulus'],lambda v:{'Y':-v[0]},ideal_volts=TRIT_VOLTS)
    assert not nominal['passed'] and nominal['max_error_v']>.5
    assert np.isfinite(run['waveforms']['v(Y)']).all()


def test_intrinsic_device_changes_cannot_be_hidden_as_wire_capacitance():
    source='.subckt A a y VDD VMID VSS\nXRN y n VDD F_RR W=2.8u L=30u\n.ends A\n'
    wire=source.replace('.ends A','Ctfwire0 y 0 1e-14\n.ends A')
    assert device_fingerprint(source)==device_fingerprint(wire)
    assert device_fingerprint(source)!=device_fingerprint(reverse_negative_resistors(source))


def test_corner_figure_keeps_unsettled_delays_missing():
    case={'dut':'full_add','state':'complete','conditions':{'temperature_c':27.,'supply_scale':1.},
          'dc':{'max_static_current_a':.001},'transient':{
              name:{'max_error_v':1.,'max_settling_s':None,'passed':False} for name in ['nominal','tracking']}}
    fig=corners_figure({'temperatures_c':[27.],'supply_scales':[1.],'rows':[case]})
    assert fig.data[3].z[0][0] is None
    assert 'FAIL' in fig.data[0].text[0][0]
