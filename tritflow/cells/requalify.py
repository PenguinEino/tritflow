"""Pinned-PDK qualification with an exhaustive pre/post result ledger.

Geometry is compared as merged drawing-layer regions, independently of GDS
headers and hierarchy serialization. JSON changes retain exact leaf values;
electrical summaries compare matching sensitized arcs, never unrelated maxima.
"""
from __future__ import annotations

from tritflow.sim.tools import ngspice_binary

import difflib
import gzip
import json
from pathlib import Path
import re
import shutil
import platform
import subprocess
import sys
import tempfile

import klayout.db as db

from tritflow import CELLS_DIR
from tritflow.sim.provenance import pdk_provenance
from .circuits import circuits
from .reference import ORIGINALS,canonical,device_parameters,sha
from .timing import write_json


def record_environment(out):
    """Record actual native/Python tool versions rather than assuming the pin."""
    from .verify import BINARY
    value={'python':sys.version,'platform':platform.platform(),'klayout_python':db.__version__,
           'klayout_executable':subprocess.check_output([str(BINARY),'-v'],text=True).strip(),
           'ngspice_version':subprocess.check_output([ngspice_binary(),'--version'],text=True).strip(),
           'pdk_provenance':pdk_provenance()}
    write_json(Path(out)/'requalification/environment.json',value)
    return value


def snapshot(live, destination):
    """Preserve prior views/tables/reference extractions, without raw waveforms."""
    live,destination=Path(live),Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    for name in ('generation.json','verify_report.json','equivalence_report.json',
                 'timing_report.json','poly_timing_report.json','pdk_provenance.json',
                 'timing_validation.json','template.json','library.json','all.spice'):
        if (live/name).exists():shutil.copy2(live/name,destination/name)
    for cell in circuits():
        folder=destination/cell;folder.mkdir(exist_ok=True)
        for path in (live/cell).glob(f'{cell}.*'):
            if path.is_file():shutil.copy2(path,folder/path.name)
        for prefix in ('equivalence/reference','equivalence/parasitic/reference'):
            if (live/prefix/cell).exists():
                shutil.copytree(live/prefix/cell,destination/prefix/cell,dirs_exist_ok=True)
        folder=live/'equivalence/parasitic'/cell
        if folder.exists():
            target=destination/'equivalence/parasitic'/cell;target.mkdir(parents=True,exist_ok=True)
            for path in folder.iterdir():
                if path.is_file():shutil.copy2(path,target/path.name)
    for path in (live/'equivalence').rglob('tb.spice'):
        target=destination/path.relative_to(live);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)


def geometry_difference(before, after, cell):
    """Report every changed drawing region and text label in physical units."""
    layouts=[]
    for path in (before,after):
        layout=db.Layout();layout.read(str(path));layouts.append(layout)
    assert layouts[0].dbu==layouts[1].dbu
    layers=sorted({(layout.get_info(i).layer,layout.get_info(i).datatype)
                   for layout in layouts for i in layout.layer_indexes()})
    changes={};label_changes={}
    for layer in layers:
        regions=[];labels=[]
        for layout in layouts:
            top=layout.cell(cell);index=layout.layer(*layer)
            regions.append(db.Region(top.begin_shapes_rec(index)).merged())
            iterator=top.begin_shapes_rec(index);texts=[]
            while not iterator.at_end():
                shape=iterator.shape()
                if shape.is_text():texts.append(str(shape.text.transformed(iterator.trans())))
                iterator.next()
            labels.append(sorted(texts))
        delta=regions[0]^regions[1]
        if not delta.is_empty():changes[str(layer)]={'xor_area_um2':delta.area()*layouts[0].dbu**2,
                                                    'xor_polygons':delta.count()}
        if labels[0]!=labels[1]:label_changes[str(layer)]={'before':labels[0],'after':labels[1]}
    return {'identical':not changes and not label_changes,'drawing_layers':changes,'labels':label_changes}


def _gds_without_timestamps(path):
    """Canonical GDS bytes with only BGNLIB/BGNSTR date payloads zeroed."""
    data=bytearray(Path(path).read_bytes());offset=0
    while offset<len(data):
        length=int.from_bytes(data[offset:offset+2],'big')
        if length<4 or offset+length>len(data):raise ValueError('Invalid GDS record')
        if data[offset+2] in (1,5):data[offset+4:offset+length]=bytes(length-4)
        offset+=length
    return data


