"""Measured-slew timing labels with symbolic primary-input compatibility.

A label carries one local transition and a narrow equivalent-ramp interval.
Measured output slew maps that interval into downstream labels, preserving
more delay/slew correlation than independent extrema. Backward path search
intersects source conditions rather than splicing incompatible PI histories.
Reachable side-input states include settled endpoints and intermediate logical
levels. This still relaxes their time alignment and full pulse amplitude; it
is a finite scalar timing model, not arbitrary-waveform signoff.
"""
from __future__ import annotations

from itertools import product
import math
from pathlib import Path
import time

from tritflow.netlist import GateNetlist
from tritflow.synth.simulate import CELL_INPUTS,ordered_instances
from .logic import Diagram,TRITS
from .report import PathStage
from .model import ModelDomainError


def _segments(model,arc,load,lo,hi,width,policy):
    """Split a measured piecewise-linear surface at output-ramp bin boundaries."""
    axis=model.data['axes']['input_transition_s']
    if lo<axis[0]-1e-18 or hi>axis[-1]+1e-18:
        raise ModelDomainError(f'Label full-ramp interval [{lo:g},{hi:g}] exceeds measured axis {axis}')
    lo=max(lo,axis[0]);hi=min(hi,axis[-1])
    changing=arc['output_from']!=arc['output_to']
    knots=sorted({lo,hi,*[r for r in axis if lo<r<hi]})
    def sample(r):
        return (r,model.sample(arc,load,r,field='propagation_s' if changing else 'recovery_s',load_policy=policy),
            model.sample(arc,load,r,field='tail_s',load_policy=policy) if changing else 0.,
            model.sample(arc,load,r,field='output_slew_10_90_s',load_policy=policy)/.8 if changing else 0.)
    samples=[sample(r) for r in knots]
    if changing:
        extra=[]
        for first,last in zip(samples,samples[1:]):
            if first[3]==last[3]:continue
            for k in range(math.floor(min(first[3],last[3])/width)+1,math.ceil(max(first[3],last[3])/width)):
                f=(k*width-first[3])/(last[3]-first[3])
                extra.append(tuple(first[i]+f*(last[i]-first[i]) for i in range(4)))
        samples=sorted(samples+extra)
    return list(zip(samples,samples[1:])) or [(samples[0],samples[0])]


