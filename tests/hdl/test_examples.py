"""Compare all small arithmetic examples with independent integer references."""

from pathlib import Path

import numpy as np
import pytest

from tritflow.hdl import load
from tritflow.synth import evaluate_netlist, synthesize


EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def circuit_table(name, params=None):
    design = load(EXAMPLES / f"{name}.tv", top=name, params=params)
    table = design.truth_table()
    net = synthesize(design)
    actual = evaluate_netlist(net, {key: table[key] for key in design.inputs})
    for key in design.outputs:
        np.testing.assert_array_equal(actual[key], table[key])
    return table, net


def split_integer(value):
    """Balanced remainder and next digit, derived only from integer arithmetic."""
    remainder = (value + 1) % 3 - 1
    return remainder, (value - remainder) // 3


@pytest.mark.parametrize("name, inputs", [("half_add", ["a", "b"]), ("full_add", ["a", "b", "cin"])])
def test_adders_all_inputs(name, inputs):
    table, net = circuit_table(name)
    total = sum(table[key].astype(np.int64) for key in inputs)
    expected_sum, expected_carry = split_integer(total)
    np.testing.assert_array_equal(table["sum"], expected_sum)
    np.testing.assert_array_equal(table["carry" if name == "half_add" else "cout"], expected_carry)
    assert net.report()["cells"] == ({"NANY": 5, "INV": 2} if name == "half_add" else {"NANY": 11, "INV": 5})


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_parameterized_adder_exhaustive_integer_reference(n):
    table, net = circuit_table("adder", {"N": n})
    a = sum(table[f"a[{i}]"].astype(np.int64) * 3**i for i in range(n))
    b = sum(table[f"b[{i}]"].astype(np.int64) * 3**i for i in range(n))
    remainder = a + b + table["cin"]
    for i in range(n):
        digit, remainder = split_integer(remainder)
        np.testing.assert_array_equal(table[f"sum[{i}]"], digit)
    np.testing.assert_array_equal(table["cout"], remainder)
    assert net.report()["cells"] == {"INV": 5*n, "NANY": 11*n}
    assert net.report()["equivalence"]["vectors"] == 3 ** (2*n+1)


def test_mul1_all_inputs():
    table, net = circuit_table("mul1")
    np.testing.assert_array_equal(table["p"], table["a"] * table["b"])
    assert net.report()["cells"] == {"NAND": 2, "NOR": 1, "INV": 1}


def test_mac1_all_inputs_and_taped_out_auxiliary_outputs():
    table, net = circuit_table("mac1")
    total = table["x"] + table["a"] * table["b"] + table["cin"]
    s, carry = split_integer(total)
    np.testing.assert_array_equal(table["sum"], s)
    np.testing.assert_array_equal(table["cout"], carry)
    np.testing.assert_array_equal(table["and_out"], np.minimum(table["a"], table["b"]))
    np.testing.assert_array_equal(table["or_out"], np.maximum(table["a"], table["b"]))
    assert net.report()["cells"] == {"INV": 9, "NANY": 11, "NAND": 2, "NOR": 1}


def test_minmax_all_inputs():
    table, _ = circuit_table("minmax")
    np.testing.assert_array_equal(table["lo"], np.minimum(table["a"], table["b"]))
    np.testing.assert_array_equal(table["hi"], np.maximum(table["a"], table["b"]))


def test_sign_all_inputs():
    table, _ = circuit_table("sign")
    np.testing.assert_array_equal(table["s"], np.sign(table["a"]))
    np.testing.assert_array_equal(table["opposite"], -np.sign(table["a"]))
