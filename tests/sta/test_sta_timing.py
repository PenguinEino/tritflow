"""Numerical interpolation, graph semantics, sensitization and publication safety."""
from itertools import product
import json
from pathlib import Path

import pytest

from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.sta import analyze, ModelDomainError, TimingLibrary
from tritflow.sta.logic import Diagram, function
from tritflow.sta.plot import validation_figure
from tritflow.sta.validate import fingerprint, statistics
from tritflow.synth.simulate import CELL_INPUTS, ordered_instances


def net(instances, inputs=('a','b'), outputs=('y',)):
    return GateNetlist('test', [Port(n,'input') for n in inputs]+[Port(n,'output') for n in outputs], instances)


def evaluate(n, values):
    result = dict(values)
    for inst in ordered_instances(n):
        result[inst.pins['Y']] = function(inst.cell, [result[inst.pins[p]] for p in CELL_INPUTS[inst.cell]])
    return result


def brute(n, models, loads):
    """Independent exhaustive oracle for the additive settled-endpoint model."""
    names = [p.name for p in n.ports if p.dir=='input']
    states = list(product((-1,0,1), repeat=len(names)))
    maxima = {p.name:{} for p in n.ports if p.dir=='output'}
    for first, last in product(states, repeat=2):
        before, after = evaluate(n,dict(zip(names,first))), evaluate(n,dict(zip(names,last)))
        arrival = dict.fromkeys(names,0.)
        for inst in ordered_instances(n):
            pins = CELL_INPUTS[inst.cell]
            start = {p:before[inst.pins[p]] for p in pins}
            end = {p:after[inst.pins[p]] for p in pins}
            changed = [p for p in pins if start[p]!=end[p]]
            if not changed:
                arrival[inst.pins['Y']] = 0.; continue
            arc = next(a for a in models[inst.cell].arcs if a['from_inputs']==start and a['to_inputs']==end)
            delay = models[inst.cell].sample(arc, loads[inst.pins['Y']]['total_f'])
            arrival[inst.pins['Y']] = max(arrival[inst.pins[p]] for p in changed)+delay
        for name in maxima:
            pair = f'{before[name]}->{after[name]}'
            # Constant endpoints with no event in their fanin have no arrival.
            if arrival[name]>0 or before[name]!=after[name]:
                maxima[name][pair] = max(maxima[name].get(pair,0),arrival[name])
    return maxima


def test_bilinear_physical_axes_and_failed_points(library):
    model = library['INV'];arc=model.arcs[0]
    midpoint = model.sample(arc,(1e-15+2e-12)/2,(1e-9+100e-9)/2)
    assert midpoint == pytest.approx(arc['settling_s'][0][0]+3e-9)
    with pytest.raises(ModelDomainError): model.sample(arc,3e-12)
    assert model.sample(arc,3e-12,load_policy='linear') > model.sample(arc,2e-12)
    with pytest.raises(ModelDomainError): model.sample(arc,5e-12,load_policy='linear')
    with pytest.raises(ModelDomainError): model.sample(arc,1e-14,1e-10,load_policy='linear')
    arc['settling_s'][1][1]=None
    with pytest.raises(ModelDomainError): model.sample(arc,1e-12,50e-9)
    # Exact valid nodes do not depend on failed zero-weight neighbors.
    assert model.sample(arc,1e-15,1e-9)==arc['settling_s'][0][0]


def test_reconvergence_matches_every_exhaustive_transition(library):
    n=net([Instance('i','INV',{'A':'a','Y':'na'}),
           Instance('n','NANY',{'A':'na','B':'b','Y':'m'}),
           Instance('q','NOR',{'A':'a','B':'m','Y':'y'})])
    report=analyze(n,library=library,load_policy='error')
    expected=brute(n,library,report.loads)
    assert report.transition_arrival['y']==pytest.approx(expected['y'])
    assert report.arrival['y']==pytest.approx(max(expected['y'].values()))
    pattern=report.sensitizing_pattern
    before,after=evaluate(n,pattern['before']),evaluate(n,pattern['after'])
    for stage in report.critical_path:
        inst=next(i for i in n.instances if i.name==stage.instance)
        assert stage.from_inputs=={p:before[inst.pins[p]] for p in CELL_INPUTS[inst.cell]}
        assert stage.to_inputs=={p:after[inst.pins[p]] for p in CELL_INPUTS[inst.cell]}
        assert tuple(stage.output_transition)==(before[stage.output_net],after[stage.output_net])


