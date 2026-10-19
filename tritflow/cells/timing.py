"""Measured ternary settling surfaces with exact sensitizing input assignments.

Use SIM's public harness and measurements unchanged. All directed state changes
are measured; single-pin arcs retain their side-input trits, while synchronous
multi-input changes are explicitly separated. Tables never replace an unsettled
or failed transition by a finite delay. Time is referenced to input edge START.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from types import CodeType
from pathlib import Path
import shutil
import tempfile

import numpy as np
from tritflow import CELLS_DIR, PDK_ROOT, PASS_BAND
from tritflow.sim import build_testbench, input_vectors, run_ngspice, measure_sequence, SimulationError
from tritflow.sim.characterize import input_capacitance
from tritflow.sim.provenance import pdk_provenance
from tritflow.sim.tools import simulator_identity
from .circuits import circuits, ideal
from .reference import sha
from .regression import guesses

LOADS_F = (5e-15, 10e-15, 20e-15, 50e-15, 100e-15, 200e-15, 500e-15, 1e-12)
RAMPS_S = (1e-9, 10e-9, 50e-9, 150e-9)
# Freeze source provenance at import, including SIM code loaded by this producer.
_CODE_PATHS = [Path(__file__), Path(__file__).with_name('regression.py')]
_CODE_PATHS += [Path(__file__).parents[1]/'sim'/name for name in
                ('bench.py','runner.py','measure.py','spice.py','characterize.py')]
CODE_SHA256 = {str(p.relative_to(Path(__file__).parents[1])): sha(p) for p in _CODE_PATHS}
MODEL_SHA256 = {p.name:sha(p) for p in sorted((PDK_ROOT/'libs.tech/spice/models').iterdir()) if p.is_file()}
PDK_PROVENANCE = pdk_provenance()


def _measurement_code():
    """Stable semantic bytecode, excluding filenames/line numbers/interning flags."""
    def stable(value):
        if isinstance(value,CodeType):
            return [value.co_code.hex(),value.co_names,value.co_varnames,
                    value.co_argcount,value.co_kwonlyargcount,[stable(c) for c in value.co_consts]]
        if isinstance(value,(tuple,list)):return [stable(v) for v in value]
        if isinstance(value,frozenset):return sorted(stable(v) for v in value)
        if isinstance(value,bytes):return {'bytes':value.hex()}
        return value
    signature=[stable(f.__code__) for f in (point,_slew,guesses,ideal)]
    return {'cells_bytecode':hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest(),
            'sim_source':{k:v for k,v in CODE_SHA256.items() if k.startswith('sim/')},
            'simulator':simulator_identity()}


def write_json(path, value):
    """Atomic individual file replacement inside a private library generation."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name('.'+path.name+'.next')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)


def _slew(time, voltage, before, after, start, end):
    """Last directional 10/90%-of-ideal-step crossings; null for no level change."""
    if before==after:return None
    direction=1 if after>before else -1
    mask=(time>=start)&(time<=end);t=time[mask];y=voltage[mask]
    times=[]
    for fraction in (.1,.9):
        threshold=5*(before+fraction*(after-before))
        z=direction*(y-threshold)
        edges=np.flatnonzero((z[:-1]<0)&(z[1:]>=0))
        if not len(edges):return None
        i=int(edges[-1]);times.append(float(t[i]+(t[i+1]-t[i])*(-z[i])/(z[i+1]-z[i])))
    return times[1]-times[0] if times[1]>=times[0] else None


