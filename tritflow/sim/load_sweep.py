"""Equal external loads on both full-adder outputs: first observed 500 ns FAIL."""
from __future__ import annotations

import json
import math
from pathlib import Path

from tritflow import ROOT
from tritflow.netlist import GateNetlist
from .postlayout import (_save, file_hash, run_postlayout, _simulate_cached,
                         representative_vectors, arithmetic_oracle)
from .scaling import experiment_sources, _key, _valid_cache

RESULT = ROOT/'results/full_add_load_sweep.json'
DEFAULT_LOADS = (10e-15,100e-15,1e-12,3e-12,10e-12,30e-12,100e-12,300e-12,1e-9)


def sweep_output_load(directory=ROOT/'build/full_add', *, loads_f=DEFAULT_LOADS,
                      hold_s=500e-9, step_s=2e-9, relative_resolution=.02,
                      absolute_resolution_f=50e-15, timeout=600, destination=RESULT):
    """Coarse ascending sweep, then refine the first measured PASS/FAIL bracket.

    All 27 input states are visited in a documented lexicographic sequence, not
    all 702 directed transitions. The window is checked at end minus 1 ns, and
    settling must stay in band through the segment end. No monotonic guarantee
    outside measured points is implied. Both outputs receive the stated load
    to ground, in addition to the extracted GDS wire capacitance.
    """
    loads = [float(v) for v in loads_f]
    if (not loads or any(not math.isfinite(v) or v<0 for v in loads)
            or any(a>=b for a,b in zip(loads,loads[1:]))):
        raise ValueError('loads_f must be finite, nonnegative and strictly increasing')
    if relative_resolution<=0 or absolute_resolution_f<=0:
        raise ValueError('Boundary resolution must be positive')
    directory = Path(directory).resolve();destination = Path(destination)
    netfile = directory/'full_add.json'
    net = GateNetlist.load(netfile)
    paths = [netfile,directory/f'{net.top}.gds',directory/f'{net.top}.pnr.json']
    sources = experiment_sources()|{str(p):file_hash(p) for p in paths}
    options = dict(loads_f=loads,hold_s=hold_s,step_s=step_s,
                   relative_resolution=relative_resolution,absolute_resolution_f=absolute_resolution_f)
    digest = _key(dict(sources=sources,conditions=options))
    if destination.is_file():
        cached = json.loads(destination.read_text())
        if _valid_cache(cached,digest): return cached
    qualification = run_postlayout(directory,plots=False,hold_s=hold_s,step_s=step_s,timeout=timeout)
    if not qualification['passed']:
        raise RuntimeError('Nominal full-add postlayout must qualify before load sweep')
    out = directory/'load_sweep';out.mkdir(parents=True,exist_ok=True)
    circuit = (directory/'postlayout/postlayout.spice').read_text()
    inputs = [p.name for p in net.ports if p.dir=='input']
    outputs = [p.name for p in net.ports if p.dir=='output']
    vectors,labels = representative_vectors('full_add',inputs)
    expected = arithmetic_oracle('full_add',inputs)
    rows = []; artifacts = [directory/'postlayout/postlayout.spice']
    def sample(load):
        mode = f'load_{load.hex()}'
        run = _simulate_cached(out,mode,circuit,net.top,inputs,outputs,vectors,expected,
                              hold_s=hold_s,step_s=step_s,load_f=load,timeout=timeout)
        measured = run['measurements']
        failures = [dict(segment=i,input_trits=r['input_trits'],output=pin,**value)
                    for i,r in enumerate(measured['rows']) for pin,value in r['outputs'].items()
                    if not value['passed'] or value['settling_s'] is None]
        row = dict(load_f=load,passed=measured['passed'],max_error_v=measured['max_error_v'],
                   max_settling_s=measured['max_settling_s'],
                   unsettled=measured['unsettled'],failures=failures,
                   measurements=str(out/mode/'measurements.json'))
        rows.append(row)
        artifacts.extend(out/mode/name for name in ('simulation.json','measurements.json','waveforms.npz'))
        print(f'full_add load {load*1e12:.6g} pF: {"PASS" if row["passed"] else "FAIL"}',flush=True)
        return row
    lower = upper = None
    for load in loads:
        row = sample(load)
        if not row['passed']:
            upper = load
            break
        lower = load
    coarse_first_fail = upper
    if lower is not None and upper is not None:
        while upper-lower > max(absolute_resolution_f,relative_resolution*upper):
            midpoint = (lower+upper)/2
            if sample(midpoint)['passed']: lower = midpoint
            else: upper = midpoint
    current = experiment_sources()|{str(p):file_hash(p) for p in paths}
    if current != sources:
        raise RuntimeError('Inputs/code changed during load sweep; rerun for the current revision')
    result = dict(schema_version=1,state='complete',configuration_sha256=digest,sources_sha256=sources,
        conditions=options|{'edge_s':1e-9,'band_v':.5,'load_application':'equal capacitor from each output to ground, plus actual-GDS wire C'},
        input_order=inputs,outputs=outputs,vectors=vectors,labels=labels,rows=sorted(rows,key=lambda r:r['load_f']),
        boundary_found=lower is not None and upper is not None,
        boundary=dict(last_pass_f=lower,first_fail_f=upper,coarse_first_fail_f=coarse_first_fail,
                      width_f=None if lower is None or upper is None else upper-lower),
        scope='First observed failure on the stated sequence within 500 ns; refined local measured bracket, not exhaustive-transition or PVT guarantee. Unsettled delays remain null.',
        artifacts_sha256={str(p):file_hash(p) for p in artifacts})
    destination.parent.mkdir(parents=True,exist_ok=True);_save(destination,result)
    return result


def load_sweep_results(path=RESULT):
    """Instant notebook read of precomputed measurements and the boundary."""
    return json.loads(Path(path).read_text())
