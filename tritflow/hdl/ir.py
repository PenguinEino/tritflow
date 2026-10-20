"""Bit-level ternary DAG and batched, vectorized combinational simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

from tritflow.netlist import Port
from .parser import Location
from .semantics import EXTENDED, evaluate_operation


@dataclass(eq=False)
class Node:
    """One trit-valued operation; primitive metadata preserves authored cells.

    Arithmetic args concatenate two equally wide MSB-first operands; value is
    the result's LSB-based digit index. Comparisons use the same operand format
    and return +/-1. A mux has (condition, then, else) args and Kleene consensus;
    select is a procedural join with a crisp +/-1 condition.
    A case has (predicate, data) pairs followed by a fallback digit; predicates
    retain exact label equalities so the mapper can prove a one-hot partition.
    Shifts concatenate a width-trit data operand and a self-sized amount;
    value selects the result digit. Negative amounts reverse the direction.
    """

    op: str
    args: tuple[Node, ...] = ()
    value: int | None = None
    name: str = ""
    hier: str = ""
    loc: Location | None = None
    primitive: str = ""
    width: int = 0


def reachable(outputs: Iterable[Node]) -> list[Node]:
    """Return only live nodes in driver-before-load order."""
    ordered: list[Node] = []
    visited: set[Node] = set()
    for root in outputs:
        stack = [(root, False)]
        while stack:
            node, expanded = stack.pop()
            if node in visited:
                continue
            if expanded:
                visited.add(node)
                ordered.append(node)
            else:
                stack.append((node, True))
                stack.extend((arg, False) for arg in reversed(node.args) if arg not in visited)
    return ordered


def input_batches(names: list[str], count: int, *, exhaustive: bool, seed: int = 0,
                  batch_size: int = 8192):
    """Generate base-three input rows without allocating an entire truth table."""
    rng = np.random.default_rng(seed)
    for start in range(0, count, batch_size):
        size = min(batch_size, count - start)
        if exhaustive:
            row = np.arange(start, start + size, dtype=np.int64)
            values = np.empty((size, len(names)), dtype=np.int8)
            for col in reversed(range(len(names))):
                values[:, col] = row % 3 - 1
                row //= 3
        else:
            values = rng.integers(-1, 2, (size, len(names)), dtype=np.int8)
        yield {name: values[:, col] for col, name in enumerate(names)}


def normalize_inputs(names: list[str], values: dict) -> dict[str, np.ndarray]:
    """Validate trits before narrowing to int8, then broadcast input arrays."""
    if set(values) != set(names):
        raise ValueError(f"expected inputs {names}; received {list(values)}")
    arrays = []
    for name in names:
        array = np.asarray(values[name])
        if not np.isin(array, [-1, 0, 1]).all():
            raise ValueError(f"input {name!r} contains a value outside trits -1, 0, +1")
        arrays.append(array.astype(np.int8))
    return dict(zip(names, np.broadcast_arrays(*arrays))) if names else {}


@dataclass
class Design:
    """Flattened circuit before cell assignment, with one DAG node per trit.

    ``ports`` retain declared bit indices and direction; ``inputs`` maps input
    names to source nodes and ``outputs`` maps output names to driving nodes.
    Operations include neg/min/max/nany, integer arithmetic result digits,
    comparisons and Kleene muxes. An authored primitive
    also records its cell name so synthesis can retain the original circuit.
    """

    top: str
    ports: list[Port]
    outputs: dict[str, Node]
    inputs: dict[str, Node]
    params: dict[str, int] = field(default_factory=dict)

    @property
    def nodes(self) -> list[Node]:
        return reachable(self.outputs.values())

    def evaluate(self, inputs: dict) -> dict[str, np.ndarray]:
        """Compute ideal settled outputs for scalar or broadcast NumPy inputs.

        Supply every bit-blasted input exactly once, with values -1/0/+1 rather
        than voltages. Output dictionary keys match the output port names. This
        evaluates the source DAG, independently of the mapped cell simulator
        used for synthesis equivalence checks.
        """
        values = normalize_inputs(list(self.inputs), inputs)
        shape = next(iter(values.values())).shape if values else ()
        results: dict[Node, np.ndarray] = {}
        for node in self.nodes:
            args = [results[arg] for arg in node.args]
            if node.op == "input":
                result = values[node.name]
            elif node.op == "const":
                result = np.full(shape, node.value, dtype=np.int8)
            elif node.op == "neg":
                result = -args[0]
            elif node.op == "min":
                result = np.minimum(*args)
            elif node.op == "max":
                result = np.maximum(*args)
            elif node.op == "nany":
                result = -np.clip(args[0] + args[1], -1, 1)
            elif node.op in EXTENDED:
                result = evaluate_operation(node.op, args, node.value, width=node.width)
            else:
                raise ValueError(f"unknown IR operation {node.op!r}")
            results[node] = result
        return {name: results[node] for name, node in self.outputs.items()}

    simulate = evaluate

    def truth_table(self, *, max_inputs: int = 12) -> dict[str, np.ndarray]:
        """Return columns for all input/output bits, ordered -1, 0, +1.

        The limit avoids accidentally constructing an enormous notebook table;
        synthesis uses streaming batches instead.
        """
        names = list(self.inputs)
        if len(names) > max_inputs:
            raise ValueError(f"truth_table has {len(names)} inputs; increase max_inputs explicitly")
        chunks = []
        for inputs in input_batches(names, 3 ** len(names), exhaustive=True):
            outputs = self.evaluate(inputs)
            size = len(next(iter(inputs.values()))) if inputs else 1
            chunks.append({**inputs, **{k: np.broadcast_to(v, (size,)) for k, v in outputs.items()}})
        return {name: np.concatenate([c[name] for c in chunks]) for name in [*names, *self.outputs]}
