"""Exhaustive ternary rewrite checks, cell mapping and electrical fanout trees."""

from copy import deepcopy
import random

import numpy as np
import pytest

from tritflow.hdl import load, loads
from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.synth import check_equivalence, evaluate_netlist, fanouts, optimize, synthesize
from tritflow.synth.simulate import ordered_instances


def design(expression, *, extra=""):
    return loads(f"module m(input trit a,b,output trit y); {extra} assign y={expression}; endmodule")


@pytest.mark.parametrize("expression,expected", [
    ("~a", {"INV": 1}),
    ("~(a&b)", {"NAND": 1}),
    ("~(a|b)", {"NOR": 1}),
    ("a&b", {"NAND": 1, "INV": 1}),
    ("a|b", {"NOR": 1, "INV": 1}),
    ("nany(a,b)", {"NANY": 1}),
    ("1'tT", {"TIEN": 1}),
    ("1't0", {"TIEZ": 1}),
    ("1't1", {"TIEP": 1}),
    ("~~a", {"BUF": 1}),
    ("~a & ~b", {"NOR": 1}),
    ("~a | ~b", {"NAND": 1}),
])
def test_cell_mapping(expression, expected):
    net = synthesize(design(expression))
    assert net.report()["cells"] == expected
    assert net.report()["equivalence"] == {"passed": True, "mode": "exhaustive", "vectors": 9, "seed": None}


@pytest.mark.parametrize("expression", [
    "~~a", "~~~~a", "a&a", "a|a", "a&1'tT", "a&1't1", "a|1'tT", "a|1't1",
    "a&1't0", "a|1't0", "nany(a,1't0)", "nany(1't0,~a)",
    "~a&~b", "~a|~b", "~(a&b)", "~(a|b)", "~nany(a,b)",
    "~(1'tT & 1't0)", "1'tT | 1't1", "nany(1't1,1'tT)",
    "1't0 & 1't1", "1'tT & 1't1", "1't0 | 1'tT", "1'tT | 1't0",
    "a & ~a", "a | ~a", "nany(a,~a)",
])
def test_every_rewrite_exhaustive_against_source(expression):
    source = design(expression)
    optimized = optimize(source)
    table = source.truth_table()
    inputs = {name: table[name] for name in source.inputs}
    np.testing.assert_array_equal(optimized.evaluate(inputs)["y"], table["y"])
    check_equivalence(source, synthesize(source))


@pytest.mark.parametrize("expression", ["a&~a", "a|~a"])
def test_boolean_complement_laws_are_not_applied(expression):
    net = synthesize(design(expression))
    assert evaluate_netlist(net, {"a": 0, "b": 1})["y"] == 0
    assert not any(inst.cell.startswith("TIE") for inst in net.instances)


def test_common_subexpressions_commute_and_dead_logic_is_removed():
    source = loads("""module m(input trit a,b,output trit y,z);
      wire trit dead;
      assign dead=~(a|b);
      assign y=nany(a,b);
      assign z=nany(b,a);
      endmodule""")
    net = synthesize(source)
    assert net.report()["cells"] == {"NANY": 1, "BUF": 1}
    assert len([node for node in optimize(source).nodes if node.op == "nany"]) == 1


def test_explicit_gates_remain_one_to_one_even_with_constant_inputs():
    d = loads("""module m(output trit y);
      wire trit w,z; inv one(w,1'tT); inv two(z,w); buf three(y,z);
      endmodule""")
    n = synthesize(d)
    assert n.report()["cells"] == {"TIEN": 1, "INV": 2, "BUF": 1}
    assert {i.name for i in n.instances} >= {"one", "two", "three"}
    assert evaluate_netlist(n, {})["y"] == -1


def test_de_morgan_only_removes_single_use_inversions():
    d = loads("""module m(input trit a,b,output trit x,y,z);
      assign x=~a; assign y=~b; assign z=x&y; endmodule""")
    net = synthesize(d)
    assert net.report()["cells"] == {"INV": 3, "NAND": 1}


@pytest.mark.parametrize("expression", ["~(a&b) & ~(a|b)", "~(a&b) | ~(a|b)"])
def test_de_morgan_does_not_expand_fused_nand_nor(expression):
    source = design(expression)
    before = synthesize(source, optimize_logic=False)
    after = synthesize(source)
    assert after.report()["total_cells"] <= before.report()["total_cells"]
    check_equivalence(source, after)


def test_composed_rewrites_and_mapping_random_expression_corpus():
    rng = random.Random(2027)

    def expr(depth):
        if depth == 0:
            return rng.choice(["a", "b", "1'tT", "1't0", "1't1"])
        op = rng.choice(["neg", "min", "max", "nany"])
        left = expr(depth - 1)
        if op == "neg":
            return f"~({left})"
        right = expr(depth - 1)
        if op == "nany":
            return f"nany({left},{right})"
        return f"({left}){'&' if op == 'min' else '|'}({right})"

    for _ in range(100):
        source = design(expr(4))
        net = synthesize(source)
        check_equivalence(source, net)


