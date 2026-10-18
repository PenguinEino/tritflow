"""Net-name preservation, load accounting, physical geometry and SIM agreement."""

from copy import deepcopy
import json
from pathlib import Path

import klayout.db as db
import pytest

from tritflow.extract import DEFAULT_CAP_COEFFICIENTS, gds_wire_capacitance
from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.pnr import Library, PnrResult, mock_library, place_and_route, strict_lvs
from tritflow.pnr.gds import DBU
from tritflow.pnr.parasitics import estimate_net_parasitics
from .circuits import chain


def test_receiving_pin_bias_envelopes_fanout_and_unused_nets():
    library = mock_library()
    for name, caps in (
        ("NANY", [("A", 2e-15), ("A", 3e-15), ("B", 7e-15)]),
        ("INV", [("A", 5e-15)]),
    ):
        library.cells[name].characterization = {
            "input_capacitance": {
                "rows": [{"pin": pin, "capacitance_f": cap} for pin, cap in caps],
                "max_f": 99e-15,
            }
        }
    net = GateNetlist(
        "loads",
        [Port("a", "input"), Port("unused", "input"), Port("y", "output")],
        [
            Instance("g0", "NANY", {"A": "a", "B": "a", "Y": "n[0]"}, "digit[0]"),
            Instance("g1", "INV", {"A": "n[0]", "Y": "y"}),
            Instance("g2", "INV", {"A": "n[0]", "Y": "singleton"}),
        ],
    )
    data = {
        "wires": [
            {"net": "a", "layer": "M1", "width": 2.0, "points": [[0, 0], [10, 0]]}
        ],
        "vias": [],
        "pins": [{"name": "unused", "layer": "M2", "rect": [0, 3, 4, 7]}],
    }
    report = estimate_net_parasitics(data, net, library)
    a = report["nets"]["a"]
    assert set(report["nets"]) == net.nets()
    assert a["fanout"] == 2 and a["pin_count"] == 3
    assert a["cell_input_capacitance_f"] == pytest.approx(10e-15)
    assert a["wirelength_um"] == {"M1": 10.0, "M2": 0.0}
    # The exporter draws square ends: 12 by 2, perimeter 28 (not flush 10 by 2).
    coeff = DEFAULT_CAP_COEFFICIENTS["M1"]
    expected = 24 * coeff["area_f_per_um2"] + 28 * coeff["fringe_f_per_um"]
    assert a["wire_capacitance_f"] == pytest.approx(expected, rel=1e-12, abs=1e-30)
    assert a["total_load_f"] == pytest.approx(expected + 10e-15)
    assert report["nets"]["n[0]"]["fanout"] == 2
    assert report["nets"]["n[0]"]["cell_input_capacitance_f"] == pytest.approx(10e-15)
    assert report["nets"]["singleton"]["wire_capacitance_f"] == 0
    assert report["nets"]["unused"]["wire_capacitance_f"] > 0
    assert report["nets"]["unused"]["fanout"] == 0
    assert report["nets"]["a"]["pins"][0]["hier"] == "digit[0]"
    duplicated = deepcopy(data)
    duplicated["wires"] *= 2
    other = estimate_net_parasitics(duplicated, net, library)
    assert other["nets"]["a"]["wire_capacitance_f"] == a["wire_capacitance_f"]
    assert other["nets"]["a"]["wirelength_um"]["M1"] == 20


def test_automatic_sidecar_matches_exported_routing_and_is_portable(tmp_path):
    library = mock_library()
    result = place_and_route(
        chain(3), library, output_dir=tmp_path, run_pdk_drc=False, anneal_steps=0
    )
    path = tmp_path / "chain3.net_parasitics.json"
    report = json.loads(path.read_text())
    assert report == result.data["net_parasitics"] == result.net_parasitics()
    assert report["totals"]["wirelength_um"] == result.stats["wirelength_um"]
    assert report["totals"]["via_count"] == result.stats["via_count"]
    assert report["nets"]["a"]["cell_input_capacitance_f"] is None
    assert report["nets"]["a"]["total_load_f"] is None
    assert report["nets"]["a"]["missing_pin_capacitance"] == ["g0.A"]
    assert not report["totals"]["complete_pin_characterization"]
    assert (
        report["nets"]["z"]["total_load_f"] == report["nets"]["z"]["wire_capacitance_f"]
    )
    assert not report["nets"]["z"]["external_load_included"]
    # Sum signal regions and compare to the actual routing child, subtracting
    # independently reconstructed power. Supply metal must not leak into C.
    from tritflow.pnr.gds import box, wire_box

    layout = db.Layout()
    layout.read(str(result.gds_path))
    routing = layout.cell("chain3__routing")
    power = result.data["power"]
    for layer, pair in (("M1", (13, 0)), ("M2", (20, 0))):
        actual = db.Region(routing.begin_shapes_rec(layout.layer(*pair)))
        supplies = db.Region()
        for wire in power["rails"] + power["straps"]:
            if wire["layer"] == layer:
                supplies.insert(box(wire_box(wire)))
        half = (
            library.template["rules"]["V1"]
            + 2 * library.template["rules"][f"V1_enc_{layer}"]
        ) / 2
        for via in power["vias"]:
            x, y = via["x"], via["y"]
            supplies.insert(box([x - half, y - half, x + half, y + half]))
        if layer == "M2":
            for pin in power["pins"]:
                supplies.insert(box(pin["rect"]))
        signal = (actual - supplies).merged()
        assert sum(
            n["layers"].get(layer, {}).get("area_um2", 0)
            for n in report["nets"].values()
        ) == pytest.approx(signal.area() * DBU**2)
        assert sum(
            n["layers"].get(layer, {}).get("perimeter_um", 0)
            for n in report["nets"].values()
        ) == pytest.approx(signal.perimeter() * DBU)
    # Reconstructed notebook objects use their frozen snapshot, no live library.
    restored = PnrResult(
        result.gds_path,
        result.json_path,
        result.stats,
        json.loads(result.json_path.read_text()),
    )
    restored.data["library"]["source"] = "/missing/library"
    assert restored.net_parasitics() == report


