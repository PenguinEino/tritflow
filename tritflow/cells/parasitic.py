"""Compare taped-out and compact cells with SIM's estimated GDS metal capacitance.

Keep the strict device-only identity proof separate. Added C is geometry-dependent,
so both circuits must pass the original electrical checks, but their settling times
need not coincide. Poly resistance is assessed geometrically, not silently simulated
as a calibrated distributed RC model.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile

import klayout.db as db

from tritflow import CELLS_DIR, PDK_ROOT
from tritflow.extract import (append_wire_capacitance, gds_wire_capacitance,
                              reference_net_map)
from tritflow.sim.spice import simulation_netlist
from .equivalence import compare_cell, compare_chain
from .reference import ORIGINALS, prepare, prepare_buf, sha

DEVICE_SCOPE = ('Device-level identity only: neither extraction includes interconnect '
                'parasitics. Identical numbers do not prove physical layout performance equivalence.')
POLY_SHEET_OHM = 20.0
PUBLIC = {'VIN': 'A', 'VOUT': 'Y', 'V+': 'VDD', 'V-': 'VSS'}


def public_name(name):
    """Canonicalize only the independent source's public signal/rail names."""
    return PUBLIC.get(name.upper(), name.upper())


def capacitance_view(gds, report, top, text, cell):
    """Use the public SIM APIs, retaining LVS correspondence for every net."""
    caps = gds_wire_capacitance(gds, report, top=top)
    mapping = reference_net_map(report, top)
    inverse = {layout: public_name(reference) for reference, layout in mapping.items()}
    if set(caps['nets']) != set(inverse):
        raise ValueError(f'{cell}: incomplete LVS net correspondence')
    # Public ports were canonicalized in the original extracted SPICE; anonymous
    # internal nodes retain their original extraction names (including $ escapes).
    spice_map = {net: PUBLIC.get(net.upper(), net) for net in caps['nets']}
    annotated = append_wire_capacitance(text, cell, caps, net_map=spice_map)
    named = {inverse[net]: {**row, 'extracted_net': spice_map[net]}
             for net, row in caps['nets'].items()}
    caps.update(reference_nets=named, reference_to_layout_net=mapping,
                gds_sha256=sha(gds), lvs_report_sha256=sha(report),
                annotated_sha256=None)
    return annotated, caps


def two_inv_capacitance(inv_caps, buf_text):
    """Two original INV macros with ideal connecting wires, not a taped-out BUF.

    Sum Y(first)+A(second) on MID and both supply capacitances. Do not invent
    geometric overlap or an original inter-macro routed connection.
    """
    named = {}
    for stage in (0, 1):
        public = {'A': 'A' if stage == 0 else 'MID', 'Y': 'MID' if stage == 0 else 'Y',
                  'VDD': 'VDD', 'VMID': 'VMID', 'VSS': 'VSS'}
        for reference, row in inv_caps['reference_nets'].items():
            key = public.get(reference, f'STAGE{stage}_{reference}')
            node = public.get(reference)
            if node is not None:
                node = 'mid' if node == 'MID' else node
            else:
                extracted = row['extracted_net']
                if extracted.startswith('$'):
                    extracted = '\\' + extracted
                node = f'stage{stage}_' + simulation_netlist(extracted)
            target = named.setdefault(key, {'capacitance_f': 0., 'layers': {}, 'extracted_net': node})
            target['capacitance_f'] += row['capacitance_f']
            for layer, geometry in row['layers'].items():
                values = target['layers'].setdefault(layer, {k: 0. for k in geometry})
                for k, value in geometry.items():
                    values[k] += value
    caps = {'nets': {v['extracted_net']: v for v in named.values()}, 'reference_nets': named,
            'coefficients': inv_caps['coefficients'], 'assumptions': inv_caps['assumptions'],
            'scope': 'Two original extracted INV macros; ideal inter-macro connection, no added route. No taped-out BUF exists.'}
    return append_wire_capacitance(buf_text, 'BUF', caps), caps


