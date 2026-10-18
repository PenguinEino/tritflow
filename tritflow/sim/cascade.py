"""Measure real input loading and error propagation through repeated ternary cells."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from tritflow import CELLS_DIR
from .bench import simulate, input_vectors
from .characterize import logic_value
from .spice import CELL_PINS, subcircuits

NEUTRAL = {'NAND':1, 'NOR':-1, 'NANY':0}
REFERENCE_SEQUENCE = [(-1,), (0,), (1,), (0,), (-1,), (1,), (-1,)]


def cascade_bench(cell, subckts, *, depth=5, fanout=None, driven_pin='A', bias=None, model=None):
    """Return wrapper text, formal pins, ideal oracle for chain or fanout loading.

    A chain propagates through five cells; for binary cells the other input is
    neutral so each receiver acts as an inverter. A fanout driver drives one
    specified pin of N identical receivers; their other pin is biased explicitly.
    Every receiver output gets 10 fF; the driver's only load is actual gate inputs.
    """
    if cell not in ('INV','BUF','NAND','NOR','NANY') or depth < 1 or (fanout is not None and fanout < 1):
        raise ValueError('Choose a logic cell, positive depth and positive fanout')
    pins = list(CELL_PINS[cell][:-1])
    if driven_pin not in pins:
        raise ValueError(f'{cell} has no input {driven_pin}')
    bias = NEUTRAL.get(cell,0) if bias is None else bias
    if bias not in (-1,0,1): raise ValueError('Receiver bias must be a trit')
    count = depth if fanout is None else fanout+1
    outputs = [f'y{i}' for i in range(count)]
    lines = ['.subckt CASCADE ' + ' '.join(pins+outputs+['VDD','VMID','VSS']),
             f'Vbias bias 0 {bias*5}']
    for k in range(count):
        source = 'y0' if fanout is not None else f'y{k-1}'
        arguments = pins if k==0 else [source if p==driven_pin else 'bias' for p in pins]
        lines.append(f'Xstage{k} ' + ' '.join(arguments+[outputs[k],'VDD','VMID','VSS',model or cell]))
    lines.append('.ends CASCADE')
    def expected(vector):
        values = {outputs[0]:logic_value(cell,vector)}
        for k in range(1,count):
            previous = values['y0' if fanout is not None else outputs[k-1]]
            values[outputs[k]] = logic_value(cell,[previous if p==driven_pin else bias for p in pins])
        return values
    loads = {pin:10e-15 if fanout is not None or k==count-1 else 0 for k,pin in enumerate(outputs)}
    if fanout is not None: loads['y0']=0
    return '\n'.join(lines)+'\n'+subckts, pins, outputs, expected, loads


def characterize_cascade(cell, subckts=None, *, fanouts=(1,2,4,8), hold_s=200e-9,
                         step_s=.5e-9, workdir=None, destination=None, top=None, inputs=None, output="Y",
                         pdk=None, temperature_c=27, edge_s=1e-9):

    """All driver DC states plus six scalar transitions, receiver pin/bias sweeps.

    Max fanout requires driver AND every receiver to pass every stressed pin/bias
    case, and five-stage neutral-input chains to restore all tested levels.
    Fanout is bounded by the largest tested value, not extrapolated from input C.
    """
    if subckts is None: subckts=(CELLS_DIR/'out'/cell/f'{cell}.ext.spice').read_text()
    original_source = subckts
    model = cell
    if top is not None or inputs is not None or output != 'Y':
        definition = subcircuits(subckts)[(top or cell).lower()]
        canonical = list(CELL_PINS[cell][:-1])
        mapping = dict(zip([p.lower() for p in (inputs or canonical)], canonical))
        mapping.update({output.lower():'Y', 'vdd':'VDD', 'vmid':'VMID', 'vss':'VSS'})
        adapter = '.subckt SIM_CELL ' + ' '.join(list(CELL_PINS[cell])+['VDD','VMID','VSS']) + '\n'
        adapter += 'Xsrc ' + ' '.join(mapping[p.lower()] for p in definition['pins']) + ' ' + (top or cell) + '\n.ends SIM_CELL\n'
        subckts = adapter + subckts
        model = 'SIM_CELL'
    fanouts = sorted(set(fanouts))
    if not fanouts or fanouts[0] < 1: raise ValueError('Fanouts must be positive')
    pins = list(CELL_PINS[cell][:-1])
    neutral = NEUTRAL.get(cell,0)
    vectors = [tuple(v[0] if p=='A' else neutral for p in pins) for v in REFERENCE_SEQUENCE]
    vectors += [v for v in input_vectors(len(pins)) if v not in vectors]
    work = Path(workdir) if workdir else None
    cases=[]
    for driven in pins:
        settings=[('chain',None,neutral)]
        settings += [('fanout',n,bias) for n in fanouts for bias in ((-1,0,1) if len(pins)==2 else (0,))]
        for mode,n,bias in settings:
            circuit,inputs,outputs,expected,loads=cascade_bench(cell,subckts,fanout=n,driven_pin=driven,bias=bias,model=model)
            label=f'{mode}_{driven}_n{n or 5}_b{bias}'
            result=simulate(circuit,'CASCADE',inputs,outputs,vectors,expected,loads_f=loads,
                            hold_s=hold_s,step_s=step_s,edge_s=edge_s,pdk=pdk,temperature_c=temperature_c,timeout=300,
                            workdir=work/label if work else None)
            measured=result['measurements']
            cases.append({'mode':mode,'driven_pin':driven,'fanout':n,'receiver_bias_trit':bias,
                          'depth':5 if n is None else 2,**measured})
            if work:
                (work/label/'measurements.json').write_text(json.dumps(measured,indent=2)+'\n')
    chains_pass=all(c['passed'] for c in cases if c['mode']=='chain')
    passing=[]
    for n in fanouts:
        if chains_pass and all(c['passed'] for c in cases if c['mode']=='fanout' and c['fanout']<=n):
            passing.append(n)
    report={'schema_version':1,'cell':cell,'source_sha256':hashlib.sha256(original_source.encode()).hexdigest(),
            'hold_s':hold_s,'edge_s':edge_s,'step_s':step_s,'temperature_c':temperature_c,'input_vectors':[list(v) for v in vectors],
            'fanouts_tested':fanouts,'chain_depth':5,'chains_passed':chains_pass,
            'suggested_max':max(passing,default=0),'passed':all(c['passed'] for c in cases),'cases':cases,
            'method':'measured self-loading; every receiver pin and other-input trit bias; five-stage chains',
            'scope':'nominal 27 C, ideal rails, 10 fF per receiver/final output; no interconnect RC or PVT'}
    if destination:
        p=Path(destination);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


def replay_reference(folder=Path.home()/'balanced-ternary-logic/simulation/cascade', *, workdir=None):
    """Replay the saved RR20 two-inverter reference without importing its scripts."""
    folder=Path(folder)
    source=folder/'inverter_chain_tb.spice'
    raw=source.read_text();definition=subcircuits(raw)['inverter']['text']
    adapter='.subckt INV A Y VDD VMID VSS\nXref A Y VDD VSS inverter\n.ends INV\n'+definition
    circuit,inputs,outputs,expected,loads=cascade_bench('INV',adapter,depth=2)
    result=simulate(circuit,'CASCADE',inputs,outputs,REFERENCE_SEQUENCE,expected,
                    hold_s=20e-9,step_s=.05e-9,loads_f=loads,workdir=workdir)
    saved=np.loadtxt(folder/'inverter_chain_tran.txt')
    differences=[]
    for end in np.arange(1,8)*20e-9-1e-9:
        differences.append(abs(float(np.interp(end,result['waveforms']['time'],result['waveforms']['v(y1)']))
                               -float(np.interp(end,saved[:,0],saved[:,5]))))
    return {'source':str(source),'source_sha256':hashlib.sha256(raw.encode()).hexdigest(),
            'resistor_length_um':20,'hold_s':20e-9,'saved_waveform_max_checkpoint_difference_v':max(differences),
            'measurements':result['measurements'],'passed':result['measurements']['passed'] and max(differences)<.01}


def attach_cascade(characterization, cascade):
    """Replace the capacitance heuristic with a measured, bounded fanout result."""
    if characterization['source_sha256'] != cascade['source_sha256']:
        raise ValueError('Cascade and isolated-cell measurements use different netlists')
    old = characterization.get('fanout', {})
    characterization['cascade'] = cascade
    characterization['fanout'] = {
        'suggested_max':cascade['suggested_max'], 'tested_counts':cascade['fanouts_tested'],
        'capacitance_estimate_max':old.get('capacitance_estimate_max',old.get('suggested_max')),
        'method':cascade['method'], 'scope':cascade['scope'], 'chain_depth':5}
    isolated_passed=all(r['passed'] for r in characterization.get('dc',[])) and all(r['passed'] for r in characterization.get('transient',[]))
    characterization['passed'] = isolated_passed and cascade['chains_passed'] and cascade['suggested_max'] >= 1
    return characterization


def main():
    import argparse
    from .characterize import characterize_cell
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cells',nargs='+',default=['INV','BUF','NANY','NAND','NOR'])
    parser.add_argument('--fanouts',nargs='+',type=int,default=[1,2,4,8])
    parser.add_argument('--out',type=Path,default=Path('build/cascade'))
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    reference=replay_reference(workdir=args.out/'reference_rr20')
    (args.out/'reference.json').write_text(json.dumps(reference,indent=2)+'\n')
    passed=reference['passed']
    for cell in args.cells:
        source=(CELLS_DIR/'out'/cell/f'{cell}.ext.spice').read_text()
        path=CELLS_DIR/'out'/cell/f'{cell}.char.json'
        isolated=json.loads(path.read_text()) if path.exists() else {}
        if isolated.get('source_sha256') != hashlib.sha256(source.encode()).hexdigest():
            isolated=characterize_cell(cell,source,include_cascade=False)
        report_path=args.out/f'{cell}.cascade.json'
        report=json.loads(report_path.read_text()) if report_path.exists() else {}
        if report.get('source_sha256')!=hashlib.sha256(source.encode()).hexdigest() or report.get('fanouts_tested')!=sorted(set(args.fanouts)):
            report=characterize_cascade(cell,source,fanouts=args.fanouts,workdir=args.out/cell,
                                       destination=report_path)
        if source != (CELLS_DIR/'out'/cell/f'{cell}.ext.spice').read_text():
            raise RuntimeError(f'{cell} changed during characterization; rerun')
        attach_cascade(isolated,report)
        path.write_text(json.dumps(isolated,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'cell':cell,'chains_passed':report['chains_passed'],'fanout':report['suggested_max']}),flush=True)
        passed=passed and isolated['passed']
    return 0 if passed else 1


if __name__=='__main__': raise SystemExit(main())
