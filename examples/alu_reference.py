"""Independent integer specification and representative stimuli for alu.tv.

No HDL IR or gate network is used to predict the result. Min/max intentionally
compare balanced digits, since TritVerilog &/| are digit-wise operations.
"""

from itertools import product


def encode(value, width):
    """Return MSB-first balanced digits, discarding digits beyond width."""
    digits = []
    for _ in range(width):
        digit = (value+1) % 3 - 1
        digits.append(digit)
        value = (value-digit)//3
    return tuple(reversed(digits))


def decode(digits):
    value = 0
    for digit in digits:
        value = 3*value + int(digit)
    return value


def result(a, b, op):
    """Exact integer result for opcode -4..+4, in the specified order."""
    if op in (-1, 0):
        combine = min if op == -1 else max
        return decode(combine(x, y) for x, y in zip(encode(a, 2), encode(b, 2)))
    return {-4: a+b, -3: a-b, -2: -a, 1: 3*a, 2: (a+1)//3,
            3: (a > b)-(a < b), 4: a*b}[op]


def expected(vector):
    """flow.simulate callback; inputs follow alu's declared a, b, op order."""
    a, b, op = (decode(vector[i:i+2]) for i in (0, 2, 4))
    return {f'r[{i}]': digit for i, digit in zip((3, 2, 1, 0), encode(result(a, b, op), 4))}


def representative_vectors():
    """Greedily cover all nine opcodes and -1/0/+1 on each output digit."""
    uncovered = {('op', k) for k in range(-4, 5)}
    uncovered |= {(f'r[{i}]', v) for i in range(4) for v in (-1, 0, 1)}
    candidates = list(product((-1, 0, 1), repeat=6))
    coverage = {v: {('op', decode(v[4:]))} | set(expected(v).items()) for v in candidates}
    selected = []
    while uncovered:
        best = max(candidates, key=lambda v: len(coverage[v] & uncovered))
        if not coverage[best] & uncovered:
            raise AssertionError(f'unreachable ALU coverage: {uncovered}')
        selected.append(best)
        uncovered -= coverage[best]
        candidates.remove(best)
    return selected


def check_truth_table(design, net):
    """Check all 729 inputs against the independent oracle, source and cells."""
    from tritflow.synth import evaluate_netlist

    table = design.truth_table()
    actual = evaluate_netlist(net, {k: table[k] for k in design.inputs})
    for row in range(729):
        vector = tuple(int(table[k][row]) for k in design.inputs)
        reference = expected(vector)
        for key, value in reference.items():
            assert int(table[key][row]) == value, (vector, key, 'source')
            assert int(actual[key][row]) == value, (vector, key, 'cells')
    return 729
