"""Readable rounded tables preserve actual data and expandable native precision."""

import importlib.util
import json
from pathlib import Path

import pytest


spec=importlib.util.spec_from_file_location("notebook_presentation",Path(__file__).resolve().parents[1]/"presentation.py")
presentation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(presentation)


def test_table_is_compact_and_native_evidence_keeps_precision(monkeypatch):
    outputs=[]
    monkeypatch.setattr(presentation,"display",outputs.append)
    value={"settling_ns":1/3,"passed":False}
    presentation.table([["Measured",value]],details="Full conditions")
    assert "0.3333" in outputs[0].data and "False" in outputs[0].data
    assert "<details>" in outputs[0].data
    presentation.evidence("Raw <measurement>",value)
    assert str(1/3) in outputs[1].data and "&lt;measurement&gt;" in outputs[1].data
    assert value["settling_ns"] == 1/3


@pytest.mark.parametrize("view",["layout_figure","placement_animation","routing_progress"])
def test_native_control_views_keep_data_frames_and_actions_when_spaced(tmp_path,view):
    from tritflow import flow
    from tritflow.pnr import mock_library,place_and_route
    from tritflow.viz import layout
    net=flow.loads("module controls(input trit a,output trit y); wire trit n; inv g0(n,a); inv g1(y,n); endmodule").synthesize()
    result=place_and_route(net,mock_library(),output_dir=tmp_path,anneal_steps=5,
                          history_every=1,run_pdk_drc=False)
    original=getattr(layout,view)(result)
    before=json.loads(original.to_json())
    spaced=presentation.title_controls(original)
    after=json.loads(spaced.to_json())
    assert json.loads(original.to_json()) == before
    assert before["data"] == after["data"]
    assert before.get("frames") == after.get("frames")
    assert before["layout"].get("sliders") == after["layout"].get("sliders")
    assert before["layout"]["title"]["text"] == after["layout"]["title"]["text"]
    assert [m["buttons"] for m in before["layout"]["updatemenus"]] == [m["buttons"] for m in after["layout"]["updatemenus"]]
    assert after["layout"]["margin"]["t"] >= 140


def test_show_uses_spaced_copy(monkeypatch):
    import plotly.graph_objects as go
    fig=go.Figure(go.Scatter(x=[1],y=[2]))
    fig.update_layout(title="Heading",updatemenus=[{"buttons":[{"label":"Play","method":"animate","args":[None]}]}])
    outputs=[]
    monkeypatch.delenv("TRITFLOW_NOTEBOOK_HEADLESS",raising=False)
    monkeypatch.setattr(presentation,"display",outputs.append)
    presentation.show(fig)
    assert outputs[0] is not fig
    assert outputs[0].layout.title.y == .99