def point(cell, text, load_f, ramp_s, folder, *, timeout=600., max_step_s=None):
    """One Euler-tour transient covers every directed input vector change once.

    A >=300 ns plateau after each ramp allows 1 pF loading to restore. A failure
    is retained as a failed/null sample, never converted into a passing delay.
    Timestep is recorded per ramp and is an upper bound (ngspice also adapts it).
    """
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    inputs=list(circuits()[cell].inputs);vectors=input_vectors(len(inputs),transitions=True)
    hold=ramp_s+300e-9
    step=max_step_s if max_step_s is not None else min(ramp_s/20,2e-9)
    bench=build_testbench(text,cell,inputs,['Y'],vectors,loads_f=load_f,
                          edge_s=ramp_s,hold_s=hold,step_s=step,nodeset=guesses(text),
                          initial_outputs={'Y':ideal(cell,vectors[0])})
    result={'cell':cell,'load_f':load_f,'input_transition_s':ramp_s,'hold_s':hold,
            'max_step_s':step,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'code_sha256':CODE_SHA256,'measurement_code':_measurement_code(),'model_sha256':MODEL_SHA256,
            'pdk_provenance':PDK_PROVENANCE,
            'complete':False,'rows':[]}
    try:
        run=run_ngspice(bench['netlist'],bench['commands'],bench['probes'],workdir=folder,timeout=timeout)
        data=run['data']
        if data['time'][-1]<len(vectors)*hold-step*1e-3:
            raise SimulationError('Transient ended before the complete tour')
        measured=measure_sequence(data,bench,lambda v:{'Y':ideal(cell,v)})
        for index,row in enumerate(measured['rows'][1:],1):
            before,after=vectors[index-1],vectors[index]
            y=row['outputs']['Y'];start=index*hold;end=(index+1)*hold
            result['rows'].append({'from':list(before),'to':list(after),
                'settling_s':y['settling_s'],'output_slew_10_90_s':_slew(data['time'],data['v(y)'],ideal(cell,before),ideal(cell,after),start,end),
                'error_v':y['error_v'],'passed':y['passed'] and y['settling_s'] is not None,
                'status':'ok' if y['passed'] and y['settling_s'] is not None else 'unsettled' if y['settling_s'] is None else 'level_error'})
        result['initial_state_passed']=measured['rows'][0]['passed']
        result['passed']=measured['passed'];result['complete']=True
        result['max_error_v']=measured['max_error_v']
        result['max_settling_s']=measured['max_settling_s']['Y']
    except SimulationError as exc:
        result.update(error=str(exc),passed=False)
        for before,after in zip(vectors,vectors[1:]):
            result['rows'].append({'from':list(before),'to':list(after),'settling_s':None,
                'output_slew_10_90_s':None,'error_v':None,'passed':False,'status':'simulation_error'})
    # Retain decks/logs/measurements; huge text waveforms are reproducible, not
    # duplicated across every table point. Fine-resolution evidence is separate.
    (folder/'waveform.txt').unlink(missing_ok=True)
    write_json(folder/'measurements.json',result)
    return result


def _axis(values,name):
    values=tuple(float(v) for v in values)
    if not values or any(not np.isfinite(v) or v<=0 for v in values) or list(values)!=sorted(set(values)):
        raise ValueError(f'{name} must be strictly increasing finite positive values')
    return values


def _grid_step(ramp_s,cell):
    """Coarsening is adopted only for the INV/NAND spot-checked fast ramps.

    NANY's simultaneous-input hazard timing is sensitive to the timestep; keep
    its original 50 ps ceiling for 1 ns edges, as for unvalidated NOR/BUF.
    """
    return min(max(ramp_s/20,.25e-9),2e-9) if cell in ('INV','NAND') else min(ramp_s/20,2e-9)


