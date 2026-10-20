"""Close unary truth vectors under cell composition on balanced trits.

Each tuple lists a function's outputs at -1, 0, +1. Starting with the
input wire and constant ties, a fixed point enumerates every unary circuit
these cells can express. This is a cell-basis check, not an HDL synthesizer.
"""

from itertools import product

TRITS = (-1, 0, 1)


def inv(a):
    return -a


def nand(a, b):
    return -min(a, b)


def nor(a, b):
    return -max(a, b)


def nany(a, b):
    return -max(-1, min(1, a + b))


def unary_closure(*, unary=(), binary=(), constants=()):
    """Enumerate realizable one-input truth tables, including an input wire."""
    known = {TRITS} | {(c, c, c) for c in constants}
    while True:
        previous = set(known)
        known.update(tuple(f(a) for a in x) for f in unary for x in previous)
        known.update(tuple(f(a, b) for a, b in zip(x, y, strict=True))
                     for f in binary for x, y in product(previous, repeat=2))
        if known == previous:
            return known


def surjective_and_depends_on_both(function):
    """Check the two-input premise of Słupecki's completeness criterion."""
    table = {(a, b): function(a, b) for a, b in product(TRITS, repeat=2)}
    depends_a = any(len({table[a, b] for a in TRITS}) > 1 for b in TRITS)
    depends_b = any(len({table[a, b] for b in TRITS}) > 1 for a in TRITS)
    return set(table.values()) == set(TRITS) and depends_a and depends_b
