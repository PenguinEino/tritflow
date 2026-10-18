"""Transition-conditioned graph timing with exact settled endpoint sensitization.

For each net and directed trit pair we first compute a graph arrival envelope,
retaining every predecessor arc. A best-first backward search uses that envelope
as an upper bound and intersects *all* from/to pin conditions along each path.
Reduced ternary decision diagrams encode those conditions. Empty intersections
are false paths; the first feasible primary-input leaf is the largest modeled
arrival. Keeping every predecessor avoids losing alternate paths at reconvergence.

The electrical approximation is intentionally simpler: add the cell's measured
settling to the latest changing-input arrival. Every stage uses the requested
full ramp (default 1 ns). This counts finite ramp time at each stage and does
not propagate waveform shape/slew. Simultaneous tables assume synchronous equal
ramps although a real circuit develops skew. Local unchanged-output recovery is
reported, but a glitch on an endpoint-stable intermediate net cannot be carried
to the next gate without waveform information. These are nominal analytical
estimates, not guaranteed upper bounds. Validation quantifies those limitations.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import heapq
import json
import math
from pathlib import Path
import re
import time
from dataclasses import replace

from tritflow.netlist import GateNetlist
from tritflow.synth.simulate import CELL_INPUTS, ordered_instances
from .logic import Diagram, TRITS
from .model import TimingLibrary
from .report import PathStage, TimingReport


@dataclass
class _Choice:
    parent: tuple
    stage: PathStage
    region: int


def _worst(target, choices, upper, conditions, dd, allowed, budget, *, midpoint=False, ramp=1e-9):
    """Branch and bound over paths, with exact conjunction of endpoint conditions."""
    sequence = 0
    endpoint_tail=max((c.stage.settling_tail_s for c in choices[target]),default=0.) if midpoint else 0.
    heap = [(-(upper[target]+endpoint_tail), sequence, target, 0., allowed, ())]
    best_seen = {}
    expanded = 0
    while heap:
        _, _, node, delay, region, path = heapq.heappop(heap)
        expanded += 1
        if expanded > budget:
            raise RuntimeError("STA path-search budget exceeded; no partial report published")
        if not choices[node]:
            region = dd.intersect(region, conditions[node])
            if region:
                stages = []
                arrival = ramp/2 if midpoint else 0.
                for stage in reversed(path):
                    arrival += stage.delay_s
                    stages.append(replace(stage, arrival_s=arrival))
                if midpoint and stages:
                    arrival+=stages[-1].settling_tail_s
                    stages[-1]=replace(stages[-1],arrival_s=arrival)
                return arrival, region, stages, expanded
            continue
        for choice in choices[node]:
            remaining = dd.intersect(region, choice.region)
            if not remaining: continue
            cumulative = delay + choice.stage.delay_s
            if midpoint and not path:cumulative+=choice.stage.settling_tail_s
            key = choice.parent, remaining
            if cumulative <= best_seen.get(key, -1.): continue
            best_seen[key] = cumulative
            sequence += 1
            heapq.heappush(heap, (-(cumulative+upper[choice.parent]), sequence,
                choice.parent, cumulative, remaining, path+(choice.stage,)))
    return 0., 0, [], expanded


def _input_order(name):
    match = re.fullmatch(r"(.*)\[(\d+)\]", name)
    return (int(match[2]), match[1]) if match else (-1, name)


def _load_data(pnr):
    if pnr is None: return None
    if isinstance(pnr, (str, Path)): return json.loads(Path(pnr).read_text())
    return pnr.data if hasattr(pnr, "data") else pnr


def _settling_analyze(netlist, pnr=None, *, library=None, output_load_f=10e-15,
            input_transition_s=1e-9, load_policy="linear", wire_caps=None,
            vector_pairs=None, max_nodes=1_000_000, max_labels=100_000):
    """Estimate output settling with a verifiable critical endpoint pattern.

    ``netlist`` accepts GateNetlist, JSON dict or filename. ``pnr`` accepts a
    PnrResult, PNR JSON dict or filename. PNR route C is obtained from the public
    extraction estimator. ``wire_caps`` optionally supplies *logical-net* C
    (e.g. LVS-mapped full-GDS C, including connected cell terminal metal), in
    preference to route-only C. The default output test load is 10 fF.

    ``vector_pairs`` optionally restricts analysis to complete (before, after)
    input dict pairs, useful for comparison to SIM's actual vector sequence.
    With None, all endpoint pairs are considered symbolically, without sampling.
    Load extension is explicit in report warnings and limited to [0,2*Cmax];
    choose ``load_policy='error'`` to forbid it. Ramps never extrapolate.
    ``max_nodes`` bounds live symbolic nodes and ``max_labels`` bounds search
    expansions per output transition. Limits raise, without partial success.
    """
    started = time.perf_counter()
    if isinstance(netlist, (str, Path)): netlist = GateNetlist.load(netlist)
    if isinstance(netlist, dict): netlist = GateNetlist.from_dict(netlist)
    ordered = ordered_instances(netlist)
    if load_policy not in {"error", "linear"}: raise ValueError("Unknown load policy")
    models = library or TimingLibrary(i.cell for i in ordered)
    midpoint=getattr(models,'metric',None)=='midpoint'
    inputs = sorted((p.name for p in netlist.ports if p.dir == "input"), key=_input_order)
    outputs = [p.name for p in netlist.ports if p.dir == "output"]
    dd = Diagram([(phase, name) for name in inputs for phase in ("before", "after")], max_nodes)
    variables = {key: index for index, key in enumerate(dd.variables)}
    allowed = 1
    if vector_pairs is not None:
        allowed = 0
        for before, after in vector_pairs:
            if set(before) != set(inputs) or set(after) != set(inputs):
                raise ValueError("Vector pairs must specify every primary input exactly")
            if any(v not in TRITS for state in (before, after) for v in state.values()):
                raise ValueError("Vector values must be -1, 0 or +1")
            region = dd.intersect(*(dd.literal(variables[phase, name], state[name])
                                    for phase, state in (("before", before), ("after", after))
                                    for name in inputs))
            allowed = dd.apply("or", allowed, region)
    truth = {}
    choices, upper, conditions = {}, {}, {}
    for name in inputs:
        truth[name] = [{v: dd.literal(variables[phase, name], v) for v in TRITS}
                       for phase in ("before", "after")]
        for a,b in product(TRITS, repeat=2):
            region = dd.intersect(allowed, truth[name][0][a], truth[name][1][b])
            if a != b and region:
                key = name,a,b
                choices[key] = []
                upper[key] = 0.
                conditions[key] = region
    data = _load_data(pnr)
    wire_scope = "Fanout only; no wire capacitance supplied."
    if wire_caps is None and data is not None:
        from tritflow.extract import wire_capacitance
        wire_caps = wire_capacitance(data)
        wire_scope = "Merged PNR routes and external pin C; cell terminal metal is not included."
    elif wire_caps is not None:
        wire_scope = "Caller-supplied logical-net wire C (validation uses LVS-mapped full top-net metal)."
    caps = (wire_caps or {}).get("nets", wire_caps or {})
    unknown = set(caps) - netlist.nets() - {"VDD", "VMID", "VSS"}
    if unknown: raise ValueError(f"Wire capacitance contains unknown logical nets: {sorted(unknown)}")
    loads = {net: {"fanout_f": 0., "wire_f": float(caps.get(net, {}).get("capacitance_f", 0.))
                   if isinstance(caps.get(net, 0.), dict) else float(caps.get(net, 0.)),
                   "external_f": 0.} for net in netlist.nets()}
    for inst in ordered:
        for pin in CELL_INPUTS[inst.cell]:
            loads[inst.pins[pin]]["fanout_f"] += models[inst.cell].capacitance(pin)
    for name in outputs:
        loads[name]["external_f"] = float(output_load_f.get(name, 0.) if isinstance(output_load_f, dict) else output_load_f)
    for row in loads.values():
        if any(not math.isfinite(v) or v < 0 for v in row.values()):
            raise ValueError("All capacitances must be finite and nonnegative")
        row["total_f"] = sum(row.values())
    warnings = []
    total_choices = 0
    for inst in ordered:
        model = models[inst.cell]
        pins = CELL_INPUTS[inst.cell]
        name = inst.pins["Y"]
        truth[name] = [dd.gate(inst.cell, [truth[inst.pins[p]][phase] for p in pins]) for phase in range(2)]
        if not pins: continue
        load = loads[name]["total_f"]
        axis = model.data["axes"]["load_f"]
        if not axis[0] <= load <= axis[-1]:
            warnings.append(f"{inst.name}/{inst.cell}: load {load:g} F outside [{axis[0]:g}, {axis[-1]:g}] F; policy={load_policy}.")
        for arc in model.arcs:
            condition = dd.intersect(allowed, *(truth[inst.pins[p]][phase][arc[key][p]]
                 for phase, key in ((0, "from_inputs"), (1, "to_inputs")) for p in pins))
            if not condition: continue
            changing=arc['output_from']!=arc['output_to']
            if midpoint:
                delay=model.sample(arc,load,input_transition_s,load_policy=load_policy,
                                   field='propagation_s' if changing else 'recovery_s')
                tail=model.sample(arc,load,input_transition_s,load_policy=load_policy,field='tail_s') if changing else 0.
                slew=model.sample(arc,load,input_transition_s,load_policy=load_policy,field='output_slew_10_90_s') if changing else None
            else:
                delay = model.sample(arc, load, input_transition_s, load_policy=load_policy)
                tail,slew=0.,None
            transition = (arc["output_from"], arc["output_to"])
            key = name,*transition
            for pin in arc["changed_inputs"]:
                pair = (arc["from_inputs"][pin], arc["to_inputs"][pin])
                parent = inst.pins[pin],*pair
                if parent not in upper: continue
                arrival = upper[parent] + delay
                stage = PathStage(inst.name, inst.cell, pin, inst.pins[pin], name,
                    pair, transition, arc["from_inputs"], arc["to_inputs"], arc["id"],
                    delay, arrival, load, input_transition_s,tail,slew,
                    'midpoint' if midpoint and changing else 'local_recovery' if midpoint else 'settling')
                choices.setdefault(key, []).append(_Choice(parent, stage, condition))
                upper[key] = max(upper.get(key, float('-inf')), arrival)
                total_choices += 1
    arrival, transitions, paths, patterns = {}, {}, {}, {}
    total_expanded = 0
    graph_nodes = len(dd.nodes)
    peak_nodes = graph_nodes
    for name in outputs:
        transitions[name] = {}
        best = None
        for a,b in product(TRITS, repeat=2):
            key = name,a,b
            if key not in upper: continue
            dd.rollback(graph_nodes)
            value, region, path, expanded = _worst(key, choices, upper, conditions, dd, allowed, max_labels,
                                                 midpoint=midpoint,ramp=input_transition_s)
            peak_nodes = max(peak_nodes, len(dd.nodes))
            total_expanded += expanded
            if region:
                transitions[name][f"{a}->{b}"] = value
                if best is None or value > best[0]: best = value,dd.witness(region),path
        arrival[name] = best[0] if best else 0.
        paths[name] = best[2] if best else []
        if best:
            witness = best[1]
            patterns[name] = {phase: {p: witness[phase,p] for p in inputs} for phase in ("before", "after")}
        else:
            patterns[name] = {"before": None, "after": None}
    report=TimingReport(netlist.top, arrival, transitions, paths, patterns, loads,
        ["Nominal ±5/0 V models; settling means final entry into ideal ±0.5 V through the measured observation window.",
         "Exact endpoint sensitization; maximum additive cell settling with a fixed full input ramp at every stage.",
         "No propagated slew, analog waveform/skew or intermediate endpoint-stable glitch propagation; no guaranteed upper bound.",
         "Simultaneous-input table delays use synchronous equal ramps; path endpoint patterns do not prove hazard-free operation.",
         "Fanout C uses maximum measured biased input C; default external output load is 10 fF.",
         wire_scope, "Estimated metal C only; no signal wire R, calibrated poly RC, PVT or package effects.",
         "Linear load extension, when enabled, is limited to zero through twice maximum measured load; input ramps never extrapolate."],
        warnings, {"cell_generation": models.generation, "timing_sha256": models.hashes,
                   "load_policy": load_policy, "input_transition_s": input_transition_s},
        {"decision_nodes": peak_nodes, "graph_nodes": graph_nodes,
         "graph_choices": total_choices, "search_expansions": total_expanded,
         "runtime_s": time.perf_counter()-started, "all_endpoint_pairs": vector_pairs is None})
    if midpoint:
        report.assumptions[1]='Measured midpoint delays compose; only the endpoint settling tail is added. Global graph uses a fixed input ramp.'
        report.provenance['metric']='midpoint_with_endpoint_tail'
    return report


def analyze(netlist,pnr=None,**kwargs):
    """Analyze ternary timing; STA-owned midpoint tables are the default model.

    Passing a legacy TimingLibrary explicitly retains the historical additive
    settling model for controlled ablations. With vector_pairs, midpoint analysis
    also propagates measured output slew between gates. See sta/README.md.
    """
    library=kwargs.get('library')
    if library is None:
        from .propagation import PropagationLibrary
        net=GateNetlist.load(netlist) if isinstance(netlist,(str,Path)) else GateNetlist.from_dict(netlist) if isinstance(netlist,dict) else netlist
        kwargs['library']=library=PropagationLibrary([i.cell for i in net.instances])
    pairs=kwargs.get('vector_pairs')
    if getattr(library,'metric',None)=='midpoint' and pairs is not None:
        from .propagation import analyze_patterns
        options=kwargs.copy();options.pop('vector_pairs')
        ordered_events=options.pop('ordered_events',True)
        if pnr is not None and options.get('wire_caps') is None:
            from tritflow.extract import wire_capacitance
            options['wire_caps']=wire_capacitance(_load_data(pnr))
        if ordered_events and options.get('propagate_slew',True):
            from .events import analyze_events
            options.pop('propagate_slew',None)
            return analyze_events(netlist,pairs,**options)
        return analyze_patterns(netlist,pairs,**options)
    return _settling_analyze(netlist,pnr,**kwargs)