def json_changes(before,after,path=''):
    """Yield all exact JSON differences, including added/removed metadata."""
    if isinstance(before,dict) and isinstance(after,dict):
        for key in sorted(set(before)|set(after)):
            q=f'{path}/{key}'
            if key not in before:yield {'path':q,'change':'added','after':after[key]}
            elif key not in after:yield {'path':q,'change':'removed','before':before[key]}
            else:yield from json_changes(before[key],after[key],q)
    elif isinstance(before,list) and isinstance(after,list) and len(before)==len(after):
        for i,(a,b) in enumerate(zip(before,after)):yield from json_changes(a,b,f'{path}/{i}')
    elif before!=after:
        row={'path':path,'change':'changed','before':before,'after':after}
        if type(before) in (int,float) and type(after) in (int,float):row['difference']=after-before
        yield row


def extract_native_references(out,reference=Path.home()/'balanced-ternary-logic'):
    """Also retain pinned extraction of the untouched taped-out GDS labels.

    This separates deck-induced extraction changes from the legacy-label alias
    needed for strict public port checking. Named copies receive strict LVS;
    these native copies are extraction-only evidence, not a second LVS claim.
    """
    from tritflow.extract import extract_layout
    from .verify import BINARY
    out=Path(out).resolve();folder=out/'requalification/native_reference';records={}
    for cell,top in ORIGINALS.items():
        gds=Path(reference)/f'{top}.gds'
        result=extract_layout(gds,top,folder/cell,executable=BINARY,timeout=240)
        records[cell]={'gds_sha256':sha(gds),'extracted_sha256':sha(result['extracted']),
                       'extracted':str(Path(result['extracted']).relative_to(out))}
    write_json(folder/'manifest.json',{'pdk_provenance':pdk_provenance(),'cells':records})
    return records


def _bench_audit(baseline,out,old_models,new_models):
    """Compare retained electrical protocols, normalizing model paths by hash."""
    def normalized(text,models):
        def include(match):
            name=Path(match[1]).name
            return '.include MODEL_SHA256_'+models[name] if name in models else match[0]
        text=re.sub(r'(?im)^\s*\.include\s+"([^"]+)"',include,text)
        return [' '.join(line.lower().split()) for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith('*')]
    rows=[]
    def active(lines):
        text='\n'.join(lines)
        if not any(line.startswith('x') and line.split()[-1]=='buf' for line in lines):
            text=re.sub(r'(?ms)^\.subckt buf\b.*?^\.ends\b[^\n]*\n?','',text)
        return [line for line in text.splitlines() if line and not line.startswith('.nodeset ')]
    for before in sorted((baseline/'equivalence').rglob('tb.spice')):
        relative=before.relative_to(baseline);after=out/relative
        if not after.exists():continue
        a,b=normalized(before.read_text(),old_models),normalized(after.read_text(),new_models)
        row={'path':str(relative),'before_sha256':sha(before),'after_sha256':sha(after),
             'same_normalized_deck':a==b,'active_network_and_stimulus_identical':active(a)==active(b),
             'nodeset_hints_identical':[s for s in a if s.startswith('.nodeset ')]==[s for s in b if s.startswith('.nodeset ')]}
        if a!=b:
            delta=out/'requalification/bench_differences'/relative.with_suffix('.spice.diff')
            delta.parent.mkdir(parents=True,exist_ok=True)
            delta.write_text(''.join(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),fromfile='before',tofile='pinned')))
            row['difference_file']=str(delta.relative_to(out))
        rows.append(row)
    return {'checked':len(rows),'normalized_text_mismatches':sum(not row['same_normalized_deck'] for row in rows),
            'active_network_or_stimulus_mismatches':sum(not row['active_network_and_stimulus_identical'] for row in rows),'rows':rows,
            'scope':'Text audit normalizes model include paths by recorded content hash, whitespace, comments and SPICE-insensitive case. The separate active-network check additionally omits only uninstantiated BUF definitions and .nodeset hints; changed hints remain explicit with full diffs. No old PDK files are read or used.'}


def _timing_difference(before,after):
    """Pair every timing sample by sensitizing vectors and both measured axes."""
    def arcs(table):
        return {(tuple(sorted(a['from_inputs'].items())),tuple(sorted(a['to_inputs'].items()))):a
                for a in table['arcs']+table['simultaneous']}
    left,right=arcs(before),arcs(after)
    comparable=before['axes']==after['axes'] and left.keys()==right.keys()
    result={'same_axes_and_sensitizations':comparable,
            'before_worst_settling_s':before.get('max_settling_s'),
            'pinned_worst_settling_s':after.get('max_settling_s')}
    if comparable:
        for field in ('settling_s','output_slew_10_90_s','error_v'):
            deltas=[];changed_nulls=0
            for key in left:
                for a,b in zip(left[key][field],right[key][field]):
                    for x,y in zip(a,b):
                        changed_nulls+=(x is None)!=(y is None)
                        if x is not None and y is not None:deltas.append(abs(y-x))
            result[f'max_abs_{field}_difference']=max(deltas,default=0.)
            result[f'{field}_changed_nulls']=changed_nulls
    def caps(table):
        return {(tuple(r['input_trits']),r['pin']):r['capacitance_f'] for r in table['input_capacitance']['rows']}
    a,b=caps(before),caps(after)
    result['same_input_C_biases']=a.keys()==b.keys()
    result['max_abs_input_capacitance_difference_f']=max((abs(b[k]-a[k]) for k in a.keys()&b.keys()),default=0.)
    return result


