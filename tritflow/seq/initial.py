"""Rail-bounded Newton starting guesses for resistor-loaded gate internal nodes.

The PDK RR model can have off-rail algebraic roots. These topology-based guesses
choose a starting root; ngspice still solves the complete device equations and
no value is held during a transient. They are not an analog gate model.
"""


def gate_nodes(cell, pins):
    """Return trit guesses for the published INV/lattice/NANY divider networks."""
    if cell.startswith('TIE'):
        return {}
    a, y = pins['A'], pins['Y']
    def inv(value):
        return {'p':1 if value <= 0 else -1, 'n':-1 if value >= 0 else 1}
    if cell == 'INV':
        return inv(a)
    if cell == 'BUF':
        first,second = inv(a),inv(-a)
        return {'mid':-a,**{n+'0':v for n,v in first.items()},**{n+'1':v for n,v in second.items()}}
    b = pins['B']
    if cell == 'NAND':
        p = 1 if min(a,b) <= 0 else y
        n = -1 if min(a,b) >= 0 else y
        return {'p':p,'n':n,'nn':-1 if b >= 0 else n}
    if cell == 'NOR':
        p = 1 if max(a,b) <= 0 else y
        n = -1 if max(a,b) >= 0 else y
        return {'p':p,'n':n,'pp':1 if a <= 0 else p}
    if cell == 'NANY':
        p = 1 if max(a,b) <= 0 else y
        n = -1 if min(a,b) >= 0 else y
        return {'p':p,'n':n,'pp':1 if a <= 0 else p,
                'nn':-1 if b >= 0 else n,'c1':0,'c2':0}
    raise ValueError('unknown initial-guess cell '+cell)
