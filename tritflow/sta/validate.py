"""Reproduce STA/SPICE comparisons without running or modifying SIM producers.

Publication uses content fingerprints before/after reading. A changed result,
table or consumed physical artifact causes a retry. Historical/stale evidence
can be compared, but is explicitly excluded from current qualification.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from tritflow import ROOT
from tritflow.extract import reference_net_map
from tritflow.netlist import GateNetlist
from .analyze import analyze
from .model import TimingLibrary

PIN = "5d963db9d44e192d37a0489c208bfccf2e2f690c"
DESIGNS = [*(('scaling', f'adder{n}', ROOT/'build/adder_scaling'/f'adder{n}') for n in range(1,7)),
           *(('example', name, ROOT/'build'/name) for name in ('adder4','full_add','mac1','mul1'))]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


_IMPORTED_CODE_SHA256 = {p.name: _sha(p) for p in Path(__file__).parent.glob('*.py')}


def fingerprint(root=ROOT):
    """Track all foreign results, current cell tables and consumed physical evidence."""
    root = Path(root)
    paths = [p for p in (root/'results').rglob('*') if p.is_file()
             and 'sta' not in p.relative_to(root/'results').parts
             and not p.name.endswith(('.tmp', '.lock'))]
    paths += list((root/'cells/out').glob('*/*.timing.json'))
    paths += list((root/'cells/out').glob('*/*.ext.spice'))
    paths += [root/'cells/out/generation.json']
    for _, name, directory in DESIGNS:
        directory = root/directory.relative_to(ROOT)
        out = directory/'postlayout'
        paths += [out/p for p in ('summary.json','capacitance.json','vectors.json','lvs.json','post/measurements.json')]
        paths += list((out/'inputs').glob('*.json'))
        paths += list((out/'lvs').glob('*.lvsdb'))
        paths += list((out/'lvs').glob('reference.spice'))
        paths += [directory/f'{name}.json', directory/f'{name}.pnr.json']
    return {str(p.relative_to(root)): _sha(p) if p.exists() else None for p in sorted(set(paths))}


def statistics(rows, field):
    """Empirical signed/absolute errors only; never a statistical confidence bound."""
    usable = [r for r in rows if r.get('simulated_s') is not None and r['simulated_s'] > 0]
    if not usable: return {'count': 0}
    delta = np.array([r[field]-r['simulated_s'] for r in usable])
    relative = np.array([(r[field]/r['simulated_s']-1)*100 for r in usable])
    return {'count': len(usable), 'mean_error_s': float(np.mean(delta)),
            'mae_s': float(np.mean(abs(delta))), 'rmse_s': float(np.sqrt(np.mean(delta**2))),
            'max_absolute_error_s': float(max(abs(delta))),
            'mean_absolute_percent_error': float(np.mean(abs(relative))),
            'min_signed_percent_error': float(min(relative)), 'max_signed_percent_error': float(max(relative)),
            'underprediction_count': int(sum(delta < 0)),
            'interpretation': 'Observed extrema on this nominal finite vector set; not guaranteed error bounds.'}


def _read(path):
    return json.loads(Path(path).read_text())


def _validate_design(group, name, directory, models, scaling):
    out = directory/'postlayout'
    summary = _read(out/'summary.json')
    if summary.get('state') != 'complete' or 'settling' not in summary:
        raise RuntimeError(f'SIM publication is incomplete: {out}/summary.json')
    netfile = out/'inputs'/f'{summary["top"]}.json'
    net = GateNetlist.load(netfile)
    caps = _read(out/'capacitance.json')
    lvs = _read(out/'lvs.json')
    mapping = reference_net_map(lvs['report'], net.top)
    missing = net.nets()-mapping.keys()
    if missing: raise ValueError(f'LVS does not map logical nets: {sorted(missing)}')
    logical_caps = {n: caps['nets'][mapping[n]]['capacitance_f'] for n in net.nets()}
    measured = _read(out/'post/measurements.json')
    plan = _read(out/'vectors.json')
    pairs = [(dict(zip(plan['input_order'], row['previous_trits'])),
              dict(zip(plan['input_order'], row['input_trits']))) for row in measured['rows'][1:]
             if row['previous_trits'] is not None]
    kwargs = dict(library=models, wire_caps=logical_caps,
                  output_load_f=summary['output_load_f'], input_transition_s=1e-9)
    predicted = analyze(net, **kwargs)
    tested = analyze(net, vector_pairs=pairs, **kwargs)
    # A report's historical inputs_unchanged flag does not establish freshness now.
    stale = [p for p,h in summary.get('input_sha256', {}).items() if not Path(p).is_file() or _sha(p) != h]
    pdk = summary.get('pdk_provenance', {})
    pinned = pdk.get('qualified_commit') == PIN and pdk.get('checkout_commit') == PIN
    if pdk.get('consumed_sha256', {}).get('libs.tech/klayout/tech/lvs/01_Extract.lvs') is None:
        pinned = False
    published = None
    if group == 'scaling':
        published = next((r for r in scaling.get('rows', []) if r['n'] == int(name[5:])), None)
    outputs = []
    for pin, value in predicted.arrival.items():
        observed = measured['max_settling_s'][pin]
        expected = summary['settling']['post_max_settling_s'][pin]
        if observed != expected: raise RuntimeError(f'SIM summary/measurement mismatch: {name}/{pin}')
        if published and published.get('settling', {}).get('post_max_settling_s', {}).get(pin) != observed:
            stale.append('results/adder_scaling.json does not match physical measurement snapshot')
        outputs.append({'design': f'{group}/{name}', 'output': pin,
            'predicted_s': value, 'tested_predicted_s': tested.arrival[pin], 'simulated_s': observed,
            'error_s': None if observed is None else value-observed,
            'error_percent': None if not observed else 100*(value/observed-1),
            'tested_error_percent': None if not observed else 100*(tested.arrival[pin]/observed-1)})
    current = bool(summary.get('passed') and measured.get('passed') and pinned and not stale)
    if group == 'scaling' and not published: current = False
    report_name = f'{group}_{name}'
    record = {'group': group, 'design': name, 'outputs': outputs, 'pinned_pdk': pinned,
        'sim_passed': summary.get('passed'), 'qualified_current': current,
        'stale_inputs': sorted(set(stale)), 'vector_count': len(measured['rows']),
        'coverage': plan.get('coverage'), 'output_load_f': summary['output_load_f'],
        'sample_step_s': measured['sample_step_s'],
        'all_pairs_report': f'{report_name}.timing.json', 'tested_pairs_report': f'{report_name}.tested.timing.json',
        'all_pairs_runtime_s': predicted.statistics['runtime_s'],
        'tested_pairs_runtime_s': tested.statistics['runtime_s'],
        'load_extension_count': len(predicted.warnings),
        'wire_scope': caps.get('scope'),
        'electrical_scope': 'Maximum biased device input C plus exact same LVS-mapped top-net metal C used by SIM; fixed full 1 ns ramp per cell.'}
    return record, {f'{report_name}.timing.json': predicted.to_dict(),
                    f'{report_name}.tested.timing.json': tested.to_dict()}


def validate(*, output_dir=None, retries=3):
    """Refresh all ten designs, retrying if the shared publication changes."""
    output = Path(output_dir or ROOT/'results/sta')
    output.mkdir(parents=True, exist_ok=True)
    for attempt in range(retries):
        if _IMPORTED_CODE_SHA256 != {p.name: _sha(p) for p in Path(__file__).parent.glob('*.py')}:
            raise RuntimeError('STA source changed after import; restart validation to execute current code')
        before = fingerprint()
        models = TimingLibrary(('INV','NAND','NOR','NANY','BUF','TIEP','TIEZ','TIEN'))
        scaling = _read(ROOT/'results/adder_scaling.json')
        records, reports = [], {}
        for group, name, directory in DESIGNS:
            print(f'STA: {group}/{name}', flush=True)
            try:
                record, artifacts = _validate_design(group, name, directory, models, scaling)
                records.append(record); reports.update(artifacts)
            except (OSError, ValueError, RuntimeError, KeyError) as error:
                records.append({'group': group, 'design': name, 'qualified_current': False,
                                'error': f'{type(error).__name__}: {error}', 'outputs': []})
        after = fingerprint()
        if _IMPORTED_CODE_SHA256 != {p.name: _sha(p) for p in Path(__file__).parent.glob('*.py')}:
            raise RuntimeError('STA source changed during validation; restart the producer')
        if before != after:
            print('STA: publication changed during validation; retrying', flush=True)
            continue
        rows = [r for d in records for r in d['outputs']]
        current = [r for d in records if d['qualified_current'] for r in d['outputs']]
        result = {'schema_version': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
            'complete': len(records) == 10 and all(d['outputs'] for d in records),
            'qualified_current': len(records) == 10 and all(d['qualified_current'] for d in records),
            'accuracy_passed': None,
            'scope': 'Nominal analytical estimates checked against finite post-layout SPICE sequences; no accuracy acceptance threshold or certified error bound is claimed.',
            'limitations': ['Full graph considers all settled input endpoint pairs; SPICE maxima cover only consecutive documented vectors.',
                'Tested-pair comparison removes endpoint coverage differences, but does not reproduce analog slew/skew/history or propagated glitches.',
                'Maximum biased AC input C and additive per-cell settling can be strongly pessimistic; inspect measured error before use.',
                'Wire coefficients are assumed, not calibrated PEX; signal/poly RC, PVT and package are outside the model.',
                'Explicit bounded load extensions are uncharacterized estimates, not measured table points.'],
            'designs': records, 'cell_generation': models.generation,
            'statistics': {'all_endpoint_pairs': statistics(rows, 'predicted_s'),
                           'sim_endpoint_pairs': statistics(rows, 'tested_predicted_s'),
                           'current_all_endpoint_pairs': statistics(current, 'predicted_s'),
                           'current_sim_endpoint_pairs': statistics(current, 'tested_predicted_s')},
            'source_sha256': before,
            'sta_code_sha256': _IMPORTED_CODE_SHA256,
            'stable_snapshot': True, 'attempts': attempt+1}
        for name, data in reports.items(): _save(output/name, data)
        _save(output/'validation.json', result)
        from .plot import validation_figure
        validation_figure(result).write_html(output/'validation.html', include_plotlyjs='cdn')
        return result
    raise RuntimeError('Shared results changed on every validation attempt; rerun when a publication finishes')


def _save(path, data):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch-seconds', type=float, default=0,
                        help='After initial validation, revalidate changed results for this many seconds')
    args = parser.parse_args()
    validate()
    deadline = time.monotonic()+args.watch_seconds
    previous = fingerprint()
    while time.monotonic() < deadline:
        time.sleep(min(5., max(0., deadline-time.monotonic())))
        current = fingerprint()
        if current != previous:
            validate()
            previous = fingerprint()


if __name__ == '__main__': main()