def compare_results(out):
    """Write the full difference ledger and a compact physical/electrical summary."""
    out=Path(out).resolve();baseline=out/'requalification/baseline';folder=out/'requalification'
    report={'pdk_provenance':pdk_provenance(),
            'baseline_generation':json.loads((baseline/'generation.json').read_text()),
            'scope':'Comparison with the exact pre-Phase-7 published generation. Its physical decks were the dev snapshot; Phase 6 model bytes were already pinned-compatible. Metadata and result changes are retained separately from geometric identity.',
            'cells':{},'original_extractions':{},'wire_capacitor_counts':{},'json_files':{},'text_files':{}}
    report['introduced_root_files']={path.name:sha(path) for path in out.glob('*.json') if not (baseline/path.name).exists()}
    native_path=folder/'native_reference/manifest.json'
    native=json.loads(native_path.read_text())['cells'] if native_path.exists() else {}
    all_changes=[];numeric=[]
    for path in sorted(baseline.rglob('*.json')):
        relative=path.relative_to(baseline)
        # Compare public tables, not duplicated reference fixture helper files.
        if relative.parts[0]=='equivalence':continue
        target=out/relative
        if not target.exists():continue
        changes=list(json_changes(json.loads(path.read_text()),json.loads(target.read_text())))
        for change in changes:
            change={'file':str(relative),**change};all_changes.append(change)
            if 'difference' in change:numeric.append(change)
        report['json_files'][str(relative)]={'before_sha256':sha(path),'after_sha256':sha(target),
            'changed_leaves':len(changes),'numeric_changes':sum('difference' in c for c in changes)}
    for cell in circuits():
        old,new=baseline/cell,out/cell
        physical=geometry_difference(old/f'{cell}.gds',new/f'{cell}.gds',cell)
        physical['gds_equal_excluding_timestamps']=_gds_without_timestamps(old/f'{cell}.gds')==_gds_without_timestamps(new/f'{cell}.gds')
        physical['artifact_sha256']={}
        for path in sorted(old.glob(f'{cell}.*')):
            target=new/path.name
            if not target.is_file():continue
            physical['artifact_sha256'][path.name]={'before':sha(path),'after':sha(target),'identical':path.read_bytes()==target.read_bytes()}
        report['cells'][cell]=physical
        a,b=old/f'{cell}.timing.json',new/f'{cell}.timing.json'
        if a.exists() and b.exists():physical['timing_difference']=_timing_difference(json.loads(a.read_text()),json.loads(b.read_text()))
        for suffix in ('spice','ext.spice','lvs.spice'):
            a,b=old/f'{cell}.{suffix}',new/f'{cell}.{suffix}'
            if a.read_bytes()!=b.read_bytes():
                delta=''.join(difflib.unified_diff(a.read_text().splitlines(True),b.read_text().splitlines(True),fromfile='before',tofile='pinned'))
                target=folder/f'{cell}.{suffix}.diff';target.write_text(delta)
                report['text_files'][f'{cell}/{cell}.{suffix}']=str(target.relative_to(out))
        for label in ('original','compact'):
            relative=Path('equivalence/parasitic')/cell/f'{label}.wirec.spice'
            if (out/relative).exists():
                report['wire_capacitor_counts'][f'{cell}/{label}']={epoch:len(re.findall(r'(?im)^Ctfwire', (root/relative).read_text()))
                    for epoch,root in [('before',baseline),('pinned',out)]}
        old_ext=baseline/'equivalence/reference'/cell/'original.ext.spice'
        new_ext=out/'equivalence/reference'/cell/'original.ext.spice'
        if old_ext.exists() and new_ext.exists():
            report['original_extractions'][cell]={'before_sha256':sha(old_ext),'after_sha256':sha(new_ext),
                'public_text_identical':old_ext.read_bytes()==new_ext.read_bytes(),
                'intrinsic_parameters_identical':device_parameters(old_ext.read_text())==device_parameters(new_ext.read_text())}
            old_raw=old_ext.with_name('extracted.raw.spice');new_raw=new_ext.with_name('extracted.raw.spice')
            if old_raw.exists() and new_raw.exists():
                report['original_extractions'][cell].update(raw_before_sha256=sha(old_raw),raw_after_sha256=sha(new_raw),
                    raw_text_identical=old_raw.read_bytes()==new_raw.read_bytes())
                if old_raw.read_bytes()!=new_raw.read_bytes():
                    target=folder/f'{cell}.original_raw.diff'
                    target.write_text(''.join(difflib.unified_diff(old_raw.read_text().splitlines(True),new_raw.read_text().splitlines(True),fromfile='before',tofile='pinned')))
                    report['text_files'][f'original/{cell}']=str(target.relative_to(out))
                if cell in native:
                    untouched=out/native[cell]['extracted']
                    report['original_extractions'][cell]['unmodified_labels_pinned']={
                        'path':native[cell]['extracted'],'sha256':sha(untouched),
                        'raw_text_identical_to_dev':old_raw.read_bytes()==untouched.read_bytes(),
                        'canonical_device_text_identical_to_dev':canonical(old_raw.read_text(),cell)==canonical(untouched.read_text(),cell),
                        'intrinsic_parameters_identical_to_dev':device_parameters(old_raw.read_text())==device_parameters(untouched.read_text())}
    before=json.loads((baseline/'verify_report.json').read_text())['deck_sha256']
    after=json.loads((out/'verify_report.json').read_text())['deck_sha256']
    report['deck_changes']=[{'path':key,'before':before.get(key),'after':after.get(key)}
        for key in sorted(set(before)|set(after)) if before.get(key)!=after.get(key)]
    old_models=json.loads((baseline/'equivalence_report.json').read_text())['model_sha256']
    new_models=json.loads((out/'equivalence_report.json').read_text())['model_sha256']
    report['model_bytes_identical']=old_models==new_models
    report['electrical_bench_audit']=_bench_audit(baseline,out,old_models,new_models)
    report['numeric_changes']=len(numeric)
    report['numeric_changes_by_file']={name:sum(c['file']==name for c in numeric) for name in report['json_files']}
    report['geometry_identical']=all(c['identical'] for c in report['cells'].values())
    def passed_file(path):
        if not path.exists():return False
        value=json.loads(path.read_text())
        return value.get('passed',False) and value.get('complete',True)
    equivalence=json.loads((out/'equivalence_report.json').read_text())
    verification=json.loads((out/'verify_report.json').read_text())
    report['qualification']={
        'drawing_DRC_strict_LVS_DC':verification['passed'],
        'all_324_abutments':verification['abutment']['passed'] and verification['abutment']['ordered_pair_orientation_cases']==324,
        'independent_device_equivalence':equivalence['passed'],
        'estimated_wire_C_equivalence':equivalence.get('parasitic_aware',{}).get('passed',False),
        'timing_surfaces':passed_file(out/'timing_report.json'),
        'poly_R_sensitivity':passed_file(out/'poly_timing_report.json'),
        'all_SIM_characterizations':all(passed_file(out/c/f'{c}.char.json') for c in circuits() if c!='FILL')}
    for key,path in [('negative_rail_fixtures',folder/'rail_negatives/report.json'),
                     ('regression_suite',folder/'regression.json'),('table_integrity',out/'timing_validation.json')]:
        if path.exists():report['qualification'][key]=passed_file(path)
    report['passed']=all(report['qualification'].values())
    report['all_changes_file']='requalification/all_differences.json.gz'
    report['numeric_changes_file']='requalification/numeric_differences.json.gz'
    for name,data in [('all_differences',all_changes),('numeric_differences',numeric)]:
        with gzip.open(folder/f'{name}.json.gz','wt') as stream:json.dump(data,stream,allow_nan=False)
    write_json(folder/'report.json',report)
    return report


