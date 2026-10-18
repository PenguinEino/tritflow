"""Analytic resistor networks and an explicit three-rail PNR geometry."""
import pytest
from tritflow.extract import solve_resistive_network, estimate_ir_drop


def test_analytic_rail_and_kcl():
    result = solve_resistive_network([('pad','a',10),('a','b',20)], {'pad':5}, {'a':-.001,'b':-.002})
    assert result['voltage_v']['a'] == pytest.approx(4.97)
    assert result['voltage_v']['b'] == pytest.approx(4.93)
    assert result['pad_injection_a']['pad'] == pytest.approx(.003)
    both = solve_resistive_network([('left','tap',10),('tap','right',10)], {'left':5,'right':5}, {'tap':-.002})
    assert both['voltage_v']['tap'] == pytest.approx(4.99)
    with pytest.raises(ValueError, match='Floating'):
        solve_resistive_network([('a','b',10)], {}, {'a':-.001})
    with pytest.raises(ValueError): solve_resistive_network([('a','b',0)], {'a':5})


def test_geometry_to_three_rails_and_midpoint():
    power = {'rails':[], 'straps':[], 'vias':[], 'pins':[]}
    template = {'rails': {'VDD':[9,11], 'VMID':[4,6], 'VSS':[-1,1]}}
    for rail, y in [('VDD',10),('VMID',5),('VSS',0)]:
        power['rails'].append({'net':rail, 'layer':'M1', 'width':2, 'points':[[0,y],[100,y]]})
        power['pins'].append({'name':rail,'layer':'M1','rect':[-1,y-1,1,y+1]})
    pnr = {'power':power, 'placements':[{'inst':'g1','cell':'INV','x':40,'y':0}]}
    char = {'INV': {'dc':[{'input_trits':[0], 'rail_current_a':{'VDD':-.002, 'VMID':0, 'VSS':.001}}]}}
    r = estimate_ir_drop(pnr,template,{'INV':{'width':20}},char,sheet_ohm={'M1':.1,'M2':.1},instance_vectors={'g1':[0]})
    cell = r['cells']['g1']
    # 50 um / 2 um * .1 ohm/sq = 2.5 ohm to each rail's pad.
    assert cell['rail_v']['VDD'] == pytest.approx(4.995)
    assert cell['rail_v']['VSS'] == pytest.approx(-4.9975)
    assert cell['zero_level_shift_v'] == pytest.approx(-.00125)
    assert sum(r['pad_injection_a'].values()) == pytest.approx(.001)


def test_strap_vias_and_dual_feeds():
    power = {'rails':[], 'straps':[], 'vias':[], 'pins':[]}
    template = {'rails': {r:[y-1,y+1] for r,y in [('VDD',10),('VMID',5),('VSS',0)]}}
    for rail, y in [('VDD',10),('VMID',5),('VSS',0)]:
        power['rails'].append({'net':rail,'layer':'M1','width':2,'points':[[0,y],[100,y]]})
        for x in (0,100):
            power['straps'].append({'net':rail,'layer':'M2','width':2,'points':[[x,y],[x,20]]})
            power['vias'].append({'net':rail,'x':x,'y':y})
            power['pins'].append({'name':rail,'layer':'M2','rect':[x-1,19,x+1,21]})
    pnr={'power':power,'placements':[{'inst':'g','cell':'NANY','x':40,'y':0}]}
    char={'NANY':{'dc':[{'input_trits':[0,0],'rail_current_a':{'VDD':-.002,'VMID':-.001,'VSS':.002}}]}}
    r=estimate_ir_drop(pnr,template,{'NANY':{'width':20}},char)
    cell=r['cells']['g']
    assert 4.99 < cell['rail_v']['VDD'] < 5
    assert cell['zero_level_shift_v'] is None
    assert cell['clamp_zero_shift_v'] < 0
    power['pins']=[]
    with pytest.raises(ValueError,match='Floating'): estimate_ir_drop(pnr,template,{'NANY':{'width':20}},char)
