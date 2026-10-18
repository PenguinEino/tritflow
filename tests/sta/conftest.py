"""Small complete synthetic ternary tables; no external simulator is needed."""
import hashlib
from itertools import product
import json

import pytest

from tritflow.sta.logic import function
from tritflow.sta.model import TimingLibrary


@pytest.fixture
def library(tmp_path):
    for cell, pins in {'INV':['A'], 'BUF':['A'], 'NANY':['A','B'],
                       'NAND':['A','B'], 'NOR':['A','B'], 'TIEZ':[]}.items():
        directory = tmp_path/cell; directory.mkdir()
        source = b'* synthetic test source\n'
        (directory/f'{cell}.ext.spice').write_bytes(source)
        arcs, simultaneous = [], []
        states = list(product((-1,0,1), repeat=len(pins)))
        for before, after in product(states, repeat=2):
            changed = [p for p,a,b in zip(pins,before,after) if a != b]
            if not changed: continue
            old, new = function(cell,before), function(cell,after)
            delay = (5 + sum((v+1)*(i+1) for i,v in enumerate(before))
                     + sum((v+1)*(i+2) for i,v in enumerate(after)))*1e-9
            row = {'id': f'{cell}:{before}:{after}', 'from_inputs': dict(zip(pins,before)),
                'to_inputs': dict(zip(pins,after)), 'changed_inputs':changed,
                'output_from':old,'output_to':new,
                'input_pin':changed[0] if len(changed)==1 else None,
                'settling_s': [[delay, delay+2e-9],[delay+4e-9,delay+6e-9]],
                'passed':[[True,True],[True,True]]}
            (arcs if len(changed)==1 else simultaneous).append(row)
        data = {'schema_version':1,'cell':cell,'complete':True,'passed':True,
            'kind':'logic' if pins else 'constant', 'inputs':pins,
            'axes':{'load_f':[1e-15,2e-12],'input_transition_s':[1e-9,100e-9]},
            'source_sha256':hashlib.sha256(source).hexdigest(),
            'generation':{'id':'synthetic'}, 'arcs':arcs,'simultaneous':simultaneous,
            'input_capacitance':{'per_pin':{p:{'max_f':10e-15} for p in pins}}}
        (directory/f'{cell}.timing.json').write_text(json.dumps(data))
    return TimingLibrary(['INV','BUF','NANY','NAND','NOR','TIEZ'], tmp_path)