def requalify(*,jobs=3):
    """Fresh pinned build, all electrical checks, comparison, atomic publication.

    Run the CELLS regression suite independently before release. A failed stage
    remains private with its logs; no existing characterization is reused.
    """
    from .layout import build
    from .verify import verify
    from .publish import characterize,publish
    from .equivalence import equivalence
    from .parasitic import compare
    from .timing import characterize_all
    live=CELLS_DIR/'out';source=(live/'generation.json').read_bytes()
    stage=Path(tempfile.mkdtemp(prefix='.cells-pinned-',dir=CELLS_DIR))
    snapshot(live,stage/'requalification/baseline');build(stage);record_environment(stage)
    for run in (verify,equivalence,compare):
        if not run(stage)['passed']:raise RuntimeError(f'Qualification failed; stage retained at {stage}')
    characterize(stage)
    if not characterize_all(stage,jobs=jobs)['passed']:raise RuntimeError(f'Timing failed; stage retained at {stage}')
    extract_native_references(stage);compare_results(stage)
    if (live/'generation.json').read_bytes()!=source:raise RuntimeError(f'Live generation changed; stage retained at {stage}')
    if (live/'sizing').exists():shutil.copytree(live/'sizing',stage/'sizing')
    generation=publish(stage,reason='Complete public pinned-PDK requalification, physical rail proof and exact pre/post difference ledger')
    shutil.rmtree(stage)
    return generation
