"""Ternary PWL stimuli, rail current probes, and notebook-friendly simulation."""
from __future__ import annotations

from itertools import product
import math
import re

from tritflow import TRIT_VOLTS, VDD, VMID, VSS
from .runner import run_ngspice, SimulationError
from .spice import subcircuits, simulation_netlist, model_includes, logical_spice_names, rename_formal_nodes


def restore_signals(data, bench):
    """Restore logical spelling without aliasing distinct HDL names a and A."""
    result = dict(data)
    mapping = bench.get('signal_names', {})
    for logical, encoded in mapping.items():
        result[f'v({logical})'] = data[f'v({encoded})'.lower()]
    counts = {name.lower(): sum(other.lower() == name.lower() for other in mapping) for name in mapping}
    for logical in mapping:
        if counts[logical.lower()] == 1:
            result[f'v({logical})'.lower()] = result[f'v({logical})']
    return result


def input_vectors(ninputs: int, *, transitions: bool = False, max_transitions: int = 10000) -> list[tuple]:
    """Enumerate all states, optionally an Euler tour of all directed state changes.

    The complete directed graph has 3**n * (3**n - 1) edges. Explicitly reject
    impractical tours instead of silently downgrading transition coverage.
    """
    if ninputs < 0:
        raise ValueError('ninputs must be nonnegative')
    nstates = 3 ** ninputs
    if (transitions and nstates * (nstates - 1) > max_transitions) or nstates > max_transitions + 1:
        raise ValueError('Exhaustive stimulus exceeds the configured budget')
    states = list(product((-1, 0, 1), repeat=ninputs))
    if not transitions or len(states) == 1:
        return states
    adjacency = {i: [j for j in range(len(states)) if j != i] for i in range(len(states))}
    stack, tour = [0], []
    while stack:
        if adjacency[stack[-1]]:
            stack.append(adjacency[stack[-1]].pop())
        else:
            tour.append(stack.pop())
    return [states[i] for i in reversed(tour)]


def build_testbench(subckts: str, top: str, inputs: list[str], outputs: list[str],
                    vectors, *, hold_s: float = 200e-9, edge_s: float = 1e-9,
                    step_s: float = 0.5e-9, loads_f: float | dict = 10e-15,
                    nodeset: dict | None = None, initial_outputs: dict | None = None,
                    pdk=None, temperature_c: float = 27, supplies_v: dict | None = None) -> dict:
    """Drive any subckt by its declared pins; input vectors contain trits, not volts.

    Edges begin at k*hold_s. Outputs and optional hierarchical internal nodes get
    .nodeset initial guesses, never .ic/uic constraints on the transient solution.
    """
    vectors = [tuple(row) for row in vectors]
    supplies = {'VDD':VDD,'VMID':VMID,'VSS':VSS}
    if supplies_v is not None:
        if set(supplies_v)-supplies.keys():raise ValueError('Unknown supply rail')
        supplies.update(supplies_v)
    if (any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in supplies.values())
            or not supplies['VDD']>supplies['VMID']>supplies['VSS']
            or not math.isfinite(temperature_c) or temperature_c<=-273.15):
        raise ValueError('Require finite ordered supply rails and physical temperature')
    trit_volts={-1:supplies['VSS'],0:supplies['VMID'],1:supplies['VDD']}
    if not vectors or any(len(row) != len(inputs) or any(v not in TRIT_VOLTS for v in row) for row in vectors):
        raise ValueError('Input vectors must contain one valid trit per input')
    if not (0 < step_s <= hold_s and 0 < edge_s < hold_s - 1e-9):
        raise ValueError('Require positive step, edge and >1 ns checking margin after each edge')
    from tritflow.synth.writers import spice_names
    logical = inputs + outputs
    names = spice_names(logical, ('VDD', 'VMID', 'VSS', '0'))
    definitions = subcircuits(subckts)
    safe_top = spice_names([top])[top]
    try:
        definition = definitions.get(top.lower(), definitions.get(safe_top.lower()))
        pins = definition['pins']
    except (KeyError, TypeError) as exc:
        raise ValueError(f'Missing .subckt {top}') from exc
    if definition is None: raise ValueError(f'Missing .subckt {top}')
    annotated = logical_spice_names(subckts)
    encoded_for = {name: encoded for encoded, name in annotated.items()}
    decoded = {encoded_for.get(name, name): name for name in logical
               if encoded_for.get(name, name) in pins}
    if len(set(logical)) != len(logical) or set(decoded.values()) != set(logical) or len(decoded) != len(logical):
        raise ValueError(f'Input/output pins do not match {top}: {pins}')
    declared = {p.lower() for p in pins if p not in decoded}
    if declared-{'vdd','vmid','vss'}:
        raise ValueError(f'Input/output pins do not match {top}: {pins}')
    if not {'vdd', 'vss'} <= declared:
        raise ValueError('VDD and VSS supply pins are required')
    # Formal order stays positional. Rewrite exact tokens in this top only;
    # SPICE must never see two formals differing only in case.
    rename = {p: names[name] for p, name in decoded.items()}
    rewritten = rename_formal_nodes(definition, rename)
    subckts = subckts.replace(definition['text'], rewritten, 1)
    pins = [rename.get(p, p) for p in pins]
    models = model_includes() if pdk is None else model_includes(pdk)
    lines = ['TritFlow ternary testbench', models, simulation_netlist(subckts),
             f'.temp {temperature_c:g}', '.options rshunt=1e12',
             *(f'{rail} {rail} 0 {value:g}' for rail,value in supplies.items()),
             'Xdut ' + ' '.join(pins) + f' {definition["name"]}']
    for col, pin in enumerate(inputs):
        points = [f'0 {trit_volts[vectors[0][col]]:g}']
        for k in range(1, len(vectors)):
            points.extend([f'{k * hold_s:.15g} {trit_volts[vectors[k-1][col]]:g}',
                           f'{k * hold_s + edge_s:.15g} {trit_volts[vectors[k][col]]:g}'])
        # Explicit DC value: ngspice 42 (Colab's apt package) takes 0 V for a bare PWL
        # source in .dc, which silently ignored the held inputs of dc_transfer.
        lines.append(f'Vin{col} {names[pin]} 0 DC {trit_volts[vectors[0][col]]:g} PWL(' + ' '.join(points) + ')')
    for i, pin in enumerate(outputs):
        load = loads_f.get(pin, 0) if isinstance(loads_f, dict) else loads_f
        if load < 0:
            raise ValueError('Load capacitance cannot be negative')
        if load:
            lines.append(f'Cload{i} {names[pin]} 0 {load:.15g}')
    guesses = {pin: trit_volts[(initial_outputs or {}).get(pin, 0)] for pin in outputs}
    guesses.update(nodeset or {})
    for pin, voltage in guesses.items():
        lines.append(f'.nodeset v({names.get(pin,pin)})={voltage:.15g}')
    probes = [f'v({names[p]})' for p in logical] + ['i(vdd)', 'i(vmid)', 'i(vss)']
    return dict(netlist='\n'.join(lines), commands=f'tran {step_s:.15g} {len(vectors)*hold_s:.15g} 0 {step_s:.15g}',
                probes=probes, vectors=vectors, inputs=inputs, outputs=outputs,
                hold_s=hold_s, edge_s=edge_s, step_s=step_s,supplies_v=supplies,temperature_c=temperature_c,
                signal_names=names)


