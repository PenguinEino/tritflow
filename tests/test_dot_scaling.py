"""Arithmetic, carry witnesses, matched timing and recorded-evidence integrity."""

from copy import deepcopy
import gzip
from itertools import product
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "notebook"))

from examples.dot_scaling import (CONDITIONS, RESULT, _power_rows, compare_timing,
                                  dot_oracle, dot_source, fixed_weight_timing,
                                  output_width, size_conditions, supply_energy, vector_plan, verify_record)
from tritflow import flow
from tritflow.sta import analyze
from tritflow.synth import evaluate_netlist


@pytest.mark.parametrize("n,width,count,mode", [(2, 2, 15, "exhaustive"), (4, 2, 46, "exhaustive"),
                                                (8, 3, 122, "random"), (16, 4, 315, "random"),
                                                (32, 4, 675, "random")])
def test_synthesized_dot_uses_full_range_and_seed_zero(n, width, count, mode):
    net = flow.loads(dot_source(n)).synthesize(seed=0)
    inputs = [p.name for p in net.ports if p.dir == "input"]
    outputs = [p.name for p in net.ports if p.dir == "output"]
    assert output_width(n) == width == len(outputs)
    assert len(net.instances) == count
    assert net.equivalence["passed"] and net.equivalence["mode"] == mode
    assert net.equivalence["vectors"] == (3**(2*n) if mode == "exhaustive" else 100_000)
    assert net.equivalence["seed"] == (None if mode == "exhaustive" else 0)
    plan = vector_plan(n, inputs, outputs)
    oracle = dot_oracle(n, inputs, outputs)
    for vector in plan["vectors"]:
        assert evaluate_netlist(net, dict(zip(inputs, vector))) == oracle(vector)


def test_integer_oracle_independent_of_hdl_for_all_dot2_states():
    inputs = ["x1", "w0", "x0", "w1"]
    oracle = dot_oracle(2, inputs, ["y[1]", "y[0]"])
    for vector in product((-1, 0, 1), repeat=4):
        values = dict(zip(inputs, vector))
        digits = oracle(vector)
        assert digits["y[0]"] + 3*digits["y[1]"] == values["w0"]*values["x0"] + values["w1"]*values["x1"]


@pytest.mark.parametrize("n", [2, 4, 8, 16, 32])
def test_both_longest_output_carry_polarities_and_fixed_weights(n):
    inputs = [*(f"x{i}" for i in reversed(range(n))), *(f"w{i}" for i in reversed(range(n)))]
    width = output_width(n)
    outputs = [f"y[{i}]" for i in range(width)]
    plan = vector_plan(n, inputs, outputs)
    assert len(plan["vectors"]) == 11
    states = [dict(zip(inputs, v)) for v in plan["vectors"]]
    for state in states:
        assert [state[f"w{i}"] for i in range(n)] == plan["weights"]
    for first, last, sign in ((1, 2, 1), (5, 6, -1)):
        before, after = plan["expected"][first], plan["expected"][last]
        assert before[f"y[{width-1}]"] == 0
        assert after[f"y[{width-1}]"] == sign
        for i in range(width-1):
            assert before[f"y[{i}]"] == sign
            assert after[f"y[{i}]"] == -sign
        assert {p for p in inputs if states[first][p] != states[last][p]} == {"x0"}
        assert plan["expected"][last+1] == before


@pytest.mark.parametrize("n", [True, 0, 1, -2, 2.5])
def test_invalid_term_counts(n):
    with pytest.raises(ValueError):
        dot_source(n)


def test_large_circuits_get_documented_observation_time_and_routing_capacity():
    assert size_conditions(4)["hold_s"] == 1e-6
    assert size_conditions(16)["hold_s"] == pytest.approx(1.25e-6)
    assert size_conditions(32)["hold_s"] == 4e-6
    assert size_conditions(16)["pnr_options"]["channel_tracks"] == 24
    assert size_conditions(32)["pnr_options"]["current_density_a_per_um"] < size_conditions(16)["pnr_options"]["current_density_a_per_um"]
    assert "pnr_options" not in CONDITIONS


