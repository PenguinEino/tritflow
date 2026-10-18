"""Midpoint propagation and endpoint-only settling with measured output slew.

The table is independently characterized from isolated transistor cells. No
circuit-specific fit or scale factor is used. A 10–90% output slew becomes an
equivalent full linear input ramp by dividing by 0.8 at the receiving gate.
This preserves width, not waveform shape. Multi-input surfaces remain equal-
ramp synchronous observations; unequal arrival times are a documented limit.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import time

from tritflow import ROOT
from tritflow.netlist import GateNetlist
from tritflow.synth import evaluate_netlist
from tritflow.synth.simulate import CELL_INPUTS, ordered_instances
from .model import CellTiming, ModelDomainError, TimingLibrary, _bracket
from .report import PathStage, TimingReport


class PropagationCell(CellTiming):
    """Interpolate signed midpoint delays; all other time intervals are nonnegative."""

    def sample(self, arc, load_f, ramp_s=1e-9, *, load_policy='error', field='propagation_s'):
        import math
        i,x=_bracket(self.data['axes']['load_f'],load_f,extend=load_policy=='linear')
        j,y=_bracket(self.data['axes']['input_transition_s'],ramp_s)
        value=0.
        for row,wy in ((j,1-y),(j+1,y)):
            for col,wx in ((i,1-x),(i+1,x)):
                weight=wx*wy
                if abs(weight)<1e-14:continue
                point=arc[field][row][col]
                if (not arc['passed'][row][col] or point is None or not math.isfinite(point)
                        or (field!='propagation_s' and point<0)):
                    raise ModelDomainError(f'Invalid {field}: {arc["id"]} [{row}][{col}]')
                value+=weight*point
        return value if field=='propagation_s' else max(0.,value)


class PropagationLibrary(TimingLibrary):
    """STA-owned midpoint tables checked against the current CELLS publication."""

    metric='midpoint'

    def __init__(self,cells,root=None):
        cells=tuple(cells)
        super().__init__(cells)
        root=Path(root or ROOT/'results/sta/propagation/tables')
        for cell in sorted(set(cells)):
            if self.cells[cell].data['kind']!='logic':continue
            path=root/f'{cell}.propagation.json';raw=path.read_bytes();data=json.loads(raw)
            base=self.cells[cell].data
            if (data.get('schema_version')!=2 or not data.get('complete') or not data.get('passed')
                    or data['source_sha256']!=base['source_sha256']
                    or data['model_sha256']!=base['model_sha256'] or data['generation']!=base['generation']):
                raise ValueError(f'Stale or failed propagation table: {path}')
            self.cells[cell]=PropagationCell(data)
            self.hashes[str(path)]=hashlib.sha256(raw).hexdigest()


def analyze_patterns(netlist, pairs, *, library, wire_caps=None, output_load_f=10e-15,
                     input_transition_s=1e-9, propagate_slew=True, load_policy='linear'):
    """Pattern-conditioned block timing, adding a settling tail only at outputs.

    Every pattern is a complete primary-input endpoint pair. At a gate, use
    that exact measured vector class, and propagate the latest candidate input
    midpoint plus its table d50. The winning candidate also supplies output
    slew. These blocks do not model skew-induced intermediate logic states or
    propagate glitches on endpoint-stable nets. Such limitations are reported,
    not treated as proof that a stable net has no analog activity.
    """
    started=time.perf_counter()
    from .analyze import _settling_analyze
    # Reuse validated load construction through the legacy graph entry point
    # on an empty pattern set; it performs no active timing-arc interpolation.
    if isinstance(netlist,(str,Path)):netlist=GateNetlist.load(netlist)
    if isinstance(netlist,dict):netlist=GateNetlist.from_dict(netlist)
    report=_settling_analyze(netlist,library=library,wire_caps=wire_caps,
              output_load_f=output_load_f,input_transition_s=input_transition_s,
              vector_pairs=[],load_policy=load_policy)
    ordered=ordered_instances(netlist)
    inputs=[p.name for p in netlist.ports if p.dir=='input']
    outputs=list(report.arrival)
    record={p:None for p in outputs};warnings=set(report.warnings);pattern_results=[]
    for before,after in pairs:
        if set(before)!=set(inputs) or set(after)!=set(inputs):raise ValueError('Incomplete timing pattern')
        old={n:int(v) for n,v in evaluate_netlist(netlist,before,return_all=True).items()}
        new={n:int(v) for n,v in evaluate_netlist(netlist,after,return_all=True).items()}
        states={p:{'midpoint':input_transition_s/2,'slew':input_transition_s*.8,'tail':0.,'path':[]}
                for p in inputs if old[p]!=new[p]}
        for inst in ordered:
            pins=CELL_INPUTS[inst.cell];name=inst.pins['Y']
            first={p:old[inst.pins[p]] for p in pins};last={p:new[inst.pins[p]] for p in pins}
            if first==last:continue
            arc=next(a for a in library[inst.cell].arcs if a['from_inputs']==first and a['to_inputs']==last)
            changing=old[name]!=new[name];candidates=[]
            for pin in arc['changed_inputs']:
                parent=states.get(inst.pins[pin])
                if parent is None:continue
                requested=parent['slew']/.8 if propagate_slew else input_transition_s
                axis=library[inst.cell].data['axes']['input_transition_s']
                ramp=min(max(requested,axis[0]),axis[-1])
                if ramp!=requested:
                    warnings.add(f'{inst.name}: equivalent input ramp {requested:g} s clipped to {ramp:g} s; measured ramp domain.')
                model=library[inst.cell];load=report.loads[name]['total_f']
                delay=model.sample(arc,load,ramp,field='propagation_s' if changing else 'recovery_s',load_policy=load_policy)
                tail=model.sample(arc,load,ramp,field='tail_s',load_policy=load_policy) if changing else 0.
                slew=model.sample(arc,load,ramp,field='output_slew_10_90_s',load_policy=load_policy) if changing else None
                midpoint=parent['midpoint']+delay
                stage=PathStage(inst.name,inst.cell,pin,inst.pins[pin],name,
                    (old[inst.pins[pin]],new[inst.pins[pin]]),(old[name],new[name]),first,last,
                    arc['id'],delay,midpoint,load,ramp,
                    settling_tail_s=tail,output_slew_10_90_s=slew,metric='midpoint' if changing else 'local_recovery')
                candidates.append({'midpoint':midpoint,'slew':slew,'tail':tail,'path':parent['path']+[stage]})
            if candidates:
                winner=max(candidates,key=lambda c:c['midpoint'])
                if changing:states[name]=winner
                if name in outputs:
                    winner=max(candidates,key=lambda c:c['midpoint']+c['tail'])
                    value=winner['midpoint']+winner['tail']
                    pair=f'{old[name]}->{new[name]}'
                    report.transition_arrival[name][pair]=max(report.transition_arrival[name].get(pair,0.),value)
                    if record[name] is None or value>record[name][0]:record[name]=value,winner,before,after
        result={p:(states[p]['midpoint']+states[p]['tail'] if p in states else 0.) for p in outputs}
        pattern_results.append(result)
    for pin,row in record.items():
        if row is None:continue
        value,winner,before,after=row
        report.arrival[pin]=value
        path=winner['path'].copy()
        path[-1]=replace(path[-1],arrival_s=value)
        report.paths[pin]=path;report.patterns[pin]={'before':before,'after':after}
    report.assumptions=[
        'Measured input/output ideal-step midpoint propagation; settling tail added at the endpoint only.',
        'Output 10–90% slew / 0.8 sets the next equivalent full linear ramp.' if propagate_slew else 'Fixed input ramp at every stage (composition ablation).',
        'Exact pattern endpoint classes, maximum biased AC input C plus supplied logical-net wire C.',
        'No skew-dependent intermediate states, intermediate endpoint-stable glitch propagation or waveform-shape model.',
        'Synchronous multi-input table observations are approximations when input midpoints differ; no guaranteed bound.']
    report.warnings=sorted(warnings)
    report.provenance['metric']='midpoint_with_endpoint_tail'
    report.statistics['pattern_count']=len(pattern_results)
    report.statistics['propagate_slew']=propagate_slew
    report.statistics['runtime_s']=time.perf_counter()-started
    return report
