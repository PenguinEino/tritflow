"""Actual mask warnings, cache invalidation, and fail-closed optional checks."""
import copy
from pathlib import Path
import shutil

import pytest

from tritflow import CELLS_DIR, PDK_ROOT
from tritflow.pnr import Library, PnrResult, mock_library, place_and_route
from tritflow.pnr import signoff as run_signoff
from .circuits import chain


def test_real_input_gate_warnings_fail_and_verified_cache_is_reused(tmp_path, monkeypatch):
    if not (CELLS_DIR/"out/library.json").exists():
        pytest.skip("Real cell library not published")
    import importlib
    module = importlib.import_module("tritflow.pnr.signoff")
    library = Library.load()
    result = place_and_route(chain(1), library, output_dir=tmp_path/"design")
    original_gds = result.gds_path.read_bytes()
    original_power = copy.deepcopy(result.data["power"])
    pdk = tmp_path/"pdk"
    for group in ("drc", "lvs"):
        source = PDK_ROOT/"libs.tech/klayout/tech"/group
        shutil.copytree(source, pdk/"libs.tech/klayout/tech"/group)
    options = dict(pdk_root=pdk, output_dir=tmp_path/"signoff")
    report = result.signoff(**options)
    assert not report["clean"] and not report["submission_ready"]
    assert report["drawing_drc"]["clean"] and report["drawing_lvs"]["matched"]
    assert report["mdp"]["completed"]
    assert report["mdp"]["metal_preservation"]["clean"]
    assert not any(report["mdp"]["metal_preservation"]["xor_area_um2"].values())
    assert set(report["mask_drc"]["categories"]) == {"WAR06: Floating SG Detected"}
    count = report["mask_drc"]["violations"]
    assert count > 0
    assert report["floating_gate_attribution"]["counts"] == {"external_input_gate": count}
    assert {n for m in report["floating_gate_attribution"]["markers"] for n in m["nets"]} == {"a"}
    assert report["mask_lvs"]["matched"] is None and not report["mask_lvs"]["defined"]
    assert report["drawing_audit"]["waiver_polygon_count"] == 0
    assert result.gds_path.read_bytes() == original_gds and result.data["power"] == original_power
    def must_recompute(*args, **kwargs):
        raise RuntimeError("a new native check was requested")
    native_run = module._run
    monkeypatch.setattr(module, "_run", must_recompute)
    # Repeated calls, including the public functional API, reuse the same proof.
    assert result.signoff(**options)["cache_hit"]
    assert run_signoff(result, **options)["cache_hit"]
    # Changes to source, rule, reference, or checked output cannot reuse a pass.
    for path in (result.gds_path, pdk/"libs.tech/klayout/tech/drc/run_IP62.drc",
                 Path(report["mask_drc"]["report_path"])):
        previous = path.read_bytes()
        path.write_bytes(previous+b"\n")
        with pytest.raises(RuntimeError, match="new native check"):
            result.signoff(**options)
        path.write_bytes(previous)
    reference = copy.deepcopy(result.netlist)
    reference.instances[0].pins["A"] = "another_input"
    with pytest.raises(RuntimeError, match="new native check"):
        result.signoff(netlist=reference, **options)
    monkeypatch.setattr(module, "_run", native_run)
    assert not result.signoff(**options)["cache_hit"]
    assert result.signoff(**options)["cache_hit"]


def test_mdp_exit_zero_without_output_is_not_success(tmp_path, monkeypatch):
    if not (CELLS_DIR/"out/library.json").exists():
        pytest.skip("Real cell library not published")
    import importlib
    module = importlib.import_module("tritflow.pnr.signoff")
    result = place_and_route(chain(1), Library.load(), output_dir=tmp_path/"design")
    original = module._run
    def broken_mdp(command, directory, label, timeout):
        if label == "mdp":
            log = directory/"mdp.log"; log.write_text("No mask output despite exit 0\n")
            return {"exit_code": 0, "log_path": str(log)}
        return original(command, directory, label, timeout)
    monkeypatch.setattr(module, "_run", broken_mdp)
    with pytest.raises(RuntimeError, match="MDP failed to generate"):
        result.signoff(output_dir=tmp_path/"signoff")
    assert not (tmp_path/"signoff/signoff.summary.json").exists()


def test_visited_warning_items_are_still_failures(tmp_path, monkeypatch):
    import importlib
    module = importlib.import_module("tritflow.pnr.signoff")
    def fake_report(command, directory, label, timeout):
        (directory/f"{label}.lyrdb").write_text("""<report-database><items><item>
          <category>'WAR06: Floating SG Detected'</category><visited>true</visited>
          </item></items></report-database>""")
        return {"exit_code": 0}
    monkeypatch.setattr(module, "_run", fake_report)
    report = module._drc("unused", "unused", "unused", "top", tmp_path, "mask", 1.)
    assert report["violations"] == 1 and not report["clean"]


def test_mock_signoff_is_rejected_and_missing_reference_is_clear(tmp_path):
    result = place_and_route(chain(1), mock_library(), output_dir=tmp_path, run_pdk_drc=False)
    with pytest.raises(ValueError, match="real device cells"):
        result.signoff()
    result.data["library"]["mock"] = False
    reopened = PnrResult(result.gds_path, result.json_path, result.stats, result.data)
    with pytest.raises(ValueError, match="gate reference"):
        reopened.signoff()
