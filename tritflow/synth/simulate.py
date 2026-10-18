"""Independent cell-level evaluator and streaming synthesis equivalence checks."""

from __future__ import annotations

from collections import deque

import numpy as np

from tritflow.hdl.ir import Design, input_batches, normalize_inputs
from tritflow.netlist import GateNetlist


CELL_INPUTS = {
    "INV": ("A",), "BUF": ("A",), "NAND": ("A", "B"),
    "NOR": ("A", "B"), "NANY": ("A", "B"),
    "TIEP": (), "TIEZ": (), "TIEN": (),
}


def ordered_instances(net: GateNetlist):
    """Validate single drivers/pins and topologically order arbitrary gate JSON."""
    inputs = [p.name for p in net.ports if p.dir == "input"]
    if len({p.name for p in net.ports}) != len(net.ports):
        raise ValueError("duplicate netlist port")
    if any(p.dir not in {"input", "output"} for p in net.ports):
        raise ValueError("port direction must be input or output")
    drivers = dict.fromkeys(inputs, -1)
    names = set()
    for index, inst in enumerate(net.instances):
        if inst.name in names:
            raise ValueError(f"duplicate instance {inst.name!r}")
        names.add(inst.name)
        if inst.cell not in CELL_INPUTS or set(inst.pins) != {*CELL_INPUTS.get(inst.cell, ()), "Y"}:
            raise ValueError(f"invalid cell or pin set for {inst.name!r}")
        output = inst.pins["Y"]
        if output in drivers:
            raise ValueError(f"multiple drivers of {output!r}")
        drivers[output] = index
    successors = [[] for _ in net.instances]
    degree = []
    for index, inst in enumerate(net.instances):
        dependencies = set()
        for pin in CELL_INPUTS[inst.cell]:
            signal = inst.pins[pin]
            if signal not in drivers:
                raise ValueError(f"undriven signal {signal!r}")
            if drivers[signal] >= 0:
                dependencies.add(drivers[signal])
        degree.append(len(dependencies))
        for parent in dependencies:
            successors[parent].append(index)
    for port in net.ports:
        if port.name not in drivers:
            raise ValueError(f"undriven output {port.name!r}")
    ready = deque(i for i, count in enumerate(degree) if not count)
    ordered = []
    while ready:
        index = ready.popleft()
        ordered.append(net.instances[index])
        for child in successors[index]:
            degree[child] -= 1
            if degree[child] == 0:
                ready.append(child)
    if len(ordered) != len(net.instances):
        raise ValueError("combinational cycle in gate netlist")
    return ordered


def evaluate_netlist(net: GateNetlist, inputs: dict, *, ordered=None,
                     return_all: bool = False) -> dict[str, np.ndarray]:
    """Evaluate ideal cell levels independently of the source expression graph.

    ``inputs`` maps each bit-blasted input name to -1/0/+1 scalars or NumPy
    arrays. The usual return contains output ports; ``return_all=True`` also
    exposes input and internal nets for a gate graph or signal inspection.
    INV negates, NAND/NOR negate min/max, and NANY negates the saturated sum.
    These are settled logic values, without device delay or analog voltages.
    """
    values = normalize_inputs([p.name for p in net.ports if p.dir == "input"], inputs)
    shape = next(iter(values.values())).shape if values else ()
    for inst in ordered if ordered is not None else ordered_instances(net):
        args = [values[inst.pins[pin]] for pin in CELL_INPUTS[inst.cell]]
        if inst.cell in {"TIEP", "TIEZ", "TIEN"}:
            result = np.full(shape, {"TIEP": 1, "TIEZ": 0, "TIEN": -1}[inst.cell], dtype=np.int8)
        elif inst.cell == "INV":
            result = -args[0]
        elif inst.cell == "BUF":
            result = args[0]
        elif inst.cell == "NAND":
            result = -np.minimum(args[0], args[1])
        elif inst.cell == "NOR":
            result = -np.maximum(args[0], args[1])
        else:
            total = args[0] + args[1]
            result = np.where(total > 0, -1, np.where(total < 0, 1, 0)).astype(np.int8)
        values[inst.pins["Y"]] = result
    if return_all:
        return values
    return {p.name: values[p.name] for p in net.ports if p.dir == "output"}


def check_equivalence(design: Design, net: GateNetlist, *, seed: int = 0,
                      random_vectors: int = 100_000, batch_size: int = 8192) -> dict:
    """Exhaust all <=12 input trits; otherwise check reproducible random vectors."""
    names = list(design.inputs)
    expected_ports = [(p.name, p.dir) for p in design.ports]
    if [(p.name, p.dir) for p in net.ports] != expected_ports:
        raise ValueError("source and mapped port interfaces differ")
    exhaustive = len(names) <= 12
    count = 3 ** len(names) if exhaustive else random_vectors
    if count < 1:
        raise ValueError("equivalence requires at least one vector")
    ordered = ordered_instances(net)
    for inputs in input_batches(names, count, exhaustive=exhaustive, seed=seed, batch_size=batch_size):
        expected = design.evaluate(inputs)
        actual = evaluate_netlist(net, inputs, ordered=ordered)
        for name in expected:
            mismatch = np.asarray(expected[name] != actual[name]).reshape(-1)
            if mismatch.any():
                row = int(np.flatnonzero(mismatch)[0])
                vector = {key: int(value[row]) for key, value in inputs.items()}
                raise ValueError(f"equivalence failed for output {name!r}, inputs {vector}")
    return {"passed": True, "mode": "exhaustive" if exhaustive else "random",
            "vectors": count, "seed": None if exhaustive else seed}