@pytest.mark.parametrize("n", [2, 4])
def test_fixed_weight_sta_has_identical_original_loads_paths_and_arrivals(n):
    net = flow.loads(dot_source(n)).synthesize()
    inputs = [p.name for p in net.ports if p.dir == "input"]
    outputs = [p.name for p in net.ports if p.dir == "output"]
    plan = vector_plan(n, inputs, outputs)
    states = [dict(zip(inputs, v)) for v in plan["vectors"]]
    caps = {name: 30e-15 for name in net.nets()}
    original = analyze(net, vector_pairs=list(zip(states, states[1:])), wire_caps=caps,
                       output_load_f=CONDITIONS["load_f"], input_transition_s=CONDITIONS["edge_s"])
    constrained = fixed_weight_timing(net, plan, caps, CONDITIONS)
    assert constrained.arrival == pytest.approx(original.arrival)
    assert constrained.loads == original.loads
    assert constrained.paths == original.paths
    assert constrained.patterns == original.patterns
    assert len(net.ports) == 2*n + len(outputs)
    assert all(not inst.name.startswith("_sta_weight_") for inst in net.instances)


def test_unsettled_or_unsimulated_output_does_not_become_a_timing_point():
    prediction = {"y": 2e-9}
    assert compare_timing(prediction, {"measurements": None})[0]["spice_s"] is None
    rows = [{"outputs": {"y": {"passed": True, "settling_s": 0.}}},
            {"outputs": {"y": {"passed": False, "settling_s": None}}}]
    result = compare_timing(prediction, {"measurements": {"rows": rows}})[0]
    assert result["spice_s"] is None and result["signed_error_percent"] is None
    assert result["passed"] is False
    rows[1]["outputs"]["y"] = {"passed": True, "settling_s": 1e-9}
    assert compare_timing(prediction, {"measurements": {"rows": rows}})[0]["signed_error_percent"] == pytest.approx(100.)


def test_static_power_includes_negative_rail_with_source_current_convention():
    row = {"input_trits": [0], "passed": True, "rail_current_a": {"VDD": -.01, "VMID": .002, "VSS": .008}}
    measured = _power_rows([row], ["zero"], 20, {"VDD": 5., "VMID": 0., "VSS": -5.})[0]
    assert measured["static_power_w"] == pytest.approx(.09)
    assert measured["power_per_cell_w"] == pytest.approx(.0045)
    assert measured["rail_current_per_cell_a"]["VSS"] == pytest.approx(.0004)


def test_supply_power_integrates_nonuniform_samples_and_complete_holds():
    import numpy as np

    t = np.array([0., .1, .45, 1., 1.1, 1.8, 2.])
    p = .02 + .04*t
    waves = {"time": t, "i(vdd)": -p/10, "i(vss)": p/10, "i(vmid)": np.zeros_like(t)}
    energy = supply_energy(waves, CONDITIONS | {"hold_s": 1.}, ["a", "b"])
    assert energy["supply_energy_j"] == pytest.approx(.12)
    assert energy["average_supply_power_w"] == pytest.approx(.06)
    assert [r["average_supply_power_w"] for r in energy["segments"]] == pytest.approx([.04, .08])
    assert not energy["switching_energy_separated"]


