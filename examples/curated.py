"""Notebook circuit choices and independent integer arithmetic specifications.

These references never inspect HDL, optimized IR or mapped gate functions.
They also serve as the expected-output callback for transistor simulation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping


def radix3(value: int, width: int, name: str) -> dict[str, int]:
    """Encode an integer as width little-endian balanced trits, rejecting overflow."""
    out = {}
    for i in range(width):
        digit = (value+1) % 3-1
        out[f"{name}[{i}]"] = digit
        value = (value-digit)//3
    if value:
        raise ValueError("integer does not fit the specified balanced-ternary width")
    return out


def integer(v: Mapping[str, int], name: str, width: int) -> int:
    """Decode a bit-blasted bus using arithmetic weights, independent of gates."""
    return sum(int(v[f"{name}[{i}]"])*3**i for i in range(width))


def sign_reference(v):
    s = (int(v["a"]) > 0)-(int(v["a"]) < 0)
    return {"s": s, "opposite": -s}


def compare_reference(v):
    a, b = integer(v, "a", 2), integer(v, "b", 2)
    return {"cmp": (a > b)-(a < b)}


def multiply_reference(v):
    return radix3(integer(v, "a", 2)*integer(v, "b", 2), 4, "p")


def sorter_reference(v):
    lo, hi = sorted((int(v["a"]), int(v["b"])))
    return {"lo": lo, "hi": hi}


@dataclass(frozen=True)
class Example:
    """One source/top and an independent expected-output function."""

    top: str
    description: str
    reference: Callable[[Mapping[str, int]], dict[str, int]]

    @property
    def path(self):
        return Path(__file__).with_name(self.top+".tv")

    def oracle(self, inputs):
        def expected(vector):
            return self.reference(dict(zip(inputs, vector, strict=True)))
        return expected


DESIGNS = {
    "sign": Example("sign", "One trit's sign and its opposite", sign_reference),
    "compare2": Example("compare2", "Signed comparison of two two-trit integers", compare_reference),
    "mul2": Example("mul2", "Exact two-trit by two-trit product in four trits", multiply_reference),
    "minmax": Example("minmax", "Sort two scalar trits into ascending order", sorter_reference),
}
