"""Reduced ordered ternary decision diagrams for two settled endpoint vectors.

Each decision has three branches (-1, 0, +1). Boolean leaves describe a set
of vectors, allowing reconvergent side-input conditions to be intersected
exactly without enumerating 3**(2*number_of_inputs) vector pairs.
"""
from __future__ import annotations

from itertools import product

TRITS = (-1, 0, 1)


def function(cell, values):
    """Ideal settled cell function; these values do not model analog hazards."""
    if cell == "INV": return -values[0]
    if cell == "BUF": return values[0]
    if cell == "NAND": return -min(values)
    if cell == "NOR": return -max(values)
    if cell == "NANY": return -max(-1, min(1, sum(values)))
    return {"TIEP": 1, "TIEZ": 0, "TIEN": -1}[cell]


class Diagram:
    """Canonical sets, including exact union, intersection, difference and witness."""

    def __init__(self, variables, max_nodes=1_000_000):
        self.variables = variables
        self.max_nodes = max_nodes
        self.nodes = [(len(variables), ()), (len(variables), ())]
        self.unique = {}
        self.cache = {}

    def node(self, variable, children):
        children = tuple(children)
        if len(set(children)) == 1: return children[0]
        key = (variable, children)
        if key not in self.unique:
            if len(self.nodes) >= self.max_nodes:
                raise RuntimeError("STA decision-diagram node budget exceeded; no partial report published")
            self.unique[key] = len(self.nodes)
            self.nodes.append(key)
        return self.unique[key]

    def literal(self, variable, value):
        return self.node(variable, [int(v == value) for v in TRITS])

    def apply(self, op, a, b):
        if op in {"and", "or"} and a > b:
            a, b = b, a
        if op == "and":
            if a == 0 or b == 0: return 0
            if a == 1: return b
            if b == 1 or a == b: return a
        elif op == "or":
            if a == 1 or b == 1: return 1
            if a == 0: return b
            if b == 0 or a == b: return a
        elif op == "diff":
            if a == 0 or b == 1 or a == b: return 0
            if b == 0: return a
        key = (op, a, b)
        if key in self.cache: return self.cache[key]
        va, ca = self.nodes[a]; vb, cb = self.nodes[b]
        variable = min(va, vb)
        children = [self.apply(op, ca[i] if va == variable else a,
                              cb[i] if vb == variable else b) for i in range(3)]
        result = self.node(variable, children)
        self.cache[key] = result
        return result

    def intersect(self, *nodes):
        result = 1
        for node in nodes:
            result = self.apply("and", result, node)
            if result == 0: break
        return result

    def witness(self, node):
        if node == 0: raise ValueError("Empty sensitization condition")
        values = dict.fromkeys(self.variables, 0)
        while node > 1:
            variable, children = self.nodes[node]
            branch = next(i for i, child in enumerate(children) if child)
            values[self.variables[variable]] = TRITS[branch]
            node = children[branch]
        return values

    def rollback(self, size):
        """Release search-only nodes; persistent graph conditions precede size."""
        self.nodes = self.nodes[:size]
        self.unique = {key: index for index, key in enumerate(self.nodes[2:], 2)}
        self.cache.clear()

    def gate(self, cell, inputs):
        result = dict.fromkeys(TRITS, 0)
        for values in product(TRITS, repeat=len(inputs)):
            condition = self.intersect(*(signal[v] for signal, v in zip(inputs, values)))
            trit = function(cell, values)
            result[trit] = self.apply("or", result[trit], condition)
        return result
