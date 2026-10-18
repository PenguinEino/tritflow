"""SPICE midpoint-propagation surfaces, published only in results/sta.

For a changing output, d50 = t50(output) - t50(changing input), slew is the
last-directional 10–90% interval, and tail = final-band-entry - t50(output).
Only d50 composes between gates; the settling tail belongs to the endpoint.
Synchronous multiple-input observations retain that qualification explicitly.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from tritflow import CELLS_DIR, ROOT, PDK_ROOT
from tritflow.cells.regression import guesses
from tritflow.sim import build_testbench, input_vectors, run_ngspice
from tritflow.sim.bench import restore_signals
from tritflow.sim.provenance import pdk_provenance
from .diagnose import write
from .logic import function
from .metrics import edge_metrics

LOADS = (10e-15,100e-15,500e-15,1e-12,2e-12)
RAMPS = (.25e-9,1e-9,5e-9,15e-9,50e-9,150e-9)
FIELDS = ('propagation_s','tail_s','output_slew_10_90_s','settling_s','recovery_s')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def profile(cell, load, ramp, output, *, step=None):
    """All 6/72 directed endpoint changes at one load/ramp point, with real SPICE."""
    source = CELLS_DIR/'out'/cell/f'{cell}.ext.spice'
    template = json.loads((source.parent/f'{cell}.timing.json').read_text())
    text=source.read_text();inputs=template['inputs']
    step = step or .25e-9
    vectors=input_vectors(len(inputs),transitions=True);hold=ramp+250e-9
    bench=build_testbench(text,cell,inputs,['Y'],vectors,loads_f=load,edge_s=ramp,
            hold_s=hold,step_s=step,nodeset=guesses(text),initial_outputs={'Y':function(cell,vectors[0])})
    provenance={'source_sha256':sha(source), 'model_sha256':{p.name:sha(p) for p in sorted((PDK_ROOT/'libs.tech/spice/models').iterdir()) if p.is_file()},
        'code_sha256':{p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('metrics.py')]},
        'load_f':load,'input_transition_s':ramp,'step_s':step,'hold_s':hold,
        'pdk_provenance':pdk_provenance()}
    folder=Path(output)/'runs'/cell/f'r{ramp:.6g}_c{load:.6g}'
    cache=folder/'measurements.json'
    if cache.exists():
        prior=json.loads(cache.read_text())
        old=prior['provenance']
        # Earlier finer-step/longer-plateau observations are valid measurements
        # of the same edges. Keep their original provenance, never relabel them.
        if (prior['passed'] and all(old[k]==provenance[k] for k in
                ('source_sha256','model_sha256','load_f','input_transition_s','pdk_provenance'))
                and old['code_sha256']['metrics.py']==provenance['code_sha256']['metrics.py']
                and old['step_s']<=step and old['hold_s']>=hold):return prior
    run=run_ngspice(bench['netlist'],bench['commands'],bench['probes'],timeout=600,workdir=folder)
    data=restore_signals(run['data'],bench);rows=[]
    for k,(before,after) in enumerate(zip(vectors,vectors[1:]),1):
        old,new=function(cell,before),function(cell,after)
        edge=edge_metrics(data['time'],data['v(Y)'],old,new,k*hold,(k+1)*hold)
        reference=.5*ramp
        rows.append({'from':list(before),'to':list(after),
            'propagation_s':None if edge['midpoint_s'] is None else edge['midpoint_s']-reference,
            'tail_s':edge['tail_s'],'output_slew_10_90_s':edge['slew_10_90_s'],
            'settling_s':edge['settling_s'],
            'recovery_s':None if edge['settling_s'] is None else max(0.,edge['settling_s']-reference),
            'midpoint_crossing_count':edge['midpoint_crossing_count'],
            'passed':edge['settling_s'] is not None and (old==new or
                       (edge['midpoint_s'] is not None and edge['slew_10_90_s'] is not None and edge['tail_s']>=0))})
    result={'cell':cell,'provenance':provenance,'rows':rows,'passed':all(r['passed'] for r in rows)}
    write(cache,result)
    if load==100e-15 and ramp==1e-9:np.savez_compressed(folder/'waveforms.npz',**data)
    (folder/'waveform.txt').unlink(missing_ok=True)
    return result


def characterize(*,output=None,jobs=2,cells=('INV','NAND','NOR','NANY','BUF'),loads=LOADS,ramps=RAMPS):
    """Characterize independent isolated cells; circuit validation is not fitted."""
    output=Path(output or ROOT/'results/sta/propagation')
    points={c:{} for c in cells}
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        pending={pool.submit(profile,c,l,r,output):(c,l,r) for c in cells for r in ramps for l in loads}
        for future in as_completed(pending):
            cell,load,ramp=pending[future];point=future.result();points[cell][ramp,load]=point
            print(f'{cell} {load*1e15:g} fF {ramp*1e9:g} ns: {"PASS" if point["passed"] else "FAIL"}',flush=True)
    for cell in cells:
        base=json.loads((CELLS_DIR/'out'/cell/f'{cell}.timing.json').read_text())
        data=deepcopy(base);data['schema_version']=2
        data['axes']={'load_f':list(loads),'input_transition_s':list(ramps)}
        data['metric']='Last directional ideal-step midpoint propagation, plus endpoint-only final settling tail.'
        data['created_utc']=datetime.now(timezone.utc).isoformat()
        data['base_timing_sha256']=sha(CELLS_DIR/'out'/cell/f'{cell}.timing.json')
        data['code_sha256']={p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('metrics.py')]}
        lookups={key:{(tuple(r['from']),tuple(r['to'])):r for r in p['rows']} for key,p in points[cell].items()}
        for arc in data['arcs']+data['simultaneous']:
            key=tuple(arc['from_inputs'][p] for p in data['inputs']),tuple(arc['to_inputs'][p] for p in data['inputs'])
            for field in FIELDS+('passed','midpoint_crossing_count'):
                arc[field]=[[lookups[r,l][key][field] for l in loads] for r in ramps]
            for field in ('status','error_v'):arc.pop(field,None)
        data['runs']=[p['provenance'] for p in points[cell].values()]
        data['conditions']['hold_s_by_ramp']=[min(points[cell][r,l]['provenance']['hold_s'] for l in loads) for r in ramps]
        data['conditions']['max_step_s_by_ramp']=[max(points[cell][r,l]['provenance']['step_s'] for l in loads) for r in ramps]
        data['coverage']['measured_grid_points']=len(loads)*len(ramps)
        data['max_settling_s']=max(row['settling_s'] or 0. for point in points[cell].values() for row in point['rows'])
        data['complete']=len(points[cell])==len(loads)*len(ramps)
        data['passed']=all(p['passed'] for p in points[cell].values())
        data['conditions']['delay_reference']='Input ideal-step midpoint to output ideal-step midpoint. Full-ramp axis unchanged.'
        data['scope']='Isolated extracted devices, ideal input ramps, lumped external C. No multi-input skew characterization.'
        write(output/'tables'/f'{cell}.propagation.json',data)
    write(output/'summary.json',{'cells':list(cells),'loads_f':list(loads),'ramps_s':list(ramps),
        'passed':all(p['passed'] for table in points.values() for p in table.values()),
        'table_sha256':{c:sha(output/'tables'/f'{c}.propagation.json') for c in cells}})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=int,default=2)
    parser.add_argument('--cells',nargs='+',default=['INV','NAND','NOR','NANY','BUF'])
    parser.add_argument('--resolution',action='store_true',help='50 ps INV/NANY control at 100 fF, 1 ns ramp')
    args=parser.parse_args()
    if args.resolution:
        result=[]
        for cell in ('INV','NANY'):
            fine=profile(cell,100e-15,1e-9,ROOT/'results/sta/resolution',step=.05e-9)
            primary=json.loads((ROOT/f'results/sta/propagation/runs/{cell}/r1e-09_c1e-13/measurements.json').read_text())
            pairs=list(zip(primary['rows'],fine['rows']))
            delta={field:max((abs(a[field]-b[field]) for a,b in pairs if a[field] is not None and b[field] is not None),default=0.) for field in FIELDS}
            result.append({'cell':cell,'primary_step_s':primary['provenance']['step_s'],
                'fine_step_s':fine['provenance']['step_s'],'max_absolute_difference_s':delta,
                'changing_output_d50_within_250ps':delta['propagation_s']<=.25e-9,
                'passed':primary['passed'] and fine['passed']})
            print(cell,delta,flush=True)
        write(ROOT/'results/sta/resolution/comparison.json',{'controls':result,
            'scope':'100 fF, 1 ns ramp controls only; finite-grid sampling is not a bound over all loads/ramps or circuit glitches.'})
    else:characterize(jobs=args.jobs,cells=args.cells)


if __name__=='__main__':main()
