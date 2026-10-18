"""Reproducible ripple-adder scaling through public synthesis and real PNR.

Cached notebook reads are separate from this expensive producer. Every result
uses a documented independent radix-3 oracle and physical extraction/LVS; failed
runs remain failed rows rather than fabricated timing/area points.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from tritflow import ROOT, CELLS_DIR, PDK_ROOT
from tritflow.hdl import load
from tritflow.synth import synthesize, write_artifacts, evaluate_netlist
from tritflow.pnr import Library, PnrResult, place_and_route
from tritflow.extract import reference_net_map
from .characterize import dc_operating_points
from .postlayout import _save, file_hash, run_postlayout
from .bench import input_vectors
from .spice import simulation_netlist

RESULT = ROOT/'results'/'adder_scaling.json'
_IMPORTED_CODE_SHA256 = {}


def experiment_sources():
    """Fingerprint code, HDL, published cells, PDK decks/models; exclude outputs."""
    paths = [ROOT/'cells/template.json', ROOT/'cells/out/library.json', ROOT/'tritflow/__init__.py',
             ROOT/'tritflow/netlist.py']
    for folder in ('hdl','synth','pnr','sim','extract'):
        paths += sorted((ROOT/'tritflow'/folder).glob('*.py'))
    # Cell-generator implementation does not affect an already published
    # library; fingerprint the consumed views below, plus the sizing ID table.
    paths.append(ROOT/'tritflow/cells/circuits.py')
    paths += [ROOT/'examples'/f'{name}.tv' for name in ('adder','full_add','half_add')]
    for name in ('INV','NAND','NOR','NANY','BUF','TIEP','TIEZ','TIEN','FILL'):
        for suffix in ('.gds','.spice','.ext.spice','.abstract.json','.char.json'):
            path = CELLS_DIR/'out'/name/f'{name}{suffix}'
            if path.is_file(): paths.append(path)
    for folder in ('libs.tech/spice/models', 'libs.tech/klayout/tech/lvs', 'libs.tech/klayout/tech/drc'):
        paths += [p for p in sorted((PDK_ROOT/folder).rglob('*')) if p.is_file()]
    paths += sorted((PDK_ROOT/'openIP62/IP62/Technology/doc').glob('*.pdf'))
    # Python modules already loaded by this process keep executing that code
    # while other streams edit files. Freeze its provenance at import, while
    # checking live HDL/library/model/deck inputs before and after every run.
    # A fresh producer process fingerprints new code and invalidates old caches.
    hashes = {str(p):file_hash(p) for p in paths
              if not _IMPORTED_CODE_SHA256 or p.suffix != '.py'}
    return hashes|_IMPORTED_CODE_SHA256


def _key(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def adder_vectors(n, inputs):
    """Exercise both full-length carry polarities, assertion/release and overflow."""
    cases = []
    def add(label, a, b, cin):
        values = {f'a[{i}]':a[i] for i in range(n)}|{f'b[{i}]':b[i] for i in range(n)}|{'cin':cin}
        # HDL scalarizes width-one buses; both forms have the same arithmetic.
        if n == 1: values |= {'a':a[0], 'b':b[0]}
        cases.append((label, tuple(values[p] for p in inputs)))
    z = [0]*n
    add('zero',z,z,0)
    for polarity, name in ((1,'positive'),(-1,'negative')):
        add(f'{name}_setup',[polarity]*n,z,0)
        add(f'{name}_carry_assert_all_digits',[polarity]*n,z,polarity)
        add(f'{name}_carry_release_all_digits',[polarity]*n,z,0)
    add('positive_overflow',[1]*n,[1]*n,1)
    add('negative_overflow',[-1]*n,[-1]*n,-1)
    add('opposite_operands',[1]*n,[-1]*n,0)
    add('alternating',[(-1)**i for i in range(n)],[(-1)**(i+1) for i in range(n)],1)
    if n == 1:
        cases += [(f'exhaustive_{i}',v) for i,v in enumerate(input_vectors(len(inputs)))]
    return [v for _,v in cases], [label for label,_ in cases]


def adder_oracle(n, inputs, outputs):
    """Compute little-endian balanced-ternary addition without mapped gates."""
    def expected(vector):
        values = dict(zip(inputs,vector)); carry = values['cin']; out = {}
        for i in range(n):
            a = values.get(f'a[{i}]', values.get('a'))
            b = values.get(f'b[{i}]', values.get('b'))
            total = a+b+carry
            carry = (total+1)//3
            pin = f'sum[{i}]' if f'sum[{i}]' in outputs else 'sum'
            out[pin] = total-3*carry
        return out|{'cout':carry}
    return expected


def _artifacts(paths):
    return {str(p):file_hash(p) for p in paths if p.is_file()}


def _valid_cache(record, digest):
    return (record.get('configuration_sha256') == digest and record.get('state') == 'complete'
            and bool(record.get('artifacts_sha256'))
            and all(Path(p).is_file() and file_hash(p)==h for p,h in record['artifacts_sha256'].items()))


def static_points(net, circuit, lvs_report, vectors, expected, *, folder, timeout=900):
    """Independent DC solves, seeded by matched ideal internal-net voltages.

    The LVS cross-reference maps reference gate nets to actual extracted names.
    .nodeset supplies Newton guesses only, never .ic/uic or voltage constraints.
    Output checks still use the independent integer arithmetic oracle.
    """
    inputs = [p.name for p in net.ports if p.dir=='input']
    outputs = [p.name for p in net.ports if p.dir=='output']
    mapping = {key.lower():value for key,value in reference_net_map(lvs_report,net.top).items()}
    ports = {p.name.lower() for p in net.ports}
    def guesses(vector):
        values = evaluate_netlist(net,dict(zip(inputs,vector)),return_all=True)
        result = {}
        for name,value in values.items():
            if name.lower() in ports: continue
            if name.lower() not in mapping:
                raise RuntimeError(f'LVS does not map internal reference net {name}')
            node = mapping[name.lower()]
            node = simulation_netlist('\\'+node if node.startswith('$') else node)
            result['xdut.'+node] = 5*int(value)
        return result
    models = {p.name:file_hash(p) for p in sorted((PDK_ROOT/'libs.tech/spice/models').iterdir()) if p.is_file()}
    digest = _key(dict(circuit=circuit,vectors=vectors,models=models,
        expected=[expected(v) for v in vectors],mapping=mapping,
        code={name:file_hash(Path(__file__).with_name(name))
              for name in ('scaling.py','characterize.py','bench.py','spice.py','runner.py')}))
    folder = Path(folder);folder.mkdir(parents=True,exist_ok=True)
    manifest = folder/'static_cache.json';data_path = folder/'static.json'
    if manifest.is_file() and data_path.is_file():
        cached = json.loads(manifest.read_text())
        if cached.get('sha256')==digest and cached.get('data_sha256')==file_hash(data_path):
            return json.loads(data_path.read_text())
    dc = dc_operating_points(circuit,net.top,inputs,outputs,vectors,expected,
                            timeout=timeout,workdir=folder/'static',nodeset=guesses)
    for row in dc:
        row['static_power_w'] = -sum(v*row['rail_current_a'][rail]
                                    for rail,v in (('VDD',5.),('VMID',0.),('VSS',-5.)))
    _save(data_path,dc)
    _save(manifest,dict(sha256=digest,data_sha256=file_hash(data_path)))
    return dc


def run_size(n, *, build_root=None, seeds=(7,0,19), hold_s=1e-6, step_s=2e-9,
             load_f=10e-15, timeout=900):
    """Build, LVS and measure one real adder; resume only hash-matching evidence."""
    if isinstance(n,bool) or not isinstance(n,int) or n<1:
        raise ValueError('Adder width must be a positive integer')
    directory = Path(build_root or ROOT/'build'/'adder_scaling')/f'adder{n}'
    directory.mkdir(parents=True,exist_ok=True)
    sources = experiment_sources()
    options = dict(n=n,seeds=list(seeds),hold_s=hold_s,step_s=step_s,load_f=load_f,timeout=timeout)
    digest = _key(dict(sources=sources,options=options))
    record_path = directory/'scaling.json'
    if record_path.is_file():
        record = json.loads(record_path.read_text())
        if _valid_cache(record,digest): return record
    started = time.monotonic()
    record = dict(n=n,state='running',passed=False,configuration_sha256=digest,
                  sources_sha256=sources,conditions=options,error=None)
    _save(record_path,record)
    try:
        print(f'N={n}: synthesis',flush=True)
        design = load(ROOT/'examples/adder.tv',top='adder',params={'N':n})
        net = synthesize(design); net.top = f'adder{n}'
        write_artifacts(net,directory)
        inputs = [p.name for p in net.ports if p.dir=='input']
        outputs = [p.name for p in net.ports if p.dir=='output']
        vectors,labels = adder_vectors(n,inputs)
        expected = adder_oracle(n,inputs,outputs)
        attempts = []
        library = Library.load(CELLS_DIR)
        if library.mock: raise RuntimeError('Scaling requires real published cells')
        # Retain valid physical work if a downstream analysis implementation or
        # a PDK model changes. Geometry/characterization/PNR changes invalidate it.
        physical_sources = {p:h for p,h in sources.items()
                            if '/tritflow/sim/' not in p and '/tritflow/extract/' not in p
                            and '/libs.tech/spice/' not in p and '/tech/lvs/' not in p}
        physical_key = _key(dict(sources=physical_sources,seeds=list(seeds),n=n))
        physical_manifest = directory/'physical_cache.json'
        cached_physical = json.loads(physical_manifest.read_text()) if physical_manifest.is_file() else {}
        if _valid_cache(cached_physical,physical_key):
            data = json.loads((directory/f'{net.top}.pnr.json').read_text())
            pnr = PnrResult(directory/f'{net.top}.gds',directory/f'{net.top}.pnr.json',data['stats'],data)
            attempts = cached_physical['pnr_attempts']
            print(f'N={n}: cached qualified PNR',flush=True)
        for seed in (() if attempts else seeds):
            print(f'N={n}: PNR seed {seed}',flush=True)
            try:
                pnr = place_and_route(net,library,output_dir=directory,seed=seed)
                attempts.append(dict(seed=seed,passed=True))
                break
            except (RuntimeError,ValueError) as error:
                attempts.append(dict(seed=seed,passed=False,error=str(error)))
        if not attempts or not attempts[-1]['passed']:
            raise RuntimeError(f'No qualified PNR: {attempts}')
        _save(physical_manifest,dict(configuration_sha256=physical_key,state='complete',
            pnr_attempts=attempts,artifacts_sha256=_artifacts([
                directory/f'{net.top}.gds',directory/f'{net.top}.pnr.json'])))
        print(f'N={n}: extraction/LVS and pre/post transient',flush=True)
        summary = run_postlayout(directory,hold_s=hold_s,step_s=step_s,load_f=load_f,
                                 timeout=timeout,plots=False,vectors=vectors,labels=labels,expected=expected)
        out = directory/'postlayout'
        pre = json.loads((out/'pre/measurements.json').read_text())
        post = json.loads((out/'post/measurements.json').read_text())
        carry_indices = [i for i,label in enumerate(labels) if '_carry_' in label]
        endpoint_pins = ['cout', f'sum[{n-1}]' if n>1 else ('sum[0]' if 'sum[0]' in outputs else 'sum')]
        carry = {}
        for mode,measured in (('pre',pre),('post',post)):
            samples = [dict(segment=i,label=labels[i],outputs={p:measured['rows'][i]['outputs'][p] for p in endpoint_pins})
                       for i in carry_indices]
            delays = [r['outputs'][p]['settling_s'] for r in samples for p in endpoint_pins]
            carry[mode] = dict(max_settling_s=None if any(d is None for d in delays) else max(delays),
                               endpoint_max_settling_s={p:(None if any(r['outputs'][p]['settling_s'] is None for r in samples)
                                  else max(r['outputs'][p]['settling_s'] for r in samples)) for p in endpoint_pins},
                               transitions=samples)
        print(f'N={n}: static operating points',flush=True)
        unique = list(dict.fromkeys(tuple(v) for v in vectors))
        lvs = json.loads((out/'lvs.json').read_text())
        dc = static_points(net,(out/'postlayout.spice').read_text(),lvs['report'],unique,expected,
                           timeout=timeout,folder=out)
        if experiment_sources() != sources:
            raise RuntimeError('Inputs/code changed during scaling run; rerun to qualify the new revision')
        artifacts = [directory/f'{net.top}{suffix}' for suffix in ('.json','.gds','.pnr.json')]
        artifacts += [out/name for name in ('summary.json','lvs.json','prelayout.spice','postlayout.spice',
            'capacitance.json','ir_drop.json','pdk_parameters.json','vectors.json','static.json','static_cache.json','pre/measurements.json','post/measurements.json',
            'pre/waveforms.npz','post/waveforms.npz')]
        artifacts += [Path(lvs['extracted']),Path(lvs['report'])]
        record.update(state='complete',passed=summary['passed'] and all(r['passed'] for r in dc),
            python_code_scope='source hashes frozen at producer import; fresh process required to use edited Python modules',
            cell_count=len(net.instances),die_area_um2=pnr.stats['die_area_um2'],die_size_um=pnr.stats['die_size_um'],
            seed=attempts[-1]['seed'],pnr_attempts=attempts,drc_clean=pnr.data['checks']['pdk_drc']['clean'],
            lvs_matched=summary['lvs_matched'],pre_passed=summary['pre_passed'],post_passed=summary['post_passed'],
            pre_max_error_v=summary['pre_max_error_v'],post_max_error_v=summary['post_max_error_v'],
            carry=carry,settling=summary['settling'],
            max_rail_deviation_v=summary['max_rail_deviation_v'],max_zero_shift_v=summary['max_zero_shift_v'],
            interconnect_parameters=summary['interconnect_parameters'],em_check=summary['em_check'],
            static_power_worst_w=max(r['static_power_w'] for r in dc),
            static_power_mean_w=sum(r['static_power_w'] for r in dc)/len(dc),
            static_vector_count=len(dc),static_scope='maximum/mean over documented unique representative states; N=1 includes all 27',
            vector_plan=dict(input_order=inputs,labels=labels,vectors=vectors,expected=[expected(v) for v in vectors]),
            synthesis_equivalence=net.equivalence,scope=summary['scope'],
            artifacts_sha256=_artifacts(artifacts))
    except Exception as error:
        record.update(state='failed',passed=False,error=f'{type(error).__name__}: {error}')
    record['runtime_s'] = time.monotonic()-started
    _save(record_path,record)
    print(f'N={n}: {record["state"]}, PASS={record["passed"]}, {record["runtime_s"]:.1f}s',flush=True)
    return record


def run_scaling(sizes=range(1,7), *, jobs=1, destination=RESULT, **kwargs):
    """Produce the chapter-7 result matrix; independent sizes may run in processes."""
    from concurrent.futures import ProcessPoolExecutor
    from functools import partial
    sizes = list(sizes)
    if jobs<1 or not sizes or len(sizes)!=len(set(sizes)):
        raise ValueError('Require unique sizes and at least one worker')
    if jobs == 1:
        rows = [run_size(n,**kwargs) for n in sizes]
    else:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            rows = list(pool.map(partial(run_size,**kwargs),sizes))
    result = dict(schema_version=1,experiment='real-layout balanced-ternary ripple-adder scaling',
        rows=rows,passed=all(r['passed'] for r in rows),
        measurement='1 ns ramps; settling from ramp start to final entry into ±0.5 V, through entire segment; 2 ns default max timestep',
        coverage='four directed full-length carry assertion/release transitions, both polarities; overflow/zero/opposite/alternating; N=1 additionally all 27 states',
        limits='Nominal models only. Static power covers documented states. Resistive-divider cells draw DC current even without switching. IR envelope is separate from ideal-rail SPICE. Wire C and metal R remain assumptions where the open PDK supplies no value. PDK current limits are width/cut-specific; linear width scaling is not EM sign-off. Routing heuristics/seed can change die area.')
    result['fits'] = fit_scaling(result)
    path = Path(destination);path.parent.mkdir(parents=True,exist_ok=True);_save(path,result)
    return result


def load_scaling(path=RESULT):
    """Read precomputed notebook data without running synthesis, PNR or ngspice."""
    return json.loads(Path(path).read_text())


def _linear_fit(x, y, *, x_unit, y_unit):
    """OLS with a free intercept; residual scatter is not a PVT uncertainty."""
    import numpy as np
    x,y = np.asarray(x,dtype=float),np.asarray(y,dtype=float)
    if len(x)<2 or len(set(x))<2: return None
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Fit requires finite measured points')
    centered = x-x.mean()
    slope = float(centered@(y-y.mean())/(centered@centered))
    intercept = float(y.mean()-slope*x.mean())
    predicted = slope*x+intercept;residual = y-predicted
    variance = float(np.sum((y-y.mean())**2))
    return dict(slope=slope,intercept=intercept,x_unit=x_unit,y_unit=y_unit,
        point_count=len(x),x=x.tolist(),y=y.tolist(),predicted=predicted.tolist(),residual=residual.tolist(),
        r_squared=None if variance==0 else 1-float(residual@residual)/variance,
        rms_residual=float(np.sqrt(np.mean(residual**2))),max_abs_residual=float(max(abs(residual))))


def fit_scaling(result):
    """Describe measured carry/trit and power/cell for this fixed adder cell mix.

    Fits cover all passing measured widths, without forcing delay through zero
    or extrapolating to unmeasured N. Power is a documented-state DC maximum,
    not switching power, energy/operation, or a universal cell-library constant.
    """
    rows = sorted((r for r in result['rows'] if r.get('passed') and r.get('state')=='complete'),key=lambda r:r['n'])
    carry = {}
    for mode in ('pre','post'):
        selected = [r for r in rows if r['carry'][mode]['max_settling_s'] is not None]
        carry[mode] = _linear_fit([r['n'] for r in selected],
            [r['carry'][mode]['max_settling_s'] for r in selected],x_unit='trit',y_unit='s')
    return dict(method='ordinary least squares, free intercept, all passing measured widths',
        widths=[r['n'] for r in rows],carry=carry,
        static_power=_linear_fit([r['cell_count'] for r in rows],[r['static_power_worst_w'] for r in rows],
                                 x_unit='mapped cell',y_unit='W'),
        scope='Nominal deterministic samples, not PVT confidence bounds or unmeasured-width predictions. Power per cell is an effective average for this adder mix and documented-state maximum. Resistive dividers draw DC at idle; frequency reduction alone does not remove that current.')


def compare_phase3(result, *, baseline=ROOT/'results/phase3_assumed', destination=ROOT/'results/phase4_comparison.json'):
    """Publish measured changes, distinguishing layout changes from parameter changes."""
    baseline = Path(baseline)
    old = json.loads((baseline/'adder_scaling.json').read_text())
    previous = {r['n']:r for r in old['rows'] if r.get('passed')}
    scaling = []
    for row in result['rows']:
        if not row.get('passed') or row['n'] not in previous: continue
        before = previous[row['n']]
        def gds_hash(r):
            return next((h for p,h in r['artifacts_sha256'].items() if p.endswith(f'/adder{r["n"]}.gds')),None)
        scaling.append(dict(n=row['n'],gds_unchanged=gds_hash(row)==gds_hash(before),
            die_area_delta_um2=row['die_area_um2']-before['die_area_um2'],
            carry_delta_s={mode:row['carry'][mode]['max_settling_s']-before['carry'][mode]['max_settling_s'] for mode in ('pre','post')},
            static_power_delta_w=row['static_power_worst_w']-before['static_power_worst_w'],
            rail_deviation_delta_v=row['max_rail_deviation_v']-before['max_rail_deviation_v'],
            zero_shift_delta_v=row['max_zero_shift_v']-before['max_zero_shift_v']))
    original = []
    for name in ('adder4','full_add','mac1','mul1'):
        before = json.loads((baseline/f'{name}.postlayout.json').read_text())
        after = json.loads((ROOT/f'build/{name}/postlayout/summary.json').read_text())
        original.append(dict(design=name,passed=after['passed'],
            post_settling_delta_s={pin:value-before['settling']['post_max_settling_s'][pin]
                                  for pin,value in after['settling']['post_max_settling_s'].items()},
            rail_deviation_delta_v=after['max_rail_deviation_v']-before['max_rail_deviation_v'],
            zero_shift_delta_v=after['max_zero_shift_v']-before['max_zero_shift_v']))
    comparison = dict(scaling=scaling,original_postlayout=original,
        interpretation='Metal/contact/via R and substrate/fringe C were not published in reviewed IP62 data; numerical R/C defaults retained. New PDK current-limit checks/provenance do not alter ideal-rail ngspice. Nonzero changes can include independently changed PNR geometry, extracted device values, or numerical convergence; they are not invented PDK R/C corrections.')
    _save(destination,comparison)
    return comparison


_IMPORTED_CODE_SHA256.update({p:h for p,h in experiment_sources().items() if p.endswith('.py')})