def assemble(cell,text,points,loads_f,ramps_s,capacitance,*,source_generation=None,model_sha256=None):
    """Build per-sensitization matrices in [ramp][load] order, with no interpolation."""
    circuit=circuits()[cell];inputs=list(circuit.inputs)
    kind='physical' if cell=='FILL' else 'constant' if not inputs else 'logic'
    report={'schema_version':1,'cell':cell,'inputs':inputs,'output':None if cell=='FILL' else 'Y',
            'kind':kind,'created_utc':datetime.now(timezone.utc).isoformat(),
            'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'source_generation':source_generation,
            'axes':{'load_f':list(loads_f),'input_transition_s':list(ramps_s)},
            'conditions':{'temperature_c':27.,'supplies_v':{'VDD':5.,'VMID':0.,'VSS':-5.},'band_v':PASS_BAND,
                'input_ramp_definition':'Full 0–100% linear voltage ramp; synchronized when multiple inputs change.',
                'delay_reference':'Input edge START; final entry into ideal +/-0.5 V band, staying through observation end.',
                'hold_s_by_ramp':[r+300e-9 for r in ramps_s],
                'max_step_s_by_ramp':[_grid_step(r,cell) for r in ramps_s],
                'output_slew_definition':'Last directional 10% to 90% crossings of the ideal output step; null for unchanged output or missing crossings.'},
            'scope':'Nominal device-only PDK extraction; no cell wire C or poly R in the primary timing model. Add PNR net wire C separately; do not double count cell-pin metal.',
            'model_sha256':model_sha256 or {},'code_sha256':CODE_SHA256,'pdk_provenance':PDK_PROVENANCE,
            'input_capacitance':capacitance,'arcs':[],'simultaneous':[],
            'interpolation':'Only within both measured axes and through passing/non-null samples. No implicit extrapolation.',
            'complete':True,'passed':True}
    if kind!='logic':
        if kind=='constant':report['constant_trit']=ideal(cell,())
        report['coverage']={'directed_vector_transitions':0,'single_pin_arcs':0,'simultaneous_transitions':0,'measured_grid_points':0}
        return report
    expected=len(loads_f)*len(ramps_s)
    if len(points)!=expected:raise ValueError(f'{cell}: incomplete load/ramp surface')
    indexed={(float(p['input_transition_s']),float(p['load_f'])):p for p in points}
    report['runs']=[{k:p[k] for k in ('load_f','input_transition_s','hold_s','max_step_s',
                                     'complete','passed','measurement_code')} for p in sorted(points,key=lambda p:(p['input_transition_s'],p['load_f']))]
    if len(indexed)!=expected:raise ValueError('Duplicate load/ramp condition')
    vectors=input_vectors(len(inputs),transitions=True)
    transitions=sorted(set((tuple(a),tuple(b)) for a,b in zip(vectors,vectors[1:])))
    lookup={key:{(tuple(row['from']),tuple(row['to'])):row for row in p['rows']} for key,p in indexed.items()}
    for number,(before,after) in enumerate(transitions):
        changed=[p for p,a,b in zip(inputs,before,after) if a!=b]
        pin=changed[0] if len(changed)==1 else None
        arc={'id':f'{cell}:{number:02d}','input_pin':pin,'output_pin':'Y',
             'from_inputs':dict(zip(inputs,before)),'to_inputs':dict(zip(inputs,after)),
             'changed_inputs':changed,'side_inputs':{p:a for p,a,b in zip(inputs,before,after) if a==b},
             'input_from':before[inputs.index(pin)] if pin else None,
             'input_to':after[inputs.index(pin)] if pin else None,
             'output_from':ideal(cell,before),'output_to':ideal(cell,after)}
        for field in ('settling_s','output_slew_10_90_s','passed','status','error_v'):
            arc[field]=[[lookup[(r,load)][(before,after)][field] for load in loads_f] for r in ramps_s]
        report['arcs' if pin else 'simultaneous'].append(arc)
    report['complete']=all(p['complete'] for p in points)
    report['passed']=all(p['passed'] for p in points)
    report['coverage']={'directed_vector_transitions':len(transitions),'single_pin_arcs':len(report['arcs']),
                        'simultaneous_transitions':len(report['simultaneous']),'measured_grid_points':expected,
                        'output_transition_classes':sorted({f'{a["output_from"]}->{a["output_to"]}' for a in report['arcs']})}
    report['max_settling_s']=max((p.get('max_settling_s') or 0 for p in points),default=0)
    report['failures']=[{'input_transition_s':p['input_transition_s'],'load_f':p['load_f'],
                         'rows':[r for r in p['rows'] if not r['passed']],
                         'error':p.get('error')} for p in points if not p['passed']]
    return report


