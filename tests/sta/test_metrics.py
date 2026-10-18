"""Crossing references distinguish ternary transitions and composing quantities."""
import numpy as np
import pytest

from tritflow.sta.metrics import crossings, edge_metrics


@pytest.mark.parametrize('before,after',[(-1,0),(0,1),(-1,1),(1,0),(0,-1),(1,-1)])
def test_relative_midpoint_and_endpoint_tail(before,after):
    time=np.linspace(0,10e-9,1001)
    voltage=np.interp(time,[0,2e-9,6e-9,10e-9],[5*before,5*before,5*after,5*after])
    result=edge_metrics(time,voltage,before,after,0,10e-9)
    assert result['midpoint_s']==pytest.approx(4e-9)
    assert result['slew_10_90_s']==pytest.approx(3.2e-9)
    fraction=1-.5/abs(5*(after-before))
    assert result['settling_s']==pytest.approx(2e-9+4e-9*fraction)
    assert result['tail_s']==pytest.approx(result['settling_s']-4e-9)


def test_recrossing_and_endpoint_stable_hazard():
    time=np.array([0,1,2,3,4,5,6,7])*1e-9
    voltage=np.array([-5,-5,1,-1,1,5,5,5])
    assert len(crossings(time,voltage,-1,1,0,7e-9))==2
    result=edge_metrics(time,voltage,-1,1,0,7e-9)
    assert result['midpoint_s']>3e-9
    hazard=edge_metrics(time,np.array([0,0,5,5,0,0,0,0]),0,0,0,7e-9)
    assert hazard['midpoint_s'] is None and hazard['tail_s'] is None
    assert hazard['settling_s']>3e-9


def test_only_endpoint_tail_is_added():
    # A 3 ns first-cell propagation and 4 ns second-cell propagation compose
    # to 7 ns. The first cell's 10 ns tail overlaps the second cell's response.
    first={'input_midpoint':.5e-9,'output_midpoint':3.5e-9,'tail':10e-9}
    second={'input_midpoint':3.5e-9,'output_midpoint':7.5e-9,'tail':2e-9}
    delay=(first['output_midpoint']-first['input_midpoint']+
           second['output_midpoint']-second['input_midpoint'])
    assert .5e-9+delay+second['tail']==pytest.approx(9.5e-9)
    assert .5e-9+delay+first['tail']+second['tail']!=pytest.approx(9.5e-9)
