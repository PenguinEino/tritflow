"""Language contract: widths, elaboration scopes, diagnostics and simulation."""

import re

import numpy as np
import pytest

from tritflow.hdl import HDLError, elaborate, load, loads, parse


def test_ast_and_vector_literal_concat_select():
    source = """module m(input trit [3:0] a, output trit [5:0] y);
      assign y = {a[2:1], 4'tT01T};
    endmodule"""
    ast = parse(source, "test.tv")
    assert ast.modules["m"].filename == "test.tv"
    d = elaborate(ast)
    table = d.truth_table()
    assert len(table["a[0]"]) == 81
    np.testing.assert_array_equal(table["y[5]"], table["a[2]"])
    np.testing.assert_array_equal(table["y[4]"], table["a[1]"])
    for index, digit in enumerate([-1, 1, 0, -1]):
        assert (table[f"y[{index}]"] == digit).all()


def test_ascending_vector_indices_and_nonzero_lsb():
    d = loads("""module m(input trit [2:4] a,output trit [6:4] y);
      assign y = {a[2:3],a[4]}; endmodule""")
    t = d.truth_table()
    for y, a in [(6, 2), (5, 3), (4, 4)]:
        np.testing.assert_array_equal(t[f"y[{y}]"], t[f"a[{a}]"])


def test_parameters_localparams_named_instances_and_generate_scopes():
    d = loads("""
    module bitinv(input trit a,output trit y); assign y=~a; endmodule
    module bank #(parameter N=2)(input trit [N-1:0] a,output trit [N-1:0] y);
      localparam START=(N*3)/3-1, LAST=(-7%3)+1;
      genvar i;
      generate for(i=START;i>=LAST;i--) begin:digit
        localparam K=i;
        wire trit w;
        bitinv u(.y(w),.a(a[K]));
        assign y[i]=w;
      end endgenerate
    endmodule
    module top(input trit [2:0] x,output trit [2:0] z);
      bank #(.N(3)) u (.a(x),.y(z));
    endmodule
    """, top="top")
    table = d.truth_table()
    for i in range(3):
        np.testing.assert_array_equal(table[f"z[{i}]"], -table[f"x[{i}]"])
    assert {n.hier for n in d.nodes if n.op == "neg"} == {f"u.digit[{i}].u" for i in range(3)}


def test_body_parameter_override_and_dependent_defaults():
    d = loads("""module m #(parameter N=2, parameter M=N+1)
      (input trit [M-1:0] a, output trit [M-1:0] y);
      parameter EXTRA=2; localparam K=EXTRA*N;
      assign y=a;
      endmodule""", params={"N": 3, "EXTRA": 4})
    assert d.params == {"N": 3, "M": 4, "EXTRA": 4, "K": 12}
    assert len(d.inputs) == 4


def test_forward_references_and_generate_increment():
    d = loads("""module m(input trit a,output trit [1:0] y);
      assign y[0]=w;
      wire trit w;
      assign w=~a;
      generate for(genvar i=1;i<2;i++) begin:g assign y[i]=a; end endgenerate
      endmodule""")
    t = d.truth_table()
    np.testing.assert_array_equal(t["y[0]"], -t["a"])
    np.testing.assert_array_equal(t["y[1]"], t["a"])


def test_comments_and_include_original_error_location(tmp_path):
    child = tmp_path / "child.tv"
    child.write_text("// comment\nmodule bad(output trit y);\n assign y=missing;\nendmodule\n")
    top = tmp_path / "top.tv"
    top.write_text('/* `include "nonexistent.tv" */\n`include "child.tv"\nmodule m(output trit y); bad u(.y(y)); endmodule')
    with pytest.raises(HDLError, match=rf"{re.escape(str(child))}:3:11: undeclared"):
        load(top, top="m")


def test_recursive_include_diagnosed(tmp_path):
    path = tmp_path / "bad.tv"
    path.write_text('`include "bad.tv"')
    with pytest.raises(HDLError, match="recursive `include"):
        load(path)


