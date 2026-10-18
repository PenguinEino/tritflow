"""Audit pinned publications and compare their numbers with the superseded run.

This is a fast reader: expensive producers remain examples/postlayout_all.py,
examples/adder_scaling.py, and the characterize/sizing/corners/diagnose modules.
The resulting manifest detects a later atomic cell or PNR publication.
"""
from __future__ import annotations
import json
from pathlib import Path
from tritflow import ROOT, CELLS_DIR
from .postlayout import _save, file_hash
from .provenance import pdk_provenance


def _read(path):
    path=Path(path)
    return json.loads(path.read_text()) if path.is_file() else None


def _changes(old,new,fields):
    return {key:{'before':old.get(key),'after':new.get(key),
                 'delta':new[key]-old[key] if isinstance(old.get(key),(int,float)) and isinstance(new.get(key),(int,float)) else None}
            for key in fields if old.get(key)!=new.get(key)}


def qualified_pdk(record, expected):
    """A commit label alone cannot qualify data from different consumed decks."""
    actual=record.get('pdk_provenance',{})
    return (actual.get('qualified_commit')==expected['qualified_commit']
            and actual.get('consumed_sha256')==expected['consumed_sha256'])


def publish_audit(destination=ROOT/'results/pinned_requalification.json'):
    """Hash live consumed inputs, reject stale evidence, publish numerical deltas."""
    baseline=ROOT/'results/dev_before_pinned'
    pdk=pdk_provenance();changes={};errors=[];sources={};artifacts={}
    def consume(path):
        sources[str(path.resolve())]=file_hash(path)
    def verify(record,field):
        for name,digest in record.get(field,{}).items():
            path=Path(name)
            if not path.is_file() or file_hash(path)!=digest:errors.append(f'Stale {field}: {name}')
    for design in ('adder4','full_add','mac1','mul1'):
        path=ROOT/f'build/{design}/postlayout/summary.json';record=_read(path)
        if not record or not record.get('passed'):errors.append(f'No passing postlayout: {design}');continue
        if not qualified_pdk(record,pdk):errors.append(f'Unqualified PDK: {design}')
        verify(record,'input_sha256');sources.update(record['input_sha256']);consume(path)
        old=_read(baseline/f'build/{design}/postlayout/summary.json') or {}
        change=_changes(old,record,['pre_max_error_v','post_max_error_v','max_rail_deviation_v','max_zero_shift_v'])
        change['settling']={mode:_changes(old.get('settling',{}).get(mode,{}),record['settling'][mode],list(record['settling'][mode]))
                            for mode in ('pre_max_settling_s','post_max_settling_s')}
        wire=(path.parent/'postlayout.spice').read_text();caps=_read(path.parent/'capacitance.json')
        expected=sum(v['capacitance_f']>0 for v in caps['nets'].values())
        if wire.count('Ctfwire')!=expected:errors.append(f'Wire C device count differs: {design}')
        changes[design]=change
    scaling=_read(ROOT/'results/adder_scaling.json')
    if not scaling or not scaling.get('passed'):errors.append('Scaling is incomplete')
    else:
        if not qualified_pdk(scaling,pdk):errors.append('Unqualified PDK: scaling')
        verify(scaling,'sources_sha256');sources.update(scaling['sources_sha256'])
        previous={r['n']:r for r in (_read(baseline/'results/adder_scaling.json') or {}).get('rows',[])}
        values=[]
        for row in scaling['rows']:
            verify(row,'artifacts_sha256');old=previous.get(row['n'],{})
            spice=next((Path(p) for p in row['artifacts_sha256'] if p.endswith('/postlayout/postlayout.spice')),None)
            if spice and spice.is_file():
                caps=_read(spice.parent/'capacitance.json')
                if spice.read_text().count('Ctfwire')!=sum(v['capacitance_f']>0 for v in caps['nets'].values()):
                    errors.append(f'Scaling N={row["n"]} has missing wire C devices')
            change=_changes(old,row,['die_area_um2','cell_count','static_power_worst_w','max_rail_deviation_v','max_zero_shift_v'])
            change['carry']={mode:_changes(old.get('carry',{}).get(mode,{}),row['carry'][mode],['max_settling_s']) for mode in ('pre','post')}
            values.append(dict(n=row['n'],changes=change))
        changes['scaling']=values
        changes['fits']={'before':(_read(baseline/'results/adder_scaling.json') or {}).get('fits'),'after':scaling.get('fits')}
    load=_read(ROOT/'results/full_add_load_sweep.json')
    if not load or not load.get('boundary_found'):errors.append('Load boundary is incomplete')
    else:
        if not qualified_pdk(load,pdk):errors.append('Unqualified PDK: load sweep')
        verify(load,'sources_sha256');verify(load,'artifacts_sha256');sources.update(load['sources_sha256'])
        old=_read(baseline/'results/full_add_load_sweep.json') or {}
        changes['load_boundary']=_changes(old.get('boundary',{}),load['boundary'],list(load['boundary']))
    for cell in ('INV','NANY','NAND','NOR','BUF','TIEP','TIEZ','TIEN'):
        path=CELLS_DIR/f'out/{cell}/{cell}.char.json';record=_read(path);consume(path)
        if not record or not record.get('passed') or record.get('pdk_provenance',{}).get('qualified_commit')!=pdk['qualified_commit']:
            errors.append(f'Unqualified characterization: {cell}');continue
        source=CELLS_DIR/f'out/{cell}/{cell}.ext.spice';consume(source)
        if file_hash(source)!=record['source_sha256']:errors.append(f'Stale characterization: {cell}')
        old=_read(baseline/f'cells/out/{cell}/{cell}.char.json') or {}
        changes[f'{cell}_characterization']=_changes(old,record,['max_static_current_a'])
        def metrics(value):
            return dict(max_input_capacitance_f=value.get('input_capacitance',{}).get('max_f'),
                max_dc_error_v=max((abs(e) for r in value.get('dc',[]) for e in r['error_v'].values()),default=None),
                max_settling_s=max((t for r in value.get('transient',[]) for t in r['max_settling_s'].values() if t is not None),default=None),
                suggested_fanout=value.get('fanout',{}).get('suggested_max'))
        changes[f'{cell}_characterization'].update(_changes(metrics(old),metrics(record),list(metrics(record))))
    from .sizing import load_grid
    for cell in ('INV','NANY'):
        record=load_grid(cell);path=CELLS_DIR/f'out/sizing/{cell}.grid.json';consume(path)
        old=_read(baseline/f'cells/out/sizing/{cell}.grid.json') or {}
        oldrows={json.dumps(r['dimensions'],sort_keys=True):r for r in old.get('rows',[])}
        changed=[]
        for i,row in enumerate(record['rows']):
            previous=oldrows.get(json.dumps(row['dimensions'],sort_keys=True),{})
            delta=_changes(previous,row,['max_error_v','max_static_current_a','passed','error'])
            if delta:changed.append(dict(index=i,changes=delta))
        changes[f'{cell}_sizing']={'before_pass':sum(r['passed'] for r in old.get('rows',[])),
            'after_pass':sum(r['passed'] for r in record['rows']),
            'changed_candidates':changed,
            'adopted':_changes((old.get('rows') or [{}])[0],record['rows'][0],['max_error_v','max_static_current_a'])}
    corner=_read(ROOT/'results/corners/summary.json')
    if not corner or len(corner['rows'])!=54 or any(r['state']!='complete' for r in corner['rows']):errors.append('Corner matrix is incomplete')
    else:
        if not qualified_pdk({'pdk_provenance':corner['inventory'].get('pdk_provenance',{})},pdk):errors.append('Unqualified PDK: corners')
        for row in corner['rows']:verify(row,'sources_sha256');sources.update(row['sources_sha256'])
    for path in sorted((ROOT/'results').glob('*.json')):
        if path.name not in ('pinned_requalification.json',):artifacts[str(path.resolve())]=file_hash(path)
    for path in (CELLS_DIR/'generation.json',CELLS_DIR/'out/generation.json',CELLS_DIR/'template.json'):
        if path.is_file():consume(path)
    result=dict(pdk_provenance=pdk,passed=not errors,errors=sorted(set(errors)),
        sources_sha256=sources,artifacts_sha256=artifacts,changes_from_dev=changes,
        comparison_scope='Pre-wire baseline now uses exactly the extracted intrinsic devices. Wire-C no-op bug corrected. Geometry also changes to reserve PNR current margin; old/new differences are not PDK R/C coefficient updates.')
    _save(destination,result);return result


if __name__=='__main__':
    result=publish_audit();print(json.dumps({'passed':result['passed'],'errors':result['errors']},indent=2))
    raise SystemExit(0 if result['passed'] else 1)
