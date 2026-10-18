"""Optional pattern timing with ordered pin events and midpoint pulse filtering.

This keeps measured single-pin conditions when reconvergent pins arrive at
different times. Equal-time pin changes use synchronous multi-pin tables.
It is an event approximation, not an analog waveform simulator: pulses reversed
before the pending output midpoint are cancelled, and overlapping ramps remain
an explicitly counted limitation. Stable-output analog hazards cannot be sent
downstream from a scalar recovery time alone.
"""
from __future__ import annotations

from dataclasses import dataclass,replace
from itertools import groupby
from pathlib import Path
import time

from tritflow.synth import evaluate_netlist
from tritflow.synth.simulate import CELL_INPUTS,ordered_instances
from tritflow.netlist import GateNetlist
from .logic import function
from .report import PathStage


@dataclass
class Edge:
    time:float
    before:int
    after:int
    slew:float
    tail:float
    path:list


def analyze_events(netlist,pairs,*,library,wire_caps=None,output_load_f=10e-15,
                   input_transition_s=1e-9,load_policy='linear',max_events=100000):
    """Propagate midpoint events for the supplied complete endpoint vector pairs."""
    from .analyze import _settling_analyze
    started=time.perf_counter();pairs=list(pairs)
    if isinstance(netlist,(str,Path)):netlist=GateNetlist.load(netlist)
    if isinstance(netlist,dict):netlist=GateNetlist.from_dict(netlist)
    report=_settling_analyze(netlist,library=library,wire_caps=wire_caps,
        output_load_f=output_load_f,input_transition_s=input_transition_s,vector_pairs=[],load_policy=load_policy)
    ordered=ordered_instances(netlist);inputs=[p.name for p in netlist.ports if p.dir=='input']
    outputs=list(report.arrival);warnings=set(report.warnings)
    counters={'cancelled_pulses':0,'overlapping_ramps':0,'unpropagated_local_hazards':0,'time_order_clamps':0}
    for before,after in pairs:
        event_count=0
        old={n:int(v) for n,v in evaluate_netlist(netlist,before,return_all=True).items()}
        new={n:int(v) for n,v in evaluate_netlist(netlist,after,return_all=True).items()}
        edges={p:[Edge(input_transition_s/2,old[p],new[p],.8*input_transition_s,0.,[])]
               for p in inputs if old[p]!=new[p]}
        recoveries={}
        for inst in ordered:
            pins=CELL_INPUTS[inst.cell];name=inst.pins['Y'];model=library[inst.cell]
            pin_values={p:old[inst.pins[p]] for p in pins}
            incoming=sorted([(e.time,p,e) for p in pins for e in edges.get(inst.pins[p],[])],key=lambda x:x[0])
            event_count+=len(incoming)
            if event_count>max_events:raise RuntimeError('Pattern event budget exceeded; no partial timing report')
            generated=[];recovery=[]
            for _,group in groupby(incoming,key=lambda x:round(x[0],15)):
                changes=list(group);first=pin_values.copy()
                for _,pin,event in changes:pin_values[pin]=event.after
                last=pin_values.copy()
                if first==last:continue
                arc=next(a for a in model.arcs if a['from_inputs']==first and a['to_inputs']==last)
                a,b=function(inst.cell,list(first.values())),function(inst.cell,list(last.values()))
                samples=[]
                for _,pin,parent in changes:
                    if first[pin]==last[pin]:continue
                    requested=parent.slew/.8;axis=model.data['axes']['input_transition_s']
                    ramp=min(max(requested,axis[0]),axis[-1]);load=report.loads[name]['total_f']
                    if ramp!=requested:warnings.add(f'{inst.name}: equivalent full ramp {requested:g} s clipped to {ramp:g} s.')
                    delay=model.sample(arc,load,ramp,load_policy=load_policy,
                                       field='propagation_s' if a!=b else 'recovery_s')
                    tail=model.sample(arc,load,ramp,load_policy=load_policy,field='tail_s') if a!=b else 0.
                    slew=model.sample(arc,load,ramp,load_policy=load_policy,field='output_slew_10_90_s') if a!=b else parent.slew
                    t=parent.time+delay
                    stage=PathStage(inst.name,inst.cell,pin,inst.pins[pin],name,
                        (first[pin],last[pin]),(a,b),first,last,arc['id'],delay,t,load,ramp,
                        tail,slew,'ordered_midpoint' if a!=b else 'local_recovery')
                    samples.append(Edge(t,a,b,slew,tail,parent.path+[stage]))
                if not samples:continue
                event=max(samples,key=lambda e:e.time)
                if a==b:
                    if event.time>max(e.time for _,_,e in changes)+1e-18:
                        recovery.append(event);counters['unpropagated_local_hazards']+=1
                    continue
                # Midpoint inertial approximation: a reversed request arriving
                # before the pending output crosses its midpoint suppresses it.
                if generated and max(e.time for _,_,e in changes)<generated[-1].time and event.after==generated[-1].before:
                    generated.pop();counters['cancelled_pulses']+=1
                    current=generated[-1].after if generated else old[name]
                    if event.after==current:continue
                if generated:
                    previous=generated[-1]
                    if event.time-previous.time<.5*(event.slew+previous.slew)/.8:
                        counters['overlapping_ramps']+=1
                    if event.time<=previous.time:
                        counters['time_order_clamps']+=1
                        delta=previous.time+1e-15-event.time
                        stage=event.path[-1]
                        event=replace(event,time=event.time+delta,path=event.path[:-1]+[
                            replace(stage,delay_s=stage.delay_s+delta,arrival_s=stage.arrival_s+delta,
                                    time_order_adjustment_s=stage.time_order_adjustment_s+delta)])
                generated.append(event)
            edges[name]=generated;recoveries[name]=recovery
        for pin in outputs:
            candidates=[]
            if edges.get(pin):candidates.append(edges[pin][-1])
            candidates.extend(recoveries.get(pin,[]))
            if not candidates:continue
            event=max(candidates,key=lambda e:e.time+e.tail)
            value=event.time+event.tail
            pair=f'{old[pin]}->{new[pin]}'
            report.transition_arrival[pin][pair]=max(report.transition_arrival[pin].get(pair,0.),value)
            if value>report.arrival[pin]:
                path=event.path.copy();path[-1]=replace(path[-1],arrival_s=value)
                report.arrival[pin]=value;report.paths[pin]=path
                report.patterns[pin]={'before':before,'after':after}
    report.assumptions=[
        'Midpoint propagation plus endpoint-only settling tail; measured output slew supplies each receiving input ramp.',
        'Ordered reconvergent pin events select measured intermediate single-pin classes; equal-time events use synchronous tables.',
        'Pending pulses reversed before output midpoint are suppressed (inertial approximation). Overlapping ramps and time-order clamps are counted.',
        'Only scalar stable-output recovery is available: local analog glitches cannot be propagated to subsequent gates.',
        'Path pin values may be timed intermediate states rather than just the whole-vector endpoints. No analog or timing-bound claim.']
    report.warnings=sorted(warnings)
    report.statistics.update(counters|{'runtime_s':time.perf_counter()-started,'pattern_count':len(pairs),'event_model':True})
    report.provenance['metric']='ordered_midpoint_with_endpoint_tail'
    return report
