"""Arithmetic coverage and cache validation independent of expensive full PNR."""
import json
from pathlib import Path

import pytest

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


@pytest.mark.parametrize('loads_pf',[
    [.01,1,12.8125,12.96875,30],
    [2,1,.1],
])
def test_load_sweep_log_range_stays_within_measured_loads(loads_pf):
    rows=[{'load_f':load*1e-12,'max_error_v':.1,'max_settling_s':{'sum':100e-9},
           'passed':True,'failures':[]} for load in loads_pf]
    last_pass,first_fail=sorted(loads_pf)[-2:]
    result={'rows':rows,'conditions':{'hold_s':500e-9},'outputs':['sum'],
            'boundary_found':True,'boundary':{'last_pass_f':last_pass*1e-12,'first_fail_f':first_fail*1e-12}}
    figure=load_sweep_figure(result)
    assert figure.layout.xaxis.type=='log'
    assert figure.layout.xaxis.autorange is False
    # Plotly log ranges are exponents. The old boundary annotation stretched
    # autorange to ~10**13 pF, despite the largest measured load being 30 pF.
    lower,upper=(10**bound for bound in figure.layout.xaxis.range)
    assert lower==pytest.approx(min(loads_pf))
    assert upper==pytest.approx(max(loads_pf))
    boundary=next(a for a in figure.layout.annotations if a.text.startswith('Measured PASS'))
    window=next(a for a in figure.layout.annotations if a.text.endswith('ns window'))
    assert boundary.xref==boundary.yref=='paper' and boundary.y>1
    assert window.xref=='x domain' and window.yref=='y'
    assert window.yanchor=='top'  # window text below the line; boundary above plot


def test_imported_code_provenance_is_frozen_but_model_inputs_are_live(monkeypatch):
    from tritflow.sim import scaling
    before=scaling.experiment_sources()
    code_path=str(Path(scaling.__file__))
    model_path=next(p for p in before if '/libs.tech/spice/models/' in p)
    original=scaling.file_hash
    def changed(path):
        if str(path) in (code_path,model_path): return 'changed-on-disk'
        return original(path)
    monkeypatch.setattr(scaling,'file_hash',changed)
    after=scaling.experiment_sources()
    assert after[code_path]==before[code_path]  # running modules do not reload
    assert after[model_path]=='changed-on-disk'  # solver reads the current models


def test_fits_recover_delay_per_trit_and_effective_power_per_cell():
    import pytest
    from tritflow.sim.scaling import fit_scaling
    from tritflow.viz.scaling import scaling_fit_figure
    rows=[]
    for n in [1,2,3]:
        rows.append({'n':n,'cell_count':16*n,'state':'complete','passed':True,
                     'carry':{'pre':{'max_settling_s':(5+49*n)*1e-9},
                              'post':{'max_settling_s':(7+50*n)*1e-9}},
                     'static_power_worst_w':.004*16*n+.001})
    # Failed designs are diagnostics, not measured fit points.
    rows.append(dict(rows[-1],n=99,passed=False))
    result={'rows':rows};fits=fit_scaling(result)
    assert fits['widths']==[1,2,3]
    assert fits['carry']['pre']['slope']==pytest.approx(49e-9)
    assert fits['carry']['post']['intercept']==pytest.approx(7e-9)
    assert fits['static_power']['slope']==pytest.approx(.004)
    assert fits['static_power']['intercept']==pytest.approx(.001)
    assert fits['static_power']['r_squared']==pytest.approx(1)
    assert len(scaling_fit_figure(result).data)==6
    assert fit_scaling({'rows':rows[:1]})['carry']['pre'] is None


def test_comparison_reports_concurrent_or_missing_original_runs(tmp_path,monkeypatch):
    from tritflow.sim import scaling
    monkeypatch.setattr(scaling,'ROOT',tmp_path)
    base=tmp_path/'baseline';base.mkdir()
    (base/'adder_scaling.json').write_text('{"rows":[]}')
    (base/'adder4.postlayout.json').write_text('{"passed":true}')
    live=tmp_path/'build/adder4/postlayout';live.mkdir(parents=True)
    (live/'summary.json').write_text('{"passed":false,"state":"running"}')
    result=scaling.compare_phase3({'rows':[]},baseline=base,destination=tmp_path/'comparison.json')
    assert result['original_postlayout_complete'] is False
    assert result['original_postlayout'][0]['state']=='running'
    assert result['original_postlayout'][1]['state']=='unavailable'
