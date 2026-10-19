"""Source-level transistor/resistor sizing, with content-addressed DC caches.

Dimensions are in micrometres. A sweep changes only W/L on named schematic
instances, never connectivity or extracted junction geometry. These simulations
are an educational nominal-bias experiment, not layout or PVT qualification.
"""
from __future__ import annotations
from .provenance import pdk_provenance
from .tools import simulator_identity

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np
from tritflow import CELLS_DIR, PDK_ROOT, PASS_BAND, VDD, VMID, VSS
from tritflow.cells.circuits import circuits
from .bench import dc_transfer, input_vectors
from .characterize import dc_operating_points, logic_value
from .postlayout import _save, file_hash
from .runner import SimulationError

CACHE = CELLS_DIR/'out'/'sizing'
SCOPE = 'nominal source-level DC sizing; no layout/parasitic/PVT qualification'


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _analysis_hashes():
    return {name:file_hash(Path(__file__).with_name(name))
            for name in ('sizing.py','bench.py','runner.py','characterize.py','spice.py')}


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
        raise ValueError(f'{name} must be a finite number')
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f'{name} must be finite')
    return value


def _dimension_um(token):
    match = re.fullmatch(r'([+\-\d.eE]+)([a-zA-Z]*)', token)
    scales = {'': 1e6, 'u': 1., 'n': .001, 'm': 1e3, 'p': 1e-6}
    if not match or match[2].lower() not in scales:
        raise ValueError(f'Unsupported published SPICE dimension {token!r}')
    return float(match[1])*scales[match[2].lower()]


def published_dimensions(cell):
    """Resolve canonical IDs and W/L from the current published schematic text."""
    if cell not in ('INV', 'NAND', 'NOR', 'NANY'):
        raise ValueError('cell must be INV, NAND, NOR or NANY')
    circuit = circuits()[cell]
    ids = [row[0] for row in circuit.mos] + [row[0] for row in circuit.resistors]
    source = (CELLS_DIR/'out'/cell/f'{cell}.spice').read_text()
    dimensions = {}
    for device in ids:
        matches = re.findall(rf'(?im)^X{re.escape(device)}\s+(.+)$', source)
        if len(matches) != 1:
            raise ValueError(f'Published schematic must contain exactly one X{device}')
        dimensions[device] = {}
        for field, parameter in (('w_um', 'W'), ('l_um', 'L')):
            values = re.findall(rf'(?i)\b{parameter}\s*=\s*(\S+)', matches[0])
            if len(values) != 1:
                raise ValueError(f'Missing/ambiguous {parameter} on {device}')
            value = _dimension_um(values[0])
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f'Invalid published {parameter} on {device}')
            dimensions[device][field] = value
    return source, dimensions


def _variant(source, dimensions):
    for device, fields in dimensions.items():
        def replace(line):
            result = line[0]
            for field, parameter in (('w_um', 'W'), ('l_um', 'L')):
                result = re.sub(rf'(?i)\b{parameter}\s*=\s*\S+',
                                f'{parameter}={fields[field]:.15g}u', result)
            return result
        source = re.sub(rf'(?im)^X{re.escape(device)}\s+.+$', replace, source)
    return source


