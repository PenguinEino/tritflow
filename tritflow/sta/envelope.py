"""Conservative local-class envelope, separate from matched-event accuracy.

Settled primary-input endpoints do not constrain transient side-input states.
Consequently this analysis admits every measured local class independently.
An activity clock bounds both output midpoints and unchanged-output recovery;
a recovery clock can launch downstream activity even on an endpoint-stable net.
Only the final gate adds its measured midpoint-to-band tail. Maxima of linear
ramp interpolation occur at measured axis knots, so no ramp is silently clipped.

This is an upper envelope of the characterized scalar model, not a theorem for
arbitrary analog pulses, input skew or PVT. Validation establishes conservatism
against every published nominal simulation separately. No circuit measurements
or fitted margin enter this module.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import time

from tritflow.netlist import GateNetlist
from tritflow.synth.simulate import CELL_INPUTS, ordered_instances
from .report import PathStage


def analyze_envelope(netlist, pnr=None, *, library, wire_caps=None,
                     output_load_f=10e-15, input_transition_s=1e-9,
                     load_policy='linear', fixed_ramp=False, include_recovery=True,
                     max_nodes=1_000_000, max_labels=100_000):
    """Bound all local classes at the actual load over the measured ramp domain.

    Primary-input ramps are known; internal ramps range over the entire table.
    Correlation between path classes, slew and delay is intentionally relaxed.
    ``fixed_ramp`` and ``include_recovery`` expose controlled diagnostic ablations.
    Paths are maximizing envelope terms, with no asserted sensitizing vector.
    """
    started=time.perf_counter()
    from .analyze import _settling_analyze
    if isinstance(netlist,(str,Path)):netlist=GateNetlist.load(netlist)
    if isinstance(netlist,dict):netlist=GateNetlist.from_dict(netlist)
    report=_settling_analyze(netlist,pnr,library=library,wire_caps=wire_caps,
        output_load_f=output_load_f,input_transition_s=input_transition_s,
        load_policy=load_policy,vector_pairs=[],max_nodes=max_nodes,max_labels=max_labels)
    inputs={p.name for p in netlist.ports if p.dir=='input'}
    clocks={p:(input_transition_s/2,[]) for p in inputs}
    primary_slew={p:input_transition_s*.8 for p in inputs}
    # All measured full-level widths, including classes other than the winning
    # delay, are retained to expose a non-closed slew domain rather than clip it.
    slew_upper=dict(primary_slew)
    domain_violations=[];candidates_count=0
    for inst in ordered_instances(netlist):
        pins=CELL_INPUTS[inst.cell];name=inst.pins['Y'];model=library[inst.cell]
        if not pins:continue
        load=report.loads[name]['total_f'];axis=model.data['axes']['input_transition_s']
        clock_candidates=[];end_candidates=[];transitions={};widths=[]
        for pin in pins:
            parent=inst.pins[pin]
            if parent not in clocks:continue  # No primary-input activity in this cone.
            if parent not in inputs and slew_upper[parent]/.8>axis[-1]:
                domain_violations.append({'instance':inst.name,'pin':pin,'input_net':parent,
                    'full_ramp_upper_s':slew_upper[parent]/.8,'table_max_ramp_s':axis[-1]})
            ramps=[input_transition_s] if fixed_ramp or parent in inputs else axis
            # Strict sampling rejects out-of-domain primary ramps, failed knots
            # and null observations. Internal axes are never extrapolated.
            for arc in model.arcs:
                if pin not in arc['changed_inputs']:continue
                changing=arc['output_from']!=arc['output_to']
                for ramp in ramps:
                    delay=model.sample(arc,load,ramp,load_policy=load_policy,
                        field='propagation_s' if changing else 'recovery_s')
                    tail=model.sample(arc,load,ramp,load_policy=load_policy,field='tail_s') if changing else 0.
                    width=model.sample(arc,load,ramp,load_policy=load_policy,field='output_slew_10_90_s') if changing else None
                    t=clocks[parent][0]+delay
                    stage=PathStage(inst.name,inst.cell,pin,parent,name,
                        (arc['from_inputs'][pin],arc['to_inputs'][pin]),
                        (arc['output_from'],arc['output_to']),arc['from_inputs'],arc['to_inputs'],
                        arc['id'],delay,t,load,ramp,0.,width,
                        'midpoint_envelope' if changing else 'recovery_guard')
                    path=clocks[parent][1]+[stage]
                    if changing or include_recovery:clock_candidates.append((t,path))
                    end_candidates.append((t+tail,path,tail))
                    pair=f'{arc["output_from"]}->{arc["output_to"]}'
                    transitions[pair]=max(transitions.get(pair,float('-inf')),t+tail)
                    if width is not None:widths.append(width)
                    candidates_count+=1
        if not clock_candidates:continue
        clocks[name]=max(clock_candidates,key=lambda c:c[0])
        slew_upper[name]=max(widths,default=0.)
        if name in report.arrival:
            value,path,tail=max(end_candidates,key=lambda c:c[0])
            path[-1]=replace(path[-1],settling_tail_s=tail,arrival_s=value)
            report.arrival[name]=value;report.paths[name]=path
            report.transition_arrival[name]=transitions
    # Direct primary-input outputs settle at the end of their specified ramp.
    for name in report.arrival:
        if name in inputs:report.arrival[name]=input_transition_s
        report.patterns[name]={'before':None,'after':None,
            'reason':'Independent transient local classes; no joint endpoint witness is asserted.'}
    load_extended=any('outside' in w for w in report.warnings)
    report.assumptions=[
        'Conservative envelope of measured local midpoint/recovery terms; endpoint tail added once, using the same local class and ramp.',
        'All transient local classes are admitted independently, including pulses on endpoint-stable nets; maximizing path classes need not be jointly realizable.',
        'Known primary ramp; every internal measured ramp knot is considered (piecewise-linear maxima).' if not fixed_ramp else 'Fixed-ramp diagnostic ablation.',
        'Unchanged-output recovery can launch downstream activity; it is a conservative guard clock, not a measured full-level crossing.' if include_recovery else 'Recovery clocks are not propagated (diagnostic ablation).',
        'Maximum biased AC device input C plus supplied metal/output C; no load correction or circuit-fitted delay margin.',
        'Finite nominal table-domain envelope, not a certified bound for arbitrary slew, analog pulse shape, skew, PVT or signal/poly RC.']
    if domain_violations:
        report.warnings.append(f'{len(domain_violations)} internal pins have an all-class slew upper limit beyond the measured ramp domain; this domain is not closed. Empirical coverage is qualified separately.')
    report.provenance['metric']='local_class_ramp_envelope'
    report.provenance['bound_scope']='Upper envelope of characterized scalar terms; empirical simulation coverage is separate.'
    report.provenance['fixed_ramp']=fixed_ramp
    report.provenance['recovery_guard']=include_recovery
    report.statistics={'runtime_s':time.perf_counter()-started,'all_endpoint_pairs':True,
        'local_candidates':candidates_count,'joint_endpoint_witness':False,
        'slew_domain_closed':not domain_violations,'slew_domain_violations':domain_violations,
        'load_in_measured_domain':not load_extended,'net_activity_clock_s':{n:c[0] for n,c in clocks.items()},
        'net_slew_upper_10_90_s':slew_upper}
    return report