def test_unsensitizable_level_transition_and_tied_inputs(library):
    n=net([Instance('i','INV',{'A':'a','Y':'na'}),
           Instance('g','NANY',{'A':'a','B':'na','Y':'y'})], inputs=('a',))
    report=analyze(n,library=library)
    assert set(report.transition_arrival['y'])=={'0->0'}
    tied=net([Instance('g','NANY',{'A':'a','B':'a','Y':'y'})],inputs=('a',))
    r=analyze(tied,library=library)
    assert r.arrival['y']>0
    assert all(s.from_inputs['A']==s.from_inputs['B'] and s.to_inputs['A']==s.to_inputs['B'] for s in r.critical_path)
    assert r.transition_arrival['y']==pytest.approx(brute(tied,library,r.loads)['y'])


def test_vector_filter_constants_direct_ports_and_domains(library):
    n=net([Instance('t','TIEZ',{'Y':'z'}),Instance('g','NANY',{'A':'a','B':'z','Y':'y'})],inputs=('a',))
    pairs=[({'a':0},{'a':1})]
    r=analyze(n,library=library,vector_pairs=pairs)
    assert set(r.transition_arrival['y'])=={'0->-1'}
    assert r.sensitizing_pattern=={'before':{'a':0},'after':{'a':1}}
    direct=GateNetlist('wire',[Port('a','input'),Port('y','output')],[Instance('t','TIEZ',{'Y':'y'})])
    assert analyze(direct,library=library).arrival['y']==0
    with pytest.raises(ValueError,match='every primary input'): analyze(n,library=library,vector_pairs=[({}, {})])
    with pytest.raises(ValueError,match='nonnegative'): analyze(n,library=library,output_load_f=-1)
    with pytest.raises(ValueError,match='unknown logical'): analyze(n,library=library,wire_caps={'nonexistent':1e-14})
    with pytest.raises(RuntimeError,match='budget'): analyze(n,library=library,max_nodes=3)


def test_fanout_and_merged_route_load_and_html(library,tmp_path):
    n=net([Instance('i','INV',{'A':'a','Y':'m'}),Instance('g','NANY',{'A':'m','B':'m','Y':'y'})],inputs=('a',))
    pnr={'wires':[{'net':'m','layer':'M1','width':2,'points':[[0,0],[10,0]]}],'pins':[]}
    r=analyze(n,pnr,library=library)
    assert r.loads['m']['fanout_f']==pytest.approx(20e-15)
    assert r.loads['m']['wire_f']>0
    assert r.loads['y']['external_f']==1e-14
    assert r.loads['m']['total_f']==pytest.approx(r.loads['m']['wire_f']+20e-15)
    text=r.to_html(tmp_path/'report.html');assert 'Sensitizing' in text and 'plotly' in text
    r.save(tmp_path/'report.json');assert json.loads((tmp_path/'report.json').read_text())['top']=='test'


def test_source_hash_guard(library):
    path=library.root/'INV/INV.ext.spice';path.write_text('* changed\n')
    with pytest.raises(ValueError,match='Stale'):TimingLibrary(['INV'],library.root)


