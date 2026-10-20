"""Opt-in TDFF library extension; existing cells/out is immutable.

Only import_tdff knows the circuit stream's artifact layout. Its copied files,
not the reference tree, are consumed thereafter. A final summary is preferred;
otherwise qualified delivery candidates are explicitly marked as such.
"""
from hashlib import sha256
import json
from pathlib import Path
import shutil

from tritflow import CELLS_DIR
from tritflow.pnr.library import Cell, Library

EXTENSION = CELLS_DIR / 'out_seq'


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def import_tdff(source=Path.home()/'balanced-ternary-seq', destination=EXTENSION):
    """Snapshot independently qualified GDS, abstract and device references."""
    source, destination = Path(source), Path(destination)
    summary = source/'reports/tdff_summary.json'
    final = json.loads(summary.read_text()) if summary.exists() else None
    if final is not None and (not final['passed'] or final['ports'] != ['D','CLK','Q','VDD','VMID','VSS']):
        raise ValueError('final TDFF interface/qualification differs')
    paths = {'gds': source/'tdff.gds', 'abstract': source/'layout/tdff.abstract.json',
             'spice': source/('tdff.spice' if summary.exists() else 'simulation/tdff/core.spice'), 'ext.spice': source/'tdff.extracted'}
    if final is not None:
        for suffix,key in [('gds','gds'),('abstract','abstract'),('spice','schematic_netlist'),('ext.spice','extracted')]:
            if digest(paths[suffix]) != final['artifact_sha256'][key]:
                raise ValueError(f'final TDFF {key} hash mismatch')
    reports = [source/'reports'/f'tdff_{name}.json' for name in ('layout','extracted','clock','waveforms')]
    hashes = {str(p.relative_to(source)): digest(p) for p in [*paths.values(), *reports]}
    layout = json.loads(reports[0].read_text())
    extracted = json.loads(reports[1].read_text())
    if not all(json.loads(p.read_text())['passed'] is True for p in reports):
        raise ValueError('TDFF circuit delivery has failed qualification')
    if not layout['drc']['passed'] or not layout['lvs']['matched']:
        raise ValueError('TDFF requires drawing DRC and strict device LVS')
    if layout['gds_sha256'] != digest(paths['gds']) or extracted['gds_sha256'] != digest(paths['gds']):
        raise ValueError('TDFF qualification does not match delivered GDS')
    if extracted['extracted_sha256'] != digest(paths['ext.spice']):
        raise ValueError('TDFF extracted qualification is stale')
    base = destination/'TDFF'
    base.mkdir(parents=True, exist_ok=True)
    for suffix, path in paths.items():
        shutil.copyfile(path, base/f'TDFF.{suffix if suffix != "abstract" else "abstract.json"}')
    for path in reports:
        shutil.copyfile(path, base/path.name)
    if summary.exists():
        shutil.copyfile(summary, base/'tdff_summary.json')
    if any(digest(source/name) != old for name,old in hashes.items()):
        raise RuntimeError('circuit delivery changed during import; retry snapshot')
    provenance = {'schema': 'tritflow.seq.library.v1', 'cell': 'TDFF',
                  'provenance': 'SEQ_CIRCUIT final' if summary.exists() else 'SEQ_CIRCUIT qualified candidate',
                  'source': str(source), 'source_sha256': hashes,
                  'pdk_commit': layout['pdk_commit'], 'pins': ['D','CLK','Q','VDD','VMID','VSS'],
                  'clock': '-1 to +1 captures D; 0 is invalid as a settled level',
                  'template_sha256': digest(CELLS_DIR/'template.json')}
    (base/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    (destination/'library.json').write_text(json.dumps({'cells':['TDFF'], 'extension_only':True}, indent=2)+'\n')
    return provenance


def load_library(root=CELLS_DIR, extension=EXTENSION):
    """Load real combinational views, then add TDFF without rewriting a manifest."""
    library = Library.load(root)
    base = Path(extension)/'TDFF'
    a = json.loads((base/'TDFF.abstract.json').read_text())
    char = base/'TDFF.char.json'
    if not char.exists():
        raise FileNotFoundError('TDFF characterization required before physical integration')
    c = json.loads(char.read_text())
    if c.get('source_sha256') != digest(base/'TDFF.ext.spice'):
        raise ValueError('TDFF characterization is stale for the extracted devices')
    final = json.loads((base/'tdff_summary.json').read_text())
    for suffix,key in [('gds','gds'),('abstract.json','abstract'),('spice','schematic_netlist'),('ext.spice','extracted')]:
        if digest(base/f'TDFF.{suffix}') != final['artifact_sha256'][key]:
            raise ValueError('TDFF extension differs from final delivery: '+suffix)
    library.cells['TDFF'] = Cell('TDFF', a['width'], a['height'], a['pins'],
        a['obstructions'], base/'TDFF.gds', c,
        {'M2': a['free_M2_tracks']}, a.get('routing', {}))
    library.source += ' + ' + str(Path(extension).resolve())
    library.validate()
    return library


def subckts(root=CELLS_DIR, extension=EXTENSION):
    return (Path(root)/'out/all.spice').read_text() + '\n' + (Path(extension)/'TDFF/TDFF.spice').read_text()
