"""State budgets, HDL independence, constant folding and reader-facing errors."""

from contextlib import contextmanager
from itertools import product
from types import SimpleNamespace

import pytest

import reuse
from tritflow import flow


@contextmanager
def quiet_step(*args, **kwargs):
    yield SimpleNamespace(done=lambda *a, **kw: None)


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4])
def test_small_stimuli_cover_every_state_without_claiming_every_transition(n):
    plan = reuse.stimulus_plan([f"a{i}" for i in range(n)])
    assert plan["mode"] == "exhaustive states"
    assert plan["vectors"][0] == (0,) * n
    assert set(plan["vectors"]) == set(product((-1, 0, 1), repeat=n))
    assert plan["unique_states"] == plan["total_states"] == 3 ** n
    assert not plan["all_directed_transitions"]
    # A reflected Gray walk changes one input per edge.
    assert all(sum(a != b for a, b in zip(left, right, strict=True)) == 1
               for left, right in zip(plan["vectors"], plan["vectors"][1:]))


def test_large_input_sample_is_bounded_repeatable_and_identified_as_partial():
    names = [f"a{i}" for i in range(24)]
    plan = reuse.stimulus_plan(names, sample_size=27, seed=7)
    assert plan == reuse.stimulus_plan(names, sample_size=27, seed=7)
    assert plan["mode"] == "sampled states"
    assert plan["unique_states"] == len(set(plan["vectors"])) == 27
    assert plan["total_states"] == 3 ** 24
    assert plan["vectors"][:3] == [(0,) * 24, (-1,) * 24, (1,) * 24]
    assert plan["seed"] == 7
    assert "Not exhaustive" in plan["method"]


@pytest.mark.parametrize("options", [{"exhaustive_limit": 0}, {"sample_size": 2}])
def test_invalid_coverage_budgets_fail(options):
    with pytest.raises(ValueError):
        reuse.stimulus_plan(["a"], **options)


def test_constant_weights_remove_fifteen_cells_and_keep_full_arithmetic():
    circuit = flow.loads(reuse.DEFAULT_SOURCE)
    net = circuit.synthesize()
    table = circuit.truth_table()
    assert (table["y[0]"] + 3 * table["y[1]"] ==
            table["x0"] - table["x1"] + table["x2"] + table["x3"]).all()
    assert net.report()["total_cells"] == 31
    folding = reuse._folding(circuit, net)
    assert folding["programmable_cells"] == 46
    assert folding["cells_removed"] == 15
    assert folding["reduction_pct"] == pytest.approx(100 * 15 / 46)
    # Editing the expression must not retain an obsolete folding claim.
    changed = flow.loads(reuse.DEFAULT_SOURCE.replace("x0 - x1", "x0 + x1"))
    assert reuse._folding(changed, changed.synthesize()) is None


def test_spice_oracle_evaluates_hdl_independently_of_mapped_cells(monkeypatch):
    from tritflow import synth

    def wrong_reference(*args, **kwargs):
        raise AssertionError("the electrical oracle must not evaluate mapped cells")

    circuit = flow.loads(reuse.DEFAULT_SOURCE)
    monkeypatch.setattr(synth, "evaluate_netlist", wrong_reference)
    expected = reuse._oracle(circuit, list(circuit.design.inputs))
    assert expected((1, -1, 1, 1)) == {"y[1]": 1, "y[0]": 1}
    assert expected((-1, 1, -1, -1)) == {"y[1]": -1, "y[0]": -1}


@pytest.mark.parametrize("source", [
    "module bad(input trit a, output trit y); assign y = missing; endmodule",
    "module bad(input trit a, output trit y); assign y = a endmodule",
    "module bad(input trit a, output trit y); always @(*) if (a) y = a; endmodule",
])
def test_bad_hdl_uses_existing_error_box_without_tool_runs_or_traceback(source, monkeypatch, tmp_path):
    rendered = []
    monkeypatch.setattr(reuse, "step", quiet_step)
    monkeypatch.setattr(reuse, "display", lambda value: rendered.append(value.data))
    out = tmp_path / "bad"
    assert reuse.run(source, output_dir=out) is None
    assert not out.exists()
    assert len(rendered) == 1
    assert "このセルはまだ実行できません" in rendered[0]
    assert "reuse_source.tv:" in rendered[0]
    assert "Traceback" not in rendered[0]


def test_implicit_source_uses_existing_dependency_guard(monkeypatch):
    from live import NotReady

    def missing(*names, why):
        assert names == ("reuse_source",)
        raise NotReady("6章のHDLセル", why)

    monkeypatch.setattr(reuse, "need", missing)
    with pytest.raises(NotReady, match="6章のHDLセル"):
        reuse.run()


def test_a_failed_edit_invalidates_the_previous_success_summary(monkeypatch, tmp_path):
    monkeypatch.setattr(reuse, "step", quiet_step)
    monkeypatch.setattr(reuse, "display", lambda value: None)
    (tmp_path / "summary.json").write_text('{"passed": true}')
    assert reuse.run("module broken;", output_dir=tmp_path) is None
    assert not (tmp_path / "summary.json").exists()


def test_edited_source_runs_real_drc_lvs_extraction_and_ngspice(monkeypatch, tmp_path):
    """A source edit must really reach extracted devices and the HDL oracle."""
    monkeypatch.setattr(reuse, "step", quiet_step)
    result = reuse.run("""module edited_min(input trit a, b, output trit y);
  assign y = a & b;
endmodule""", output_dir=tmp_path / "min", show=False)
    assert result.summary["passed"]
    assert result.drc["violations"] == 0
    assert result.lvs["matched"] and result.lvs["strict_ports"]
    assert result.summary["simulator"]["version"] == "42"
    assert len(result.post["measurements"]["rows"]) == 9
    for row in result.post["measurements"]["rows"]:
        assert row["outputs"]["y"]["ideal_trit"] == min(row["input_trits"])
    assert "Ctfwire" in result.extracted.spice
    assert (tmp_path / "min/spice/tb.spice").is_file()
    assert (tmp_path / "min/summary.json").is_file()


@pytest.mark.parametrize("source,states", [
    ("module constant(output trit y); assign y = 1't0; endmodule", 1),
    ("module passthrough(input trit a, unused, output trit y); assign y = a; endmodule", 9),
])
def test_constant_and_unloaded_input_circuits_run_without_special_stimuli(source, states, monkeypatch, tmp_path):
    monkeypatch.setattr(reuse, "step", quiet_step)
    result = reuse.run(source, output_dir=tmp_path, show=False)
    assert result.summary["passed"]
    assert result.summary["stimulus"]["unique_states"] == states
    assert len(result.post["measurements"]["rows"]) == states


def test_v3_bounded_fixed_weight_call_passes_with_its_actual_conditions(monkeypatch, tmp_path):
    monkeypatch.setattr(reuse, "step", quiet_step)
    result = reuse.run(reuse.DEFAULT_SOURCE, output_dir=tmp_path, show=False,
                       exhaustive_limit=27, sample_size=11, step_s=5e-9)
    assert result.summary["passed"]
    assert result.summary["stimulus"]["unique_states"] == 11
    assert result.summary["stimulus"]["total_states"] == 81
    assert result.summary["stimulus"]["mode"] == "sampled states"
    assert result.summary["conditions"]["step_s"] == 5e-9
    assert result.summary["constant_folding"]["cells_removed"] == 15
