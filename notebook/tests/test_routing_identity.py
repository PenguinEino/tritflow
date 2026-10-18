"""Bind readable run labels to native geometry, including fresh nondefault seeds."""

from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'notebook'))
from routing_identity import archive_routing, routing_files, routing_label
from editorial import context, render
from paper_evidence import load_paper


def test_paper_and_archive_realizations_are_distinct_portable_measurements():
    paper = load_paper(ROOT)
    adder,full = paper['paper_pnr']['routing'],paper['paper_post']['routing']
    assert (adder['seed'],full['seed']) == (7,19)
    archive = archive_routing(ROOT/'notebook/assets/four_designs.zip')
    assert all(r['seed'] == 0 for r in archive.values())
    assert adder['gds_sha256'] != archive['adder4']['gds_sha256']
    assert full['gds_sha256'] != archive['full_add']['gds_sha256']
    for route in (adder,full):
        for suffix,key in (('pnr.json','pnr_sha256'),('gds','gds_sha256')):
            assert paper['native_sha256'][f"build/{route['top']}/{route['top']}.{suffix}"] == route[key]
    values = context(ROOT)
    assert values['paper_adder.run_id'] == 'paper/adder4 · seed 7'
    assert values['archive.adder_run_id'] == 'four-design/adder4 · seed 0'
    assert values['sizing.predicted_shift_mv'] > 0 > values['sizing.spice_shift_mv']
    assert values['sizing.selected_current_ua'] < values['sizing.adopted_current_ua']
    assert values['sizing.selected_error_mv'] > values['sizing.adopted_error_mv']
    text = (ROOT/'notebook/narrative/B_evidence.md').read_text()
    routing_table = text.split('Use the routing realization below',1)[1].split('For each analog experiment',1)[0]
    assert '{archive.' not in render(routing_table,values)


def test_archive_rejects_changed_native_pnr_before_showing_seed_label(tmp_path):
    source = ROOT/'notebook/assets/four_designs.zip'
    altered = tmp_path/'changed.zip'
    with zipfile.ZipFile(source) as original,zipfile.ZipFile(altered,'w') as target:
        for name in original.namelist():
            raw = original.read(name)
            if name == 'adder4/adder4.pnr.json':
                data = json.loads(raw);data['seed'] += 1;raw = json.dumps(data).encode()
            target.writestr(name,raw)
    with pytest.raises(ValueError,match='routing artifact hash mismatch'):
        archive_routing(altered)


def test_fresh_nondefault_seed_label_comes_from_actual_pnr_and_gds(tmp_path):
    from tritflow import flow
    from experiments import complete_design, assert_experiment
    net = flow.load(ROOT/'examples/minmax.tv','minmax').synthesize()
    vectors = list(product((-1,0,1),repeat=2))
    result = complete_design(net,tmp_path,vectors,lambda v:{'lo':min(v),'hi':max(v)},
                             seed=23,initialize_internal=True)
    assert_experiment(result)
    route = result['routing']
    assert route == routing_files(tmp_path/'minmax.pnr.json',tmp_path/'minmax.gds','notebook')
    assert route['seed'] == 23
    assert route['gds_sha256'] == sha256((tmp_path/'minmax.gds').read_bytes()).hexdigest()
    assert 'seed 23' in routing_label(route,state='fresh',digest=True)
    assert '(fresh)' in routing_label(route,state='fresh')
