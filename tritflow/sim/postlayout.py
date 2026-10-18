"""Close the GateNetlist -> real GDS -> extracted device+wire-C simulation loop."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import shutil
import numpy as np

from tritflow import CELLS_DIR, PDK_ROOT
from tritflow.netlist import GateNetlist
from tritflow.extract import extract_layout, gds_wire_capacitance, append_wire_capacitance, estimate_ir_drop
from .bench import simulate, input_vectors, build_testbench
from .spice import gate_spice
from .characterize import characterize_cell
from tritflow.extract.technology import parameter_audit
from .provenance import pdk_provenance


def _save(path, data):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _device_fingerprint(text):
    """Hash all SPICE content except comments and the added Ctfwire elements."""
    rows=[]
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('*') or re.match(r'(?i)^Ctfwire\d+\b',line):continue
        rows.append(' '.join(line.split()).upper())
    return hashlib.sha256('\n'.join(rows).encode()).hexdigest()


def representative_vectors(design, inputs):
    """Independent arithmetic cases; adder4 includes both four-digit carry chains."""
    if design in ('full_add','mul1','mac1'):
        vectors=input_vectors(len(inputs))
        return vectors, [f'exhaustive_{i}' for i in range(len(vectors))]
    if design != 'adder4': raise ValueError(f'No documented vector plan for {design}')
    cases=[]
    def add(label,a,b,cin):
        values={f'a[{i}]':a[i] for i in range(4)}|{f'b[{i}]':b[i] for i in range(4)}|{'cin':cin}
        cases.append((label,tuple(values[p] for p in inputs)))
    z=[0]*4
    add('zero',z,z,0)
    add('positive_propagate_setup',[1]*4,z,0)
    add('positive_carry_through_all_four_digits',[1]*4,z,1)
    add('positive_carry_release_through_all_four_digits',[1]*4,z,0)
    add('negative_propagate_setup',[-1]*4,z,0)
    add('negative_carry_through_all_four_digits',[-1]*4,z,-1)
    add('negative_carry_release_through_all_four_digits',[-1]*4,z,0)
    add('positive_overflow',[1]*4,[1]*4,1)
    add('negative_overflow',[-1]*4,[-1]*4,-1)
    add('opposite_operands',[1]*4,[-1]*4,0)
    add('alternating',[1,-1,1,-1],[-1,1,-1,1],1)
    add('alternating_reverse',[-1,1,-1,1],[1,-1,1,-1],-1)
    for i in range(4):
        a=z.copy();a[i]=1
        add(f'positive_digit_{i}',a,z,0)
        a[i]=-1;add(f'negative_digit_{i}',z,a,0)
    return [v for _,v in cases],[label for label,_ in cases]


def arithmetic_oracle(design, inputs):
    """Use radix arithmetic/min/max, independent of mapped cell connectivity."""
    def expected(vector):
        values=dict(zip(inputs,vector))
        if design=='mul1': return {'p':values['a']*values['b']}
        if design=='adder4':
            carry=values['cin'];out={}
            for i in range(4):
                total=values[f'a[{i}]']+values[f'b[{i}]']+carry
                carry=(total+1)//3;out[f'sum[{i}]']=total-3*carry
            return out|{'cout':carry}
        total=(values['x']+values['a']*values['b']+values['cin'] if design=='mac1'
               else values['a']+values['b']+values['cin'])
        carry=(total+1)//3
        out={'sum':total-3*carry,'cout':carry}
        if design=='mac1': out|={'and_out':min(values['a'],values['b']),'or_out':max(values['a'],values['b'])}
        return out
    return expected


def layout_matches_library(gds, cells, root=CELLS_DIR):
    """Compare embedded masters to current cell polygons, including compacted metal."""
    import klayout.db as db
    placed=db.Layout();placed.read(str(gds))
    for name in cells:
        reference=db.Layout();reference.read(str(Path(root)/'out'/name/f'{name}.gds'))
        a,b=placed.cell(name),reference.cell(name)
        if a is None or b is None: return False
        layers={(i.layer,i.datatype) for i in placed.layer_infos()}|{(i.layer,i.datatype) for i in reference.layer_infos()}
        for layer in layers:
            ar=db.Region(a.begin_shapes_rec(placed.layer(*layer)))
            br=db.Region(b.begin_shapes_rec(reference.layer(*layer)))
            if not (ar^br).is_empty(): return False
    return True


def _delay_comparison(pre,post,outputs):
    transitions=[]
    for k,(a,b) in enumerate(zip(pre['rows'][1:],post['rows'][1:]),1):
        delta={}
        for pin in outputs:
            before,after=a['outputs'][pin]['settling_s'],b['outputs'][pin]['settling_s']
            delta[pin]=None if before is None or after is None else after-before
        transitions.append({'segment':k,'input_trits':b['input_trits'],'settling_difference_s':delta})
    return {'pre_max_settling_s':pre['max_settling_s'],'post_max_settling_s':post['max_settling_s'],
            'max_transition_increase_s':{p:max((r['settling_difference_s'][p] for r in transitions
                    if r['settling_difference_s'][p] is not None),default=None) for p in outputs},
            'transitions':transitions}


def _simulate_cached(out, mode, *args, **kwargs):
    """Serialize writes to one waveform cache when preparation overlaps PNR arrival."""
    import fcntl
    folder=Path(out)/mode;folder.mkdir(parents=True,exist_ok=True)
    with (folder/'simulation.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        return _simulate_cached_unlocked(Path(out),mode,*args,**kwargs)


def prepare_prelayout(directory, *, cells_root=CELLS_DIR, hold_s=500e-9, step_s=2e-9,
                      load_f=10e-15, timeout=600):
    """Run independent arithmetic checks while waiting for physical artifacts."""
    directory=Path(directory).resolve();design=directory.name
    net=GateNetlist.load(directory/f'{design}.json')
    used=sorted({i.cell for i in net.instances})
    text=gate_spice(net,'\n'.join((Path(cells_root)/'out'/c/f'{c}.spice').read_text() for c in used))
    inputs=[p.name for p in net.ports if p.dir=='input'];outputs=[p.name for p in net.ports if p.dir=='output']
    vectors,_=representative_vectors(design,inputs);expected=arithmetic_oracle(design,inputs)
    return _simulate_cached(directory/'postlayout','pre',text,net.top,inputs,outputs,vectors,expected,
                            hold_s=hold_s,step_s=step_s,load_f=load_f,timeout=timeout)


def _simulate_cached_unlocked(out, mode, circuit, top, inputs, outputs, vectors, expected, *,
                     hold_s, step_s, load_f, timeout, temperature_c=27, supplies_v=None,nodeset=None):
    """Reuse a completed identical electrical experiment when only metadata changed."""
    folder=out/mode;folder.mkdir(exist_ok=True)
    configuration={'circuit':circuit,'top':top,'inputs':inputs,'outputs':outputs,
                   'vectors':vectors,'expected':[expected(v) for v in vectors],
                   'hold_s':hold_s,'step_s':step_s,'load_f':load_f,
                   'analysis_sha256':{name:file_hash(Path(__file__).with_name(name))
                       for name in ('bench.py','runner.py','measure.py','spice.py')},
                   'pdk_root':str(PDK_ROOT.resolve()),
                   'models':{p.name:file_hash(p) for p in sorted((PDK_ROOT/'libs.tech/spice/models').iterdir()) if p.is_file()}}
    options={}
    if temperature_c!=27:options['temperature_c']=temperature_c
    if supplies_v is not None:options['supplies_v']=supplies_v
    if nodeset is not None:options['nodeset']=nodeset
    configuration.update(options)
    digest=hashlib.sha256(json.dumps(configuration,sort_keys=True).encode()).hexdigest()
    manifest=folder/'simulation.json'
    if all((folder/name).is_file() for name in ('simulation.json','waveforms.npz','measurements.json')) and json.loads(manifest.read_text()).get('sha256')==digest:
        with np.load(folder/'waveforms.npz') as data: waveforms={k:data[k] for k in data.files}
        bench=build_testbench(circuit,top,inputs,outputs,vectors,hold_s=hold_s,step_s=step_s,loads_f=load_f,
                              initial_outputs=expected(vectors[0]),**options)
        from .measure import measure_sequence
        measured=measure_sequence(waveforms,bench,expected)
        _save(folder/'measurements.json',measured)
        return {'waveforms':waveforms,'stimulus':bench,'measurements':measured,'cached':True}
    result=simulate(circuit,top,inputs,outputs,vectors,expected,hold_s=hold_s,step_s=step_s,
                    loads_f=load_f,timeout=timeout,workdir=folder,**options)
    _save(folder/'measurements.json',result['measurements'])
    np.savez_compressed(folder/'waveforms.npz',**result['waveforms'])
    _save(manifest,{'sha256':digest})
    return result


def _run_postlayout(directory, *, cells_root=CELLS_DIR, hold_s=500e-9, step_s=2e-9,
                   load_f=10e-15, timeout=600, refresh_characterization=True, plots=True,
                   vectors=None, labels=None, expected=None):
    """Validate current PNR files, snapshot sources, LVS, wire C, pre/post and IR.

    The build directory basename is the example name; JSON top is authoritative.
    Every input/library hash is checked again at completion. Stale layouts or
    inputs changed during a run raise instead of publishing an up-to-date PASS.
    """
    directory=Path(directory).resolve();design=directory.name;root=Path(cells_root).resolve()
    out=directory/'postlayout';out.mkdir(parents=True,exist_ok=True)
    _save(out/'summary.json',{'passed':False,'state':'running','design':design})
    netfile=directory/f'{design}.json';net=GateNetlist.load(netfile)
    gds=directory/f'{net.top}.gds';pnrfile=directory/f'{net.top}.pnr.json'
    used=sorted({i.cell for i in net.instances})
    if not gds.is_file() or not pnrfile.is_file(): raise FileNotFoundError(f'PNR must publish {gds} and {pnrfile}')
    if not layout_matches_library(gds,used,root):
        raise RuntimeError('PNR GDS embeds a different cell revision; rerun PNR with current cells/out')
    for cell in used:
        source=root/'out'/cell/f'{cell}.ext.spice';char=root/'out'/cell/f'{cell}.char.json'
        if not char.is_file() or json.loads(char.read_text()).get('source_sha256')!=file_hash(source):
            if not refresh_characterization: raise RuntimeError(f'{cell} characterization is stale')
            characterize_cell(cell,source.read_text(),destination=char)
    paths=[netfile,gds,pnrfile,root/'template.json']
    paths += [p for p in sorted((PDK_ROOT/'openIP62/IP62/Technology/doc').glob('*.pdf')) if p.is_file()]
    paths += [p for p in sorted((PDK_ROOT/'libs.tech/spice/models').glob('*')) if p.is_file()]
    paths += [p for p in sorted((PDK_ROOT/'libs.tech/klayout/tech/lvs').rglob('*')) if p.is_file()]
    for cell in used:
        paths += [root/'out'/cell/f'{cell}{ext}' for ext in ('.gds','.spice','.ext.spice','.abstract.json','.char.json')]
    hashes={str(p):file_hash(p) for p in paths}
    inputs_snapshot=out/'inputs';inputs_snapshot.mkdir(exist_ok=True)
    for source in (netfile,gds,pnrfile):
        target=inputs_snapshot/source.name;shutil.copyfile(source,target)
        if file_hash(target)!=hashes[str(source)]:
            raise RuntimeError(f'Input changed during snapshot: {source}')
    snapshot=out/'library';snapshot.mkdir(exist_ok=True)
    for p in paths:
        if p.parent.name in used:
            target=snapshot/p.parent.name;target.mkdir(exist_ok=True);shutil.copyfile(p,target/p.name)
            if file_hash(target/p.name)!=hashes[str(p)]: raise RuntimeError(f'Cell changed during snapshot: {p}')
    shutil.copyfile(root/'template.json',snapshot/'template.json')
    cell_text='\n'.join((snapshot/c/f'{c}.spice').read_text() for c in used)
    schematic_text=gate_spice(net,cell_text);(out/'schematic.spice').write_text(schematic_text)
    inputs=[p.name for p in net.ports if p.dir=='input'];outputs=[p.name for p in net.ports if p.dir=='output']
    custom_plan = vectors is not None
    if custom_plan:
        vectors = list(vectors)
        if expected is None or labels is None or len(labels) != len(vectors):
            raise ValueError('Custom vectors require matching labels and an independent expected function')
    else:
        vectors,labels=representative_vectors(design,inputs);expected=arithmetic_oracle(design,inputs)
    _save(out/'vectors.json',{'input_order':inputs,'labels':labels,'vectors':vectors,
          'expected':[expected(v) for v in vectors], 'coverage':('documented directed arithmetic cases' if custom_plan
              else 'all inputs' if design!='adder4' else '20 directed arithmetic cases; both four-digit ripple carries')})
    run_gds=inputs_snapshot/gds.name
    lvs=extract_layout(run_gds,net.top,out/'lvs',gate_netlist=net,cell_subckts=cell_text,timeout=timeout)
    _save(out/'lvs.json',lvs)
    if not lvs['matched']: raise RuntimeError(f'LVS mismatch: {lvs["errors"]}; see {out}/lvs.json')
    # Keep every intrinsic device, terminal assignment and junction parameter
    # identical. The source F_RR PLUS orientation differs from extraction and
    # changes where its one-ended intrinsic capacitance is connected.
    pre_text=Path(lvs['extracted']).read_text();(out/'prelayout.spice').write_text(pre_text)
    caps=gds_wire_capacitance(run_gds,lvs['report'],top=net.top);_save(out/'capacitance.json',caps)
    post_text=append_wire_capacitance(pre_text,net.top,caps)
    if _device_fingerprint(pre_text)!=_device_fingerprint(post_text):
        raise RuntimeError('Wire-C annotation changed intrinsic device content')
    (out/'postlayout.spice').write_text(post_text)
    results={}
    for mode,text in [('pre',pre_text),('post',post_text)]:
        results[mode]=_simulate_cached(out,mode,text,net.top,inputs,outputs,vectors,expected,
            hold_s=hold_s,step_s=step_s,load_f=load_f,timeout=timeout)
    chars={c:json.loads((snapshot/c/f'{c}.char.json').read_text()) for c in used}
    abstracts={c:json.loads((snapshot/c/f'{c}.abstract.json').read_text()) for c in used}
    pnr=json.loads((inputs_snapshot/pnrfile.name).read_text());template=json.loads((snapshot/'template.json').read_text())
    ir=estimate_ir_drop(pnr,template,abstracts,chars);_save(out/'ir_drop.json',ir)
    audit=parameter_audit();_save(out/'pdk_parameters.json',audit)
    if plots:
        from tritflow.viz.waves import waveform_figure
        waveform_figure(results['post'],pre=results['pre'],title=f'{design}: pre/post-layout').write_html(out/'waveforms.html')
    changed=[name for name,digest in hashes.items() if not Path(name).is_file() or file_hash(name)!=digest]
    unchanged=not changed
    summary={'schema_version':1,'design':design,'top':net.top,'input_sha256':hashes,
             'pdk_provenance':pdk_provenance(),
             'inputs_unchanged':unchanged,'changed_inputs':changed,'lvs_matched':lvs['matched'],'vector_count':len(vectors),
             'hold_s':hold_s,'step_s':step_s,'output_load_f':load_f,
             'comparison_scope':'Exact same GDS-extracted devices and terminal orientation: device-only (pre-wire) versus device+estimated wire C. Original GateNetlist schematic remains the independent LVS reference in schematic.spice.',
             'device_only_sha256':file_hash(out/'prelayout.spice'),
             'matched_device_fingerprint':_device_fingerprint(pre_text),
             'pre_passed':results['pre']['measurements']['passed'],
             'post_passed':results['post']['measurements']['passed'],
             'pre_max_error_v':results['pre']['measurements']['max_error_v'],
             'post_max_error_v':results['post']['measurements']['max_error_v'],
             'settling':_delay_comparison(results['pre']['measurements'],results['post']['measurements'],outputs),
             'max_rail_deviation_v':max(abs(v) for c in ir['cells'].values() for v in c['rail_deviation_v'].values()),
             'max_zero_shift_v':max((abs(c['zero_level_shift_v']) for c in ir['cells'].values() if c['zero_level_shift_v'] is not None),default=0),
             'interconnect_parameters':{'sheet_ohm_per_square':ir['sheet_ohm_per_square'],
                 'via_ohm':ir['via_ohm'],'wire_capacitance':caps['coefficients'],
                 'resistance_origin':ir['parameter_origin'],'capacitance_origin':caps['parameter_origin']},
             'em_check':ir['em_check'],'pdk_parameter_sources':audit['source_sha256'],
             'scope':caps['assumptions']+' '+ir['assumptions']}
    summary['passed']=unchanged and lvs['matched'] and summary['pre_passed'] and summary['post_passed']
    summary['state']='complete' if unchanged else 'stale'
    _save(out/'summary.json',summary)
    (out/'error.json').unlink(missing_ok=True)
    if not unchanged: raise RuntimeError('Inputs changed during post-layout run; rerun against the new PNR/library revision: '+', '.join(changed))
    return summary


def run_postlayout(directory, *, cells_root=CELLS_DIR, hold_s=500e-9, step_s=2e-9,
                   load_f=10e-15, timeout=600, refresh_characterization=True, plots=True,
                   vectors=None, labels=None, expected=None):
    """Serialize one design's extraction, snapshots, simulation and result publication."""
    import fcntl
    directory=Path(directory).resolve();out=directory/'postlayout';out.mkdir(parents=True,exist_ok=True)
    with (out/'.run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        return _run_postlayout(directory,cells_root=cells_root,hold_s=hold_s,step_s=step_s,
            load_f=load_f,timeout=timeout,refresh_characterization=refresh_characterization,plots=plots,
            vectors=vectors,labels=labels,expected=expected)
