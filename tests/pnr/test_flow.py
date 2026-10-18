"""Routing coverage, deterministic optimization, and independent fault detection."""
import json

import klayout.db as db
import pytest

from tritflow import CELLS_DIR
from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.pnr import Library, connectivity, mock_library, place_and_route, routing_drc
from tritflow.pnr.power import power_plan
from tritflow.pnr.placement import place

from .circuits import chain, fanout_tree, random_dag


@pytest.fixture
def library():
    # Explicit fixture stays provisional even after the real cells are published.
    return mock_library()


@pytest.mark.parametrize("circuit", [chain(30), fanout_tree(5), random_dag(50), random_dag(200)])
def test_synthetic_coverage(circuit, library, tmp_path):
    result = place_and_route(circuit, library, output_dir=tmp_path, seed=4, anneal_steps=150)
    assert result.stats["routed_nets"] == len(circuit.nets())
    assert all(check["clean"] for check in result.data["checks"].values())
    assert result.data["checks"]["pdk_drc"]["violations"] == 0
    assert 0 < result.stats["utilization"] < 1
    assert result.stats["library_mock"]
    assert result.stats["max_supply_drop_v"] > 0
    assert json.loads(result.json_path.read_text())["placements"] == result.data["placements"]
    layout = db.Layout()
    layout.read(str(result.gds_path))
    top = layout.cell(circuit.top)
    assert top.child_instances() > len(circuit.instances)
    assert layout.cell(f"{circuit.top}__routing") is not None
    # All conductors and cells must fit the declared die boundary.
    assert top.bbox().left >= 0 and top.bbox().bottom >= 0
    assert top.bbox().right <= round(result.data["die"][0]/layout.dbu)
    assert top.bbox().top <= round(result.data["die"][1]/layout.dbu)
    channel_ys = {y for c in result.data["channels"] for y in c["tracks"]}
    assert all(w["points"][0][1] in channel_ys for w in result.data["wires"] if w["layer"] == "M1")


def test_deterministic_seed(library, tmp_path):
    circuit = random_dag(20)
    a = place_and_route(circuit, library, output_dir=tmp_path/"a", seed=71, anneal_steps=100, run_pdk_drc=False)
    b = place_and_route(circuit, library, output_dir=tmp_path/"b", seed=71, anneal_steps=100, run_pdk_drc=False)
    # Wall-clock measurements vary; all physical/optimization records must agree.
    a.data["stats"].pop("runtime_s")
    b.data["stats"].pop("runtime_s")
    assert a.data == b.data
    assert a.gds_path.read_bytes() == b.gds_path.read_bytes()
    assert a.data["history"][-1]["hpwl"] <= a.data["history"][0]["hpwl"]


def test_connectivity_detects_actual_open_and_short(library, tmp_path):
    circuit = chain(1)
    result = place_and_route(circuit, library, output_dir=tmp_path, anneal_steps=0, run_pdk_drc=False)
    data = result.data
    # Remove every signal wire from the physical GDS while preserving the route
    # record: checks must inspect actual drawn shapes, not trust that record.
    layout = db.Layout()
    layout.read(str(result.gds_path))
    route_cell = layout.cell(f"{circuit.top}__routing")
    route_cell.shapes(layout.layer(20, 0)).clear()
    damaged = tmp_path/"open.gds"
    layout.write(str(damaged))
    assert not connectivity(damaged, data, circuit, library)["clean"]
    # An extra horizontal bridge on M2 shorts the two actual terminal landings.
    layout = db.Layout()
    layout.read(str(result.gds_path))
    pl = data["placements"][0]
    x0 = pl["x"]+9
    x1 = pl["x"]+27
    y0, y1 = pl["y"]+60, pl["y"]+75
    route_cell = layout.cell(f"{circuit.top}__routing")
    route_cell.shapes(layout.layer(20, 0)).insert(db.DBox(x0-1.7, y0-1.7, x1+1.7, y1+1.7))
    damaged = tmp_path/"short.gds"
    layout.write(str(damaged))
    report = connectivity(damaged, data, circuit, library)
    assert any(e.startswith("Short:") for e in report["errors"])


def test_drc_detects_missing_enclosure(library, tmp_path):
    circuit = chain(1)
    result = place_and_route(circuit, library, output_dir=tmp_path, anneal_steps=0, run_pdk_drc=False)
    layout = db.Layout()
    layout.read(str(result.gds_path))
    routing = layout.cell(f"{circuit.top}__routing")
    x = result.data["die"][0]/2
    routing.shapes(layout.layer(19, 0)).insert(db.DBox(x, .5, x+1.4, 1.9))
    broken = tmp_path/"unenclosed.gds"
    layout.write(str(broken))
    report = routing_drc(broken, result.data, library)
    assert "V1_enclosure_M1" in report["errors"]
    assert "V1_enclosure_M2" in report["errors"]