def analyze_windows(netlist,pnr=None,*,library,wire_caps=None,output_load_f=10e-15,
                    input_transition_s=1e-9,load_policy='linear',bin_s=5e-9,
                    side_states='reachable',max_nodes=1_000_000,max_labels=100_000):
    """Time all PI endpoint pairs with measured local slew and compatibility.

    ``side_states='endpoint'`` restricts every class to settled endpoints;
    ``reachable`` also admits transient local states, ignoring relative time;
    ``free`` is the unconditioned transition/slew ablation. Recovery remains a
    local endpoint observation, never a fabricated full-level input crossing.
    Out-of-domain labels raise; no clipped result is presented as a bound.
    """
    started=time.perf_counter()
    from .analyze import _settling_analyze,_input_order,_worst,_Choice
    if side_states not in {'endpoint','reachable','free'}:raise ValueError('Unknown side-state policy')
    if not math.isfinite(bin_s) or bin_s<=0:raise ValueError('Slew bin must be finite and positive')
    if isinstance(netlist,(str,Path)):netlist=GateNetlist.load(netlist)
    if isinstance(netlist,dict):netlist=GateNetlist.from_dict(netlist)
    report=_settling_analyze(netlist,pnr,library=library,wire_caps=wire_caps,
        output_load_f=output_load_f,input_transition_s=input_transition_s,
        load_policy=load_policy,vector_pairs=[],max_nodes=max_nodes,max_labels=max_labels)
    inputs=sorted((p.name for p in netlist.ports if p.dir=='input'),key=_input_order)
    dd=Diagram([(phase,p) for p in inputs for phase in ('before','after')],max_nodes)
    variables={v:k for k,v in enumerate(dd.variables)}
    truth={};reach={};choices={};upper={};conditions={};intervals={};by_net={}
    for name in inputs:
        truth[name]=[{v:dd.literal(variables[phase,name],v) for v in TRITS} for phase in ('before','after')]
        reach[name]={v:dd.apply('or',truth[name][0][v],truth[name][1][v]) for v in TRITS}
        by_net[name]=[]
        for a,b in product(TRITS,repeat=2):
            if a==b:continue
            key=(name,a,b,0);by_net[name].append(key)
            choices[key]=[];upper[key]=0.;conditions[key]=dd.intersect(truth[name][0][a],truth[name][1][b])
            intervals[key]=(input_transition_s,input_transition_s)
    total_choices=0
    for inst in ordered_instances(netlist):
        pins=CELL_INPUTS[inst.cell];name=inst.pins['Y'];model=library[inst.cell]
        truth[name]=[dd.gate(inst.cell,[truth[inst.pins[p]][phase] for p in pins]) for phase in range(2)]
        reach[name]={v:dd.apply('or',truth[name][0][v],truth[name][1][v]) for v in TRITS}
        by_net[name]=[]
        if not pins:continue
        load=report.loads[name]['total_f']
        for arc in model.arcs:
            # Pins tied to one physical signal cannot move independently.
            if any(inst.pins[p]==inst.pins[q] and
                any(arc[field][p]!=arc[field][q] for field in ('from_inputs','to_inputs'))
                for p in pins for q in pins):continue
            changing=arc['output_from']!=arc['output_to']
            for pin in arc['changed_inputs']:
                if side_states=='endpoint':
                    region=dd.intersect(*(truth[inst.pins[p]][phase][arc[field][p]]
                        for phase,field in ((0,'from_inputs'),(1,'to_inputs')) for p in pins))
                elif side_states=='reachable':
                    region=dd.intersect(*(reach[inst.pins[p]][arc[field][p]]
                        for field in ('from_inputs','to_inputs') for p in pins if p!=pin))
                else:region=1
                if not region:continue
                for parent in by_net.get(inst.pins[pin],[]):
                    if parent[1:3]!=(arc['from_inputs'][pin],arc['to_inputs'][pin]):continue
                    condition=dd.intersect(region,conditions[parent])
                    if not condition:continue
                    lo,hi=intervals[parent]
                    for first,last in _segments(model,arc,load,lo,hi,bin_s,load_policy):
                        selected=max((first,last),key=lambda row:row[1]);ramp,delay,_,_=selected
                        # Delay and endpoint settling maxima on this same narrow
                        # segment can occur at different ends. Store their exact
                        # residual, rather than independently maximizing the tail.
                        endpoint=max(row[1]+row[2] for row in (first,last))
                        tail=endpoint-delay
                        low,high=sorted((first[3],last[3]))
                        bucket=math.floor((low+high)/2/bin_s) if changing else -1
                        key=(name,arc['output_from'],arc['output_to'],bucket)
                        if key not in choices:
                            by_net[name].append(key);choices[key]=[];conditions[key]=0
                            upper[key]=float('-inf');intervals[key]=(low,high)
                        oldlo,oldhi=intervals[key];intervals[key]=(min(low,oldlo),max(high,oldhi))
                        arrival=upper[parent]+delay
                        stage=PathStage(inst.name,inst.cell,pin,inst.pins[pin],name,
                            parent[1:3],key[1:3],arc['from_inputs'],arc['to_inputs'],arc['id'],
                            delay,arrival,load,ramp,tail,selected[3]*.8 if changing else None,
                            'slew_window' if changing else 'local_recovery')
                        choices[key].append(_Choice(parent,stage,region));upper[key]=max(upper[key],arrival)
                        conditions[key]=dd.apply('or',conditions[key],condition);total_choices+=1
                        if total_choices>max_labels*10:raise RuntimeError('Slew-window graph budget exceeded')
        # Stable recovery is not a logical transition or a slew. It terminates
        # locally; changing intermediate states remain available to side pins.
        for key in by_net[name]:
            if key[1]!=key[2]:
                for v in key[1:3]:reach[name][v]=dd.apply('or',reach[name][v],conditions[key])
        by_net[name]=[key for key in by_net[name] if key[1]!=key[2]]
    graph_nodes=len(dd.nodes);expanded=0
    for name in report.arrival:
        allkeys=[key for key in choices if key[0]==name]
        transitions={};best=(0.,None,[])
        for a,b in product(TRITS,repeat=2):
            found=(0.,None,[])
            keys=sorted((key for key in allkeys if key[1:3]==(a,b)),
                key=lambda key:upper[key]+max(c.stage.settling_tail_s for c in choices[key]) if choices[key] else 0.,reverse=True)
            for key in keys:
                cap=upper[key]+max((c.stage.settling_tail_s for c in choices[key]),default=0.)+input_transition_s/2
                if cap<=found[0]:break
                dd.rollback(graph_nodes)
                value,region,path,count=_worst(key,choices,upper,conditions,dd,1,max_labels,midpoint=True,ramp=input_transition_s)
                expanded+=count
                if region and value>found[0]:found=value,dd.witness(region),path
            if found[1] is not None:
                transitions[f'{a}->{b}']=found[0]
                if found[0]>best[0]:best=found
        report.arrival[name]=best[0];report.paths[name]=best[2];report.transition_arrival[name]=transitions
        report.patterns[name]={'before':None,'after':None,'reason':'No joint temporal waveform witness is asserted.'}
        if best[1] is not None:
            report.patterns[name]['compatible_primary_endpoints']={phase:{p:best[1][phase,p] for p in inputs} for phase in ('before','after')}
    report.provenance['metric']='conditioned_slew_windows'
    report.provenance['side_states']=side_states;report.provenance['slew_bin_s']=bin_s
    report.assumptions=[
        'Transition-specific narrow slew intervals follow measured output slew; d50 and endpoint settling extrema use the same segment.',
        'Backward search intersects primary-input compatibility along the entire path; local time alignment and partial pulse amplitude remain relaxed.',
        f'Side-input state policy: {side_states}; local stable recovery is not propagated as a fabricated full-level edge.',
        'Scalar-table upper estimate; nominal finite-case coverage is validated separately. Not an arbitrary analog-waveform or PVT bound.']
    report.statistics={'runtime_s':time.perf_counter()-started,'graph_nodes':graph_nodes,'graph_choices':total_choices,
        'search_expansions':expanded,'slew_domain_closed':True,'slew_domain_violations':[],
        'load_in_measured_domain':not any('outside' in w for w in report.warnings),'all_endpoint_pairs':True,
        'joint_temporal_witness':False,'unmodeled_analog_recovery_propagation':True}
    return report
