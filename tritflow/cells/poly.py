"""Gate-field-poly sheet-R sensitivity from actual GDS/LVS geometry.

The published PDK value is for RS resistor poly, not calibrated 1 µm GC wiring.
Use it explicitly as a sensitivity proxy, not as a signoff extraction parameter.
A square finite-volume mesh is Kron-reduced to metal-contact and MOS-gate nodes.
MOS channel gate areas and contacts are equipotential electrodes; intrinsic gate
capacitance stays in the PDK devices, and no guessed poly capacitance is added.
"""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re

import klayout.db as db
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu

from tritflow.extract.technology import parameter_audit
from tritflow.sim import simulation_netlist
from .reference import sha
from .timing import write_json


def _contains(polygons, point):
    return any(p.inside(point) for p in polygons)


def mesh_network(polygon, contacts, gates, *, pitch_dbu):
    """Unit-sheet network for one connected GC polygon; no dangling gate allowed.

    Cell centers sample the true polygon, including holes. Neighboring full square
    cells have conductance 1/Rsheet. Contact/channel electrodes collapse mesh
    vertices; elimination preserves the DC terminal conductance matrix. Boundary
    staircasing is explicit and checked with a finer mesh in validation.
    """
    bbox=polygon.bbox();terminals=['metal']+[f'gate_{g}' for g in sorted(gates)]
    terminal_index={name:i for i,name in enumerate(terminals)}
    occupied={};next_index=len(terminals)
    gate_polys={g:list(r.each()) for g,r in gates.items()};contact_polys=list(contacts.each())
    for i in range(bbox.left//pitch_dbu, (bbox.right+pitch_dbu-1)//pitch_dbu):
        for j in range(bbox.bottom//pitch_dbu, (bbox.top+pitch_dbu-1)//pitch_dbu):
            point=db.Point(round((i+.5)*pitch_dbu),round((j+.5)*pitch_dbu))
            if not polygon.inside(point):continue
            if _contains(contact_polys,point):index=0
            else:
                chosen=next((g for g,polys in gate_polys.items() if _contains(polys,point)),None)
                if chosen is not None:index=terminal_index[f'gate_{chosen}']
                else:index=next_index;next_index+=1
            occupied[i,j]=index
    used=set(occupied.values())
    if any(i not in used for i in range(len(terminals))):
        raise ValueError('Mesh missed a contact/gate electrode; reduce pitch or check connectivity')
    edges=defaultdict(float)
    for (i,j),a in occupied.items():
        for neighbor in ((i+1,j),(i,j+1)):
            b=occupied.get(neighbor)
            if b is not None and a!=b:edges[tuple(sorted((a,b)))]+=1.
    rr=[];cc=[];vv=[];diagonal=np.zeros(next_index)
    for (a,b),g in edges.items():
        rr.extend([a,b]);cc.extend([b,a]);vv.extend([-g,-g]);diagonal[a]+=g;diagonal[b]+=g
    rr.extend(range(next_index));cc.extend(range(next_index));vv.extend(diagonal)
    lap=coo_matrix((vv,(rr,cc)),shape=(next_index,next_index)).tocsc()
    nt=len(terminals);matrix=lap[:nt,:nt].toarray()
    if next_index>nt:
        solve=splu(lap[nt:,nt:])
        matrix-=lap[:nt,nt:]@solve.solve(lap[nt:,:nt].toarray())
    matrix=(matrix+matrix.T)/2
    pairs=[]
    for i in range(nt):
        for j in range(i+1,nt):
            conductance=-matrix[i,j]
            if conductance < -1e-8:raise ValueError('Non-passive reduced poly network')
            if conductance>1e-10:
                pairs.append({'a':terminals[i],'b':terminals[j],'squares':float(1/conductance)})
    if not pairs:raise ValueError('Empty reduced gate-poly network')
    effective=np.diag(np.linalg.inv(matrix[1:,1:]))
    return {'terminals':terminals,'edges':pairs,'mesh_vertices':len(occupied),
            'gate_to_contact_squares':{name:float(value) for name,value in zip(terminals[1:],effective)},
            'reduced_vertices':nt,'unit_sheet_conductance':matrix.tolist()}


def annotate(out,cell,*,sheet_ohm=None,pitch_um=.25):
    """Write an augmented .poly.spice beside the unmodified structural extraction."""
    from tritflow import CELLS_DIR
    out=Path(out).resolve()
    if out==(CELLS_DIR/'out').resolve():raise ValueError('Poly augmentation requires a private stage')
    folder=out/cell;text=(folder/f'{cell}.ext.spice').read_text()
    audit=parameter_audit();spec=audit['document_resistor_sheet_ohm_per_square']
    sheet=float(spec['RS_poly'] if sheet_ohm is None else sheet_ohm)
    if sheet<=0 or pitch_um<=0:raise ValueError('Require positive sheet resistance and mesh pitch')
    layout=db.Layout();layout.read(str(folder/f'{cell}.gds'));top=layout.cell(cell)
    lvs=db.LayoutVsSchematic();lvs.read(str(folder/'lvs.lvsdb'));circuit=lvs.netlist().circuit_by_name(cell)
    report={'cell':cell,'sheet_ohm_per_square':sheet,'pitch_um':pitch_um,
            'parameter_origin':'PDK RS resistor-poly specification used as a GC sensitivity proxy; GC applicability is uncalibrated.' if sheet_ohm is None else 'Explicit caller sensitivity override; not a calibrated GC parameter.',
            'pdk_source':spec,'parameter_audit_sha256':sha(Path(__file__).parents[1]/'extract/technology.py'),
            'source_sha256':sha(folder/f'{cell}.ext.spice'),'gds_sha256':sha(folder/f'{cell}.gds'),
            'scope':'GC gate-interconnect sheet R only. No poly C/contact R; MOS gate-channel regions are equipotential. RR device models and all W/L/junction parameters are unchanged. Structural LVS extraction is preserved.',
            'components':[],'gates':{},'resistors':[]}
    if circuit is None:
        if cell!='FILL':raise ValueError('Missing extracted circuit')
        report['annotated_sha256']=report['source_sha256']
        (folder/f'{cell}.poly.spice').write_text(text);write_json(folder/f'{cell}.poly.json',report)
        return text,report
    gc=db.Region(top.begin_shapes_rec(layout.layer(8,1))).merged()
    co=db.Region(top.begin_shapes_rec(layout.layer(11,0))).merged()
    active={model:db.Region(top.begin_shapes_rec(layout.layer(3,dt))).merged() for model,dt in [('PMOS',1),('NMOS',2)]}
    layers=[]
    for index in lvs.layer_indexes():
        try:
            layer=lvs.layer_by_index(index)
            if (layer.merged()^gc).is_empty():layers.append(layer)
        except TypeError:pass
    if len(layers)!=1:raise ValueError('Cannot identify physical gate poly in LVS database')
    grouped=defaultdict(list)
    for dev in circuit.each_device():
        model=dev.device_class().name
        if model not in active:continue
        net=dev.net_for_terminal('G');grouped[net.expanded_name()].append((dev,model,net))
    for net_name,devices in grouped.items():
        region=lvs.shapes_of_net(devices[0][2],layers[0],True).merged()
        gate_regions={}
        for dev,model,net in devices:
            x,y=dev.trans.disp.x,dev.trans.disp.y
            w,length=dev.parameter('W'),dev.parameter('L')
            expected=db.Region(db.DBox(x-length/2,y-w/2,x+length/2,y+w/2).to_itype(layout.dbu))
            electrode=region&active[model]&expected
            if abs(electrode.area()*layout.dbu**2-w*length)>1e-5:
                raise ValueError('GDS channel electrode disagrees with extracted MOS dimensions')
            gate_regions[dev.id()]=electrode
            report['gates'][str(dev.id())]={'node':f'tfpg_{dev.id()}', 'base_net':net_name,
                                          'origin_um':[x,y],'w_um':w,'l_um':length}
        for polygon in region.each():
            component=db.Region(polygon)
            gates={i:r for i,r in gate_regions.items() if not (r&component).is_empty()}
            if not gates:continue
            contacts=component&co
            network=mesh_network(polygon,contacts,gates,pitch_dbu=round(pitch_um/layout.dbu))
            base=simulation_netlist('\\'+net_name if net_name.startswith('$') else net_name)
            nodes={'metal':base,**{f'gate_{i}':f'tfpg_{i}' for i in gates}}
            for edge in network['edges']:
                report['resistors'].append({'name':f'Rtfpg_{len(report["resistors"])}',
                    'a':nodes[edge['a']],'b':nodes[edge['b']],'squares':edge['squares'],
                    'resistance_ohm':edge['squares']*sheet})
            network.update(net=net_name,bbox_um=[v*layout.dbu for v in (polygon.bbox().left,polygon.bbox().bottom,polygon.bbox().right,polygon.bbox().top)])
            for name,squares in network['gate_to_contact_squares'].items():
                report['gates'][name.removeprefix('gate_')]['effective_contact_resistance_ohm']=sheet*squares
            report['components'].append(network)
    lines=[];changed=set()
    for line in text.splitlines():
        tokens=line.split()
        if len(tokens)>5 and tokens[5] in ('PMOS','NMOS'):
            match=re.search(r'\$(\d+)$',tokens[0])
            if not match or match[1] not in report['gates']:raise ValueError('Unmapped extracted MOS instance')
            tokens[2]=report['gates'][match[1]]['node'];changed.add(match[1]);line=' '.join(tokens)
        if line.lower().startswith('.ends'):
            lines.append('* Gate-field-poly sheet-R sensitivity; uncalibrated GC proxy')
            for r in report['resistors']:lines.append(f'{r["name"]} {r["a"]} {r["b"]} {r["resistance_ohm"]:.15g}')
        lines.append(line)
    if changed!=set(report['gates']):raise ValueError('Not all extracted gates were annotated')
    annotated=simulation_netlist('\n'.join(lines)+'\n')
    (folder/f'{cell}.poly.spice').write_text(annotated)
    report['annotated_sha256']=sha(folder/f'{cell}.poly.spice')
    write_json(folder/f'{cell}.poly.json',report)
    return annotated,report


def characterize_sensitivity(out,*,jobs=2,loads_f=(10e-15,100e-15,1e-12),ramps_s=(1e-9,150e-9)):
    """Measure the documented RS-poly proxy at representative load/ramp corners.

    Baseline primary sweeps may run concurrently. This function produces only
    augmented measurements; finalize_sensitivity joins the completed baseline.
    """
    from concurrent.futures import ProcessPoolExecutor,as_completed
    from .circuits import circuits
    from .timing import point
    out=Path(out).resolve()
    from tritflow import CELLS_DIR
    if out==(CELLS_DIR/'out').resolve():raise ValueError('Use a private stage')
    tasks=[]
    for cell,circuit in circuits().items():
        text,report=annotate(out,cell)
        if not circuit.inputs:continue
        for ri,ramp in enumerate(ramps_s):
            for li,load in enumerate(loads_f):
                tasks.append((cell,text,load,ramp,out/cell/'timing_poly'/f'ramp_{ri:02d}_load_{li:02d}'))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        pending={pool.submit(point,*task):task for task in tasks}
        for future in as_completed(pending):
            p=future.result()
            print(f'{p["cell"]} poly-R load={p["load_f"]*1e15:g} fF ramp={p["input_transition_s"]*1e9:g} ns: {"PASS" if p["passed"] else "FAIL"}',flush=True)


def finalize_sensitivity(out):
    """Join complete primary/proxy measurements and retain every paired delta."""
    from .circuits import circuits
    from tritflow import CELLS_DIR
    out=Path(out).resolve()
    if out==(CELLS_DIR/'out').resolve():raise ValueError('Poly results require a private stage')
    summary={}
    for cell,circuit in circuits().items():
        primary=json.loads((out/cell/f'{cell}.timing.json').read_text())
        network=json.loads((out/cell/f'{cell}.poly.json').read_text())
        baselines={}
        for path in (out/cell/'timing').glob('*/measurements.json'):
            p=json.loads(path.read_text());baselines[p['load_f'],p['input_transition_s']]=p
        comparisons=[]
        for path in sorted((out/cell/'timing_poly').glob('*/measurements.json')):
            proxy=json.loads(path.read_text());baseline=baselines[proxy['load_f'],proxy['input_transition_s']]
            expected={ (tuple(r['from']),tuple(r['to'])):r for r in baseline['rows']}
            rows=[]
            for r in proxy['rows']:
                b=expected[tuple(r['from']),tuple(r['to'])]
                before,after=b['settling_s'],r['settling_s']
                rows.append({'from':r['from'],'to':r['to'],'baseline_settling_s':before,
                             'poly_settling_s':after,'difference_s':after-before if before is not None and after is not None else None,
                             'baseline_passed':b['passed'],'poly_passed':r['passed']})
            deltas=[r['difference_s'] for r in rows if r['difference_s'] is not None]
            comparisons.append({'load_f':proxy['load_f'],'input_transition_s':proxy['input_transition_s'],
                'baseline_complete':baseline['complete'],'poly_complete':proxy['complete'],
                'baseline_passed':baseline['passed'],'poly_passed':proxy['passed'],
                'max_increase_s':max(deltas,default=None),'max_abs_difference_s':max(map(abs,deltas),default=None),
                'baseline_worst_settling_s':baseline.get('max_settling_s'),
                'poly_worst_settling_s':proxy.get('max_settling_s'),'rows':rows})
        result={'cell':cell,'source_sha256':primary['source_sha256'],
                'annotated_sha256':network['annotated_sha256'],'sheet_ohm_per_square':network['sheet_ohm_per_square'],
                'parameter_origin':network['parameter_origin'],'scope':network['scope'],
                'network_file':f'{cell}/{cell}.poly.json','spice_file':f'{cell}/{cell}.poly.spice',
                'comparisons':comparisons,'complete':all(p['baseline_complete'] and p['poly_complete'] for p in comparisons),
                'passed':all(p['baseline_passed'] and p['poly_passed'] for p in comparisons)}
        write_json(out/cell/f'{cell}.poly.timing.json',result)
        primary['poly_resistance']={'adopted_in_primary':False,'sensitivity_file':f'{cell}/{cell}.poly.timing.json',
            'sheet_ohm_per_square':network['sheet_ohm_per_square'],'parameter_origin':network['parameter_origin'],
            'max_increase_s':max((p['max_increase_s'] for p in comparisons if p['max_increase_s'] is not None),default=None),
            'complete':result['complete'],'passed':result['passed']}
        write_json(out/cell/f'{cell}.timing.json',primary)
        summary[cell]=primary['poly_resistance']
    write_json(out/'poly_timing_report.json',{'cells':summary,'complete':all(r['complete'] for r in summary.values()),
                                           'passed':all(r['passed'] for r in summary.values())})
    return summary
