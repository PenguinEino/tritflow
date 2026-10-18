"""Deterministic physical-design stress circuits (not HDL synthesis fixtures)."""
import random

from tritflow.netlist import GateNetlist, Instance, Port


def chain(count=20):
    instances = [Instance(f"g{i}", "INV", {"A": "a" if i == 0 else f"n{i-1}",
                                           "Y": "z" if i == count-1 else f"n{i}"}) for i in range(count)]
    return GateNetlist(f"chain{count}", [Port("a", "input"), Port("z", "output")], instances)


def fanout_tree(depth=5):
    instances, previous = [], ["a"]
    for level in range(depth):
        current = []
        for j, source in enumerate(previous):
            for k in range(2):
                name = f"n{level}_{2*j+k}"
                instances.append(Instance(name, "INV", {"A": source, "Y": name}))
                current.append(name)
        previous = current
    return GateNetlist(f"tree{depth}", [Port("a", "input")]+[Port(n, "output") for n in previous], instances)


def random_dag(count=100, seed=17):
    rng = random.Random(seed)
    inputs = [f"a{i}" for i in range(8)]
    available, instances = list(inputs), []
    for i in range(count):
        source_a, source_b = rng.sample(available, 2)
        cell = rng.choice(["NANY", "NAND", "NOR", "INV"])
        pins = {"A": source_a, "Y": f"n{i}"}
        if cell != "INV":
            pins["B"] = source_b
        instances.append(Instance(f"g{i}", cell, pins))
        available.append(f"n{i}")
    return GateNetlist(f"dag{count}", [Port(n, "input") for n in inputs]+
                      [Port(f"n{i}", "output") for i in range(count-8, count)], instances)
