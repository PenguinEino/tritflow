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
from .propagation import PropagationLibrary as TimingLibrary

PIN = "5d963db9d44e192d37a0489c208bfccf2e2f690c"
DESIGNS = [*(('scaling', f'adder{n}', ROOT/'build/adder_scaling'/f'adder{n}') for n in range(1,7)),
           *(('example', name, ROOT/'build'/name) for name in ('adder4','full_add','mac1','mul1'))]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


_IMPORTED_CODE_SHA256 = {p.name: _sha(p) for p in Path(__file__).parent.glob('*.py')}
_DESIGN_CACHE = {}


class PublicationChanged(RuntimeError):
    """The shared producer published while validation was reading its evidence."""


def fingerprint(root=ROOT):
    """Track all foreign results, current cell tables and consumed physical evidence."""
    root = Path(root)
    paths = [p for p in (root/'results').rglob('*') if p.is_file()
             and 'sta' not in p.relative_to(root/'results').parts
             and not p.name.endswith(('.tmp', '.lock'))]
    paths += list((root/'cells/out').glob('*/*.timing.json'))
    paths += list((root/'cells/out').glob('*/*.ext.spice'))
    paths += [root/'cells/out/generation.json']
    paths += list((root/'results/sta/propagation/tables').glob('*.propagation.json'))
    for _, name, directory in DESIGNS:
        directory = root/directory.relative_to(ROOT)
        out = directory/'postlayout'
        paths += [out/p for p in ('summary.json','capacitance.json','vectors.json','lvs.json','post/measurements.json')]
        if (out/'summary.json').is_file():
            try:
                paths += [Path(p) for p in _read(out/'summary.json').get('input_sha256', {})]
            except (ValueError, OSError):
                pass  # The changing summary itself still participates in the fingerprint.
        paths += list((out/'inputs').glob('*.json'))
        paths += list((out/'lvs').glob('*.lvsdb'))
        paths += list((out/'lvs').glob('reference.spice'))
        paths += [directory/f'{name}.json', directory/f'{name}.pnr.json']
    def key(path):
        try: return str(path.relative_to(root))
        except ValueError: return str(path)
    return {key(p): _sha(p) if p.exists() else None for p in sorted(set(paths))}


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


def case_coverage(measured, predicted):
    """Check every saved output observation, including unchanged-output hazards.

    This is validation only. Measured values never alter the static envelope.
    Zero-settling observations are counted without inventing a relative error.
    """
    cases=[];missing=[]
    for index,row in enumerate(measured['rows']):
        for pin,value in predicted.items():
            observed=row['outputs'][pin]['settling_s']
            if observed is None:
                missing.append({'row':index,'output':pin});continue
            cases.append({'row':index,'output':pin,'simulated_s':observed,
                'predicted_s':value,'margin_s':value-observed,
                'initial_state':row.get('previous_trits') is None})
    violations=[r for r in cases if r['margin_s']<0]
    return {'case_count':len(cases),'initial_state_case_count':sum(r['initial_state'] for r in cases),
        'transition_case_count':sum(not r['initial_state'] for r in cases),
        'missing_cases':missing,'underprediction_count':len(violations),
        'passed':bool(cases) and not missing and not violations,
        'minimum_margin_s':min((r['margin_s'] for r in cases),default=None),
        'violations':violations,
        'limiting_case':min(cases,key=lambda r:r['margin_s']) if cases else None}


