"""Ported DC-neighborhood, transition, skew, and cascade checks.

Conditions follow check_nany.py/check_nany_extracted.py and the original
inverter_chain/nor_chain/mixed-chain benches. Use current RR30 extracted
networks rather than obsolete resistor values embedded in historical TBs.
"""
from pathlib import Path
from functools import lru_cache
import re

import numpy as np
from tritflow.sim.bench import build_testbench, input_vectors
from tritflow.sim.characterize import dc_operating_points
from tritflow.sim.measure import measure_sequence
from tritflow.sim.runner import run_ngspice
from tritflow.sim.spice import simulation_netlist
from .circuits import circuits, ideal


def guesses(text, instance='xdut'):
    """MOS connectivity supplies initial guesses, never forced ICs or devices."""
    values={}
    public={'A','B','Y','VDD','VMID','VSS'}
    for line in simulation_netlist(text).splitlines():
        t=line.split()
        if len(t)<6 or t[5] not in ('PMOS','NMOS'):continue
        voltage=5. if t[5]=='PMOS' else -5.
        for n in (t[1],t[3]):
            if n not in public:values.setdefault(n,set()).add(voltage)
    return {instance+'.'+n:(next(iter(v)) if len(v)==1 else 0.) for n,v in values.items()}


@lru_cache(maxsize=16)
def physical_initial_state(text, vector):
    """Solve a single NANY at the chain's initial bias to seed internal nodes.

    A main RR endpoint follows the output when its MOS stack is off; simply
    assigning every NMOS-side node -5 V is a poor deep-cascade starting point.
    The resulting .nodeset values guide Newton, without .ic/uic constraints.
    """
    seed=guesses(text)
    bench=build_testbench(text,'NANY',['A','B'],['Y'],[vector],loads_f=0,
                          nodeset=seed,initial_outputs={'Y':ideal('NANY',vector)})
    probes=[f'v({n})' for n in seed]
    data=run_ngspice(bench['netlist'],'op',bench['probes']+probes)['data']
    return {n.removeprefix('xdut.'):float(data[f'v({n})'][-1]) for n in seed}


def execute(bench, commands, folder, *, retain_samples=False):
    """Retain runnable decks/logs and compressed samples, avoiding huge text files."""
    folder=Path(folder)
    run=run_ngspice(bench['netlist'],commands,bench['probes'],workdir=folder,timeout=240)
    data=run['data']
    if retain_samples:np.savez_compressed(folder/'waveforms.npz',**data)
    (folder/'waveform.txt').unlink(missing_ok=True)
    return data


def grid(text, cell, folder):
    """81x81 input grid (81 for INV), plus all +/-0.5 V neighborhoods."""
    inputs=list(circuits()[cell].inputs)
    first=(-1,)*len(inputs)
    bench=build_testbench(text,cell,inputs,['Y'],[first],loads_f=10e-15,
                          initial_outputs={'Y':ideal(cell,first)},nodeset=guesses(text))
    command='dc Vin0 -5 5 0.125'+(' Vin1 -5 5 0.125' if len(inputs)==2 else '')
    data=execute(bench,command,folder,retain_samples=True)
    output=data['v(y)'];rows=[]
    for state in input_vectors(len(inputs)):
        dist=np.maximum.reduce([abs(data[f'v({p.lower()})']-5*v) for p,v in zip(inputs,state)])
        k=int(np.argmin(dist));target=5*ideal(cell,state)
        rows.append({'inputs':list(state),'output_v':float(output[k]),
                     'error_v':float(abs(output[k]-target)),
                     'half_volt_band_error_v':float(np.max(abs(output[dist<=.50001]-target)))})
    return {'passed':all(r['error_v']<=.5 and r['half_volt_band_error_v']<=.5 for r in rows),
            'points':len(output),'rows':rows,'max_error_v':max(r['error_v'] for r in rows),
            'max_half_volt_band_error_v':max(r['half_volt_band_error_v'] for r in rows)},data


def operating_points(text,cell):
    inputs=list(circuits()[cell].inputs)
    rows=dc_operating_points(text,cell,inputs,['Y'],input_vectors(len(inputs)),
                             lambda v:{'Y':ideal(cell,v)},nodeset=guesses(text))
    return {'passed':all(r['passed'] for r in rows),'rows':rows,
            'max_error_v':max(abs(r['error_v']['Y']) for r in rows),
            'max_static_current_a':max(abs(v) for r in rows for v in r['rail_current_a'].values())}


def transitions(text,cell,folder,*,load_f=10e-15,skew_input=None):
    """All directed transitions, 100 ns holds, 1 ns edges, 0.1 ns max steps.

    NANY's skew cases delay A or B by 2 ns. Delay is measured from the first
    edge start (the flow contract), which is 1+skew ns earlier than the legacy
    script's post-edge-start measurement. Checking endpoints is unchanged.
    """
    inputs=list(circuits()[cell].inputs)
    tour=input_vectors(len(inputs),transitions=True)
    bench=build_testbench(text,cell,inputs,['Y'],tour,hold_s=100e-9,edge_s=1e-9,
                          step_s=.1e-9,loads_f=load_f,nodeset=guesses(text),
                          initial_outputs={'Y':ideal(cell,tour[0])})
    if skew_input is not None:
        col=inputs.index(skew_input);points=[f'0 {5*tour[0][col]}']
        for k in range(1,len(tour)):
            t=k*bench['hold_s']+2e-9
            points.extend([f'{t:.15g} {5*tour[k-1][col]}',f'{t+1e-9:.15g} {5*tour[k][col]}'])
        bench['netlist']=re.sub(rf'(?m)^Vin{col} .*$',
                               f'Vin{col} {skew_input} 0 PWL('+ ' '.join(points)+')',bench['netlist'])
    data=execute(bench,bench['commands'],folder)
    result=measure_sequence(data,bench,lambda v:{'Y':ideal(cell,v)})
    result.update(transitions=len(tour)-1,load_f=load_f,skew_input=skew_input,
                  hold_s=100e-9,edge_s=1e-9,max_step_s=.1e-9)
    return result


