"""First-order circuit predictions independent of the measured SPICE currents.

The INV middle input enables both branches. Approximate MOS on-resistance
using nominal mobility, oxide thickness and threshold, then retain the RR
model's zero-bias geometry term. This is an explanatory estimate, not a fit.
"""

import re
from pathlib import Path

from scipy.constants import epsilon_0
from tritflow import VDD, VMID, VSS


def divider(dimensions, pdk):
    """Return branch R, zero-input voltage, current and signed supply power.

    Dimensions use µm. Only the PDK's dedicated 2.8-µm RR width branch is
    supported; other widths and nonconducting biases reject explicitly.
    """
    models = Path(pdk)/"libs.tech/spice/models"
    mos = (models/"models_IP62_mos_v2.lib").read_text()
    offsets = (models/"ip62_models").read_text()
    resistor = (models/"models_IP62_res_v5.lib").read_text()
    branch = resistor.split('.elseif (w == 2.8u)',1)[1].split('.endif',1)[0]
    number = r'([+\-]?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)'
    polynomial = re.search(number+r'\*\(\(l\*10\*\*6\)\*\*2\)'+number+
                           r'\*\(l\*10\*\*6\)'+number, branch)
    if polynomial is None:
        raise ValueError("RR geometry expression changed; review the hand estimate")
    a,b,c = map(float, polynomial.groups())
    branches = []
    for device, resistor_id, kind, rail, offset in (
            ('MP','RP','PMOS',VDD,'vthMP'), ('MN','RN','NMOS',VSS,'vthMN')):
        block = mos.split(f'.model {kind}_mst {kind}',1)[1].split('.subckt',1)[0]
        mobility = float(re.search(r'\bu0\s*=\s*'+number,block)[1])
        tox = float(re.search(r'\btox\s*=\s*'+number,block)[1])
        threshold = float(re.search(r"\bvth0\s*=\s*'"+number,block)[1])
        threshold += float(re.search(r'\b'+offset+r'\s*=\s*'+number,offsets)[1])
        overdrive = abs(VMID-rail)-abs(threshold)
        d, r = dimensions[device], dimensions[resistor_id]
        if r['w_um'] != 2.8 or overdrive <= 0:
            raise ValueError("divider approximation not applicable to this bias/width")
        ron = 1/(mobility*(3.9*epsilon_0/tox)*(d['w_um']/d['l_um'])*overdrive)
        rr = a*r['l_um']**2+b*r['l_um']+c
        if rr <= 0:
            raise ValueError("divider approximation requires positive branch resistance")
        branches.append({'rr_ohm':rr, 'ron_ohm':ron, 'total_ohm':rr+ron})
    upper,lower = branches
    current = (VDD-VSS)/(upper['total_ohm']+lower['total_ohm'])
    return {'upper':upper,'lower':lower,'current_a':current,
            'output_v':VSS+current*lower['total_ohm'], 'power_w':(VDD-VSS)*current}


def zero_dc(row):
    """Select the unique all-zero schematic DC measurement, never a maximum."""
    return next(r for r in row['dc'] if not any(r['input_trits']))


def rail_power(dc, supplies):
    """Power entering all voltage-source rails; do not double-count current."""
    return -sum(v*dc['rail_current_a'][name] for name,v in supplies.items())
