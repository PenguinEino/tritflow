"""Independent integer oracle for the three-instruction shuttle ALU.

The signed opcode selects subtract / nearest division by three / add. No IR
or mapped gate network is used to predict levels or choose coverage vectors.
"""

from itertools import product

from .alu9_reference import encode, decode


def result(a, b, op):
    return {-1: a-b, 0: (a+1)//3, 1: a+b}[op]


def expected(vector):
    a, b, op = decode(vector[:2]), decode(vector[2:4]), vector[4]
    return {f'r[{i}]': digit for i, digit in zip((2,1,0), encode(result(a,b,op),3))}


def representative_vectors():
    """Cover every instruction and all three levels on every result digit."""
    uncovered = {('op', k) for k in (-1,0,1)}
    uncovered |= {(f'r[{i}]', v) for i in range(3) for v in (-1,0,1)}
    candidates = list(product((-1,0,1),repeat=5))
    coverage = {v: {('op',v[4])} | set(expected(v).items()) for v in candidates}
    selected = []
    while uncovered:
        best = max(candidates,key=lambda v: len(coverage[v] & uncovered))
        if not coverage[best] & uncovered:
            raise AssertionError(f'unreachable ALU coverage: {uncovered}')
        selected.append(best)
        uncovered -= coverage[best]
        candidates.remove(best)
    return selected


def check_truth_table(design, net):
    """Check all 243 states against independent integers, source and cells."""
    from tritflow.synth import evaluate_netlist

    table = design.truth_table()
    actual = evaluate_netlist(net,{k:table[k] for k in design.inputs})
    for row in range(243):
        vector = tuple(int(table[k][row]) for k in design.inputs)
        for key,value in expected(vector).items():
            assert int(table[key][row]) == value, (vector,key,'source')
            assert int(actual[key][row]) == value, (vector,key,'cells')
    return 243