def characterize_library(out,*,loads_f=LOADS_F,ramps_s=RAMPS_S,jobs=3):
    """Create all nine timing files in a private generation via SIM's public API."""
    out=Path(out).resolve()
    if out==(CELLS_DIR/'out').resolve():raise ValueError('Use publish_timing for live output')
    loads_f=_axis(loads_f,'loads_f');ramps_s=_axis(ramps_s,'ramps_s')
    if jobs<1:raise ValueError('jobs must be positive')
    generation=json.loads((out/'generation.json').read_text()) if (out/'generation.json').exists() else None
    models={p.name:sha(p) for p in sorted((PDK_ROOT/'libs.tech/spice/models').iterdir()) if p.is_file()}
    texts={name:(out/name/f'{name}.ext.spice').read_text() for name in circuits()}
    points={name:[] for name in texts};tasks=[]
    for cell,circuit in circuits().items():
        if not circuit.inputs:continue
        for ri,ramp in enumerate(ramps_s):
            for li,load in enumerate(loads_f):
                folder=out/cell/'timing'/f'ramp_{ri:02d}_load_{li:02d}'
                cached=folder/'measurements.json'
                if cached.exists():
                    p=json.loads(cached.read_text())
                    if (p['source_sha256']==hashlib.sha256(texts[cell].encode()).hexdigest()
                        and p.get('compatible_measurement_code',p.get('measurement_code'))==_measurement_code() and p.get('model_sha256')==models
                        and p.get('pdk_provenance',{}).get('consumed_sha256')==PDK_PROVENANCE['consumed_sha256']
                        and p['load_f']==load and p['input_transition_s']==ramp
                        and p['max_step_s']<=_grid_step(ramp,cell) and p['hold_s']==ramp+300e-9 and p['complete']):
                        points[cell].append(p);continue
                tasks.append((cell,texts[cell],load,ramp,folder))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        pending={pool.submit(point,*task,max_step_s=_grid_step(task[3],task[0])):task for task in tasks}
        for future in as_completed(pending):
            p=future.result();points[p['cell']].append(p)
            print(f'{p["cell"]} load={p["load_f"]*1e15:g} fF ramp={p["input_transition_s"]*1e9:g} ns: {"PASS" if p["passed"] else "FAIL"}',flush=True)
    reports={}
    for cell,circuit in circuits().items():
        inputs=list(circuit.inputs)
        cap=input_capacitance(texts[cell],cell,inputs,['Y'],input_vectors(len(inputs)),
                lambda v,c=cell:{'Y':ideal(c,v)},nodeset=guesses(texts[cell])) if inputs else []
        capacitance={'method':'Biased unloaded-output AC driving-point C from SIM public input_capacitance; no added cell wire C.',
                     'frequency_hz':1e6,'rows':cap,
                     'per_pin':{pin:{'min_f':min(r['capacitance_f'] for r in cap if r['pin']==pin),
                                     'max_f':max(r['capacitance_f'] for r in cap if r['pin']==pin)} for pin in inputs}}
        report=assemble(cell,texts[cell],points[cell],loads_f,ramps_s,capacitance,source_generation=generation,model_sha256=models)
        write_json(out/cell/f'{cell}.timing.json',report);reports[cell]=report
    summary={'created_utc':datetime.now(timezone.utc).isoformat(),'source_generation':generation,
             'complete':all(r['complete'] for r in reports.values()),'passed':all(r['passed'] for r in reports.values()),
             'cells':{c:{'complete':r['complete'],'passed':r['passed'],'coverage':r['coverage'],
                         'timing_sha256':sha(out/c/f'{c}.timing.json'),'source_sha256':r['source_sha256']} for c,r in reports.items()}}
    write_json(out/'timing_report.json',summary)
    return summary


def publish_timing(*,jobs=3):
    """Snapshot live cells; characterize privately; atomically publish all tables."""
    from .publish import publish
    live=CELLS_DIR/'out';source=(live/'generation.json').read_bytes()
    stage=Path(tempfile.mkdtemp(prefix='.cells-timing-',dir=CELLS_DIR))
    shutil.copytree(live,stage,dirs_exist_ok=True)
    if (live/'generation.json').read_bytes()!=source:raise RuntimeError('Library changed during snapshot')
    summary=characterize_all(stage,jobs=jobs)
    if not summary['complete']:raise RuntimeError(f'Incomplete timing run retained at {stage}')
    if (live/'generation.json').read_bytes()!=source:raise RuntimeError(f'Library changed; results retained at {stage}')
    for path in live.glob('*/*.char.json'):(stage/path.relative_to(live)).write_bytes(path.read_bytes())
    if (live/'sizing').exists():
        if (stage/'sizing').exists():shutil.rmtree(stage/'sizing')
        shutil.copytree(live/'sizing',stage/'sizing')
    generation=publish(stage,reason='Phase 6 measured load/ramp timing tables; physical cell views unchanged')
    shutil.rmtree(stage)
    return summary,generation


def characterize_all(out,*,jobs=3,include_poly=True):
    """Complete reproducible producer: primary STA surface plus poly-R sensitivity."""
    summary=characterize_library(out,jobs=jobs)
    if include_poly:
        from .poly import characterize_sensitivity,finalize_sensitivity
        characterize_sensitivity(out,jobs=max(1,min(jobs,2)))
        values=finalize_sensitivity(out)
        summary['primary_complete']=summary['complete']
        summary['primary_passed']=summary['passed']
        summary['poly_sensitivity_complete']=all(r['complete'] for r in values.values())
        summary['poly_sensitivity_passed']=all(r['passed'] for r in values.values())
        summary['complete'] &= summary['poly_sensitivity_complete']
        summary['passed'] &= summary['poly_sensitivity_passed']
        for cell in summary['cells']:
            summary['cells'][cell]['timing_sha256']=sha(Path(out)/cell/f'{cell}.timing.json')
        write_json(Path(out)/'timing_report.json',summary)
    return summary


