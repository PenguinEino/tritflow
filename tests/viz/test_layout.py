"""Physical coordinates, hierarchy, interactive selection and honest replay."""
import json

from PIL import Image
import pytest

from tritflow.pnr import mock_library, place_and_route
from tritflow.viz.layout import (capacitance_figure, layout_figure, placement_animation, render_gds,
                                routing_progress, save_layout_views)
from tests.pnr.circuits import chain


@pytest.fixture
def result(tmp_path):
    netlist = chain(4)
    netlist.instances[0].hier = "digit[0].carry"
    return place_and_route(netlist, mock_library(), output_dir=tmp_path,
                           seed=7, anneal_steps=75, history_every=15, run_pdk_drc=False)


def test_layout_contains_routes_hierarchy_and_both_selectors(result):
    fig = layout_figure(result, highlight_net="a", highlight_instance="digit[0].carry", show_power=True)
    selected_cells = [t for t in fig.data if (t.meta or {}).get("inst") == "g0"]
    assert len(selected_cells) == 1
    assert selected_cells[0].fillcolor == "#ffe3a3"
    assert "digit[0].carry" in selected_cells[0].text
    assert selected_cells[0].x[1]-selected_cells[0].x[0] == result.data["placements"][0]["width"]
    for net in {w["net"] for w in result.data["wires"]}:
        assert any((t.meta or {}).get("net") == net for t in fig.data)
    buttons = fig.layout.updatemenus[0].buttons
    assert {"a", "z", "VDD", "VMID", "VSS"} <= {b.label for b in buttons}
    assert any("digit[0].carry" in b.label for b in fig.layout.updatemenus[1].buttons)
    assert any((t.meta or {}).get("net") == "a" and t.opacity == 1 for t in fig.data)
    assert any((t.meta or {}).get("net") == "z" and t.opacity == .12 for t in fig.data)
    assert fig.layout.yaxis.scaleanchor == "x"
    # Round-trip Plotly's public JSON representation, including embedded controls.
    assert json.loads(fig.to_json())["layout"]["updatemenus"]
    with pytest.raises(ValueError, match="Unknown net"):
        layout_figure(result, highlight_net="missing")


def test_placement_animation_links_hpwl_and_actual_snapshots(result):
    fig = placement_animation(result.json_path)
    history = result.data["history"]
    assert len(fig.frames) == len(history)
    assert list(fig.data[-2].x) == [s["step"] for s in history]
    assert list(fig.data[-2].y) == [s["hpwl"] for s in history]
    for frame, snapshot in zip(fig.frames, history):
        assert frame.name == str(snapshot["step"])
        assert frame.data[-1].x[0] == snapshot["step"]
        for trace, placement in zip(frame.data, snapshot["placements"]):
            assert trace.x[0] == placement["x"]
            assert trace.y[0] == placement["y"]
            assert trace.meta["inst"] == placement["inst"]


def test_routing_animation_uses_recorded_order(result):
    fig = routing_progress(result)
    order = result.data["routing_order"]
    assert len(fig.frames) == len(order)+1
    assert all(not t.visible for t in fig.data if (t.meta or {}).get("kind") == "route")
    first = fig.frames[1]
    for update, index in zip(first.data, first.traces):
        net = fig.data[index].meta["net"]
        assert update.visible == (net == order[0])
    assert all(t.visible for t in fig.frames[-1].data)
    assert "successful routing pass" in fig.layout.title.text


def test_gds_raster_and_portable_html_outputs(result, tmp_path):
    original = result.gds_path.read_bytes()
    path = render_gds(result.gds_path, tmp_path/"raster.png", top=result.data["top"], width=900, height=650)
    with Image.open(path) as image:
        assert image.size == (900, 650)
        assert image.info["Renderer"] == "KLayout LayoutView"
        legend = json.loads(image.info["Layer legend"])
        assert {item["name"] for item in legend} >= {"M1", "V1", "M2"}
        # A filled boundary or blank viewport must not hide all routing detail.
        colors = image.convert("RGB").getcolors(maxcolors=1000000)
        assert len(colors) > 15
        counts = {color: count for count, color in colors}
        assert counts.get((40, 105, 174), 0) > 600  # M1 beyond its legend swatch.
        assert counts.get((180, 61, 138), 0) > 600  # M2 beyond its legend swatch.
        assert max(count for count, color in colors if color != (255, 255, 255)) < image.width*image.height*.6
    assert original == result.gds_path.read_bytes()
    paths = save_layout_views(result)
    assert set(paths) == {"png", "layout", "placement", "routing", "capacitance"}
    assert all(p.is_file() for p in paths.values())
    for key in ("layout", "placement", "routing", "capacitance"):
        html = paths[key].read_text()
        assert "plotly.js" in html.lower()
        assert "cdn.plot.ly/" not in html[:300]


def test_capacitance_colours_match_logical_net_values_and_portable_snapshot(result):
    from plotly.colors import sample_colorscale
    report = result.net_parasitics()
    fig = capacitance_figure(result.json_path)
    maximum = max(n["wire_capacitance_f"] for n in report["nets"].values())
    seen = set()
    for trace in fig.data:
        if (trace.meta or {}).get("kind") != "route":
            continue
        name = trace.meta["net"]
        cap = report["nets"][name]["wire_capacitance_f"]
        assert trace.line.color == sample_colorscale("Viridis", [cap/maximum])[0]
        assert trace.marker.color == trace.line.color
        assert trace.meta["wire_capacitance_f"] == cap
        assert name in trace.hovertemplate and "fF" in trace.hovertemplate
        assert "Fan-out" in trace.hovertemplate
        seen.add(name)
    assert seen == {w["net"] for w in result.data["wires"]}
    assert fig.data[-1].marker.cmax == maximum*1e15
    assert "fF" in fig.data[-1].marker.colorbar.title.text
    assert fig.layout.yaxis.scaleanchor == "x"
    assert fig.layout.meta["parameter_origin"] == "assumption"
    assert json.loads(fig.to_json())["data"]
    # A separate JSON sidecar is also accepted, with the same colour scale.
    other = capacitance_figure(result.data, parasitics=result.json_path.with_name(f"{result.data['top']}.net_parasitics.json"))
    assert other.data[-1].marker.cmax == fig.data[-1].marker.cmax


def test_capacitance_figure_empty_equal_and_missing_data():
    data = {"top": "empty", "die": [10, 10], "placements": [], "wires": [], "vias": [], "pins": []}
    report = {"top": "empty", "nets": {}, "wire_scope": "test", "parameter_origin": "assumption"}
    assert capacitance_figure(data, parasitics=report).data[-1].marker.cmax == 1
    with pytest.raises(ValueError, match="No net parasitic report"):
        capacitance_figure(data)
    data["pins"] = [{"name": "unused", "layer": "M2", "rect": [1, 1, 2, 2]}]
    with pytest.raises(ValueError, match="missing routed nets"):
        capacitance_figure(data, parasitics=report)
    report["nets"]["unused"] = {"wire_capacitance_f": 0, "cell_input_capacitance_f": 0,
        "total_load_f": 0, "fanout": 0, "pin_count": 1, "via_count": 0}
    fig = capacitance_figure(data, parasitics=report)
    assert fig.data[0].meta["net"] == "unused"
    assert "0 fF" in fig.data[0].hovertemplate
