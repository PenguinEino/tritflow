"""Publish complete, qualified generations through one atomic directory exchange.

The public template symlink resolves through the same generation as cells/out.
Consumers that need a multi-file snapshot should open out as a directory once
or compare generation.json before and after reading; paths remain backward
compatible for the existing PNR/SIM loaders.
"""
import ctypes
from datetime import datetime,timezone
import hashlib
import json
import os
import shutil
from pathlib import Path
import tempfile

from tritflow import CELLS_DIR


def characterize(out):
    """Regenerate SIM-owned characterization alongside the new extracted views."""
    from tritflow.sim.characterize import characterize_cell
    from .circuits import circuits
    out=Path(out)
    for name in circuits():
        if name=='FILL':continue
        source=(out/name/f'{name}.ext.spice').read_text()
        result=characterize_cell(name,source,destination=out/name/f'{name}.char.json')
        if not result['passed']:raise RuntimeError(f'{name} characterization failed')
        print(f'{name} characterization passed',flush=True)


def publish(stage, *, reason):
    """Exchange an entire staged library only after matching-view checks pass."""
    stage=Path(stage).resolve();live=CELLS_DIR/'out'
    report=json.loads((stage/'verify_report.json').read_text())
    if not report['passed']:raise ValueError('Refusing an unqualified library')
    from .layout import pinned_sources
    current=pinned_sources()
    verified=report.get('pdk_provenance',{})
    generated=json.loads((stage/'pdk_provenance.json').read_text()) if (stage/'pdk_provenance.json').exists() else {}
    for evidence in (verified,generated):
        if (evidence.get('qualified_commit')!=current['qualified_commit']
            or evidence.get('consumed_sha256')!=current['consumed_sha256']):
            raise ValueError('Publication requires fresh qualification against the current public pinned PDK')
    if not generated.get('pcell_sha256') or any(hashlib.sha256((Path(current['root'])/name).read_bytes()).hexdigest()!=digest
            for name,digest in generated['pcell_sha256'].items()):
        raise ValueError('PCell sources differ from the recorded pinned build')
    entries=json.loads((stage/'library.json').read_text())
    if len(entries)!=9:raise ValueError('A publish must contain all nine cells')
    for entry in entries:
        name=entry['name'];folder=stage/name
        for key in ('gds','spice','extracted','abstract','truth','png'):
            if not (stage/entry[key]).is_file():raise ValueError(f'Missing {entry[key]}')
        for suffix,digest in report['artifact_sha256'][name].items():
            if hashlib.sha256((folder/f'{name}.{suffix}').read_bytes()).hexdigest()!=digest:
                raise ValueError(f'Stale verification for {name}.{suffix}')
        if name!='FILL':
            char=json.loads((folder/f'{name}.char.json').read_text())
            source=hashlib.sha256((folder/f'{name}.ext.spice').read_bytes()).hexdigest()
            if not char['passed'] or char['source_sha256']!=source:
                raise ValueError(f'Stale characterization for {name}')
            if char.get('pdk_provenance',{}).get('consumed_sha256')!=current['consumed_sha256']:
                raise ValueError(f'Characterization is not qualified against the pinned PDK: {name}')
    timestamp=datetime.now(timezone.utc).isoformat()
    generation={'id':timestamp,'reason':reason,'height_um':json.loads((stage/'template.json').read_text())['height']}
    timings=[stage/e['name']/f'{e["name"]}.timing.json' for e in entries]
    if any(p.exists() for p in timings):
        if not all(p.exists() for p in timings):raise ValueError('Timing publication requires all nine cell tables')
        for entry,path in zip(entries,timings):
            name=entry['name'];timing=json.loads(path.read_text())
            digest=hashlib.sha256((stage/name/f'{name}.ext.spice').read_bytes()).hexdigest()
            if not timing['complete'] or timing['source_sha256']!=digest:
                raise ValueError(f'Incomplete/stale timing table for {name}')
            if timing.get('pdk_provenance',{}).get('consumed_sha256')!=current['consumed_sha256']:
                raise ValueError(f'Timing is not qualified against the pinned PDK: {name}')
            timing['generation']=generation
            path.write_text(json.dumps(timing,indent=2,allow_nan=False)+'\n')
            entry['timing']=str(path.relative_to(stage))
            for suffix in ('poly.json','poly.timing.json'):
                extra=stage/name/f'{name}.{suffix}'
                if extra.exists():
                    evidence=json.loads(extra.read_text())
                    if evidence['source_sha256']!=digest:
                        raise ValueError(f'Stale poly evidence for {name}')
                    if evidence['annotated_sha256']!=hashlib.sha256((stage/name/f'{name}.poly.spice').read_bytes()).hexdigest():
                        raise ValueError(f'Stale poly annotation for {name}')
                    evidence['generation']=generation
                    extra.write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
        (stage/'library.json').write_text(json.dumps(entries,indent=2)+'\n')
        timing_report=json.loads((stage/'timing_report.json').read_text())
        timing_report['generation']=generation
        for name in timing_report['cells']:
            timing_report['cells'][name]['timing_sha256']=hashlib.sha256((stage/name/f'{name}.timing.json').read_bytes()).hexdigest()
        (stage/'timing_report.json').write_text(json.dumps(timing_report,indent=2,allow_nan=False)+'\n')
        poly_summary=stage/'poly_timing_report.json'
        if poly_summary.exists():
            value=json.loads(poly_summary.read_text());value['generation']=generation
            poly_summary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        validation=stage/'timing_validation.json'
        if validation.exists():
            value=json.loads(validation.read_text());value['generation']=generation
            validation.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    (stage/'generation.json').write_text(json.dumps(generation,indent=2)+'\n')
    evidence=stage/'equivalence_report.json'
    if evidence.exists():
        comparison=json.loads(evidence.read_text())
        if not comparison['passed']:
            raise ValueError('Refusing failed equivalence evidence')
        for name,proof in comparison['schematic_equivalence'].items():
            for suffix,key in [('gds','compact_gds_sha256'),('ext.spice','compact_extracted_sha256')]:
                if hashlib.sha256((stage/name/f'{name}.{suffix}').read_bytes()).hexdigest()!=proof[key]:
                    raise ValueError(f'Stale equivalence for {name}.{suffix}')
        comparison.setdefault('verified_cell_generation',comparison.get('generation'))
        comparison['generation']=generation
        if 'parasitic_aware' in comparison:
            comparison['parasitic_aware']['generation']=generation
        evidence.write_text(json.dumps(comparison,indent=2,allow_nan=False)+'\n')
    if (stage/'requalification/baseline/generation.json').exists():
        from .requalify import compare_results
        comparison=compare_results(stage);comparison['generation']=generation
        if not comparison['passed']:raise ValueError('Incomplete/failed pinned requalification evidence')
        (stage/'requalification/report.json').write_text(json.dumps(comparison,indent=2,allow_nan=False)+'\n')
    # Prepare the old generation's template before replacing the outer template
    # with a link; both resolve to the tall template until the directory swap.
    public=CELLS_DIR/'template.json'
    if not public.is_symlink():
        (live/'template.json').write_bytes(public.read_bytes())
        temporary=CELLS_DIR/'.template-next'
        temporary.unlink(missing_ok=True)
        temporary.symlink_to('out/template.json')
        os.replace(temporary,public)
    libc=ctypes.CDLL(None,use_errno=True)
    # Linux renameat2(RENAME_EXCHANGE) is atomic even for populated directories.
    if libc.renameat2(-100,os.fsencode(stage),-100,os.fsencode(live),2)!=0:
        error=ctypes.get_errno();raise OSError(error,os.strerror(error))
    status=CELLS_DIR.parent/'docs/status/CELLS.md'
    with status.open('a') as f:
        f.write(f'\nPublish {timestamp}: {reason}. Whole-library directory exchange; '
                f'height {generation["height_um"]:g} um. GDS/SPICE/extraction/abstracts/'
                'truth/PNG/characterization/verification and template belong to this generation.\n')
    return generation


def qualified_build(out, names=None):
    """Default build command: privately build/check/characterize, then publish."""
    from .layout import build
    from .verify import verify
    if names:raise ValueError('Live publication requires all cells; use --out for a focused build')
    stage=Path(tempfile.mkdtemp(prefix='.cells-next-',dir=CELLS_DIR))
    build(stage)
    if not verify(stage)['passed']:raise RuntimeError(f'Qualification failed: {stage}')
    characterize(stage)
    from .timing import characterize_all
    if not characterize_all(stage)['complete']:raise RuntimeError(f'Timing characterization incomplete: {stage}')
    result=publish(stage,reason='Compact complete-library rebuild')
    shutil.rmtree(stage)  # old generation; the exchange already made the new one live
    return result
