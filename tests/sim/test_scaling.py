"""Arithmetic coverage and cache validation independent of expensive full PNR."""
import json
from pathlib import Path

from tritflow.hdl import load
from tritflow.synth import synthesize, evaluate_netlist
from tritflow.sim.scaling import adder_oracle,adder_vectors,_valid_cache
from tritflow.sim.postlayout import file_hash
from tritflow.viz.scaling import scaling_figure,load_sweep_figure,sizing_figure
from tritflow.sim.sizing import load_grid


def test_full_length_carries_are_independently_correct():
    for n in (1,2,6):
        net=synthesize(load('examples/adder.tv',top='adder',params={'N':n}),verify=False)
        inputs=[p.name for p in net.ports if p.dir=='input']
        outputs=[p.name for p in net.ports if p.dir=='output']
        vectors,labels=adder_vectors(n,inputs);expected=adder_oracle(n,inputs,outputs)
        for v in vectors:
            assert expected(v)==evaluate_netlist(net,dict(zip(inputs,v)))
        assert len([s for s in labels if '_carry_' in s])==4
        assert expected(vectors[labels.index('positive_carry_assert_all_digits')])['cout']==1
        assert expected(vectors[labels.index('negative_carry_assert_all_digits')])['cout']==-1
        assert expected(vectors[labels.index('positive_carry_release_all_digits')])['cout']==0


def test_corrupted_or_missing_artifacts_invalidate_cache(tmp_path):
    path=tmp_path/'evidence.json';path.write_text('{}')
    row={'configuration_sha256':'abc','state':'complete','artifacts_sha256':{str(path):file_hash(path)}}
    assert _valid_cache(row,'abc')
    assert not _valid_cache(row,'changed')
    path.write_text('corrupted')
    assert not _valid_cache(row,'abc')
    path.unlink()
    assert not _valid_cache(row,'abc')


def test_figures_preserve_failed_load_and_adopted_marker():
    figure=sizing_figure(load_grid('INV'))
    assert any(t.marker.symbol=='star' for t in figure.data)
    row={'load_f':1e-12,'max_error_v':2,'max_settling_s':{'sum':100e-9},
         'unsettled':1,'passed':False,'failures':[{'output':'sum','settling_s':None}]}
    result={'rows':[row], 'conditions':{'hold_s':500e-9},'outputs':['sum'],
            'boundary_found':False,'boundary':{}}
    figure=load_sweep_figure(result)
    assert figure.data[0].y[0] is None
    assert figure.data[1].y[0]==500
