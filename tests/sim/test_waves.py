"""Plotly objects preserve voltage bands, failed windows and signed rail current."""
import numpy as np
import pytest
from tritflow.viz.waves import waveform_figure,transfer_figure


def result():
    return {'stimulus':{'outputs':['Y'],'vectors':[(0,),(1,)],'hold_s':10e-9},
        'waveforms':{'time':np.array([0,10,20])*1e-9,'v(y)':np.array([0,0,5])},
        'measurements':{'rows':[
            {'check_s':9e-9,'input_trits':[0], 'outputs':{'Y':{'ideal_trit':0,'voltage_v':0,'error_v':0,'passed':True,'settling_s':0}}},
            {'check_s':19e-9,'input_trits':[1], 'outputs':{'Y':{'ideal_trit':1,'voltage_v':4,'error_v':-1,'passed':False,'settling_s':None}}}]}}


def test_waveform_bands_overlay_and_fail_marks():
    r=result();f=waveform_figure(r,pre=r)
    assert len(f.layout.shapes)==6  # three shaded bands plus ideal level lines
    assert any(t.name=='Y: FAIL' and t.marker.symbol=='x' for t in f.data)
    assert any(t.name=='Y: pre-layout' and t.line.dash=='dash' for t in f.data)
    r['measurements']['rows'][1]['outputs']['Y']['settling_s']=2e-9
    r['measurements']['rows'][1]['outputs']['Y']['passed']=True
    f=waveform_figure(r)
    arrow=next(a for a in f.layout.annotations if a.text=='2.00 ns')
    assert arrow.x==pytest.approx(12) and arrow.ax==pytest.approx(10)
    assert any(s.type=='rect' and s.y0==-.5 and s.y1==.5 for s in f.layout.shapes)
    with pytest.raises(ValueError):waveform_figure(r,annotate_settling='invalid')


def test_dc_secondary_current_axis_and_units():
    d={'v(a)':np.array([-5,0,5]),'v(y)':np.array([5,0,-5]),'i(vdd)':np.array([0,-1e-3,0])}
    f=transfer_figure(d,'A',['Y'])
    assert f.data[1].yaxis=='y2'
    np.testing.assert_allclose(f.data[1].y,[0,-1000,0])
    assert len(f.layout.shapes)==6
