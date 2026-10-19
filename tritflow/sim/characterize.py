"""Nominal PDK cell characterization: DC, AC input C, and all directed transitions."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import numpy as np

from tritflow import CELLS_DIR, PASS_BAND, PDK_ROOT
from .bench import build_testbench, input_vectors, simulate, restore_signals
from .spice import signal_waveform
from .runner import run_ngspice, SimulationError
from .tools import simulator_identity
from .spice import CELL_PINS
from .provenance import pdk_provenance

_ANALYSIS_SHA256 = {name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                   for name in ('characterize.py','bench.py','spice.py','runner.py','measure.py','cascade.py')}


def logic_value(cell: str, values) -> int:
    """Ideal ternary truth functions, including sign inversion after min/max."""
    if cell == 'INV': return -values[0]
    if cell == 'BUF': return values[0]
    if cell == 'NANY': return -max(-1, min(1, sum(values)))
    if cell == 'NAND': return -min(values)
    if cell == 'NOR': return -max(values)
    if cell in ('TIEP', 'TIEZ', 'TIEN'): return {'TIEP': 1, 'TIEZ': 0, 'TIEN': -1}[cell]
    raise ValueError(f'No logic function for {cell}')


def dc_operating_points(subckts, top, inputs, outputs, vectors, expected, *, timeout=120,
                        workdir=None, nodeset=None, **kwargs):
    """Solve a separate DC operating point for every bias (true static currents)."""
    rows = []
    for index, vector in enumerate(vectors):
        ideal = expected(vector)
        bench = build_testbench(subckts, top, inputs, outputs, [vector],
                                initial_outputs=ideal, loads_f=0,
                                nodeset=nodeset(vector) if callable(nodeset) else nodeset, **kwargs)
        folder = None if workdir is None else Path(workdir)/f'state_{index:03d}'
        data = run_ngspice(bench['netlist'], 'op', bench['probes'],
                           timeout=timeout, workdir=folder)['data']
        data = restore_signals(data, bench)
        out = {pin: float(signal_waveform(data, pin)[-1]) for pin in outputs}
        rails=bench['supplies_v'];levels={-1:rails['VSS'],0:rails['VMID'],1:rails['VDD']}
        errors = {pin: out[pin] - levels[ideal[pin]] for pin in outputs}
        rows.append({'input_trits': list(vector), 'output_v': out, 'error_v': errors,
                     'rail_current_a': {rail: float(data[f'i({rail.lower()})'][-1])
                                        for rail in ('VDD', 'VMID', 'VSS')},
                     'passed': all(abs(error) <= PASS_BAND for error in errors.values())})
    return rows


def input_capacitance(subckts, top, inputs, outputs, vectors, expected, *, frequency_hz=1e6, **kwargs):
    """Ceff = -Im(I(Vin))/(2πf), with 1 V small-signal AC on one input.

    Other inputs and all rails are AC grounded; outputs have no external load.
    This is the biased in-circuit driving-point capacitance, including Miller
    response, not oxide area or a pin-independent constant. Every DC bias is used.
    """
    if frequency_hz <= 0:
        raise ValueError('AC frequency must be positive')
    rows = []
    for vector in vectors:
        for index, pin in enumerate(inputs):
            bench = build_testbench(subckts, top, inputs, outputs, [vector], loads_f=0,
                                    initial_outputs=expected(vector), **kwargs)
            circuit = re.sub(rf'(?m)^(Vin{index} .*?)$', r'\1 AC 1', bench['netlist'])
            probe = f'imag(i(vin{index}))'
            data = run_ngspice(circuit, f'ac lin 1 {frequency_hz:g} {frequency_hz:g}', [probe])['data']
            capacitance = -float(data[probe][-1]) / (2*np.pi*frequency_hz)
            if not np.isfinite(capacitance) or capacitance < 0:
                raise SimulationError(f'Non-capacitive input admittance at {pin}: {capacitance:g} F')
            rows.append({'input_trits': list(vector), 'pin': pin, 'capacitance_f': capacitance})
    return rows


def characterize_cell(cell: str, subckts: str | None = None, *, top: str | None = None,
                      inputs: list | None = None, output: str = 'Y',
                      loads_f=(10e-15, 100e-15, 1e-12), hold_s=200e-9,
                      step_s=0.5e-9, destination: str | Path | None = None,
                      include_cascade=True, cascade_fanouts=(1,2,4,8), **kwargs) -> dict:
    """Characterize one cell; default source is CELLS' LVS-extracted subcircuit.

    JSON never contains NaN or infinity: an unsettled transition has null delay.
    Fanout uses measured self-loading and five-stage restoration by default.
    The isolated capacitance ratio remains available as a historical estimate.
    """
    cell = cell.upper()
    if cell not in CELL_PINS or cell == 'FILL':
        raise ValueError(f'Cannot characterize {cell}')
    source = CELLS_DIR / 'out' / cell / f'{cell}.ext.spice'
    if subckts is None:
        subckts = source.read_text()
    top = top or cell
    inputs = list(CELL_PINS[cell][:-1]) if inputs is None else inputs
    expected = lambda v: {output: logic_value(cell, v)}
    states = input_vectors(len(inputs))
    tour = input_vectors(len(inputs), transitions=True)
    dc = dc_operating_points(subckts, top, inputs, [output], states, expected, **kwargs)
    cap = input_capacitance(subckts, top, inputs, [output], states, expected, **kwargs)
    transients = []
    for load in loads_f:
        run = simulate(subckts, top, inputs, [output], tour, expected,
                       hold_s=hold_s, step_s=step_s, loads_f=load, **kwargs)
        measured = run['measurements']
        transients.append({'load_f': load, **measured})
    successful_loads = [r['load_f'] for r in transients if r['passed']]
    max_cap = max((r['capacitance_f'] for r in cap), default=0)
    available = max(successful_loads, default=0)
    fanout = min(4, int(available // max_cap)) if max_cap else None
    result = {'simulator': simulator_identity(), 'schema_version': 1, 'cell': cell, 'top': top, 'inputs': inputs, 'output': output,
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'source_sha256': hashlib.sha256(subckts.encode()).hexdigest(),
              'conditions': {'temperature_c': kwargs.get('temperature_c', 27),
                             'supplies_v': {'VDD': 5, 'VMID': 0, 'VSS': -5}, 'band_v': PASS_BAND,
                             'edge_s': kwargs.get('edge_s', 1e-9), 'hold_s': hold_s, 'step_s': step_s},
              'max_static_current_a': max((abs(i) for row in dc for i in row['rail_current_a'].values()), default=0),
              'dc': dc, 'input_capacitance': {'method': 'biased AC driving-point, unloaded output',
                                            'frequency_hz': 1e6, 'rows': cap, 'max_f': max_cap},
              'transient': transients,
              'fanout': {'suggested_max': fanout, 'tested_load_f': available,
                         'method': 'min(4, floor(largest passing tested load / maximum input C))',
                         'scope': 'nominal single-cell estimate; no PVT/path qualification'},
              'passed': all(r['passed'] for r in dc) and all(r['passed'] for r in transients)}
    model_dir = Path(kwargs.get('pdk', PDK_ROOT)).expanduser() / 'libs.tech/spice/models'
    result['model_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(model_dir.iterdir()) if p.is_file()}
    result['pdk_provenance'] = pdk_provenance(kwargs.get('pdk', PDK_ROOT))
    result['analysis_sha256'] = _ANALYSIS_SHA256
    if include_cascade and inputs:
        from .cascade import characterize_cascade, attach_cascade
        cascade = characterize_cascade(cell, subckts, fanouts=cascade_fanouts,
            hold_s=hold_s, step_s=step_s, top=top, inputs=inputs, output=output,
            pdk=kwargs.get('pdk'), temperature_c=kwargs.get('temperature_c',27), edge_s=kwargs.get('edge_s',1e-9))
        attach_cascade(result, cascade)
    if destination is not None:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,prefix=path.name,suffix='.tmp',delete=False) as stream:
            stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
            temporary = Path(stream.name)
        temporary.replace(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cell', choices=[c for c in CELL_PINS if c != 'FILL'])
    parser.add_argument('--spice', type=Path)
    parser.add_argument('--top')
    parser.add_argument('--inputs', nargs='*')
    parser.add_argument('--output', default='Y')
    parser.add_argument('--destination', type=Path)
    args = parser.parse_args()
    destination = args.destination or CELLS_DIR / 'out' / args.cell / f'{args.cell}.char.json'
    result = characterize_cell(args.cell, args.spice.read_text() if args.spice else None,
                               top=args.top, inputs=args.inputs, output=args.output, destination=destination)
    print(json.dumps({'passed': result['passed'], 'destination': str(destination), 'fanout': result['fanout']}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
