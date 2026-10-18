"""Available-process, temperature and symmetric-supply robustness of TR-1um.

The open IP62 release contains TYP only. Its private L16/process corners are not
invented here. Every waveform is assessed against both nominal project levels
and supply-tracking levels, with the same inclusive absolute +/-0.5 V band.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import gzip
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np
from tritflow import ROOT,CELLS_DIR,PDK_ROOT,TRIT_VOLTS
from tritflow.netlist import GateNetlist
from tritflow.synth import evaluate_netlist
from tritflow.extract import reference_net_map
from .bench import input_vectors
from .characterize import dc_operating_points,logic_value
from .measure import measure_sequence
from .postlayout import _save,_simulate_cached,file_hash,arithmetic_oracle
from .runner import SimulationError
from .spice import CELL_PINS,simulation_netlist

RESULT=ROOT/'results/corners/summary.json'


def available_corners(pdk=PDK_ROOT):
    """Inventory actual .lib/.endl sections and the published nominal index."""
    root=Path(pdk);folder=root/'libs.tech/spice/models'
    texts={p.name:p.read_text() for p in sorted(folder.iterdir()) if p.is_file()}
    sections={name:re.findall(r'(?im)^\s*\.lib\s+([\w-]+)\s*$',text) for name,text in texts.items()}
    sections={name:rows for name,rows in sections.items() if rows}
    if sections:raise ValueError('New model sections require review before mapping process-corner names')
    defaults={k:float(v) for k,v in re.findall(r'(?im)^\s*\.parameters?\s+(\w+)\s*=\s*([\d.eE+-]+)',texts['ip62_models'])}
    return dict(available=['TYP'],lib_sections=sections,nominal_parameters=defaults,
        unavailable=['private Taguchi L16 sets 01..16','FF','SS','FS','SF'],
        evidence=[{'document':'OS00_リファレンスマニュアル_rev1.1.pdf','pages':[37,38]},
                  {'document':'OS02_回路simガイドライン_rev1.pdf','page':16,'statement':'コーナーモデルは非公開です。'}],
        temperature_fit_range_c=[27,150],
        scope='Only nominal process is distributed. -40 C is requested extrapolation beyond the published model extraction range; this is not foundry process/PVT qualification.',
        model_sha256={name:hashlib.sha256(text.encode()).hexdigest() for name,text in texts.items()})


def _key(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def _failure_list(measurements):
    return [dict(segment=i,input_trits=row['input_trits'],output=pin,**value)
            for i,row in enumerate(measurements['rows']) for pin,value in row['outputs'].items()
            if not value['passed'] or value['settling_s'] is None]


def _compact(measurements):
    unsettled=measurements['unsettled']
    maximum=max((v for v in measurements['max_settling_s'].values() if v is not None),default=None)
    return dict(passed=measurements['passed'],max_error_v=measurements['max_error_v'],
                max_settling_s=None if unsettled else maximum,unsettled=unsettled,
                failures=_failure_list(measurements))


def _adder_guesses(net,lvs_report,inputs,rails):
    mapping={a.lower():b for a,b in reference_net_map(lvs_report,net.top).items()}
    ports={p.name.lower() for p in net.ports};levels={-1:rails['VSS'],0:rails['VMID'],1:rails['VDD']}
    def guesses(vector):
        values=evaluate_netlist(net,dict(zip(inputs,vector)),return_all=True)
        result={}
        for name,value in values.items():
            if name.lower() in ports:continue
            node=mapping[name.lower()]
            node=simulation_netlist('\\'+node if node.startswith('$') else node)
            result['xdut.'+node]=levels[int(value)]
        return result
    return guesses


def _run_case(task,*,timeout=600):
    dut,temperature,scale=task;start=time.monotonic()
    inventory=available_corners();rails={'VDD':5*scale,'VMID':0.,'VSS':-5*scale}
    if dut=='full_add':
        directory=ROOT/'build/full_add';net=GateNetlist.load(directory/'full_add.json')
        top=net.top;source=directory/'postlayout/postlayout.spice';text=source.read_text()
        inputs=[p.name for p in net.ports if p.dir=='input'];outputs=[p.name for p in net.ports if p.dir=='output']
        vectors=input_vectors(len(inputs));states=vectors
        expected=arithmetic_oracle('full_add',inputs)
        lvs=json.loads((directory/'postlayout/lvs.json').read_text())
        if not lvs['matched']:raise ValueError('Full-adder PVT requires a qualified extracted layout')
        guesses=_adder_guesses(net,lvs['report'],inputs,rails)
        hold_s,step_s=500e-9,2e-9
        extra={str(p):file_hash(p) for p in [directory/'full_add.json',directory/f'{top}.gds',directory/f'{top}.pnr.json']}
    else:
        top=dut;source=CELLS_DIR/f'out/{dut}/{dut}.ext.spice';text=source.read_text()
        inputs=list(CELL_PINS[dut][:-1]);outputs=['Y'];states=input_vectors(len(inputs))
        vectors=input_vectors(len(inputs),transitions=True)
        expected=lambda v:{'Y':logic_value(dut,v)};guesses=None
        hold_s,step_s=200e-9,.5e-9;extra={}
    conditions=dict(corner='TYP',temperature_c=temperature,supply_scale=scale,supplies_v=rails,
        hold_s=hold_s,step_s=step_s,edge_s=1e-9,load_f=10e-15,
        coverage='all 27 states in lexicographic order; 26 transitions' if dut=='full_add' else 'all discrete states and every directed input-vector transition')
    sources={str(source):file_hash(source)}|extra
    code={name:file_hash(Path(__file__).with_name(name)) for name in ['corners.py','bench.py','measure.py','runner.py','spice.py','characterize.py']}
    digest=_key(dict(sources=sources,conditions=conditions,models=inventory['model_sha256'],code=code))
    cache=ROOT/f'results/corners/cases/{digest}.json.gz';cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.is_file():
        result=json.loads(gzip.decompress(cache.read_bytes()))
        if result.get('configuration_sha256')==digest:return result
    folder=ROOT/'build/corners'/digest;folder.mkdir(parents=True,exist_ok=True)
    result=dict(dut=dut,conditions=conditions,configuration_sha256=digest,sources_sha256=sources,
        model_sha256=inventory['model_sha256'],analysis_sha256=code,cache=str(cache.relative_to(ROOT)),
        state='running',error=None,dc=None,transient=None)
    try:
        dc=dc_operating_points(text,top,inputs,outputs,states,expected,temperature_c=temperature,
            supplies_v=rails,timeout=timeout,workdir=folder/'dc',nodeset=guesses)
        for row in dc:
            ideal=expected(tuple(row['input_trits']))
            row['nominal_error_v']={pin:value-TRIT_VOLTS[ideal[pin]] for pin,value in row['output_v'].items()}
            row['nominal_passed']=all(abs(v)<=.5 for v in row['nominal_error_v'].values())
            row['static_power_w']=-sum(rails[rail]*value for rail,value in row['rail_current_a'].items())
        if any(value<rails['VSS']-.5 or value>rails['VDD']+.5 for row in dc for value in row['output_v'].values()):
            result['dc_raw']=dc
            raise SimulationError('Nonphysical DC root outside supply rails; raw points retained')
        result['dc']=dict(rows=dc,tracking_passed=all(row['passed'] for row in dc),
            nominal_passed=all(row['nominal_passed'] for row in dc),
            tracking_max_error_v=max(abs(v) for row in dc for v in row['error_v'].values()),
            nominal_max_error_v=max(abs(v) for row in dc for v in row['nominal_error_v'].values()),
            max_static_current_a=max(abs(v) for row in dc for v in row['rail_current_a'].values()),
            max_static_power_w=max(row['static_power_w'] for row in dc))
        run=_simulate_cached(folder,'transient',text,top,inputs,outputs,vectors,expected,
            hold_s=hold_s,step_s=step_s,load_f=10e-15,timeout=timeout,
            temperature_c=temperature,supplies_v=rails,nodeset=None if guesses is None else guesses(vectors[0]))
        tracking=run['measurements'];nominal=measure_sequence(run['waveforms'],run['stimulus'],expected,ideal_volts=TRIT_VOLTS)
        result['transient']=dict(tracking=_compact(tracking),nominal=_compact(nominal),
                                 input_order=inputs,measurements=str(folder/'transient/measurements.json'))
        _save(folder/'both_measurements.json',dict(tracking=tracking,nominal=nominal))
        result['state']='complete'
    except (SimulationError,OSError,ValueError) as error:
        result['state']='solver_error';result['error']=f'{type(error).__name__}: {error}'
    result['runtime_s']=time.monotonic()-start
    if any(not Path(p).is_file() or file_hash(p)!=h for p,h in sources.items()):
        raise RuntimeError('Source files changed during corner case; rerun against one revision')
    if available_corners()['model_sha256']!=inventory['model_sha256']:
        raise RuntimeError('PDK models changed during corner case')
    if result['state']=='complete':
        temp=cache.with_suffix('.tmp');temp.write_bytes(gzip.compress(json.dumps(result,allow_nan=False).encode(),mtime=0));temp.replace(cache)
    tracking=result.get('transient',{});tracking=None if tracking is None else tracking.get('tracking')
    print(f'{dut} T={temperature:g}C rails=±{5*scale:g}V: {result["state"]}, tracking={None if tracking is None else tracking["passed"]}',flush=True)
    return result


def run_corners(*,temperatures=(-40.,27.,85.),supply_scales=(.9,1.,1.1),
                cells=('INV','NAND','NOR','NANY','BUF'),include_adder=True,jobs=3,timeout=600):
    """Compute only the available nominal process across the requested T/V grid."""
    inventory=available_corners()
    if any(c not in ('INV','NAND','NOR','NANY','BUF') for c in cells):raise ValueError('Unsupported cell')
    if jobs<1 or any(not np.isfinite(t) or t<=-273.15 for t in temperatures) or any(not np.isfinite(s) or s<=0 for s in supply_scales):
        raise ValueError('Invalid T/V grid or worker count')
    tasks=[(dut,float(t),float(s)) for dut in list(cells)+(['full_add'] if include_adder else []) for t in temperatures for s in supply_scales]
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        rows=list(pool.map(partial(_run_case,timeout=timeout),tasks))
    result=dict(schema_version=1,inventory=inventory,temperatures_c=list(temperatures),supply_scales=list(supply_scales),
        band_v=.5,rows=rows,
        criteria={'nominal':'Project -5/0/+5 V ideals, inclusive ±0.5 V; no supply recentering.',
                  'tracking':'Actual VSS/VMID/VDD ideals, same inclusive ±0.5 V; separates rail scaling from restoration.'},
        scope='TYP process only. Dual rails scale together, VMID stays 0. Cell device-only views, 10 fF output; full adder includes actual-GDS estimated wire C. -40 C extrapolates beyond published 27..150 C model extraction range. No process-corner/PVT sign-off claim.')
    RESULT.parent.mkdir(parents=True,exist_ok=True);_save(RESULT,result)
    return result


def load_corners(path=RESULT):return json.loads(Path(path).read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=int,default=3)
    parser.add_argument('--temperatures',type=float,nargs='+',default=[-40.,27.,85.])
    parser.add_argument('--supply-scales',type=float,nargs='+',default=[.9,1.,1.1])
    args=parser.parse_args();result=run_corners(jobs=args.jobs,temperatures=args.temperatures,supply_scales=args.supply_scales)
    return 0 if all(r['state']=='complete' for r in result['rows']) else 1


if __name__=='__main__':raise SystemExit(main())
