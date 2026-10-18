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
    timestamp=datetime.now(timezone.utc).isoformat()
    generation={'id':timestamp,'reason':reason,'height_um':json.loads((stage/'template.json').read_text())['height']}
    (stage/'generation.json').write_text(json.dumps(generation,indent=2)+'\n')
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
    result=publish(stage,reason='Compact complete-library rebuild')
    shutil.rmtree(stage)  # old generation; the exchange already made the new one live
    return result
