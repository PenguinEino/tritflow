"""Measured timing surfaces must preserve sensitization, ramps and failure state."""
from pathlib import Path
import hashlib
import json
import shutil

import klayout.db as db
import pytest

from tritflow import CELLS_DIR
from tritflow.cells.timing import point,assemble,_axis,LOADS_F,RAMPS_S
from tritflow.cells.poly import annotate,mesh_network
from tritflow.cells.reference import device_parameters
from tritflow.cells.regression import operating_points


@pytest.fixture(scope='module')
def inverter_surface(tmp_path_factory):
    folder=tmp_path_factory.mktemp('timing_surface')
    text=(CELLS_DIR/'out/INV/INV.ext.spice').read_text()
    loads=(10e-15,1e-12);ramps=(1e-9,150e-9)
    points=[point('INV',text,load,ramp,folder/f'{ri}_{li}')
            for ri,ramp in enumerate(ramps) for li,load in enumerate(loads)]
    return assemble('INV',text,points,loads,ramps,{'per_pin':{}}),points


def test_load_ramp_axes_reference_and_observed_slow_output(inverter_surface):
    report,points=inverter_surface
    assert report['passed'] and report['complete']
    assert report['coverage']['single_pin_arcs']==6 and report['coverage']['simultaneous_transitions']==0
    assert report['axes']=={'load_f':[10e-15,1e-12],'input_transition_s':[1e-9,150e-9]}
    assert len({a['id'] for a in report['arcs']})==6
    for arc in report['arcs']:
        assert arc['changed_inputs']==['A'] and arc['side_inputs']=={}
        assert arc['output_from']==-arc['input_from'] and arc['output_to']==-arc['input_to']
        assert len(arc['settling_s'])==2 and all(len(row)==2 for row in arc['settling_s'])
        assert all(v is not None for row in arc['output_slew_10_90_s'] for v in row)
    slow=max(a['settling_s'][1][1] for a in report['arcs'])
    fast=max(a['settling_s'][0][1] for a in report['arcs'])
    assert slow>fast and slow>100e-9  # full ramp is included; no 50% subtraction.
    assert all(p['hold_s']>p['input_transition_s']+250e-9 for p in points)


def test_every_two_input_transition_keeps_side_bias_or_is_explicitly_simultaneous(tmp_path):
    text=(CELLS_DIR/'out/NAND/NAND.ext.spice').read_text()
    measured=point('NAND',text,10e-15,150e-9,tmp_path)
    assert measured['complete'] and measured['passed']
    report=assemble('NAND',text,[measured],(10e-15,),(150e-9,),{'per_pin':{}})
    assert len(report['arcs'])==36 and len(report['simultaneous'])==36
    assert {tuple(a['side_inputs'].values()) for a in report['arcs']}=={(-1,),(0,),(1,)}
    for arc in report['arcs']:
        pin=arc['input_pin'];other='B' if pin=='A' else 'A'
        assert arc['side_inputs']=={other:arc['from_inputs'][other]}
        assert arc['from_inputs'][other]==arc['to_inputs'][other]
    assert all(len(a['changed_inputs'])==2 and a['input_pin'] is None for a in report['simultaneous'])
    assert any(a['output_from']==a['output_to'] for a in report['arcs'])


def test_unsettled_values_are_not_replaced_by_a_delay(inverter_surface):
    report,points=inverter_surface
    # Preserve a real electrical-failure sample through table assembly.
    import copy
    failed=copy.deepcopy(points)
    row=failed[0]['rows'][0];row.update(settling_s=None,passed=False,status='unsettled')
    failed[0]['passed']=False
    text=(CELLS_DIR/'out/INV/INV.ext.spice').read_text()
    r=assemble('INV',text,failed,(10e-15,1e-12),(1e-9,150e-9),{})
    target=next(a for a in r['arcs'] if list(a['from_inputs'].values())==row['from'] and list(a['to_inputs'].values())==row['to'])
    assert r['complete'] and not r['passed']
    assert target['settling_s'][0][0] is None and target['status'][0][0]=='unsettled'
    assert 'null' in json.dumps(r,allow_nan=False)
    with pytest.raises(ValueError,match='incomplete'):
        assemble('INV',text,failed[:-1],(10e-15,1e-12),(1e-9,150e-9),{})


def test_constant_and_filler_have_no_invented_timing_arcs():
    for cell,kind in [('TIEP','constant'),('TIEZ','constant'),('TIEN','constant'),('FILL','physical')]:
        text=(CELLS_DIR/'out'/cell/f'{cell}.ext.spice').read_text()
        r=assemble(cell,text,[],LOADS_F,RAMPS_S,{'rows':[],'per_pin':{}})
        assert r['passed'] and r['complete'] and r['kind']==kind and r['arcs']==[]
        assert r['input_capacitance']['per_pin']=={}
    with pytest.raises(ValueError,match='strictly increasing'):_axis([1e-15,1e-15],'loads')


def test_sheet_mesh_converges_to_rectangular_poly_resistance():
    polygon=db.Polygon(db.Box(0,0,10000,1000))
    contacts=db.Region(db.Box(0,0,1000,1000));gates={1:db.Region(db.Box(9000,0,10000,1000))}
    coarse=mesh_network(polygon,contacts,gates,pitch_dbu=250)
    fine=mesh_network(polygon,contacts,gates,pitch_dbu=125)
    a=coarse['gate_to_contact_squares']['gate_1'];b=fine['gate_to_contact_squares']['gate_1']
    # Eight physical squares between 1-µm equipotential electrodes; center-cell
    # boundary staircasing overestimates by one pitch and converges under refinement.
    assert a==pytest.approx(8.25) and b==pytest.approx(8.125)
    assert abs(b-8)<abs(a-8)
    assert len(fine['edges'])==1 and fine['edges'][0]['squares']>0


def test_gds_poly_augmentation_preserves_devices_and_changes_settling(tmp_path,inverter_surface):
    folder=tmp_path/'INV';folder.mkdir()
    for filename in ['INV.gds','INV.ext.spice','lvs.lvsdb']:
        shutil.copyfile(CELLS_DIR/'out/INV'/filename,folder/filename)
    baseline=(folder/'INV.ext.spice').read_text();original_hash=hashlib.sha256(baseline.encode()).hexdigest()
    text,network=annotate(tmp_path,'INV',sheet_ohm=120.)
    assert len(network['gates'])==2 and network['resistors']
    assert device_parameters(baseline)==device_parameters(text)
    assert hashlib.sha256((folder/'INV.ext.spice').read_bytes()).hexdigest()==original_hash
    assert all(g['effective_contact_resistance_ohm']>0 for g in network['gates'].values())
    dc=operating_points(text,'INV');original=operating_points(baseline,'INV')
    assert dc['passed'] and dc['max_error_v']==pytest.approx(original['max_error_v'],abs=1e-6)
    proxy=point('INV',text,10e-15,1e-9,tmp_path/'poly')
    _,measured=inverter_surface
    base=next(p for p in measured if p['load_f']==10e-15 and p['input_transition_s']==1e-9)
    assert proxy['passed'] and proxy['max_settling_s']>base['max_settling_s']+10e-12