def finalize_retained(out,*,allow_legacy_fingerprint=False):
    """Reassemble exact retained measurements, repairing interrupted run artifacts.

    The explicit legacy option is for this producer's audited nominal-compatible
    SIM/PDK migration only. Original producer fingerprints remain recorded; compatibility
    metadata never changes a measured voltage/delay. Public SIM/model/source and
    numerical settings are checked before accepting any retained sample.
    """
    import re
    out=Path(out).resolve()
    if out==(CELLS_DIR/'out').resolve():raise ValueError('Finalize only in a private stage')
    audit_path=out/'timing_compatibility/compatibility_audit.json'
    audit=json.loads(audit_path.read_text()) if audit_path.exists() else {}
    audited=(audit.get('settling_time_AST_identical') and audit.get('nominal_measurement_common_fields_identical')
             and not audit.get('mismatches'))
    reports={}
    for cell,circuit in circuits().items():
        path=out/cell/f'{cell}.timing.json';previous=json.loads(path.read_text())
        text=(out/cell/f'{cell}.ext.spice').read_text();digest=hashlib.sha256(text.encode()).hexdigest()
        loads=previous['axes']['load_f'];ramps=previous['axes']['input_transition_s'];points=[]
        if circuit.inputs:
            for ri,ramp in enumerate(ramps):
                for li,load in enumerate(loads):
                    folder=out/cell/'timing'/f'ramp_{ri:02d}_load_{li:02d}'
                    p=json.loads((folder/'measurements.json').read_text())
                    command=re.search(r'(?m)^tran\s+(\S+)\s+(\S+)',(folder/'tb.spice').read_text())
                    physics=(p['source_sha256']==digest and p.get('model_sha256')==MODEL_SHA256
                             and p['load_f']==load and p['input_transition_s']==ramp
                             and p['hold_s']==ramp+300e-9 and p['max_step_s']<=_grid_step(ramp,cell))
                    code=p.get('compatible_measurement_code',p.get('measurement_code'))==_measurement_code()
                    record=audit.get('records',{}).get(str((folder/'measurements.json').relative_to(out)),{})
                    compatibility=(audited and record.get('measurement_sha256')==sha(folder/'measurements.json')
                                   and record.get('deck_sha256')==sha(folder/'tb.spice'))
                    legacy=(allow_legacy_fingerprint and (p['measurement_code']['sim_source']==_measurement_code()['sim_source'] or compatibility))
                    deck=(command is not None and abs(float(command[1])-p['max_step_s'])<1e-20)
                    if not (physics and (code or legacy) and deck and p['complete']):
                        shutil.copyfile(folder/'measurements.json',folder/'measurements.pre-repair.json')
                        p=point(cell,text,load,ramp,folder,max_step_s=_grid_step(ramp,cell))
                    elif not code:
                        p['compatible_measurement_code']=_measurement_code()
                        p['compatibility_reason']='Audited nominal circuit/model equivalence and unchanged settling calculation across SIM/name/supply/PDK-path updates; original at-run fingerprint retained. See timing_compatibility/compatibility_audit.json.'
                    p['deck_sha256']=sha(folder/'tb.spice')
                    write_json(folder/'measurements.json',p);points.append(p)
        inputs=list(circuit.inputs)
        cap=input_capacitance(text,cell,inputs,['Y'],input_vectors(len(inputs)),
                lambda v,c=cell:{'Y':ideal(c,v)},nodeset=guesses(text)) if inputs else []
        capacitance={'method':'Biased unloaded-output AC driving-point C from current SIM public input_capacitance; no added cell wire C.',
                     'frequency_hz':1e6,'rows':cap,
                     'per_pin':{pin:{'min_f':min(r['capacitance_f'] for r in cap if r['pin']==pin),
                                     'max_f':max(r['capacitance_f'] for r in cap if r['pin']==pin)} for pin in inputs}}
        report=assemble(cell,text,points,loads,ramps,capacitance,
                        source_generation=previous.get('source_generation'),model_sha256=MODEL_SHA256)
        write_json(path,report);reports[cell]=report
    summary={'created_utc':datetime.now(timezone.utc).isoformat(),
             'complete':all(r['complete'] for r in reports.values()),'passed':all(r['passed'] for r in reports.values()),
             'cells':{c:{'complete':r['complete'],'passed':r['passed'],'coverage':r['coverage'],
                         'timing_sha256':sha(out/c/f'{c}.timing.json'),'source_sha256':r['source_sha256']} for c,r in reports.items()}}
    write_json(out/'timing_report.json',summary)
    return summary