@pytest.mark.parametrize("body, message", [
    ("assign y=a/a;", "division"),
    ("assign y=a%a;", "remainder"),
    ("always @(posedge a) y=a;", "syntax"),
    ("always @* if (a) y=a;", "latch"),
    ("assign y=1'tx;", "x/z"),
    ("assign y=1'tz;", "x/z"),
    ("assign y=2't1;", "exactly its width"),
    ("assign y=unknown;", "undeclared"),
    ("assign y=a; assign y=~a;", "multiple drivers"),
    ("assign a=1't0; assign y=a;", "multiple drivers"),
    ("wire trit w; assign y=w;", "undriven"),
    ("wire trit w; assign w=~y; assign y=w;", "combinational cycle"),
    ("wire trit w; assign w=~w; assign y=a;", "combinational cycle"),
    ("assign y=a[0];", "scalar"),
    ("inv g(y,a,a);", "requires"),
    ("foo u(.a(a),.y(y));", "unknown module"),
    ("assign y=foo(a,a);", "only the builtin"),
    ("", "undriven output"),
])
def test_located_errors(body, message):
    source = "module m(input trit a,output trit y);\n" + body + "\nendmodule"
    with pytest.raises(HDLError, match=message) as exc:
        loads(source, filename="bad.tv")
    assert re.match(r"bad\.tv:\d+:\d+: ", str(exc.value))


@pytest.mark.parametrize("source,message", [
    ("module m(input trit [1:0] a,output trit y); assign y=a[2]; endmodule", "outside"),
    ("module m(input trit [2:0] a,output trit [1:0] y); assign y=a[0:1]; endmodule", "direction"),
    ("module m(input trit a,output trit y); wire trit [0:1] v; inv g(y,v); endmodule", "scalar"),
    ("module m(output trit y); m u(.y(y)); endmodule", "recursive module"),
    ("module m(output trit y); localparam N=1/0; assign y=1't0; endmodule", "division by zero"),
    ("module m(output trit y); genvar i; for(i=0;i<2;i=i) begin:g assign y=1't0; end endmodule", "does not terminate"),
    ("module m(output trit y); genvar i; for(i=0;i<2;j++) begin:g assign y=1't0; end endmodule", "loop variable"),
    ("module m(input trit a,output trit y); inv g(y,a); inv g(a,y); endmodule", "duplicate instance"),
])
def test_other_elaboration_errors(source, message):
    with pytest.raises(HDLError, match=message):
        loads(source)


def test_override_and_named_port_errors():
    source = """module child #(parameter N=1)(input trit a,output trit y); assign y=a; endmodule
    module top(input trit a,output trit y); child %s u(%s); endmodule"""
    for override, ports, message in [
        ("#(.BAD(1))", ".a(a),.y(y)", "unknown parameter"),
        ("#(.N(1),.N(2))", ".a(a),.y(y)", "duplicate parameter"),
        ("", ".a(a),.a(a),.y(y)", "duplicate port"),
        ("", ".a(a)", "named ports must match"),
    ]:
        with pytest.raises(HDLError, match=message):
            loads(source % (override, ports), top="top")
    with pytest.raises(HDLError, match="specify top"):
        loads(source % ("", ".a(a),.y(y)"))
    with pytest.raises(HDLError, match="integers"):
        loads("module m #(parameter N=1)(output trit y); assign y=1't0; endmodule", params={"N": 1.5})


def test_numpy_broadcast_and_validation():
    d = loads("module m(input trit a,b,output trit y); assign y=nany(a,b); endmodule")
    output = d.evaluate({"a": np.array([[-1], [0], [1]]), "b": [-1, 0, 1]})["y"]
    np.testing.assert_array_equal(output, [[1, 1, 0], [1, 0, -1], [0, -1, -1]])
    assert d.evaluate({"a": 0, "b": 1})["y"] == -1
    for bad in [256, 1.2, np.nan, "0"]:
        with pytest.raises(ValueError, match="outside trits"):
            d.evaluate({"a": bad, "b": 0})
    with pytest.raises(ValueError, match="expected inputs"):
        d.evaluate({"a": 0})


def test_constant_only_design_and_empty_ports():
    d = loads("module m(output trit [2:0] y); assign y=3'tT01; endmodule")
    table = d.truth_table()
    assert {key: value.tolist() for key, value in table.items()} == {"y[2]": [-1], "y[1]": [0], "y[0]": [1]}
    assert loads("module m(); endmodule").truth_table() == {}


def test_generate_region_localparams_and_nested_loop_scopes():
    d = loads("""module m(input trit a,output trit [3:0] y);
      generate
        localparam N=2;
        for(genvar i=0;i<N;i++) begin:outer
          for(genvar j=0;j<N;j++) begin:inner
            wire trit w;
            assign w=~a;
            assign y[i*N+j]=w;
          end
        end
      endgenerate
      endmodule""")
    t = d.truth_table()
    for i in range(4):
        np.testing.assert_array_equal(t[f"y[{i}]"], -t["a"])


@pytest.mark.parametrize("name", ["VDD", "VMID", "VSS"])
def test_global_rails_cannot_be_signal_nets(name):
    with pytest.raises(HDLError, match="reserved for a global power rail"):
        loads(f"module m(input trit {name},output trit y); assign y={name}; endmodule")
