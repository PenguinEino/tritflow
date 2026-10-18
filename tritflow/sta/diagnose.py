"""Phase-1 audit using saved output waves and independently probed internal nets.

The original SIM deck/network/stimulus is preserved, with finer sampling and
extra probes only. Artifacts remain under STA ownership, outside SIM caches.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from tritflow import ROOT
from tritflow.extract import reference_net_map
from tritflow.netlist import GateNetlist
from tritflow.sim.runner import run_ngspice
from tritflow.sim.spice import simulation_netlist
from tritflow.synth import evaluate_netlist
from tritflow.synth.simulate import CELL_INPUTS
from .metrics import edge_metrics


def write(path, value):
    path = Path(path);path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n');temporary.replace(path)


def probe(directory, destination, *, step_s=2e-9):
    """Replay one complete SIM sequence, with every logical top net observable."""
    directory, destination = Path(directory), Path(destination)
    out = directory/'postlayout'
    summary = json.loads((out/'summary.json').read_text())
    net = GateNetlist.load(out/'inputs'/f'{summary["top"]}.json')
    mapping = reference_net_map(json.loads((out/'lvs.json').read_text())['report'],net.top)
    deck = (out/'post/tb.spice').read_text()
    circuit, control = re.split(r'(?im)^\.control\s*$',deck,maxsplit=1)
    tran = re.search(r'(?im)^tran\s+\S+\s+(\S+)',control)[1]
    ports = {p.name for p in net.ports}
    from tritflow.synth.writers import spice_names
    safe = spice_names([p.name for p in net.ports if p.dir=='input']+
                       [p.name for p in net.ports if p.dir=='output'],('VDD','VMID','VSS','0'))
    probes = {}
    for name in sorted(net.nets()):
        node = mapping[name]
        node = simulation_netlist('\\'+node if node.startswith('$') else node)
        probes[name] = f'v({safe[name]})' if name in ports else f'v(xdut.{node})'
    digest = hashlib.sha256((circuit+str(step_s)+json.dumps(probes,sort_keys=True)).encode()).hexdigest()
    cache = destination/'waveforms.npz'
    meta = destination/'simulation.json'
    if cache.is_file() and meta.is_file() and json.loads(meta.read_text())['sha256']==digest:
        with np.load(cache) as data:waves={k:data[k] for k in data.files}
    else:
        result = run_ngspice(circuit,f'tran {step_s:.15g} {tran} 0 {step_s:.15g}',
                             list(probes.values()),timeout=600,workdir=destination)
        waves = {'time':result['data']['time']}|{name:result['data'][p.lower()] for name,p in probes.items()}
        np.savez_compressed(cache,**waves)
        write(meta,{'sha256':digest,'source_deck_sha256':hashlib.sha256(deck.encode()).hexdigest(),
                    'step_s':step_s,'probes':probes})
        (destination/'waveform.txt').unlink(missing_ok=True)
    plan = json.loads((out/'vectors.json').read_text());hold=summary['hold_s']
    rows=[]
    for index,(first,last) in enumerate(zip(plan['vectors'],plan['vectors'][1:]),1):
        before={n:int(v) for n,v in evaluate_netlist(net,dict(zip(plan['input_order'],first)),return_all=True).items()}
        after={n:int(v) for n,v in evaluate_netlist(net,dict(zip(plan['input_order'],last)),return_all=True).items()}
        metrics={name:edge_metrics(waves['time'],waves[name],before[name],after[name],index*hold,(index+1)*hold)
                 for name in net.nets()}
        stages=[]
        for inst in net.instances:
            output=metrics[inst.pins['Y']]
            for pin in CELL_INPUTS[inst.cell]:
                input_edge=metrics[inst.pins[pin]]
                if input_edge['midpoint_s'] is None or output['midpoint_s'] is None:continue
                stages.append({'instance':inst.name,'cell':inst.cell,'input_pin':pin,
                    'input_transition':[before[inst.pins[pin]],after[inst.pins[pin]]],
                    'output_transition':[before[inst.pins['Y']],after[inst.pins['Y']]],
                    'input_midpoint_s':input_edge['midpoint_s'],'output_midpoint_s':output['midpoint_s'],
                    'midpoint_delay_s':output['midpoint_s']-input_edge['midpoint_s'],
                    'input_slew_10_90_s':input_edge['slew_10_90_s'],
                    'output_slew_10_90_s':output['slew_10_90_s'],
                    'settling_overlap_s':input_edge['settling_s']-input_edge['midpoint_s']})
        rows.append({'segment':index,'before':dict(zip(plan['input_order'],first)),
                     'after':dict(zip(plan['input_order'],last)),'nets':metrics,'stages':stages})
    report={'top':net.top,'step_s':step_s,'source_summary_sha256':hashlib.sha256((out/'summary.json').read_bytes()).hexdigest(),
            'rows':rows,'scope':'Original network, initial guesses and full SIM sequence; finer timestep and additional probes only.'}
    write(destination/'measurements.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--name')
    parser.add_argument('--step-ns',type=float,default=2.)
    args=parser.parse_args()
    destination=ROOT/'results/sta/diagnosis'/(args.name or args.directory.name)
    probe(args.directory,destination,step_s=args.step_ns*1e-9)


if __name__=='__main__':main()
