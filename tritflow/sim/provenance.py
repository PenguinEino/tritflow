"""Content provenance of the public PDK consumed by a numerical experiment."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
from tritflow import PDK_ROOT, ROOT


def pdk_provenance(pdk=PDK_ROOT):
    """Record models and decks; reject a known checkout differing from setup pins."""
    root = Path(pdk).expanduser().resolve()
    pins = ROOT/'notebook/setup_pins.json'
    expected = json.loads(pins.read_text())['pdk_commit']
    actual = None
    if (root/'.git').exists():
        actual = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        if actual != expected:
            raise ValueError(f'Unqualified PDK checkout {actual}; require public {expected}')
    paths = []
    for folder in ('libs.tech/spice/models','libs.tech/klayout/tech/lvs','libs.tech/klayout/tech/drc'):
        paths += [p for p in sorted((root/folder).rglob('*')) if p.is_file()]
    return {'root':str(root), 'qualified_commit':expected, 'checkout_commit':actual,
        'setup_pins_sha256':hashlib.sha256(pins.read_bytes()).hexdigest(),
        'consumed_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'scope':'Public pinned PDK; numerical interconnect assumptions are separately labelled.'}