@pytest.mark.parametrize("limit", [2, 3, 4, 7])
def test_balanced_fanout_trees_count_repeated_pins(limit):
    gates = "\n".join(f"nany g{i}(y[{i}],a,a);" for i in range(40))
    d = loads(f"module m(input trit a,output trit [39:0] y); {gates} endmodule")
    net = synthesize(d, fanout_limit=limit)
    assert net.report()["cells"]["NANY"] == 40
    assert net.report()["cells"]["BUF"] > 0
    assert max(fanouts(net).values()) <= limit
    assert len({inst.pins['Y'] for inst in net.instances}) == len(net.instances)
    assert len(net.nets()) == len(net.instances) + 1
    check_equivalence(d, net)


@pytest.mark.parametrize("limit", [0, 1, -2, 2.5, True])
def test_invalid_fanout_limit(limit):
    with pytest.raises(ValueError, match=">= 2"):
        synthesize(design("a"), fanout_limit=limit)


def test_output_feedback_into_combinational_loads_and_multiple_aliases():
    d = loads("""module m(input trit a, output trit x,y,z);
      assign x=~a; assign y=~x; assign z=x; endmodule""")
    net = synthesize(d)
    check_equivalence(d, net)
    assert all(sum(i.pins["Y"] == p.name for i in net.instances) == 1 for p in net.ports if p.dir == "output")


def test_shared_min_and_nand_use_one_negative_lattice_gate():
    d = loads("""module m(input trit a,b,output trit lo,neglo);
      assign lo=a&b; assign neglo=~(a&b); endmodule""")
    net = synthesize(d)
    assert net.report()["cells"]["NAND"] == 1
    check_equivalence(d, net)


def test_threshold_twelve_exhaustive_thirteen_random_and_table_guard():
    for count, mode, vectors in [(12, "exhaustive", 3**12), (13, "random", 100_000)]:
        d = loads(f"module m(input trit [{count-1}:0] a,output trit y); assign y=~a[0]; endmodule")
        net = synthesize(d, seed=42)
        assert net.report()["equivalence"]["mode"] == mode
        assert net.report()["equivalence"]["vectors"] == vectors
        assert net.report()["equivalence"]["seed"] == (42 if count == 13 else None)
        if count == 13:
            with pytest.raises(ValueError, match="max_inputs"):
                d.truth_table()


def test_equivalence_rejects_wrong_cells_interfaces_and_invalid_netlists():
    d = design("nany(a,b)")
    net = synthesize(d)
    wrong = deepcopy(net)
    wrong.instances[0].cell = "NAND"
    with pytest.raises(ValueError, match="equivalence failed"):
        check_equivalence(d, wrong)
    wrong = deepcopy(net)
    wrong.ports[0].name = "other"
    with pytest.raises(ValueError, match="interfaces differ"):
        check_equivalence(d, wrong)


@pytest.mark.parametrize("instances,message", [
    ([Instance("g", "INV", {"A": "a", "Y": "a"})], "multiple drivers"),
    ([Instance("g", "INV", {"A": "missing", "Y": "y"})], "undriven"),
    ([Instance("g", "INV", {"A": "y", "Y": "y"})], "cycle"),
    ([Instance("g", "INV", {"A": "a", "Y": "n"}), Instance("g", "INV", {"A": "n", "Y": "y"})], "duplicate instance"),
    ([Instance("g", "INV", {"B": "a", "Y": "y"})], "pin set"),
])
def test_malformed_gate_netlists(instances, message):
    net = GateNetlist("m", [Port("a", "input"), Port("y", "output")], instances)
    with pytest.raises(ValueError, match=message):
        ordered_instances(net)


def test_random_large_adder_integer_reference():
    d = load("examples/adder.tv", top="adder", params={"N": 6})
    net = synthesize(d)
    rng = np.random.default_rng(13)
    inputs = {name: rng.integers(-1, 2, size=100_000, dtype=np.int8) for name in d.inputs}
    output = evaluate_netlist(net, inputs)
    expected = sum((inputs[f"a[{i}]"].astype(np.int64) + inputs[f"b[{i}]"]) * 3**i for i in range(6)) + inputs["cin"]
    actual = sum(output[f"sum[{i}]"].astype(np.int64) * 3**i for i in range(6)) + output["cout"].astype(np.int64) * 3**6
    np.testing.assert_array_equal(actual, expected)
    assert net.report()["equivalence"]["mode"] == "random"
