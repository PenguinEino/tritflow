"""Portable source measurements accompanying the integrator's static figures.

The export reads native artifacts once on the publishing machine. Notebook
runtime reads only this small committed record and the committed figure files;
it never opens the author's home directory or an existing build directory.
"""

from hashlib import sha256
import ast
import json
from pathlib import Path


NAMES = ('flow','gates','sizing','cell','synth','pnr','postlayout','scaling')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load_paper(root):
    """Reject changed figure/data inputs before displaying coupled captions."""
    root = Path(root)
    record = json.loads((root/'notebook/assets/paper_evidence.json').read_text())
    for name,expected in record['repository_sha256'].items():
        if digest(root/name) != expected:
            raise RuntimeError(f'Static figure evidence changed: {name}. Rebuild the paper evidence and notebook together.')
    return record


def export(root):
    """Capture current figure measurements; never regenerate or edit figures."""
    import numpy as np
    from tritflow import PDK_ROOT
    from tritflow.sim import dc_transfer
    from tritflow.sim.scaling import load_scaling, fit_scaling
    from experiments import verify_publication_sources

    root = Path(root)
    native = {}
    def read(name):
        native[name] = digest(root/name)
        return json.loads((root/name).read_text())
    net = read('build/adder4/adder4.json')
    report = read('build/adder4/adder4.report.json')
    physical = read('build/adder4/adder4.pnr.json')
    proof = read('build/adder4/adder4.lvs.summary.json')
    assert report['equivalence']['passed'] and proof['matched'] and proof['strict_ports']
    assert physical['checks']['pdk_drc']['clean']
    assert report['total_cells'] == len(net['instances'])
    for suffix in ('gds','drc.lyrdb'):
        p = root/f'build/adder4/adder4.{suffix}'
        if p.is_file(): native[str(p.relative_to(root))] = digest(p)
    import klayout.db as kdb
    layout = kdb.Layout(); layout.read(str(root/'build/adder4/adder4.gds'))
    box = layout.cell(net['top']).dbbox()
    assert np.allclose([box.width(),box.height()],physical['die'])
    summary = read('build/full_add/postlayout/summary.json')
    assert summary['passed'] and summary.get('state') != 'running', 'Full-adder publication is still running'
    pre = read('build/full_add/postlayout/pre/measurements.json')
    post = read('build/full_add/postlayout/post/measurements.json')
    assert pre['passed'] and post['passed']
    k = max(range(1,len(post['rows'])),key=lambda i:post['rows'][i]['outputs']['sum']['settling_s'])
    curve = dc_transfer((root/'cells/out/INV/INV.ext.spice').read_text(),
                        'INV',['A'],['Y'],'A',fixed_trits={},step_v=.02)
    q = curve['data']; i = int(np.argmin(abs(q['v-sweep'])))
    assert abs(q['v-sweep'][i]) < 1e-9
    from tritflow import VDD,VMID,VSS
    supplies = {'VDD':VDD,'VMID':VMID,'VSS':VSS}
    gate_point = {'output_v':float(q['v(y)'][i]),'current_a':abs(float(q['i(vdd)'][i])),
                  'power_w':-sum(v*float(q[f'i({r.lower()})'][i]) for r,v in supplies.items())}
    scale = load_scaling(root/'results/adder_scaling.json')
    for row in scale['rows']: verify_publication_sources(row,root,PDK_ROOT)
    fits = fit_scaling(scale)
    scaling_svg = (root/'figures/out/fig_scaling.svg').read_text()
    assert f"extracted devices: {fits['carry']['pre']['slope']*1e9:.1f} ns/trit" in scaling_svg
    assert f"+ wire C: {fits['carry']['post']['slope']*1e9:.1f} ns/trit" in scaling_svg
    cell_spec = ast.parse((root/'figures/fig_cell.py').read_text())
    row_cells = next(ast.literal_eval(node.value) for node in cell_spec.body
                     if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id == 'ROW' for t in node.targets))
    assert all((root/f'cells/out/{name}/{name}.gds').is_file() for name in row_cells)
    sizing_spec = ast.parse((root/'figures/fig_sizing.py').read_text())
    floor = next(ast.literal_eval(keyword.value) for node in ast.walk(sizing_spec)
                 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id == 'scatter'
                 for keyword in node.keywords if keyword.arg == 'floor_mv')
    static = {}
    for row in scale['rows']:
        source = next(p for p in row['artifacts_sha256'] if p.endswith('/postlayout/static.json'))
        path = root/'build/adder_scaling'/f"adder{row['n']}"/'postlayout/static.json'
        assert digest(path) == row['artifacts_sha256'][source]
        dc = json.loads(path.read_text())
        zero = next(r for r in dc if not any(r['input_trits']))
        static[str(row['n'])] = {'dc':zero,'native_sha256':digest(path)}
    paths = [root/f'figures/out/fig_{name}.{ext}' for name in NAMES for ext in ('png','svg')]
    paths += [root/'results/adder_scaling.json', root/'results/full_add_load_sweep.json',
              root/'notebook/narrative/reference_geometry.json',root/'cells/out/equivalence_report.json',
              root/'cells/template.json',root/'examples/adder.tv',root/'examples/half_add.tv',
              root/'examples/full_add.tv',root/'notebook/setup_pins.json']
    paths += list((root/'cells/out/sizing').glob('*.grid.json'))
    paths += list((root/'cells/out').glob('*/*.char.json'))
    paths += list((root/'figures').glob('*.py'))
    result = {'schema':1,'scope':'Recorded figure inputs; not new physical checks at notebook runtime',
              'repository_sha256':{str(p.relative_to(root)):digest(p) for p in sorted(paths)},
              'native_sha256':native,'paper_net':net,'paper_report':report,
              'paper_pnr':{'die':physical['die'],'checks':physical['checks'],
                           'history':[{'hpwl':physical['history'][i]['hpwl']} for i in (0,-1)]},
              'paper_lvs':{'matched':proof['matched'],'strict_ports':proof['strict_ports']},
              'paper_post':{'states':len({tuple(r['input_trits']) for r in post['rows']}),
                  'hold_s':summary['hold_s'],'load_f':summary['output_load_f'],
                  'pre_sum_s':pre['rows'][k]['outputs']['sum']['settling_s'],
                  'post_sum_s':post['rows'][k]['outputs']['sum']['settling_s']},
              'inv_dc':gate_point,'zero_dc':static,
              'display_settings':{'row_cells':row_cells,'sizing_floor_mv':floor}}
    (root/'notebook/assets/paper_evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    result = export(Path(__file__).resolve().parents[1])
    print('Captured',len(result['repository_sha256']),'committed figure/data inputs')
