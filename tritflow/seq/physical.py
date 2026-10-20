"""Official drawing DRC / strict device LVS for the isolated TDFF extension."""
import json
from pathlib import Path

from tritflow import PDK_ROOT
from tritflow.extract import extract_layout
from tritflow.pnr import pdk_drc
from .library import EXTENSION
from .writers import spice


def lvs(gds, netlist, cell_subckts, directory, **options):
    """Use a reference file to keep the recorded combinational SPICE module intact."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    reference = directory/'sequential_reference.spice'
    reference.write_text(spice(netlist) + '\n' + cell_subckts)
    return extract_layout(gds, netlist.top, directory, reference=reference, **options)


def qualify_cell(extension=EXTENSION, *, output_dir='build/seq_flow/cell', pdk=PDK_ROOT):
    extension, out = Path(extension), Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    base = extension/'TDFF'
    drc = pdk_drc(base/'TDFF.gds', 'TDFF', out/'TDFF.drc.lyrdb', pdk_root=pdk)
    lvs = extract_layout(base/'TDFF.gds', 'TDFF', out/'lvs',
                         reference=base/'TDFF.spice', pdk=pdk)
    report = {'drc':drc, 'lvs':lvs, 'passed':drc['clean'] and lvs['matched']}
    (out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['passed']:
        raise ValueError('TDFF independent DRC/LVS failed')
    return report