def simulate(subckts: str, top: str, inputs: list[str], outputs: list[str], vectors,
             expected=None, *, timeout=120, workdir=None, **kwargs) -> dict:
    """Return numpy waveforms plus per-vector levels, settling and rail currents.

    expected(vector) returns {output_pin: ideal_trit}. Raw currents follow SPICE
    voltage-source convention: positive from rail into the ideal source.
    """
    vectors = list(vectors)
    if expected is not None and vectors and 'initial_outputs' not in kwargs:
        kwargs['initial_outputs'] = expected(vectors[0])
    bench = build_testbench(subckts, top, inputs, outputs, vectors, **kwargs)
    run = run_ngspice(bench['netlist'], bench['commands'], bench['probes'], timeout=timeout, workdir=workdir)
    data = restore_signals(run['data'], bench)
    if 'time' not in data or data['time'][-1] < len(vectors)*bench['hold_s'] - bench['step_s'] * 1e-3:
        raise SimulationError('Transient ended before the requested final segment')
    result = {'waveforms': data, 'log': run['log'], 'stimulus': bench}
    if expected is not None:
        from .measure import measure_sequence
        result['measurements'] = measure_sequence(data, bench, expected)
    return result


def dc_transfer(subckts: str, top: str, inputs: list[str], outputs: list[str],
                sweep_pin: str, *, fixed_trits: dict | None = None,
                start_v=-5.0, stop_v=5.0, step_v=0.05, timeout=120, workdir=None, **kwargs) -> dict:
    """Sweep one ideal input voltage with the remaining inputs held at fixed trits."""
    if sweep_pin not in inputs or step_v == 0 or (stop_v-start_v)*step_v <= 0:
        raise ValueError('Invalid DC sweep pin or direction')
    vector = tuple((fixed_trits or {}).get(pin, 0) for pin in inputs)
    bench = build_testbench(subckts, top, inputs, outputs, [vector], **kwargs)
    source = f'Vin{inputs.index(sweep_pin)}'
    result = run_ngspice(bench['netlist'], f'dc {source} {start_v:g} {stop_v:g} {step_v:g}',
                       bench['probes'], timeout=timeout, workdir=workdir)
    result['data'] = restore_signals(result['data'], bench)
    return result
