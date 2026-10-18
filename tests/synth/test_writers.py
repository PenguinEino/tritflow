"""Round-trip public outputs, verify SPICE port order and exercise the CLI."""

import json
import subprocess
import sys

import pytest

from tritflow.hdl import load, loads
from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.synth import check_equivalence, spice, synthesize, tritverilog, write_artifacts


@pytest.mark.parametrize("example", ["half_add", "full_add", "adder", "mul1", "mac1", "minmax", "sign"])
def test_example_gate_source_and_json_roundtrip(example, tmp_path):
    design = load(f"examples/{example}.tv", top=example)
    net = synthesize(design)
    paths = write_artifacts(net, tmp_path)
    assert {p.name for p in paths.values()} == {f"{example}.{suffix}" for suffix in ["json", "gate.tv", "spice", "report.json", "report.txt"]}
    restored = GateNetlist.load(paths["json"])
    check_equivalence(design, restored)
    assert set(json.loads(paths["json"].read_text())) == {"top", "ports", "instances"}
    gate_design = load(paths["gate.tv"], top=example)
    check_equivalence(gate_design, net)
    report = json.loads(paths["report.json"].read_text())
    assert report["total_cells"] == len(net.instances)
    assert sum(sum(c.values()) for c in report["hierarchy"].values()) == len(net.instances)
    assert "Equivalence: PASS" in paths["report.txt"].read_text()


def test_const_tie_roundtrip_and_spice_signal_before_rails():
    d = loads("""module m(output trit [2:0] y); assign y=3'tT01; endmodule""")
    net = synthesize(d)
    gate_design = loads(tritverilog(net))
    check_equivalence(gate_design, net)
    text = spice(net)
    for line in text.splitlines():
        if line.startswith("X"):
            words = line.split()
            assert words[-4:-1] == ["VDD", "VMID", "VSS"]
            assert words[-1] in {"TIEN", "TIEZ", "TIEP"}
            assert len(words) == 6


def test_spice_cell_pin_order_and_case_sensitive_hdl_names():
    net = GateNetlist("m", [Port("a", "input"), Port("b", "input"), Port("y", "output")],
                      [Instance("g", "NAND", {"Y": "y", "B": "b", "A": "a"})])
    assert "Xg a b y VDD VMID VSS NAND" in spice(net)
    d = loads("""module m(input trit A,a,Vss,output trit y);
      assign y=nany(nany(A,a),Vss); endmodule""")
    n = synthesize(d)
    subckt = next(line for line in spice(n).splitlines() if line.startswith(".subckt"))
    names = subckt.split()[2:]
    assert len(names) == len(set(s.lower() for s in names))
    assert "* net tf_567373 = Vss" in spice(n)


def test_sim_uses_writer_and_inverse_map_for_case_and_encoded_name_collisions():
    from tritflow import CELLS_DIR
    from tritflow.sim.spice import gate_spice, logical_spice_names, subcircuits
    from tritflow.synth.writers import spice_names

    design = loads("""module names(input trit a,A,tf_61,Vdd,output trit y,Y);
        assign y=nany(a,A); assign Y=nany(tf_61,Vdd); endmodule""")
    net = synthesize(design)
    cells = (CELLS_DIR/"out/all.spice").read_text()
    text = gate_spice(net, cells)
    assert text == spice(net)+"\n"+cells
    names = spice_names(net.nets(), ("VDD","VMID","VSS","0"))
    inverse = logical_spice_names(text)
    assert all(inverse.get(safe, safe) == original for original, safe in names.items())
    formals = subcircuits(text)["names"]["pins"]
    assert len(formals) == len({p.lower() for p in formals})
    assert formals[:-3] == [names[p.name] for p in net.ports]


def test_arbitrary_gate_json_order_is_handled():
    d = loads("module m(input trit a,output trit y); wire trit w; inv g(w,a); inv h(y,w); endmodule")
    net = synthesize(d)
    net.instances.reverse()
    check_equivalence(d, net)
    assert tritverilog(net).index("inv g") < tritverilog(net).index("inv h")


def test_cli_required_artifacts_and_report(tmp_path):
    result = subprocess.run([sys.executable, "-m", "tritflow.synth", "examples/adder.tv", "--top", "adder",
                             "-P", "N=4", "-o", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "NANY=44" in result.stdout
    assert "19683 vectors" in result.stdout
    assert (tmp_path / "adder4.json").exists()
    assert GateNetlist.load(tmp_path / "adder4.json").top == "adder4"
    assert load(tmp_path / "adder4.gate.tv", top="adder4").top == "adder4"


@pytest.mark.parametrize("args", [["-P", "BAD=4"], ["-P", "N=oops"], ["-P", "N=2", "-P", "N=3"], ["--fanout-limit", "1"]])
def test_cli_reports_errors_without_tracebacks(args, tmp_path):
    result = subprocess.run([sys.executable, "-m", "tritflow.synth", "examples/adder.tv", "--top", "adder",
                             "-o", str(tmp_path), *args], capture_output=True, text=True)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert not list(tmp_path.iterdir())