def net_comparison(original, compact):
    """Compare by independently matched schematic net, never anonymous net number."""
    left, right = original['reference_nets'], compact['reference_nets']
    if set(left) != set(right):
        raise ValueError(f'Original/compact reference nets differ: {set(left) ^ set(right)}')
    rows = {}
    for name in sorted(left):
        a, b = left[name]['capacitance_f'], right[name]['capacitance_f']
        rows[name] = {'original_f': a, 'compact_f': b, 'difference_f': b-a,
                      'original_extracted_net': left[name]['extracted_net'],
                      'compact_extracted_net': right[name]['extracted_net']}
    return rows


def poly_runs(gds, report, top):
    """Inventory long straight field-poly sections, excluding active and contacts.

    Orthogonal decomposition splits bends/widenings. L/W describes each listed
    straight rectangle, not a solved terminal-to-terminal resistance. Supply
    guard-ring sections are listed separately by net; they are not gate buses.
    """
    layout = db.Layout(); layout.read(str(gds)); cell = layout.cell(top)
    lvs = db.LayoutVsSchematic(); lvs.read(str(report))
    physical = db.Region(cell.begin_shapes_rec(layout.layer(8, 1))).merged()
    candidates = []
    for index in lvs.layer_indexes():
        try:
            layer = lvs.layer_by_index(index)
            if (layer.merged() ^ physical).is_empty():
                candidates.append(layer)
        except TypeError:
            pass
    if len(candidates) != 1:
        raise ValueError(f'{top}: cannot identify physical GC in LVS database')
    cut = db.Region(cell.begin_shapes_rec(layout.layer(3, 1)))
    cut += db.Region(cell.begin_shapes_rec(layout.layer(3, 2)))
    cut += db.Region(cell.begin_shapes_rec(layout.layer(11, 0)))
    inverse = {v: public_name(k) for k, v in reference_net_map(report, top).items()}
    rows = []
    for net in lvs.netlist().circuit_by_name(top).each_net():
        field = lvs.shapes_of_net(net, candidates[0], True) - cut
        for polygon in field.decompose_trapezoids_to_region().each():
            box = polygon.bbox()
            width, length = sorted((box.width()*layout.dbu, box.height()*layout.dbu))
            if not polygon.is_box() or width <= 0 or width > 3 or length < 10:
                continue
            name = inverse[net.expanded_name()]
            rows.append({'net': name, 'bbox_um': [v*layout.dbu for v in
                         (box.left, box.bottom, box.right, box.top)],
                         'length_um': length, 'width_um': width, 'squares': length/width,
                         'resistance_ohm': POLY_SHEET_OHM*length/width,
                         'sensitivity_5_to_100_ohm_per_square': [5*length/width, 100*length/width],
                         'role': 'supply_guard' if name in ('VDD','VMID','VSS') else 'signal_field_poly'})
    return sorted(rows, key=lambda r: (-r['resistance_ohm'], r['net'], r['bbox_um']))


def poly_assumptions():
    """Do not mistake MOS diffusion RSH or resistor-poly RS for gate-poly GC."""
    models = PDK_ROOT/'libs.tech/spice/models'
    return {'layer': 'GC (8/1), gate/interconnect poly',
            'sheet_ohm_per_square': POLY_SHEET_OHM,
            'source': 'Documented engineering assumption; installed PDK has no calibrated GC sheet resistance.',
            'pdk_findings': 'F_RS uses 95*magRS ohm/square for resistor poly GR (8/2), not GC. MOS rsh=44.9607 models source/drain diffusion, not gate poly. Neither is substituted for GC.',
            'pdk_evidence_sha256': {p.name: sha(p) for p in
                                    (models/'models_IP62_res_v5.lib', models/'models_IP62_mos_v2.lib')},
            'method': 'R=Rsheet*L/W for straight rectangular field GC >=10 um long and <=3 um wide, after removing active and contact-cut areas. Orthogonal decomposition splits bends/widenings; these are segment estimates, not total gate-path resistances.',
            'limitations': 'No poly R/C added to transient simulation. No calibrated contact/spreading/distributed-poly model; sensitivity range 5..100 ohm/square. Input poly carries gate charging current; rail guard poly is not a logic-series bus.'}