def test_recorded_campaign_has_real_deck_evidence_and_consistent_measurements():
    data = json.loads(RESULT.read_text())
    verify_record(data)
    assert data["complete"] and not data.get("stale")
    assert data["requested_sizes"] == [2, 4, 8, 16, 32]
    assert {row["n"] for row in data["rows"]} >= {2, 4, 8, 16}
    assert data["review_state"] == "complete"
    assert data["provenance"]["simulator"]["version"] == "42"
    assert data["provenance"]["pdk"]["qualified_commit"] == "5d963db9d44e192d37a0489c208bfccf2e2f690c"
    for row in data["rows"]:
        assert row["state"] == "complete", row.get("error")
        assert row["synthesis"]["equivalence"]["passed"]
        assert row["pnr"]["drc"]["violations"] == 0 and row["lvs"]["matched"]
        assert row["conditions"]["seed"] == 0
        assert row["producer"]["hostname"] == data["provenance"]["runtime"]["hostname"]
        assert row["producer"]["simulator"] == data["provenance"]["simulator"]
        assert not row["pnr"]["stats"]["library_mock"]
        assert row["power"]["passed"] and row["power"]["zero_is_measured_maximum"]
        assert sum(row["wire_capacitance"]["logical_nets_f"].values()) > 0
        if row["spice"]["state"] == "simulated":
            assert row["spice"]["passed"]
            assert row["spice"]["measurements"]["unsettled"] == 0
            for segment in row["spice"]["measurements"]["rows"]:
                for output in segment["outputs"].values():
                    assert abs(output["voltage_v"] - output["ideal_voltage_v"]) <= .5
                    assert 0 <= output["settling_s"] <= row["conditions"]["hold_s"]
            for comparison in row["timing_comparison"]:
                assert comparison["passed"] and comparison["spice_s"] is not None
                assert comparison["signed_error_percent"] == pytest.approx(
                    100 * (comparison["sta_s"] / comparison["spice_s"] - 1))
        else:
            assert row["n"] == 32
            assert row["spice"]["state"] == "not_simulated" and row["spice"]["reason"]
        folder = ROOT / f"results/dot_scaling/dot{row['n']}"
        spice = gzip.decompress((folder / "postlayout.spice.gz").read_bytes()).decode()
        assert "Ctfwire" in spice
        sta = json.loads(gzip.decompress((folder / "sta.json.gz").read_bytes()))
        for name, capacitance in row["wire_capacitance"]["logical_nets_f"].items():
            assert sta["loads"][name]["wire_f"] == capacitance
            assert row["sta_device_only"]["loads"][name]["wire_f"] == 0.
        assert row["layout_penalty"]
        cells = row["synthesis"]["total_cells"]
        for state in row["power"]["rows"]:
            rails = row["conditions"]["supplies_v"]
            power = -sum(rails[rail]*current for rail, current in state["rail_current_a"].items())
            assert state["static_power_w"] == pytest.approx(power)
            assert state["power_per_cell_w"] == pytest.approx(power / cells)
        sequence = row["power"]["sequence"]
        assert sequence["duration_s"] == pytest.approx(len(row["vector_plan"]["vectors"]) * row["conditions"]["hold_s"])
        assert sequence["average_supply_power_w"] * sequence["duration_s"] == pytest.approx(sequence["supply_energy_j"])
        assert sum(s["supply_energy_j"] for s in sequence["segments"]) == pytest.approx(sequence["supply_energy_j"])
        assert not row["power"]["switching_energy_separated"]
        if row["n"] == 4:
            assert row["device_only_spice"]["passed"]
            pre = gzip.decompress((folder / "device_only.spice.gz").read_bytes()).decode()
            assert pre == "\n".join(line for line in spice.splitlines() if not line.startswith("Ctfwire")) + "\n"
    for attempt in data.get("optional_attempts", []):
        assert attempt["n"] == 32 and not attempt["passed"]
        assert attempt.get("error") or attempt.get("spice", {}).get("reason")


def test_reader_rejects_changed_sources_and_escaped_evidence():
    data = json.loads(RESULT.read_text())
    changed = deepcopy(data)
    changed["provenance"]["sources_sha256"]["source/tritflow/netlist.py"] = "0"*64
    with pytest.raises(RuntimeError, match="stale"):
        verify_record(changed)
    changed = deepcopy(data)
    changed["evidence_sha256"] = {"../outside": "0"*64}
    with pytest.raises(ValueError, match="escapes"):
        verify_record(changed)
    changed = deepcopy(data)
    changed["evidence_sha256"] = {"results/dot_scaling/nonexistent": "0"*64}
    with pytest.raises(RuntimeError, match="missing or changed"):
        verify_record(changed)