def test_invalid_netlists_fail_before_routing(library, tmp_path):
    bad = chain(2)
    bad.instances[1].pins["Y"] = "a"
    with pytest.raises(ValueError, match="Multiple drivers"):
        place_and_route(bad, library, output_dir=tmp_path)
    bad = GateNetlist("cycle", [], [Instance("g", "INV", {"A": "loop", "Y": "loop"})])
    with pytest.raises(ValueError, match="cycle"):
        place_and_route(bad, library, output_dir=tmp_path)


def test_current_sizing_and_split_trunks(library):
    placements, _, _ = place(chain(20), library, rows=20, steps=0)
    plan = power_plan(placements, library, default_cell_current_a=.002)
    assert plan["trunk_width"] >= 20
    # Many lightly loaded rows require parallel unslotted conductors globally.
    placements, _, _ = place(chain(100), library, rows=100, steps=0)
    plan = power_plan(placements, library, default_cell_current_a=.002)
    assert plan["trunks_per_supply_per_side"] > 1
    assert plan["trunk_width"] < 45
    with pytest.raises(ValueError, match="wider cell rail"):
        power_plan(placements, library, default_cell_current_a=.1)


def test_auto_selects_real_when_published(tmp_path):
    (tmp_path/"out").mkdir()
    (tmp_path/"template.provisional.json").write_text((CELLS_DIR/"template.provisional.json").read_text())
    assert Library.automatic(tmp_path).mock
    source = mock_library()
    (tmp_path/"template.json").write_text(json.dumps(source.template))
    (tmp_path/"out/library.json").write_text('["INV"]')
    cell = source.cells["INV"]
    base = tmp_path/"out/INV"
    base.mkdir()
    (base/"INV.abstract.json").write_text(json.dumps({"name": "INV", "width": cell.width,
        "height": cell.height, "pins": cell.pins, "obstructions": cell.obstructions}))
    assert not Library.automatic(tmp_path).mock


def test_real_cell_pdk_drc(tmp_path):
    if not (CELLS_DIR/"template.json").exists() or not (CELLS_DIR/"out/library.json").exists():
        pytest.skip("Real library not published yet")
    result = place_and_route(chain(3), Library.load(), output_dir=tmp_path, seed=6, anneal_steps=60)
    assert not result.stats["library_mock"]
    assert all(check["clean"] for check in result.data["checks"].values())


@pytest.mark.parametrize("real", [False, True])
def test_three_constants_are_legal_power_connections(real, tmp_path):
    if real and not (CELLS_DIR/"out/library.json").exists():
        pytest.skip("Real library not published yet")
    library = Library.load() if real else mock_library()
    circuit = GateNetlist("constants", [Port("p", "output"), Port("z", "output"), Port("n", "output")],
        [Instance("p", "TIEP", {"Y": "p"}), Instance("z", "TIEZ", {"Y": "z"}), Instance("n", "TIEN", {"Y": "n"})])
    result = place_and_route(circuit, library, output_dir=tmp_path, seed=3, anneal_steps=20)
    assert all(check["clean"] for check in result.data["checks"].values())


def test_real_four_trit_adder(tmp_path):
    if not (CELLS_DIR/"out/library.json").exists():
        pytest.skip("Real library not published yet")
    from tritflow.hdl import load
    from tritflow.synth import synthesize
    from tritflow import ROOT
    circuit = synthesize(load(ROOT/"examples/adder.tv", top="adder", params={"N": 4}))
    circuit.top = "adder4"
    result = place_and_route(circuit, Library.load(), output_dir=tmp_path, seed=7, anneal_steps=300)
    assert result.stats["routed_nets"] == len(circuit.nets())
    assert result.stats["instance_count"] >= 40
    assert all(check["clean"] for check in result.data["checks"].values())
    assert result.stats["aspect_ratio"] <= 1.5
    # Current reserve takes precedence over the earlier 45% area objective.
    assert result.stats["utilization"] >= .40
    assert result.data["power"]["dc_current_check"]["reserved_margin_met"]
    assert result.stats["runtime_s"]["total"] < 30


def test_unused_input_and_no_cells(library, tmp_path):
    circuit = GateNetlist("unused", [Port("unused_in", "input")], [])
    result = place_and_route(circuit, library, output_dir=tmp_path, run_pdk_drc=False)
    assert result.stats["routed_nets"] == 1
    assert result.data["checks"]["connectivity"]["clean"]


def test_real_dc_reserve_is_checked_before_signal_routing(tmp_path, monkeypatch):
    """An under-sized power plan must not consume a maze-routing attempt."""
    if not (CELLS_DIR/"out/library.json").exists():
        pytest.skip("Real library not published")
    import importlib
    module=importlib.import_module('tritflow.pnr.flow')
    original=module.route
    routed=[]
    def qualified_route(data,*args,**kwargs):
        check=data['power']['dc_current_check']
        assert check['defined'] and check['reserved_margin_met']
        routed.append(check['max_utilization'])
        return original(data,*args,**kwargs)
    monkeypatch.setattr(module,'route',qualified_route)
    result=place_and_route(chain(6),Library.load(),output_dir=tmp_path)
    assert routed and result.data['checks']['pdk_drc']['clean']