def _json_native(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {key: _json_native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_native(item) for item in value]
    return value


def sweep_dimensions(
    cell: str,
    candidates: Sequence[Mapping[str, Mapping[str, float]]],
    *,
    sweep_pin: str = 'A',
    fixed_trits: Mapping[str, int] | None = None,
    start_v: float = -5.0,
    stop_v: float = 5.0,
    step_v: float = 0.1,
    temperature_c: float = 27.0,
    pdk: str | Path | None = None,
    workdir: str | Path | None = None,
    timeout: float = 120.0,
) -> dict:
    """Return FRONTEND's sizing rows, automatically including the baseline once.

    Unspecified devices/dimensions inherit the published schematic. All logical
    states are solved separately for level error and signed static rail currents.
    Successful rows are cached by source, models, analysis code and conditions;
    repeat slider calls need no simulator. Supplying workdir forces execution
    and retains decks/logs there. Solver failures remain explicit failed rows.
    """
    source, baseline = published_dimensions(cell)
    inputs = list(circuits()[cell].inputs)
    if sweep_pin not in inputs:
        raise ValueError(f'Unknown sweep input {sweep_pin}')
    if fixed_trits is not None and not isinstance(fixed_trits, Mapping):
        raise ValueError('fixed_trits must map nonswept input pins to trits')
    fixed = dict(fixed_trits or {})
    if any(pin not in inputs or pin == sweep_pin or isinstance(v, bool) or v not in (-1, 0, 1)
           for pin, v in fixed.items()):
        raise ValueError('fixed_trits must give valid trits on nonswept inputs')
    fixed = {pin: int(fixed.get(pin, 0)) for pin in inputs if pin != sweep_pin}
    start_v, stop_v, step_v = (_number(v, name) for name, v in
                              [('start_v',start_v), ('stop_v',stop_v), ('step_v',step_v)])
    temperature_c = _number(temperature_c, 'temperature_c')
    timeout = _number(timeout, 'timeout')
    if (stop_v-start_v)*step_v <= 0 or timeout <= 0 or temperature_c <= -273.15:
        raise ValueError('Invalid sweep direction, temperature or timeout')
    resolved = [baseline]
    seen = {_digest(baseline)}
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError('Each candidate must map device IDs to W/L')
        dimensions = {key: dict(value) for key, value in baseline.items()}
        for device, fields in candidate.items():
            if device not in baseline or not isinstance(fields, Mapping):
                raise ValueError(f'Unknown device or invalid dimensions: {device}')
            for field, value in fields.items():
                if field not in ('w_um', 'l_um'):
                    raise ValueError(f'Unknown dimension {device}.{field}')
                value = _number(value, f'{device}.{field}')
                if value <= 0:
                    raise ValueError('Dimensions must be positive')
                dimensions[device][field] = value
        digest = _digest(dimensions)
        if digest not in seen:
            resolved.append(dimensions)
            seen.add(digest)
    root = PDK_ROOT if pdk is None else Path(pdk).expanduser().resolve()
    models = {p.name: file_hash(p) for p in sorted((root/'libs.tech/spice/models').iterdir()) if p.is_file()}
    conditions = dict(simulator=simulator_identity(), supplies_v={'VDD':VDD, 'VMID':VMID, 'VSS':VSS}, temperature_c=temperature_c,
                      band_v=PASS_BAND, sweep_pin=sweep_pin, fixed_trits=fixed,
                      start_v=start_v, stop_v=stop_v, step_v=step_v)
    result = dict(pdk_provenance=pdk_provenance(root),cell=cell, source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  model_sha256=models, device_ids=list(baseline), adopted_index=0,
                  conditions=conditions, rows=[], scope=SCOPE)
    code = _analysis_hashes()
    result['analysis_sha256'] = code
    # The published grid travels with the notebook; local per-row caches are
    # disposable. Grid candidates must stay instant even in a fresh checkout.
    published = {}
    grid_path = CACHE/f'{cell}.grid.json'
    if workdir is None and grid_path.is_file():
        grid = json.loads(grid_path.read_text())
        if all(grid.get(key)==result[key] for key in
               ('source_sha256','model_sha256','analysis_sha256','conditions')):
            published = {_digest(row['dimensions']):row for row in grid['rows']}
    cache = CACHE/'rows'/cell
    cache.mkdir(parents=True, exist_ok=True)
    for index, dimensions in enumerate(resolved):
        key = _digest(dict(source=result['source_sha256'], models=models, code=code,
                           dimensions=dimensions, conditions=conditions))
        path = cache/f'{key}.json'
        if workdir is None and _digest(dimensions) in published:
            row = published[_digest(dimensions)]
        elif workdir is None and path.is_file():
            row = json.loads(path.read_text())
        else:
            folder = None if workdir is None else Path(workdir)/f'candidate_{index:03d}'
            variant = _variant(source, dimensions)
            row = dict(dimensions=dimensions, is_adopted=(dimensions == baseline),
                       transfer=None, dc=[], max_error_v=None, max_static_current_a=None,
                       passed=False, error=None)
            try:
                row['transfer'] = _json_native(dc_transfer(variant, cell, inputs, ['Y'], sweep_pin,
                    fixed_trits=fixed, start_v=start_v, stop_v=stop_v, step_v=step_v,
                    temperature_c=temperature_c, pdk=root, timeout=timeout,
                    workdir=None if folder is None else folder/'transfer'))
                row['dc'] = dc_operating_points(variant, cell, inputs, ['Y'],
                    input_vectors(len(inputs)), lambda v: {'Y':logic_value(cell, v)},
                    temperature_c=temperature_c, pdk=root, timeout=timeout,
                    workdir=None if folder is None else folder/'dc')
                # These DC networks have only rail-bounded inputs and passive
                # loads. A finite Newton root far outside the rails is not a
                # physically meaningful sizing point, even if ngspice exits 0.
                voltages = list(row['transfer']['data']['v(y)'])
                voltages += [state['output_v']['Y'] for state in row['dc']]
                if any(v < VSS-PASS_BAND or v > VDD+PASS_BAND for v in voltages):
                    raise SimulationError('Nonphysical DC output outside supply rails; '
                                          'model/solver root rejected (raw data retained)')
                row['max_error_v'] = max(abs(v) for state in row['dc'] for v in state['error_v'].values())
                row['max_static_current_a'] = max(abs(v) for state in row['dc'] for v in state['rail_current_a'].values())
                row['passed'] = all(state['passed'] for state in row['dc'])
            except (SimulationError, OSError) as error:
                row['error'] = f'{type(error).__name__}: {error}'
            if row['error'] is None:
                _save(path, row)
        result['rows'].append(row)
    return result


def precompute_grid(cell='INV'):
    """Publish a small Cartesian grid for instant chapter-2 slider selection.

    INV varies MP/MN widths independently, common MOS L, and both RR lengths.
    NANY varies all MOS widths by one factor, common MOS L and both RR lengths.
    The adopted dimensions are read from the source, never a plot constant.
    """
    from itertools import product
    _, base = published_dimensions(cell)
    mos = [m[0] for m in circuits()[cell].mos]
    rr = [r[0] for r in circuits()[cell].resistors]
    candidates = []
    if cell == 'INV':
        axes = {'mp_w_um':[9.,11.,base['MP']['w_um'],16.,19.],
                'mn_w_um':[3.5,base['MN']['w_um'],6.5],
                'mos_l_um':[1.,2.], 'rr_l_um':[20.,30.,45.]}
        for wp, wn, length, rr_length in product(*axes.values()):
            candidates.append({'MP':{'w_um':wp,'l_um':length}, 'MN':{'w_um':wn,'l_um':length},
                               **{r:{'l_um':rr_length} for r in rr}})
    elif cell == 'NANY':
        axes = {'mos_width_factor':[.75,1.,1.25], 'mos_l_um':[1.,2.], 'rr_l_um':[20.,30.,45.]}
        for factor, length, rr_length in product(*axes.values()):
            candidates.append({**{m:{'w_um':base[m]['w_um']*factor,'l_um':length} for m in mos},
                               **{r:{'l_um':rr_length} for r in rr}})
    else:
        raise ValueError('Precomputed grids are INV and NANY')
    result = sweep_dimensions(cell, candidates)
    result['grid_axes'] = axes
    _save(CACHE/f'{cell}.grid.json', result)
    return result


def load_grid(cell='INV'):
    """Load the published grid and reject a different schematic/model revision."""
    result = json.loads((CACHE/f'{cell}.grid.json').read_text())
    source, _ = published_dimensions(cell)
    models = {p.name:file_hash(p) for p in sorted((PDK_ROOT/'libs.tech/spice/models').iterdir()) if p.is_file()}
    if (result['source_sha256'] != hashlib.sha256(source.encode()).hexdigest()
            or result['model_sha256'] != models or result.get('analysis_sha256') != _analysis_hashes()):
        raise RuntimeError('Sizing grid is stale; run python3 -m tritflow.sim.sizing')
    return result


if __name__ == '__main__':
    for name in ('INV', 'NANY'):
        grid = precompute_grid(name)
        print(f'{name}: {len(grid["rows"])} candidates; {sum(r["passed"] for r in grid["rows"])} PASS', flush=True)
