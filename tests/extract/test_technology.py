"""Published current limits and the boundary between device data and wire models."""
import pytest
from tritflow.extract import estimate_ir_drop, parameter_audit, EM_LIMITS


def test_device_resistor_and_esd_data_do_not_become_metal_substrate_parameters():
    data=parameter_audit()
    assert data['metal_sheet_ohm_per_square']['origin']=='assumption'
    assert data['wire_capacitance']['origin']=='assumption'
    assert data['via_ohm']['origin']=='assumption'
    assert data['document_resistor_sheet_ohm_per_square']['RS_poly']==120
    assert data['intermetal_esd_rule']['derived_f_per_um2']==pytest.approx(.03125e-15)
    assert data['capacitor_device']['CSIO_f_per_um2']==pytest.approx(.6e-15)
    assert data['em_limits']['page']==17


def test_via_count_changes_published_current_limit_margin():
    template={'rails':{rail:[y-1,y+1] for rail,y in [('VDD',10),('VMID',5),('VSS',0)]}}
    power={'rails':[],'straps':[],'vias':[],'pins':[]}
    for rail,y in [('VDD',10),('VMID',5),('VSS',0)]:
        power['rails'].append({'net':rail,'layer':'M1','width':10,'points':[[0,y],[100,y]]})
        power['straps'].append({'net':rail,'layer':'M2','width':6,'points':[[0,y],[0,30]]})
        power['vias'].append({'net':rail,'x':0,'y':y})
        power['pins'].append({'name':rail,'layer':'M2','rect':[-1,29,1,31]})
    pnr={'placements':[{'inst':'cell','cell':'INV','x':40,'y':0}],'power':power}
    char={'INV':{'dc':[{'input_trits':[0],'rail_current_a':{'VDD':-.001,'VMID':0,'VSS':.001}}]}}
    def solve():return estimate_ir_drop(pnr,template,{'INV':{'width':20}},char)
    one=solve();via=one['em_check']['worst_by_kind']['TC']
    assert via['current_a']==pytest.approx(.001,rel=1e-6)
    assert via['limit_a']==pytest.approx(780e-6)
    assert via['utilization']==pytest.approx(1/.78,rel=1e-6)
    assert one['em_check']['passed'] is False
    power['vias'] += [dict(v) for v in power['vias']]
    two=solve()
    assert two['em_check']['worst_by_kind']['TC']['current_a']==pytest.approx(.0005,rel=1e-6)
    assert two['em_check']['passed'] is True
    # Two parallel cuts reduce resistance too; EM checking never clamps current.
    assert two['cells']['cell']['rail_v']['VDD'] > one['cells']['cell']['rail_v']['VDD']