def test_content_fingerprint_and_statistics(tmp_path):
    (tmp_path/'results/sta').mkdir(parents=True)
    data=tmp_path/'results/x.json';data.write_text('{}')
    first=fingerprint(tmp_path)
    (tmp_path/'results/sta/validation.json').write_text('{}')
    assert fingerprint(tmp_path)==first
    data.write_text('[]');assert fingerprint(tmp_path)!=first
    rows=[{'simulated_s':10e-9,'predicted_s':12e-9,'tested_predicted_s':8e-9}]
    assert statistics(rows,'predicted_s')['max_signed_percent_error']==pytest.approx(20)
    assert statistics(rows,'tested_predicted_s')['underprediction_count']==1
    figure=validation_figure({'designs':[{'outputs':[dict(rows[0],design='a',output='y')]}]})
    assert len(figure.data)==5


def test_real_published_cells_and_six_trit_adder():
    from tritflow import ROOT
    path=ROOT/'build/adder_scaling/adder6/adder6.json'
    if not path.exists(): pytest.skip('Integration build is not present')
    report=analyze(path,library=TimingLibrary(['INV','NANY']))
    n=GateNetlist.load(path)
    before=evaluate(n,report.sensitizing_pattern['before']);after=evaluate(n,report.sensitizing_pattern['after'])
    assert report.arrival['cout']>0 and len(report.critical_path)>10
    for stage in report.critical_path:
        assert (before[stage.input_net],after[stage.input_net])==stage.input_transition
        assert (before[stage.output_net],after[stage.output_net])==stage.output_transition
    assert report.statistics['all_endpoint_pairs']


def test_active_publication_retry_reuses_only_unchanged_designs(monkeypatch,tmp_path):
    """Unrelated corner publications trigger refresh without repeating graph work."""
    import importlib
    from types import SimpleNamespace
    from tritflow import ROOT
    producer=importlib.import_module('tritflow.sta.validate')
    monkeypatch.setattr(producer,'DESIGNS',[('example','x',ROOT/'build/x')])
    monkeypatch.setattr(producer,'TimingLibrary',lambda *a:SimpleNamespace(generation='test'))
    monkeypatch.setattr(producer,'_read',lambda p:{})
    monkeypatch.setattr(producer,'_DESIGN_CACHE',{})
    calls=[]
    def design(*args):
        calls.append(True)
        return {'qualified_current':True,'outputs':[]},{}
    monkeypatch.setattr(producer,'_validate_design',design)
    first={'results/corners/summary.json':'old','build/x/postlayout/summary.json':'stable'}
    second=first|{'results/corners/summary.json':'new'}
    snapshots=iter([first,second,second,second])
    monkeypatch.setattr(producer,'fingerprint',lambda:next(snapshots))
    result=producer.validate(output_dir=tmp_path)
    assert result['attempts']==2 and result['source_sha256']==second
    assert len(calls)==1
    # A changed consumed physical summary must invalidate that cached design.
    third=second|{'build/x/postlayout/summary.json':'changed'}
    monkeypatch.setattr(producer,'fingerprint',lambda:third)
    producer.validate(output_dir=tmp_path)
    assert len(calls)==2


def test_running_sim_is_not_qualified(tmp_path):
    import importlib
    producer=importlib.import_module('tritflow.sta.validate')
    folder=tmp_path/'postlayout';folder.mkdir()
    (folder/'summary.json').write_text('{"state":"running","passed":false}')
    with pytest.raises(RuntimeError,match='incomplete'):
        producer._validate_design('example','x',tmp_path,None,{})


def test_pinned_archive_matches_git_reference_by_consumed_bytes():
    from tritflow.sta.validate import PIN,pinned_public_pdk
    reference={'qualified_commit':PIN,'checkout_commit':PIN,
        'consumed_sha256':{'libs.tech/klayout/tech/lvs/01_Extract.lvs':'deck','libs.tech/spice/models/ip62_models':'model'}}
    archive={**reference,'checkout_commit':None}
    assert pinned_public_pdk(reference,reference)
    assert pinned_public_pdk(archive,reference)
    assert not pinned_public_pdk({**archive,'consumed_sha256':{'libs.tech/klayout/tech/lvs/01_Extract.lvs':'dev'}},reference)
    assert not pinned_public_pdk({**archive,'checkout_commit':'dev'},reference)
    assert not pinned_public_pdk({'qualified_commit':PIN},reference)