def compare(out, reference=Path.home()/'balanced-ternary-logic'):
    """Run Phase 4 in a private complete-library stage, adding explicit scope."""
    out = Path(out).resolve()
    if out == (CELLS_DIR/'out').resolve():
        raise ValueError('Use publish_comparison for the live library; compare requires a private stage')
    report_path = out/'equivalence_report.json'
    base = json.loads(report_path.read_text())
    if not base['passed']:
        raise ValueError('Device-only equivalence must pass before the wire-C comparison')
    for cell, previous in base['schematic_equivalence'].items():
        if sha(out/cell/f'{cell}.gds') != previous['compact_gds_sha256'] or \
                sha(out/cell/f'{cell}.ext.spice') != previous['compact_extracted_sha256']:
            raise ValueError('Device-only proof is stale; run equivalence before parasitic')
    base['scope'] = DEVICE_SCOPE
    base['passed_scope'] = 'Device-level identity only; see parasitic_aware.passed for estimated wire-C checks.'
    base['interpretation'] = DEVICE_SCOPE + ' The parasitic_aware section is a separate assumed-metal-C experiment.'
    work = out/'equivalence/parasitic'
    proof = prepare(reference, work/'reference', out)
    original = {c: (work/'reference'/c/'original.ext.spice').read_text() for c in ORIGINALS}
    original['BUF'], proof['BUF'] = prepare_buf(original['INV'], work/'reference', out)
    compact = {c: (out/c/f'{c}.ext.spice').read_text() for c in original}
    annotated = {'original': {}, 'compact': {}}
    caps = {label: {} for label in annotated}
    poly = {}
    for cell in original:
        folder = work/cell; folder.mkdir(parents=True, exist_ok=True)
        ref = work/'reference'/cell
        if cell != 'BUF':
            gds = Path(reference).expanduser()/f'{ORIGINALS[cell]}.gds'
            old_report = ref/'lvs.lvsdb'
            annotated['original'][cell], caps['original'][cell] = capacitance_view(
                gds, old_report, ORIGINALS[cell], original[cell], cell)
            original_poly = poly_runs(gds, old_report, ORIGINALS[cell])
        else:
            annotated['original'][cell], caps['original'][cell] = two_inv_capacitance(caps['original']['INV'], original[cell])
            original_poly = [{**r, 'copy': i,
                              'net': 'MID' if i == 1 and r['net'] == 'A' else r['net']}
                             for i in (0,1) for r in poly['INV']['original']]
        current_report = ref/('lvs.lvsdb' if cell == 'BUF' else 'compact_lvs/lvs.lvsdb')
        annotated['compact'][cell], caps['compact'][cell] = capacitance_view(
            out/cell/f'{cell}.gds', current_report, cell, compact[cell], cell)
        poly[cell] = {'original': original_poly,
                      'compact': poly_runs(out/cell/f'{cell}.gds', current_report, cell)}
        for label in annotated:
            path = folder/f'{label}.wirec.spice'
            path.write_text(annotated[label][cell])
            caps[label][cell]['annotated_sha256'] = sha(path)
            (folder/f'{label}.capacitance.json').write_text(json.dumps(caps[label][cell], indent=2)+'\n')
    from tritflow.sim.provenance import pdk_provenance
    result = {'created_utc': datetime.now(timezone.utc).isoformat(),'pdk_provenance':pdk_provenance(),
              'scope': 'Nominal 27 C device models plus estimated actual-GDS connected M1/M2 lumped C to substrate. Not calibrated/signoff PEX; no poly C, coupling, shielding, via C, or signal-wire R.',
              'acceptance': 'Both layouts must pass the original +/-0.5 V bands, all original hold-time checkpoints, and DC identity. Timing differences are reported without a numerical identity requirement.',
              'interpretation': 'Added capacitors are open at DC, so DC levels and static currents should remain identical. Rail capacitors see ideal voltage sources; this is not rail IR/ground bounce simulation. Settling differences reflect estimated metal C only. Poly resistance remains an unmodeled concern assessed separately.',
              'dc_identity_tolerances': {'grid_voltage_v': 1e-4, 'static_current_a': 1e-9, 'chain_voltage_v': 1e-3},
              'conditions': base['conditions'], 'schematic_equivalence': proof,
              'capacitance_api': 'tritflow.extract.gds_wire_capacitance / append_wire_capacitance / reference_net_map',
              'capacitance_api_sha256': sha(Path(__file__).parents[1]/'extract/capacitance.py'),
              'coefficients': caps['original']['INV']['coefficients'],
              'capacitance_assumptions': caps['original']['INV']['assumptions'],
              'per_net_capacitance': {c: net_comparison(caps['original'][c], caps['compact'][c]) for c in original},
              'capacitance_details': caps, 'poly_resistance': {'assumptions': poly_assumptions(), 'cells': poly},
              'cells': {}, 'chains': {}}
    for cell in original:
        result['cells'][cell] = compare_cell(cell, annotated['original'][cell], annotated['compact'][cell],
                                             proof[cell], work/cell/'simulation', wire_c=True)
    for kind in ('inverter_two', 'nor_six', 'nany_six', 'mixed_six'):
        result['chains'][kind] = compare_chain(kind, annotated['original'], annotated['compact'], work/'chains'/kind, wire_c=True)
    result['passed'] = all(r['passed'] for r in result['cells'].values()) and all(r['passed'] for r in result['chains'].values())
    result['runner_sha256'] = {name: sha(Path(__file__).with_name(name)) for name in
                                ('parasitic.py','equivalence.py','regression.py','reference.py')}
    result['model_sha256'] = {p.name: sha(p) for p in sorted((PDK_ROOT/'libs.tech/spice/models').iterdir()) if p.is_file()}
    for cell in original:
        for suffix, key in [('gds', 'compact_gds_sha256'), ('ext.spice', 'compact_extracted_sha256')]:
            if sha(out/cell/f'{cell}.{suffix}') != proof[cell][key]:
                raise RuntimeError('Library changed during parasitic comparison')
    base['parasitic_aware'] = result
    temporary = out/'.equivalence_report.next.json'
    temporary.write_text(json.dumps(base, indent=2, allow_nan=False)+'\n')
    temporary.replace(report_path)
    return result


