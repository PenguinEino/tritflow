"""DC rail resistance estimates from PNR centerlines and characterized currents."""
from __future__ import annotations
from collections import defaultdict
import warnings
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import MatrixRankWarning, spsolve
from tritflow import RAILS
from .technology import DEFAULT_SHEET_OHM, DEFAULT_VIA_OHM, EM_LIMITS

IR_ASSUMPTION = ('Constant nominal-bias cell currents; centerline sheet-R network. '
                 'Default metal sheet R=0.05 ohm/square and via R=0.05 ohm are '
                 'assumed, not PDK characterized; no package R, self-heating or '
                 'voltage-dependent current iteration. OS00 p9 resistor sheet values do not apply to metal; '
                 'no metal/TC/contact resistance found in the open PDFs/models. '
                 'Zero shift assumes equal divider conductances.')


def solve_resistive_network(edges, fixed_v: dict, injection_a: dict | None = None) -> dict:
    """Solve nodal KCL; edges=(node_a,node_b,ohm), positive current enters a node.

    Fixed-voltage pads are Dirichlet boundaries. Every connected component must
    have a pad; floating islands raise rather than silently regularizing them.
    """
    edges, injection_a = list(edges), injection_a or {}
    nodes = set(fixed_v) | set(injection_a)
    adjacency = defaultdict(set)
    for a, b, resistance in edges:
        if not np.isfinite(resistance) or resistance <= 0 or a == b:
            raise ValueError('Resistors must connect distinct nodes with finite positive resistance')
        nodes.update((a, b)); adjacency[a].add(b); adjacency[b].add(a)
    if not all(np.isfinite(v) for v in [*fixed_v.values(), *injection_a.values()]):
        raise ValueError('Voltage and current values must be finite')
    remaining = set(nodes)
    while remaining:
        stack, component = [remaining.pop()], set()
        while stack:
            node = stack.pop()
            if node in component: continue
            component.add(node)
            stack.extend(adjacency[node] - component)
        remaining -= component
        if not component & fixed_v.keys():
            raise ValueError(f'Floating rail component has no supply pad: {next(iter(component))}')
    unknown = sorted(nodes-fixed_v.keys(), key=repr)
    index = {node: k for k, node in enumerate(unknown)}
    row, col, values = [], [], []
    rhs = np.array([injection_a.get(n, 0) for n in unknown], dtype=float)
    for a, b, resistance in edges:
        g = 1/resistance
        for node, other in ((a, b), (b, a)):
            if node in fixed_v: continue
            i = index[node]; row.append(i); col.append(i); values.append(g)
            if other in fixed_v:
                rhs[i] += g*fixed_v[other]
            else:
                row.append(i); col.append(index[other]); values.append(-g)
    solved = dict(fixed_v)
    if unknown:
        matrix = coo_matrix((values, (row, col)), shape=(len(unknown), len(unknown))).tocsc()
        with warnings.catch_warnings():
            warnings.simplefilter('error', MatrixRankWarning)
            voltage = spsolve(matrix, rhs)
        if not np.isfinite(voltage).all():
            raise ValueError('Rail network solution is non-finite')
        solved.update(zip(unknown, map(float, voltage)))
    pad_current = {n: -injection_a.get(n, 0) for n in fixed_v}
    for a, b, resistance in edges:
        current = (solved[a]-solved[b])/resistance
        if a in pad_current: pad_current[a] += current
        if b in pad_current: pad_current[b] -= current
    return {'voltage_v': solved, 'pad_injection_a': pad_current}


def _project(point, segment):
    x, y = point; a, b = segment['a'], segment['b']
    if a[0] == b[0]:
        projected = (a[0], min(max(y, min(a[1], b[1])), max(a[1], b[1])))
    else:
        projected = (min(max(x, min(a[0], b[0])), max(a[0], b[0])), a[1])
    distance = abs(x-projected[0])+abs(y-projected[1])
    return projected, distance


def _rail_graph(pnr, rail, taps, sheet, via_ohm):
    power = pnr['power']
    segments = []
    for wire in power.get('straps', []) + power.get('rails', []):
        if wire['net'] != rail: continue
        for a, b in zip(wire['points'], wire['points'][1:]):
            a, b = tuple(a), tuple(b)
            if a == b: continue
            if (a[0] != b[0] and a[1] != b[1]) or wire['width'] <= 0:
                raise ValueError('IR geometry requires Manhattan conductors of positive width')
            segments.append({'a': a, 'b': b, 'layer': wire['layer'], 'width': wire['width'], 'cuts': {a, b}})
    if not segments:
        raise ValueError(f'No conductor geometry for rail {rail}')
    def key(segment, point):
        return (segment['layer'], round(point[0], 6), round(point[1], 6))
    def attach(point, layer):
        candidates = []
        for i, segment in enumerate(segments):
            if segment['layer'] != layer: continue
            projected, distance = _project(point, segment)
            if distance <= segment['width']/2 + 1e-6:
                candidates.append((distance, i, projected))
        if not candidates:
            raise ValueError(f'{rail} {layer}: tap/pad/via at {point} touches no conductor')
        _, i, projected = min(candidates)
        segments[i]['cuts'].add(projected)
        return key(segments[i], projected)
    # Same-layer crossings and collinear conductor endpoints share graph nodes.
    for i, a in enumerate(segments):
        for b in segments[i+1:]:
            if a['layer'] != b['layer']: continue
            candidates = [a['a'], a['b'], b['a'], b['b'],
                          (a['a'][0], b['a'][1]), (b['a'][0], a['a'][1])]
            for point in candidates:
                if _project(point, a)[1] < 1e-6 and _project(point, b)[1] < 1e-6:
                    a['cuts'].add(point); b['cuts'].add(point)
    via_edges, details = [], []
    for via in power.get('vias', []):
        if via['net'] != rail: continue
        point = (via['x'], via['y'])
        a, b = attach(point, 'M1'), attach(point, 'M2')
        via_edges.append((a, b, via_ohm))
        details.append({'kind':'TC','net':rail,'x_um':point[0],'y_um':point[1],
                        'limit_a':EM_LIMITS['TC']['current_a']})
    tap_nodes = {inst: attach(point, 'M1') for inst, point in taps.items()}
    pins = power.get('pins', []) + pnr.get('pins', [])
    fixed = {}
    for pin in pins:
        if pin['name'] != rail: continue
        x0, y0, x1, y1 = pin['rect']
        fixed[attach(((x0+x1)/2, (y0+y1)/2), pin['layer'])] = {'VDD': 5., 'VMID': 0., 'VSS': -5.}[rail]
    edges = list(via_edges)
    for segment in segments:
        points = sorted(segment['cuts'])
        for a, b in zip(points, points[1:]):
            length = abs(a[0]-b[0])+abs(a[1]-b[1])
            if length:
                edges.append((key(segment, a), key(segment, b), sheet[segment['layer']]*length/segment['width']))
                kind = 'M1_step' if segment['layer']=='M1' else 'M2_field'
                limit = EM_LIMITS[kind]
                details.append({'kind':kind,'net':rail,'width_um':segment['width'],
                    'limit_a':limit['current_a']*segment['width']/limit['width_um']})
    return edges, fixed, tap_nodes, details


