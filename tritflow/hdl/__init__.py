"""Combinational TritVerilog: trit -1/0/+1 is not Verilog's four-state logic.

At settled logic levels, -1, 0 and +1 correspond to -5, 0 and +5 V on
TR-1um. ``~a`` is -a; ``a & b`` and ``a | b`` are min(a,b) and max(a,b).
``nany(a,b)`` is -clamp(a+b,-1,+1), not a Boolean NAND. There are no x/z
states or storage elements. Balanced-ternary integer +, -, * and comparisons
work on signals; context widths extend with zero and discard high trits.
``c ? a : b`` uses Kleene consensus at c=0. ``always @*`` blocks use blocking
assignments, if/else and exact case tables; incomplete assignment is an error.

``load(path, top=..., params={"N": 4})`` parses source, evaluates integer
parameters and generate loops, then flattens module connections into a DAG of
single-trit operations. ``design.inputs`` and ``design.outputs`` use physical
bit names such as ``a[0]``; source hierarchy is retained on operation nodes.
Vectors/concatenations run in declared left-to-right order, and ``4'tT01T``
uses T for -1 with the most significant digit first.

``design.evaluate({"a": -1, "b": 1})`` evaluates one vector; NumPy arrays
evaluate many vectors together. ``design.truth_table()`` returns all input and
output columns for a small circuit. Synthesis in :mod:`tritflow.synth` turns
the operations into INV/NAND/NOR/NANY and TIE cells. Logic simulation here
computes settled trits; device voltages and settling time are checked by SPICE.
"""

from .parser import AST, HDLError, parse, read_sources
from .elaborate import elaborate
from .ir import Design, Node


def load(path, *, top=None, params=None) -> Design:
    """Load .tv source and return its flattened, bit-level combinational design.

    ``path`` is a filename or list of files; relative `include paths are resolved
    beside their source file. Select ``top`` when multiple modules are defined.
    ``params`` overrides integer module parameters before widths and generate
    loops are expanded. For example, ``load("examples/adder.tv", top="adder",
    params={"N": 4})`` elaborates four full-adder slices with scalar net names.
    """
    return elaborate(read_sources(path), top=top, params=params)


def loads(text: str, *, top=None, params=None, filename="<string>") -> Design:
    """Parse and elaborate in-memory notebook source with located errors."""
    return elaborate(parse(text, filename), top=top, params=params)


__all__ = ["AST", "Design", "Node", "HDLError", "parse", "elaborate", "load", "loads"]
