"""The reading path teaches measured tradeoffs and closes the editable flow."""

from copy import deepcopy
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'notebook'))
from editorial import context, context_identity, render, TOKEN
from learning import sizing_slider
from predictions import divider
from paper_evidence import load_paper
from tritflow import PDK_ROOT
from tritflow.sim.sizing import load_grid


def test_divider_predicts_branch_strength_and_uses_no_measured_current():
    grid = load_grid('INV')
    dimensions = grid['rows'][grid['adopted_index']]['dimensions']
    baseline = divider(dimensions,PDK_ROOT)
    stronger = deepcopy(dimensions); stronger['MN']['w_um'] *= 2
    resistive = deepcopy(dimensions)
    for name in ('RP','RN'): resistive[name]['l_um'] *= 1.5
    assert divider(stronger,PDK_ROOT)['output_v'] < baseline['output_v']
    assert divider(resistive,PDK_ROOT)['current_a'] < baseline['current_a']
    assert abs(baseline['output_v']) < .5 and baseline['power_w'] > 0
    assert not np.isclose(baseline['current_a'],
                          abs(grid['rows'][grid['adopted_index']]['dc'][1]['rail_current_a']['VDD']),rtol=.01)


def test_caption_identity_tolerates_blas_last_bits_but_rejects_changed_claims():
    values = context(ROOT)
    rounded_same = {k:np.nextafter(v,np.inf) if isinstance(v,float) and v else v for k,v in values.items()}
    assert context_identity(rounded_same) == context_identity(values)
    rounded_same['scaling.wired_slope_ns'] *= 1.01
    assert context_identity(rounded_same) != context_identity(values)


def test_slider_updates_exact_measured_rows_and_keeps_reference_marker():
    grid = load_grid('INV'); figure = sizing_slider(grid,PDK_ROOT)
    steps = figure.layout.sliders[0].steps
    assert len(steps) == len(grid['rows'])
    assert figure.layout.sliders[0].active == grid['adopted_index']
    for step,row in zip(steps,grid['rows'],strict=True):
        updates,layout,indices = step.args
        assert list(indices) == [1,2,5]
        np.testing.assert_array_equal(updates['x'][0],row['transfer']['data']['v-sweep'])
        np.testing.assert_array_equal(updates['y'][0],row['transfer']['data']['v(y)'])
        assert 'Predict first:' in layout['annotations'][-1]['text']
        assert 'SPICE' in layout['annotations'][-1]['text']
    reference = grid['rows'][grid['adopted_index']]
    assert figure.data[4].marker.symbol == 'star'
    assert figure.data[4].x[0] == reference['max_static_current_a']*1e6
    assert 'x' in figure.data[3].marker.symbol  # failed candidates stay visible


def test_static_context_and_embedded_figures_have_no_unresolved_results():
    record = load_paper(ROOT); values = context(ROOT)
    assert record['paper_lvs']['matched'] and record['paper_lvs']['strict_ports']
    for name in ('00_intro.md','01_gates.md','02_sizing.md','03_cells.md','04_hdl.md',
                 '05_synthesis.md','06_pnr.md','07_results.md','09_next.md','A_limits.md','captions.md'):
        assert not TOKEN.search(render((ROOT/'notebook/narrative'/name).read_text(),values))
    document = json.loads((ROOT/'notebook/tritflow_tr1um.ipynb').read_text())
    intro = document['cells'][0]['source']
    assert 'Japan' in intro and 'taped out' in intro and 'mW' in intro and 'Open in Colab' in intro
    assert intro.index('data:image/png;base64,') < intro.index('<summary>Author')
    assert sum(c['source'].count('data:image/png;base64,') for c in document['cells']) == 9
    markdown = '\n'.join(c['source'] for c in document['cells'] if c['cell_type']=='markdown')
    assert '## Appendix A.' in markdown and not TOKEN.search(markdown)
    cells = {c['id']:c for c in document['cells']}
    edit = cells['method-edit']
    assert 'source = """\nmodule minmax(input' in edit['source'] and not edit['metadata'].get('jupyter',{}).get('source_hidden')
    order = [c['id'] for c in document['cells']]
    # The reader's edit is synthesized and checked against the oracle before any physical work.
    assert order.index('method-custom') < order.index('custom_check') < order.index('method-custom_layout') < order.index('custom')
    assert 'custom.schematic(' in cells['method-custom']['source']
    assert 'render_gds(custom_lay.gds_path' in cells['method-custom_layout']['source']
    assert 'oracle(vector)' in cells['custom_check']['source'] and 'custom_result' in cells['custom']['source']
    # Visible method cells stay short; checks live in collapsed form cells.
    for c in document['cells']:
        if c['cell_type'] == 'code' and c['id'].startswith('method-'):
            assert len(c['source'].strip().splitlines()) <= 14, c['id']
        elif c['cell_type'] == 'code':
            assert c['metadata'].get('cellView') == 'form' and c['source'].startswith('#@title'), c['id']


def test_failed_reader_edit_reports_the_arithmetic_counterexample_before_routing(tmp_path):
    from examples.curated import DESIGNS
    from experiments import load_edited
    from tritflow.synth import evaluate_netlist
    import stages
    import pytest
    namespace = {'example':DESIGNS['minmax'],'source':
        'module minmax(input trit a,b,output trit lo,hi); assign lo=a|b; assign hi=a|b; endmodule',
        'BUILD':tmp_path,'load_edited':load_edited,'evaluate_netlist':evaluate_netlist}
    exec('custom_circuit = load_edited(example, source, BUILD/"src"/example.top)\n'
         'custom = custom_circuit.synthesize()\n',namespace)
    before_physical = stages.CUSTOM_CHECK.split('details_html(',1)[0]
    with pytest.raises(AssertionError,match='Independent reference disagreement at.*expected.*HDL.*cells'):
        exec(before_physical,namespace)