def estimate_ir_drop(pnr: dict, template: dict, abstracts: dict, characterizations: dict, *,
                     instance_vectors: dict | None = None, sheet_ohm=None, via_ohm=DEFAULT_VIA_OHM) -> dict:
    """Use PNR power rails/straps/vias/pins plus char.json signed DC currents.

    abstracts/characterizations map CELL name to the corresponding JSON object.
    Without instance_vectors, independently choose the largest-magnitude current
    per rail per cell: a conservative envelope, not one realizable logic vector.
    Taps use the cell center on each template rail. Report divider zero shift for
    INV/NAND/NOR only; NANY's zero clamp uses its local VMID instead.
    """
    sheet = DEFAULT_SHEET_OHM if sheet_ohm is None else sheet_ohm
    if via_ohm <= 0 or any(v <= 0 for v in sheet.values()):
        raise ValueError('Sheet and via resistances must be positive')
    placements = pnr['placements']
    if len({p['inst'] for p in placements}) != len(placements):
        raise ValueError('Duplicate placement instance names')
    currents = {}
    for p in placements:
        rows = characterizations[p['cell']]['dc']
        if instance_vectors is not None:
            vector = list(instance_vectors[p['inst']])
            rows = [r for r in rows if r['input_trits'] == vector]
        if not rows:
            raise ValueError(f"Missing characterized current for {p['inst']}")
        currents[p['inst']] = {rail: max((r['rail_current_a'][rail] for r in rows), key=abs) for rail in RAILS}
    result = {p['inst']: {'cell': p['cell'], 'rail_v': {}, 'rail_current_a': currents[p['inst']]} for p in placements}
    pad_current, em_rows = {}, []
    for rail in RAILS:
        y0, y1 = template['rails'][rail]
        taps = {p['inst']: (p['x']+abstracts[p['cell']]['width']/2, p['y']+(y0+y1)/2) for p in placements}
        edges, fixed, nodes, details = _rail_graph(pnr, rail, taps, sheet, via_ohm)
        injection = defaultdict(float)
        for inst, node in nodes.items(): injection[node] += currents[inst][rail]
        solved = solve_resistive_network(edges, fixed, injection)
        for (a,b,resistance), detail in zip(edges,details):
            current = abs((solved['voltage_v'][a]-solved['voltage_v'][b])/resistance)
            em_rows.append(dict(detail,current_a=current,utilization=current/detail['limit_a']))
        pad_current[rail] = float(sum(solved['pad_injection_a'].values()))
        for inst, node in nodes.items(): result[inst]['rail_v'][rail] = solved['voltage_v'][node]
    for values in result.values():
        v = values['rail_v']
        values['rail_deviation_v'] = {r: v[r]-n for r, n in zip(RAILS, (5, 0, -5))}
        values['zero_level_shift_v'] = (v['VDD']+v['VSS'])/2 if values['cell'] in ('INV', 'NAND', 'NOR') else None
        values['clamp_zero_shift_v'] = v['VMID'] if values['cell'] == 'NANY' else None
    return {'cells': result, 'pad_injection_a': pad_current,
            'sheet_ohm_per_square': sheet, 'via_ohm': via_ohm,
            'parameter_origin':{'sheet':'assumption' if sheet_ohm is None else 'caller override',
                                'via':'assumption' if via_ohm == DEFAULT_VIA_OHM else 'caller override'},
            'em_check':{'passed':all(r['utilization'] <= 1+1e-9 for r in em_rows),
                'max_utilization':max((r['utilization'] for r in em_rows),default=0),
                'worst_by_kind':{kind:max((r for r in em_rows if r['kind']==kind),key=lambda r:r['utilization'],default=None)
                                 for kind in ('M1_step','M2_field','TC')},
                'limits':EM_LIMITS,
                'scope':'DC power-network envelope only, linear width scaling; conservative M1 step rating used on all M1. No contact/signal/internal-cell or transient EM qualification; not sign-off.'},
            'current_mode': 'specified vector' if instance_vectors is not None else 'independent per-rail worst-magnitude envelope',
            'assumptions': IR_ASSUMPTION}
