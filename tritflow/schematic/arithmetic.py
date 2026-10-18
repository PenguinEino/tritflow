"""Verified symbol grammars for the published ternary arithmetic cells.

The gate netlist does not serialize module port aliases. These small circuit
patterns recover them by exact, pin-order-preserving structural matching,
never by guessing that an anonymous net is a carry from its name or value.
Unknown/pruned/rewritten modules keep their real net names unless the caller
provides an explicit hierarchy port map.
"""
from collections import Counter
from dataclasses import dataclass
from itertools import permutations

from tritflow.synth.simulate import CELL_INPUTS

HALF = (
    ('g_t','NANY',('a','b'),'t'), ('g_na','INV',('a',),'na'),
    ('g_u','NANY',('b','t'),'u'), ('g_c','NANY',('na','u'),'carry'),
    ('g_d','NANY',('t','carry'),'d'), ('g_nd','INV',('d',),'nd'),
    ('g_s','NANY',('nd','carry'),'sum'),
)
FULL = tuple((f'ha1.{n}',c,tuple({'a':'a','b':'b'}.get(s,'h1_'+s) for s in ins),'h1_'+out)
             for n,c,ins,out in HALF)
FULL += tuple((f'ha2.{n}',c,tuple({'a':'h1_sum','b':'cin'}.get(s,'h2_'+s) for s in ins),'h2_'+out)
              for n,c,ins,out in HALF)
FULL += (('g_nc','NANY',('h1_carry','h2_carry'),'nc'),('g_cout','INV',('nc',),'cout'))
MUL = (('g_t1','NAND',('a','b'),'t1'),('g_t2','NOR',('a','b'),'t2'),
       ('g_t3','INV',('t2',),'t3'),('g_p','NAND',('t1','t3'),'p'))
PATTERNS = [('half_add',HALF,('a','b'),{'sum':'sum','carry':'carry'}),
            ('full_add',FULL,('a','b','cin'),{'sum':'h2_sum','cout':'cout'}),
            ('mul1',MUL,('a','b'),{'p':'p'})]


@dataclass(frozen=True)
class Arithmetic:
    module: str
    scope: str
    ports: dict[str,str]
    cells: dict[str,str]


def _fingerprints(rows,inputs):
    result=dict(inputs)
    remaining=list(rows)
    while remaining:
        ready=[r for r in remaining if all(s in result for s in r[2])]
        if not ready:return None
        for name,cell,ins,out in ready:
            result[out]=(cell,tuple(result[s] for s in ins))
            remaining.remove((name,cell,ins,out))
    return result


def match(instances,scope=''):
    """Match all cells and every ordered terminal, even with renamed instances."""
    rows=[(i.name,i.cell,tuple(i.pins[p] for p in CELL_INPUTS[i.cell]),i.pins['Y']) for i in instances]
    outputs={r[3] for r in rows}
    inputs=sorted({s for r in rows for s in r[2]}-outputs)
    for module,pattern,names,exports in PATTERNS:
        if len(rows)!=len(pattern) or len(inputs)!=len(names):continue
        if Counter(r[1] for r in rows)!=Counter(r[1] for r in pattern):continue
        expected=_fingerprints(pattern,{n:('input',n) for n in names})
        expected_counts=Counter(expected[r[3]] for r in pattern)
        for assignment in permutations(inputs):
            actual=_fingerprints(rows,{net:('input',name) for name,net in zip(names,assignment)})
            if actual is None or Counter(actual[r[3]] for r in rows)!=expected_counts:continue
            by_signature={actual[r[3]]:r for r in rows}
            # All reference nodes must have a unique corresponding device.
            if len(by_signature)!=len(rows):continue
            cells={r[0]:by_signature[expected[r[3]]][0] for r in pattern}
            ports=dict(zip(names,assignment))
            ports.update({name:by_signature[expected[signal]][3] for name,signal in exports.items()})
            return Arithmetic(module,scope,ports,cells)
    return None


def recognize(net):
    """Find exact arithmetic modules at every retained hierarchy boundary."""
    scopes={''}
    for i in net.instances:
        parts=i.hier.split('.') if i.hier else []
        scopes.update('.'.join(parts[:k]) for k in range(1,len(parts)+1))
    result={}
    for scope in sorted(scopes):
        instances=[i for i in net.instances if not scope or i.hier==scope or i.hier.startswith(scope+'.')]
        found=match(instances,scope)
        if found:result[scope]=found
    return result