def publish_comparison(reference=Path.home()/'balanced-ternary-logic'):
    """Snapshot live views, compare privately, and exchange the whole directory."""
    from .publish import publish
    live = CELLS_DIR/'out'
    source_generation = (live/'generation.json').read_bytes()
    stage = Path(tempfile.mkdtemp(prefix='.cells-wirec-', dir=CELLS_DIR))
    shutil.copytree(live, stage, dirs_exist_ok=True)
    if (live/'generation.json').read_bytes() != source_generation:
        raise RuntimeError(f'Library changed while copying; private stage retained: {stage}')
    result = compare(stage, reference)
    if (live/'generation.json').read_bytes() != source_generation:
        raise RuntimeError(f'Library generation changed; comparison retained: {stage}')
    # SIM can refresh characterization without changing geometry/generation.
    # Preserve its latest complete atomically written files before publication.
    for path in live.glob('*/*.char.json'):
        (stage/path.relative_to(live)).write_bytes(path.read_bytes())
    if (live/'sizing').exists():
        if (stage/'sizing').exists():
            shutil.rmtree(stage/'sizing')
        shutil.copytree(live/'sizing', stage/'sizing')
    generation = publish(stage, reason='Phase 4 original/compact estimated wire-C comparison; device-only scope clarified; physical cell views unchanged')
    shutil.rmtree(stage)  # exchanged previous live generation
    return result, generation
