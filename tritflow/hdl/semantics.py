"""Integer/table semantics for operations before library-cell decomposition."""

import numpy as np


EXTENDED = {'add', 'sub', 'mul', 'eq', 'ne', 'lt', 'le', 'gt', 'ge', 'mux', 'select', 'is_true'}


def evaluate_operation(op, args, digit=None):
    """Evaluate source semantics independently of adder/selector gate networks."""
    if op == 'select':
        return np.where(args[0] == 1, args[1], args[2]).astype(np.int8)
    if op == 'mux':
        c, x, y = args
        return np.where(c == 1, x, np.where(c == -1, y, np.where(x == y, x, 0))).astype(np.int8)
    if op == 'is_true':
        return np.where(args[0] == 1, 1, -1).astype(np.int8)
    width = len(args)//2
    a, b = args[:width], args[width:]
    if op in {'add', 'sub', 'mul'}:
        # Python integers preserve the specified semantics even for very wide buses.
        dtype = object if width > (19 if op == 'mul' else 38) else np.int64
        av = sum(x.astype(dtype)*3**i for i, x in enumerate(reversed(a)))
        bv = sum(x.astype(dtype)*3**i for i, x in enumerate(reversed(b)))
        value = av+bv if op == 'add' else av-bv if op == 'sub' else av*bv
        for _ in range(digit):
            remainder = (value+1)%3-1
            value = (value-remainder)//3
        return np.asarray((value+1)%3-1, dtype=np.int8)
    sign = np.zeros_like(args[0])
    for x, y in zip(a, b):
        sign = np.where(sign != 0, sign, (x > y).astype(np.int8)-(x < y).astype(np.int8))
    result = {'eq': sign == 0, 'ne': sign != 0, 'lt': sign < 0,
              'le': sign <= 0, 'gt': sign > 0, 'ge': sign >= 0}[op]
    return np.where(result, 1, -1).astype(np.int8)
