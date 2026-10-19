"""Finite-transition input charge for a lumped fanout-C approximation.

Small-signal C at the highest-gain DC bias need not equal the charge required
for a full trit transition. Integrate the ideal input-source current through
each complete transition, subtract stationary gate leakage, and divide by the
signed voltage change. This is measured charge, not a circuit-delay fit.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
from pathlib import Path

import numpy as np

from tritflow.sim.tools import simulator_identity
from tritflow import ROOT,CELLS_DIR
from tritflow.cells.regression import guesses
from tritflow.sim import input_vectors,build_testbench,run_ngspice
from tritflow.sim.bench import restore_signals
from .characterize import sha
from .diagnose import write
from .logic import function
from .metrics import edge_metrics


def cell_charge(cell, *, step_s=.1e-9):
    root=ROOT/'results/sta/charge'/cell
    source=CELLS_DIR/'out'/cell/f'{cell}.ext.spice'
    base=json.loads((source.parent/f'{cell}.timing.json').read_text())
    cache=root/'measurements.json'
    key={'simulator':simulator_identity(),'source_sha256':sha(source),'step_s':step_s,'code_sha256':sha(__file__)}
    if cache.exists():
        previous=json.loads(cache.read_text())
        if previous.get('configuration')==key:return previous
    vectors=input_vectors(len(base['inputs']),transitions=True);hold=300e-9
    bench=build_testbench(source.read_text(),cell,base['inputs'],['Y'],vectors,hold_s=hold,
            step_s=step_s,nodeset=guesses(source.read_text()),initial_outputs={'Y':function(cell,vectors[0])})
    run=run_ngspice(bench['netlist'],bench['commands'],bench['probes']+
        [f'i(vin{i})' for i in range(len(base['inputs']))],timeout=600,workdir=root)
    data=restore_signals(run['data'],bench);time=data['time'];rows=[]
    for k,(first,last) in enumerate(zip(vectors,vectors[1:]),1):
        start,end=k*hold,(k+1)*hold
        measured=edge_metrics(time,data['v(Y)'],function(cell,first),function(cell,last),start,end)
        if measured['settling_s'] is None:raise ValueError(f'Unsettled charge fixture: {cell} {first}->{last}')
        for i,pin in enumerate(base['inputs']):
            if first[i]==last[i]:continue
            current=data[f'i(vin{i})'];t=np.r_[start,time[(time>start)&(time<end)],end]
            baseline=float(np.median(current[(time>end-5e-9)&(time<=end)]))
            y=np.interp(t,time,current)-baseline
            charge=-float(np.sum((y[1:]+y[:-1])*.5*np.diff(t)))
            capacitance=charge/(5*(last[i]-first[i]))
            rows.append({'from_inputs':dict(zip(base['inputs'],first)),'to_inputs':dict(zip(base['inputs'],last)),
                'pin':pin,'charge_c':charge,'capacitance_f':capacitance})
    result={'cell':cell,'configuration':key,'rows':rows,'passed':True,
        'method':'Integral of input-source current, stationary leakage removed, divided by signed full voltage transition; fixture output 10 fF, 1 ns full ramp.',
        'adopted_in_timing_model':False,
        'limitation':'This is signed multi-terminal charge inferred from sampled source current. Negative and widely varying values do not define a nonnegative lumped shunt-C model; no replacement of published AC pin C is justified.',
        'per_pin':{p:{'min_f':min(r['capacitance_f'] for r in rows if r['pin']==p),
                      'max_f':max(r['capacitance_f'] for r in rows if r['pin']==p),
                      'mean_f':float(np.mean([r['capacitance_f'] for r in rows if r['pin']==p])),
                      'ac_max_f':base['input_capacitance']['per_pin'][p]['max_f']} for p in base['inputs']}}
    np.savez_compressed(root/'waveforms.npz',**data)
    (root/'waveform.txt').unlink(missing_ok=True)
    write(cache,result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--jobs',type=int,default=2)
    args=parser.parse_args()
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        pending={pool.submit(cell_charge,c):c for c in ('INV','NAND','NOR','NANY','BUF')}
        for future in as_completed(pending):
            result=future.result();print(result['cell'],result['per_pin'],flush=True)


if __name__=='__main__':main()
