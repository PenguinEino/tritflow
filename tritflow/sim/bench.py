"""Ternary PWL stimuli, rail current probes, and notebook-friendly simulation."""
from __future__ import annotations

from itertools import product

from tritflow import TRIT_VOLTS, VDD, VMID, VSS
from .runner import run_ngspice, SimulationError
from .spice import subcircuits, simulation_netlist, model_includes


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
                    pdk=None, temperature_c: float = 27) -> dict:
    """Drive any subckt by its declared pins; input vectors contain trits, not volts.

    Edges begin at k*hold_s. Outputs and optional hierarchical internal nodes get
    .nodeset initial guesses, never .ic/uic constraints on the transient solution.
    """
    vectors = [tuple(row) for row in vectors]
    if not vectors or any(len(row) != len(inputs) or any(v not in TRIT_VOLTS for v in row) for row in vectors):
        raise ValueError('Input vectors must contain one valid trit per input')
    if not (0 < step_s <= hold_s and 0 < edge_s < hold_s - 1e-9):
        raise ValueError('Require positive step, edge and >1 ns checking margin after each edge')
    definitions = subcircuits(subckts)
    try:
        pins = definitions[top.lower()]['pins']
    except KeyError as exc:
        raise ValueError(f'Missing .subckt {top}') from exc
    declared = {p.lower() for p in pins}
    signal = {p.lower() for p in inputs + outputs}
    if len(signal) != len(inputs + outputs) or declared - {'vdd', 'vmid', 'vss'} != signal:
        raise ValueError(f'Input/output pins do not match {top}: {pins}')
    if not {'vdd', 'vss'} <= declared:
        raise ValueError('VDD and VSS supply pins are required')
    models = model_includes() if pdk is None else model_includes(pdk)
    lines = ['TritFlow ternary testbench', models, simulation_netlist(subckts),
             f'.temp {temperature_c:g}', '.options rshunt=1e12',
             f'VDD VDD 0 {VDD:g}', f'VMID VMID 0 {VMID:g}', f'VSS VSS 0 {VSS:g}',
             'Xdut ' + ' '.join(pins) + f' {top}']
    for col, pin in enumerate(inputs):
        points = [f'0 {TRIT_VOLTS[vectors[0][col]]:g}']
        for k in range(1, len(vectors)):
            points.extend([f'{k * hold_s:.15g} {TRIT_VOLTS[vectors[k-1][col]]:g}',
                           f'{k * hold_s + edge_s:.15g} {TRIT_VOLTS[vectors[k][col]]:g}'])
        lines.append(f'Vin{col} {pin} 0 PWL(' + ' '.join(points) + ')')
    for i, pin in enumerate(outputs):
        load = loads_f.get(pin, 0) if isinstance(loads_f, dict) else loads_f
        if load < 0:
            raise ValueError('Load capacitance cannot be negative')
        if load:
            lines.append(f'Cload{i} {pin} 0 {load:.15g}')
    guesses = {pin: TRIT_VOLTS[(initial_outputs or {}).get(pin, 0)] for pin in outputs}
    guesses.update(nodeset or {})
    for pin, voltage in guesses.items():
        lines.append(f'.nodeset v({pin})={voltage:.15g}')
    probes = [f'v({p})' for p in inputs + outputs] + ['i(vdd)', 'i(vmid)', 'i(vss)']
    return dict(netlist='\n'.join(lines), commands=f'tran {step_s:.15g} {len(vectors)*hold_s:.15g} 0 {step_s:.15g}',
                probes=probes, vectors=vectors, inputs=inputs, outputs=outputs,
                hold_s=hold_s, edge_s=edge_s, step_s=step_s)


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
    data = run['data']
    if 'time' not in data or data['time'][-1] < len(vectors)*bench['hold_s'] - bench['step_s'] * 1e-3:
        raise SimulationError('Transient ended before the requested final segment')
    result = {'waveforms': data, 'log': run['log'], 'stimulus': bench}
    if expected is not None:
        from .measure import measure_sequence
        result['measurements'] = measure_sequence(data, bench, expected)
    return result


def dc_transfer(subckts: str, top: str, inputs: list[str], outputs: list[str],
                sweep_pin: str, *, fixed_trits: dict | None = None,
                start_v=-5.0, stop_v=5.0, step_v=0.05, **kwargs) -> dict:
    """Sweep one ideal input voltage with the remaining inputs held at fixed trits."""
    if sweep_pin not in inputs or step_v == 0 or (stop_v-start_v)*step_v <= 0:
        raise ValueError('Invalid DC sweep pin or direction')
    vector = tuple((fixed_trits or {}).get(pin, 0) for pin in inputs)
    bench = build_testbench(subckts, top, inputs, outputs, [vector], **kwargs)
    source = f'Vin{inputs.index(sweep_pin)}'
    return run_ngspice(bench['netlist'], f'dc {source} {start_v:g} {stop_v:g} {step_v:g}', bench['probes'])
