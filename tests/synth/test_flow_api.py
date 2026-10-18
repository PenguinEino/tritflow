"""The notebook facade delegates to public stream functions and fails honestly."""

from pathlib import Path
import shutil

import pytest

from tritflow import flow
from tritflow.netlist import GateNetlist


def test_load_truth_synthesis_and_pre_simulation_delegation(monkeypatch):
    import tritflow.sim

    n = flow.load("examples/full_add.tv", "full_add", {}).synthesize()
    assert isinstance(n, GateNetlist)
    assert n.report()["cells"] == {"INV": 5, "NANY": 11}
    assert len(flow.load("examples/half_add.tv", "half_add").truth_table()["sum"]) == 9
    calls = []

    def fake(*args, **kwargs):
        calls.append((args, kwargs))
        assert args[5]((1, 1, 0)) == {"sum": -1, "cout": 1}
        return {"measurements": {"passed": True}}

    monkeypatch.setattr(tritflow.sim, "simulate", fake)
    assert n.simulate([(1, 1, 0)], load=100e-15)["measurements"]["passed"]
    assert calls[0][1]["loads_f"] == 100e-15
    assert ".subckt full_add" in calls[0][0][0]


def test_route_and_drc_call_public_entrypoints(monkeypatch, tmp_path):
    import tritflow.pnr

    n = flow.loads("module m(input trit a,output trit y); assign y=~a; endmodule").synthesize()
    calls = []
    result = tritflow.pnr.PnrResult(tmp_path/"m.gds", tmp_path/"m.pnr.json", {"test": 1}, {"top": "m"})

    def route(net, library, **kwargs):
        assert not library.mock
        calls.append(kwargs)
        return result

    monkeypatch.setattr(tritflow.pnr, "place_and_route", route)
    monkeypatch.setattr(tritflow.pnr, "pdk_drc", lambda *a, **k: {"clean": False, "violations": 2})
    layout = n.place_and_route(output_dir=tmp_path, seed=7)
    assert calls[0]["seed"] == 7 and calls[0]["pdk_root"] == n.settings.pdk
    assert layout.stats == {"test": 1} and layout.drc()["clean"] is False


def test_lvs_mismatch_blocks_post_layout_simulation(monkeypatch, tmp_path):
    import tritflow.pnr
    from tritflow.pnr import PnrResult

    gds = tmp_path/"m.gds"
    gds.write_bytes(b"fixture")
    n = flow.loads("module m(input trit a,output trit y); assign y=~a; endmodule").synthesize()
    layout = flow.Layout(PnrResult(gds, tmp_path/"m.pnr.json", {}, {}), n, n.settings)
    monkeypatch.setattr(tritflow.pnr, "strict_lvs", lambda *a, **k: {
        "matched": False, "extracted": str(tmp_path/"absent"), "report": None, "errors": ["mismatch"]})
    assert layout.lvs()["matched"] is False
    with pytest.raises(RuntimeError, match="unmatched layout"):
        layout.extract()


def test_signoff_uses_public_pnr_result_with_carried_settings(monkeypatch, tmp_path):
    from tritflow.pnr import PnrResult

    n = flow.loads("module m(input trit a,output trit y); assign y=~a; endmodule").synthesize()
    result = PnrResult(tmp_path/"m.gds", tmp_path/"m.pnr.json", {}, {})
    layout = flow.Layout(result, n, n.settings)
    def check(self, **kwargs):
        assert self is result and kwargs["netlist"] is n
        assert not kwargs["library"].mock
        assert kwargs["pdk_root"] == n.settings.pdk
        assert kwargs["klayout_binary"] == n.settings.klayout
        assert kwargs["force"] is True and kwargs["output_dir"] == tmp_path/"mask"
        return {"clean":False, "submission_ready":False}
    monkeypatch.setattr(PnrResult, "signoff", check)
    assert layout.signoff(output_dir=tmp_path/"mask", force=True) == {"clean":False, "submission_ready":False}


@pytest.mark.skipif(not shutil.which("ngspice") or not (Path.home()/"bin/klayout/klayout").is_file(),
                    reason="local physical tools required")
def test_unused_input_full_chain_and_missing_pad_label_invalidates_lvs(tmp_path):
    import klayout.db as db

    circuit = flow.loads("module unused(input trit a,b,output trit y); assign y=~a; endmodule")
    net = circuit.synthesize()
    layout = net.place_and_route(output_dir=tmp_path, anneal_steps=0)
    assert layout.drc()["clean"]
    report = layout.lvs()
    assert report["matched"] and report["unused_input_formals_restored"] == ["b"]
    before = layout._lvs_fingerprint
    extracted = layout.extract()
    assert extracted.simulate([(-1,-1), (0,1), (1,0)], load=100e-15)["measurements"]["passed"]
    drawing = db.Layout()
    drawing.read(str(layout.gds_path))
    labels = drawing.cell(net.top).shapes(drawing.layer(49,0))
    missing = [shape for shape in labels.each() if shape.is_text() and shape.text.string == "b"]
    assert len(missing) == 1
    missing[0].delete()
    drawing.write(str(layout.gds_path))
    assert layout._fingerprint() != before
    # extract() must rerun the physical proof, rather than reuse the prior PASS.
    with pytest.raises(RuntimeError, match="unmatched layout"):
        layout.extract()
    assert layout._lvs_report["matched"] is False


@pytest.mark.skipif(not shutil.which("ngspice") or not (Path.home()/"bin/klayout/klayout").is_file(),
                    reason="local physical tools required")
def test_real_full_chain_and_reopen(tmp_path):
    circuit = flow.loads("module flow_inv(input trit a,output trit y); assign y=~a; endmodule")
    net = circuit.synthesize()
    layout = net.place_and_route(output_dir=tmp_path, anneal_steps=0)
    assert layout.drc()["clean"]
    assert layout.lvs()["matched"]
    extracted = layout.extract()
    assert extracted.capacitance["nets"]
    assert "Ctfwire" in extracted.spice
    result = extracted.simulate([(-1,), (0,), (1,)], load=100e-15)
    assert result["measurements"]["passed"]
    reopened = flow.load_layout(net, tmp_path)
    assert reopened.gds_path == layout.gds_path
    assert reopened.stats == layout.stats
