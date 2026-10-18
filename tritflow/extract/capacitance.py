"""Lumped wire-to-substrate C from merged geometry; deliberately not signoff PEX."""
from __future__ import annotations
from pathlib import Path
import re

# No interconnect R/C deck is published in the installed PDK. Assumed SiO2
# effective heights 1/2 um: epsilon0*3.9/h = 0.03453/0.01727 fF/um².
# Fringe per perimeter is an explicit engineering assumption, 0.02 fF/um.
DEFAULT_CAP_COEFFICIENTS = {
    'M1': {'area_f_per_um2': 0.03453e-15, 'fringe_f_per_um': 0.02e-15},
    'M2': {'area_f_per_um2': 0.01727e-15, 'fringe_f_per_um': 0.02e-15}}
CAP_ASSUMPTION = ('Estimated substrate C only: SiO2 epsilon_r=3.9, effective M1/M2 heights '
                  '1/2 um, fringe=0.02 fF/um perimeter. Assumed, not PDK calibrated. '
                  'No coupling, shielding, via C or signal wire R; not signoff PEX.')


def _summary(regions, dbu, coefficients):
    result = {}
    for net, layers in regions.items():
        row = {'capacitance_f': 0., 'layers': {}}
        for layer, region in layers.items():
            region = region.merged()
            area, perimeter = region.area()*dbu**2, region.perimeter()*dbu
            c = coefficients[layer]
            if min(c['area_f_per_um2'], c['fringe_f_per_um']) < 0:
                raise ValueError('Capacitance coefficients cannot be negative')
            cap = area*c['area_f_per_um2'] + perimeter*c['fringe_f_per_um']
            row['layers'][layer] = {'area_um2': area, 'perimeter_um': perimeter, 'capacitance_f': cap}
            row['capacitance_f'] += cap
        result[net] = row
    return {'nets': result, 'coefficients': coefficients, 'assumptions': CAP_ASSUMPTION}


def wire_capacitance(pnr: dict, *, coefficients=None, dbu_um=0.001) -> dict:
    """Merge same-net/layer PNR wire and pin polygons before measuring A and P.

    This estimates routed interconnect only; device intrinsic capacitance stays
    in PDK models. Path ends are flush, matching KLayout's default Path rendering.
    Via pads are included when provided as wires/pins, not guessed from via cuts.
    """
    import klayout.db as db
    coefficients = DEFAULT_CAP_COEFFICIENTS if coefficients is None else coefficients
    if dbu_um <= 0:
        raise ValueError('dbu_um must be positive')
    regions = {}
    def add(net, layer, polygon):
        if layer not in coefficients:
            raise ValueError(f'No wire-C coefficients for {layer}')
        region = regions.setdefault(net, {}).setdefault(layer, db.Region())
        region.insert(polygon)
    for wire in pnr.get('wires', []):
        if wire['width'] <= 0 or len(wire['points']) < 2:
            raise ValueError('Wire needs positive width and at least two points')
        path = db.DPath([db.DPoint(*p) for p in wire['points']], wire['width'])
        add(wire['net'], wire['layer'], path.to_itype(dbu_um).polygon())
    for pin in pnr.get('pins', []):
        box = db.DBox(*pin['rect'])
        add(pin['name'], pin['layer'], box.to_itype(dbu_um))
    return _summary(regions, dbu_um, coefficients)