VOLTAGE_SEQUENCE=[-5.,0.,5.,0.,-5.,5.,-5.,-1.,-.5,-.2,0.,.2,.5,1.,0.]


def chain_definition(texts,kind):
    """The original two-INV, six-NOR (A/B/tied), and six-stage mixed paths."""
    if kind=='inverter_two':paths=[('i',['INV']*2,'single')]
    elif kind=='nor_six':paths=[(p,['NOR']*6,p) for p in ('a','b','tied')]
    elif kind=='nany_six':paths=[(p,['NANY']*6,p) for p in ('a','b','tied')]
    elif kind=='mixed_six':paths=[('m',['INV','NAND','NOR','NANY','INV','NANY'],'mixed')]
    else:raise ValueError(kind)
    outputs=[];instances=[];nodeset={};stage_counts={}
    for path,types,mode in paths:
        previous='A'
        for i,cell in enumerate(types,1):
            out=f'{path}{i}';inst=f'stage_{path}{i}';outputs.append(out);stage_counts[out]=i
            if cell=='INV':ins=[previous]
            elif mode=='tied':ins=[previous,previous]
            else:
                fixed={'NAND':'VDD','NOR':'VSS','NANY':'VMID'}[cell]
                ins=[fixed,previous] if mode=='b' else [previous,fixed]
            instances.append(f'X{inst} '+' '.join(ins+[out,'VDD','VMID','VSS',cell]))
            seed=guesses(texts[cell],f'xdut.x{inst.lower()}')
            if cell=='NANY' and kind=='nany_six':
                variable=-1 if i%2 else 1
                vector=(variable,variable) if mode=='tied' else ((0,variable) if mode=='b' else (variable,0))
                physical=physical_initial_state(texts[cell],vector)
                seed={f'xdut.x{inst.lower()}.'+n:value for n,value in physical.items()}
            nodeset.update(seed)
            previous=out
    wrapper='\n.subckt CASCADE A '+' '.join(outputs)+' VDD VMID VSS\n'+'\n'.join(instances)+'\n.ends CASCADE\n'
    all_text=''.join(texts.values())+wrapper
    return all_text,outputs,stage_counts,nodeset


def chain(texts,kind,folder):
    """DC transfer and original cascade waveforms, including perturbed zeros."""
    text,outputs,stages,nodeset=chain_definition(texts,kind)
    # The legacy two-INV TB uses 20 ns holds and seven rail/zero states. The
    # six-stage chains use 200 ns holds and the original +/-1 V perturbations.
    sequence=VOLTAGE_SEQUENCE[:7] if kind=='inverter_two' else VOLTAGE_SEQUENCE
    vectors=[(0 if abs(v)<=1 else int(v/5),) for v in sequence]
    expected=lambda v:{p:v[0]*(-1)**stages[p] for p in outputs}
    bench=build_testbench(text,'CASCADE',['A'],outputs,vectors,
                          hold_s=20e-9 if kind=='inverter_two' else 200e-9,
                          edge_s=1e-9,step_s=.05e-9 if kind=='inverter_two' else .2e-9,
                          loads_f={p:10e-15 if stages[p]==max(stages.values()) else 0 for p in outputs},
                          nodeset=nodeset,initial_outputs=expected(vectors[0]))
    points=[f'0 {sequence[0]}']
    for k in range(1,len(sequence)):
        t=k*bench['hold_s'];points.extend([f'{t:.15g} {sequence[k-1]}',f'{t+1e-9:.15g} {sequence[k]}'])
    bench['netlist']=re.sub(r'(?m)^Vin0 .*$', 'Vin0 A 0 PWL('+' '.join(points)+')',bench['netlist'])
    data=execute(bench,bench['commands'],folder/'transient',retain_samples=True)
    measured=measure_sequence(data,bench,expected)
    grid_data=execute(bench,'dc Vin0 -5 5 '+('.015625' if kind=='inverter_two' else '.025'),
                      folder/'dc',retain_samples=True)
    nominal=[]
    for v in (-5.,0.,5.):
        k=int(np.argmin(abs(grid_data['v(a)']-v)))
        nominal.append({'input_v':v,'outputs_v':{p:float(grid_data[f'v({p})'][k]) for p in outputs},
                        'max_error_v':max(abs(grid_data[f'v({p})'][k]-v*(-1)**stages[p]) for p in outputs)})
    return {'passed':measured['passed'] and all(r['max_error_v']<=.5 for r in nominal),
            'transient':measured,'dc':nominal,'voltage_sequence':sequence,
            'stages':stages,'hold_s':bench['hold_s']},grid_data