def pessimism(rows):
    """Overestimate relative to each output's measured sequence maximum."""
    usable=[r for r in rows if r.get('simulated_s',0) and r['simulated_s']>0]
    if not usable:return {'count':0}
    factors=[r['predicted_s']/r['simulated_s'] for r in usable]
    return {'count':len(usable),'minimum_factor':min(factors),'maximum_factor':max(factors),
        'mean_factor':float(np.mean(factors)),'median_factor':float(np.median(factors)),
        'minimum_margin_s':min(r['predicted_s']-r['simulated_s'] for r in usable),
        'maximum_margin_s':max(r['predicted_s']-r['simulated_s'] for r in usable),
        'interpretation':'Static envelope / measured maximum, not matched-transition accuracy.'}


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
    endpoint = analyze(net,global_mode='endpoint',**kwargs)
    from .envelope import analyze_envelope
    relaxed_fixed=analyze_envelope(net,fixed_ramp=True,include_recovery=False,**kwargs)
    without_recovery=analyze_envelope(net,include_recovery=False,**kwargs)
    tested = analyze(net, vector_pairs=pairs, **kwargs)
    fixed = analyze(net, vector_pairs=pairs, propagate_slew=False, **kwargs)
    block = analyze(net,vector_pairs=pairs,ordered_events=False,**kwargs)
    baseline_path=ROOT/'results/sta/phase1/validation.json'
    baseline=_read(baseline_path) if baseline_path.exists() else {'designs':[]}
    legacy={r['output']:r for d in baseline['designs'] if d['group']==group and d['design']==name for r in d['outputs']}
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
            'fixed_ramp_endpoint_s':endpoint.arrival[pin],
            'fixed_ramp_class_envelope_s':relaxed_fixed.arrival[pin],
            'ramp_envelope_without_recovery_s':without_recovery.arrival[pin],
            'fixed_ramp_midpoint_s':fixed.arrival[pin],
            'synchronous_block_midpoint_s':block.arrival[pin],
            'legacy_tested_s':legacy.get(pin,{}).get('tested_predicted_s'),
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
        'load_extension_count': sum('outside' in w for w in predicted.warnings),
        'worst_case_coverage':case_coverage(measured,predicted.arrival),
        'envelope_domain':{k:predicted.statistics[k] for k in
            ('slew_domain_closed','slew_domain_violations','load_in_measured_domain')},
        'event_diagnostics':tested.statistics,
        'wire_scope': caps.get('scope'),
        'electrical_scope': 'Independent local-class/ramp envelope with propagated recovery guard; matched-pattern midpoint events retain propagated slew. Same maximum biased device C and top-net metal C.'}
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
                prefix = str(directory.relative_to(ROOT))+'/'
                consumed = {p:h for p,h in before.items() if p.startswith((prefix, 'cells/', '/', 'results/sta/propagation/tables/'))
                            or (group == 'scaling' and p == 'results/adder_scaling.json')}
                cache_key = hashlib.sha256(json.dumps(consumed, sort_keys=True).encode()).hexdigest()
                key = group, name
                cached = _DESIGN_CACHE.get(key)
                if cached and cached[0] == cache_key:
                    record, artifacts = cached[1:]
                else:
                    record, artifacts = _validate_design(group, name, directory, models, scaling)
                    _DESIGN_CACHE[key] = cache_key, record, artifacts
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
        accurate=[r for r in rows if r.get('tested_error_percent') is not None and abs(r['tested_error_percent'])<=20]
        result = {'schema_version': 3, 'created_utc': datetime.now(timezone.utc).isoformat(),
            'complete': len(records) == 10 and all(d['outputs'] for d in records),
            'qualified_current': len(records) == 10 and all(d['qualified_current'] for d in records),
            'accuracy_passed':len(rows)==39 and len(accurate)==39,
            'accuracy_target_percent':20.,'outputs_within_target':len(accurate),
            'accuracy_claim_field':'tested_predicted_s',
            'worst_case_conservative':len(records)==10 and all(d.get('worst_case_coverage',{}).get('passed',False) for d in records),
            'worst_case_validation':{
                'scope':'Every saved nominal output observation, including initial states and stable-endpoint glitches.',
                'case_count':sum(d.get('worst_case_coverage',{}).get('case_count',0) for d in records),
                'transition_case_count':sum(d.get('worst_case_coverage',{}).get('transition_case_count',0) for d in records),
                'underprediction_count':sum(d.get('worst_case_coverage',{}).get('underprediction_count',0) for d in records),
                'pessimism_vs_output_maxima':pessimism(rows),
                'certified_analog_bound':False,
                'interpretation':'Conservative on every saved nominal case; not certified for untested waveforms or PVT.',
                'all_slew_domains_closed':all(d.get('envelope_domain',{}).get('slew_domain_closed',False) for d in records)},
            'scope': 'Conservative measured-domain envelope validated against every nominal SPICE case; matched-event timing is the separate ±20% accuracy claim.',
            'outside_accuracy_target':[{'design':r['design'],'output':r['output'],'error_percent':r['tested_error_percent']}
                for r in rows if r.get('tested_error_percent') is not None and abs(r['tested_error_percent'])>20],
            'limitations': ['Conservatism is established against this complete saved nominal dataset; the characterized scalar envelope is not a certified arbitrary-waveform or PVT bound.',
                'Independent local-class/ramp maxima and recovery clocks admit unrealizable combinations; their pessimism is reported separately from matched accuracy.',
                'All-class output slew may exceed the measured input-ramp axis; non-closed domains are reported without silently clipping or claiming analog coverage.',
                'Tested-pair comparison removes endpoint coverage differences, but does not reproduce analog slew/skew/history or propagated glitches.',
                'Slew becomes an equivalent linear ramp. Ordered ideal trit events propagate logical pulses, but partial-voltage pulses and analog hazards on unchanged outputs lack a waveform model.',
                'Wire coefficients are assumed, not calibrated PEX; signal/poly RC, PVT and package are outside the model.',
                'Explicit bounded load extensions are uncharacterized estimates, not measured table points.'],
            'designs': records, 'cell_generation': models.generation,
            'statistics': {'conservative_envelope':statistics(rows,'predicted_s'),
                           'fixed_ramp_endpoint':statistics(rows,'fixed_ramp_endpoint_s'),
                           'fixed_ramp_class_envelope':statistics(rows,'fixed_ramp_class_envelope_s'),
                           'ramp_envelope_without_recovery':statistics(rows,'ramp_envelope_without_recovery_s'),
                           'all_endpoint_pairs': statistics(rows, 'predicted_s'),
                           'sim_endpoint_pairs': statistics(rows, 'tested_predicted_s'),
                           'fixed_ramp_midpoint':statistics(rows,'fixed_ramp_midpoint_s'),
                           'synchronous_block_midpoint':statistics(rows,'synchronous_block_midpoint_s'),
                           'current_all_endpoint_pairs': statistics(current, 'predicted_s'),
                           'current_sim_endpoint_pairs': statistics(current, 'tested_predicted_s')},
            'source_sha256': before,
            'sta_code_sha256': _IMPORTED_CODE_SHA256,
            'stable_snapshot': True, 'attempts': attempt+1}
        for name, data in reports.items(): _save(output/name, data)
        _save(output/'validation.json', result)
        from .plot import validation_figure,pessimism_figure
        validation_figure(result).write_html(output/'validation.html', include_plotlyjs='cdn')
        pessimism_figure(result).write_html(output/'pessimism.html',include_plotlyjs='cdn')
        return result
    raise PublicationChanged('Shared results changed on every validation attempt; retry after publication')


def _save(path, data):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch-seconds', type=float, default=0,
                        help='After initial validation, revalidate changed results for this many seconds')
    args = parser.parse_args()
    deadline = time.monotonic()+args.watch_seconds
    previous = None
    while True:
        current = fingerprint()
        if current != previous:
            try:
                result = validate()
                previous = result['source_sha256']
            except PublicationChanged:
                if not args.watch_seconds: raise
                print('STA: publishers are active; watching for the next stable snapshot', flush=True)
        if time.monotonic() >= deadline: break
        time.sleep(min(5., max(0., deadline-time.monotonic())))


if __name__ == '__main__': main()