def test_shared_sim_coefficients_are_consumed_without_copying_numbers(monkeypatch):
    monkeypatch.setitem(
        DEFAULT_CAP_COEFFICIENTS,
        "M1",
        {"area_f_per_um2": 1e-15, "fringe_f_per_um": 2e-15},
    )
    data = {
        "wires": [{"net": "a", "layer": "M1", "width": 2, "points": [[0, 0], [10, 0]]}],
        "vias": [],
        "pins": [],
    }
    result = estimate_net_parasitics(data, chain(1), mock_library())
    assert result["coefficients"] is not DEFAULT_CAP_COEFFICIENTS
    assert result["coefficients"]["M1"] is not DEFAULT_CAP_COEFFICIENTS["M1"]
    assert result["nets"]["a"]["wire_capacitance_f"] == pytest.approx(
        80e-15, rel=1e-12, abs=1e-30
    )


def test_strict_lvs_maps_internal_and_case_distinct_nets_to_sim(tmp_path):
    library = Library.load()
    net = GateNetlist(
        "cap_mapping",
        [Port("a[0]", "input"), Port("A[0]", "input"), Port("y", "output")],
        [
            Instance("g0", "NANY", {"A": "a[0]", "B": "A[0]", "Y": "internal[0]"}),
            Instance("g1", "INV", {"A": "internal[0]", "Y": "y"}),
        ],
    )
    result = place_and_route(net, library, output_dir=tmp_path, anneal_steps=0)
    lvs = strict_lvs(
        result.gds_path,
        result.data,
        net,
        library,
        tmp_path / "lvs",
        (Path(library.source) / "out/all.spice").read_text(),
    )
    assert lvs["matched"]
    saved = gds_wire_capacitance(result.gds_path, lvs["report"], top=net.top)
    cap_path = tmp_path / "capacitance.json"
    cap_path.write_text(json.dumps(saved))
    result.net_parasitics(
        lvs_report=lvs["report"]
    )  # Optional comparison without a SIM run.
    report = result.net_parasitics(lvs_report=lvs["report"], capacitance_path=cap_path)
    comparison = report["extracted_comparison"]
    assert comparison["all_mapped_signals_agree"]
    assert comparison["all_extracted_nodes_agree"]
    assert comparison["mapped_signal_net_count"] == len(net.nets())
    mapped = comparison["nets"]
    assert mapped["a[0]"]["extracted_net"] != mapped["A[0]"]["extracted_net"]
    assert mapped["internal[0]"]["extracted_net"] != "internal[0]"
    rows = library.cells["NANY"].characterization["input_capacitance"]["rows"]
    for logical, pin in (("a[0]", "A"), ("A[0]", "B")):
        assert report["nets"][logical]["cell_input_capacitance_f"] == max(
            r["capacitance_f"] for r in rows if r["pin"] == pin
        )
    assert report["totals"]["complete_pin_characterization"]
    assert (
        comparison["connected_signal_capacitance_f"]
        > report["totals"]["wire_capacitance_f"]
    )
    node = mapped["internal[0]"]["extracted_net"]
    saved["nets"][node]["capacitance_f"] *= 1.1
    cap_path.write_text(json.dumps(saved))
    mismatch = result.net_parasitics(
        lvs_report=lvs["report"], capacitance_path=cap_path
    )["extracted_comparison"]
    assert not mismatch["all_extracted_nodes_agree"]
    assert not mismatch["nets"]["internal[0]"]["agrees"]
    # A retained SIM snapshot from another physical revision must be rejected.
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / f"{net.top}.gds").write_bytes(b"stale")
    with pytest.raises(ValueError, match="different GDS"):
        result.net_parasitics(lvs_report=lvs["report"], capacitance_path=cap_path)
    with pytest.raises(ValueError, match="requires its matching lvs_report"):
        result.net_parasitics(capacitance_path=cap_path)