def gds_wire_capacitance(gds, lvs_report, *, top=None, coefficients=None) -> dict:
    """Measure per-top-net metal from actual GDS using LVS connectivity.

    The PDK report serializes anonymous layers. Locate the metal layer by exact
    polygon equality to the original GDS M1/M2, not by undocumented layer order.
    Top nets include recursively connected cell pin metal. Child-only local nets
    remain in child subcircuits and are outside this top-level estimate.
    """
    import klayout.db as db
    coefficients = DEFAULT_CAP_COEFFICIENTS if coefficients is None else coefficients
    layout = db.Layout(); layout.read(str(gds))
    cell = layout.cell(top) if top else layout.top_cell()
    if cell is None:
        raise ValueError(f'GDS top cell missing: {top}')
    lvs = db.LayoutVsSchematic(); lvs.read(str(lvs_report))
    if abs(lvs.internal_layout().dbu - layout.dbu) > 1e-12:
        raise ValueError('GDS and LVS database units differ')
    circuit = lvs.netlist().circuit_by_name(cell.name)
    if circuit is None:
        raise ValueError(f'LVS top circuit missing: {cell.name}')
    regions = {n.expanded_name(): {} for n in circuit.each_net()}
    excluded_metal = {}
    for metal, physical in (('M1', (13, 0)), ('M2', (20, 0))):
        target = db.Region(cell.begin_shapes_rec(layout.layer(*physical))).merged()
        if target.is_empty():
            continue
        candidates = []
        subsets = []
        for index in lvs.layer_indexes():
            try:
                layer = lvs.layer_by_index(index)
                united = layer.merged()
                if united.area() == target.area() and (united ^ target).is_empty():
                    candidates.append(layer)
                if united.area() > 0 and (united - target).is_empty():
                    subsets.append((united.area(),layer))
            except TypeError:  # text-only layer
                continue
        if not candidates and subsets:
            # purge_nets removes floating rail metal from the persisted database.
            # The connected metal layer is the unique largest geometric subset.
            largest=max(area for area,_ in subsets)
            candidates=[layer for area,layer in subsets if area==largest]
        if len(candidates) != 1:
            raise ValueError(f'Cannot uniquely identify {metal} in LVS report ({len(candidates)} matches)')
        excluded_metal[metal] = (target-candidates[0]).area()*layout.dbu**2
        for net in circuit.each_net():
            regions[net.expanded_name()][metal] = lvs.shapes_of_net(net, candidates[0], True)
    result = _summary(regions, layout.dbu, coefficients)
    result['scope'] = 'Actual top-net metal including connected cell pin metal; excludes child-only local nets and unconnected purged metal'
    result['excluded_unconnected_metal_um2'] = excluded_metal
    return result


def reference_net_map(lvs_report, top: str) -> dict:
    """Map matched reference top-net names to layout SPICE names via LVS xref."""
    import klayout.db as db
    result = db.LayoutVsSchematic(); result.read(str(lvs_report))
    circuit = result.netlist().circuit_by_name(top)
    if circuit is None:
        raise ValueError(f'LVS circuit missing: {top}')
    return {p.second().expanded_name(): p.first().expanded_name()
            for p in result.xref().each_net_pair(circuit) if p.first() and p.second()
            and p.status() == db.NetlistCrossReference.Match}


def append_wire_capacitance(spice: str, top: str, capacitances: dict, *, net_map=None) -> str:
    """Insert C statements inside top .subckt, rejecting unknown/new floating nets.

    Accept a wire_capacitance result or {net: farads}. Map reference names to
    extracted names with reference_net_map() when the extractor renames nets.
    """
    from tritflow.sim.spice import subcircuits
    definition = subcircuits(spice).get(top.lower())
    if definition is None:
        raise ValueError(f'Missing subcircuit {top}')
    # Parse only terminal nodes, never comments, parameters, models or device IDs.
    known = {p.lower() for p in definition['pins']}
    for line in re.sub(r'\n\s*\+\s*', ' ', definition['body']).splitlines():
        tokens = line.split()
        if not tokens or tokens[0][0].upper() not in 'XMRCLDV':
            continue
        prefix = tokens[0][0].upper()
        if prefix == 'X':
            last = next((i for i, t in enumerate(tokens) if '=' in t or t.lower() == 'params:'), len(tokens))
            nodes = tokens[1:last-1]
        else:
            nodes = tokens[1:5] if prefix == 'M' else tokens[1:3]
        known.update(n.lower() for n in nodes)
    raw = capacitances.get('nets', capacitances)
    mapped = {str(k).lower(): v for k, v in (net_map or {}).items()}
    lines = ['* Estimated lumped wire C to substrate (node 0); not signoff PEX']
    for index, (net, value) in enumerate(raw.items()):
        cap = value['capacitance_f'] if isinstance(value, dict) else value
        if cap < 0:
            raise ValueError('Wire capacitance cannot be negative')
        if not cap:
            continue
        node = mapped.get(net.lower(), net)
        if node.lower() not in known:
            # Expanded KLayout names use $1, while its SPICE writer uses \$1.
            if ('\\'+node).lower() in known:
                node = '\\'+node
            else:
                raise ValueError(f'Capacitance net {net} is absent from extracted {top}; supply an LVS net_map')
        device = f'Ctfwire{index}'
        if re.search(rf'(?im)^\s*{device}\s', definition['body']):
            raise ValueError('Wire capacitance has already been appended')
        lines.append(f'{device} {node} 0 {cap:.15g}')
    modified = re.sub(r'(?im)^\s*\.ends\b', '\n'.join(lines)+'\n.ends', definition['text'], count=1)
    return spice.replace(definition['text'], modified, 1)
