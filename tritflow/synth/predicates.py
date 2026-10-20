"""Conservative value and case-label proofs on the source expression DAG.

The unknown trit is an ordinary data value. Only a proved subset of {-1,+1}
permits Boolean-style selection; unrelated conditions never become one-hot.
"""

from itertools import product


TRITS = frozenset((-1, 0, 1))
COMPARISONS = {'eq', 'ne', 'lt', 'le', 'gt', 'ge'}


class Predicates:
    def __init__(self):
        self.cache = {}

    def values(self, node):
        """Overestimate reachable values, without enumerating primary inputs."""
        if node in self.cache:
            return self.cache[node]
        op = node.op
        if op == 'const':
            result = {node.value}
        elif op in COMPARISONS or op == 'is_true':
            result = {-1, 1}
        elif op == 'neg':
            result = {-v for v in self.values(node.args[0])}
        elif op in {'min', 'max', 'nany'}:
            pairs = product(*(self.values(a) for a in node.args))
            fn = min if op == 'min' else max if op == 'max' else lambda a,b: -max(-1,min(1,a+b))
            result = {fn(*p) for p in pairs}
        elif op == 'select':
            result = self.values(node.args[1]) | self.values(node.args[2])
        elif op == 'mux':
            result = set()
            for c, a, b in product(*(self.values(n) for n in node.args)):
                result.add(a if c == 1 else b if c == -1 else a if a == b else 0)
        elif op == 'case':
            result = set().union(*(self.values(n) for n in node.args[1::2]),
                                 self.values(node.args[-1]))
        else:
            result = TRITS
        self.cache[node] = frozenset(result)
        return self.cache[node]

    def crisp(self, node):
        return 0 not in self.values(node)


def labels(node):
    """Recover literal equality labels and their common selector, or no proof."""
    if node.op == 'eq':
        width = len(node.args)//2
        a, b = node.args[:width], node.args[width:]
        if not all(n.op == 'const' for n in b):
            a, b = b, a
        if b and all(n.op == 'const' for n in b):
            return a, {tuple(n.value for n in b)}
    elif node.op == 'max':
        a, b = (labels(n) for n in node.args)
        if a and b and a[0] == b[0]:
            return a[0], a[1] | b[1]
    return None


def case_partition(conditions):
    """Prove disjoint equality labels; return whether they cover all inputs.

    A missing proof returns None, distinct from a proved partial partition.
    No correlation between separately evaluated selector expressions is assumed.
    """
    selector, seen = None, set()
    for condition in conditions:
        proof = labels(condition)
        if proof is None:
            return None
        current, values = proof
        if selector is None:
            selector = current
        if selector != current or seen & values:
            return None
        seen |= values
    return len(seen) == 3**len(selector) if selector is not None else None
