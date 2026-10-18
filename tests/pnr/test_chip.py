"""Real pinned-deck full-chip proof, immutable macro and fail-closed publication."""

import copy
import importlib
from pathlib import Path

import klayout.db as db
import pytest

from tritflow import CELLS_DIR, PDK_ROOT, ROOT
from tritflow.hdl import load
from tritflow.pnr import (
    Library,
    PhysicalVerificationError,
    chip,
    mock_library,
    place_and_route,
)
from tritflow.synth import synthesize
from .circuits import chain


@pytest.fixture(scope="module")
def wrapped(tmp_path_factory):
    if not (CELLS_DIR / "out/library.json").exists():
        pytest.skip("Real cell library not published")
    out = tmp_path_factory.mktemp("chip")
    net = synthesize(load(ROOT / "examples/full_add.tv", top="full_add"))
    library = Library.load()
    result = place_and_route(net, library, output_dir=out / "macro", seed=0)
    before = (
        result.gds_path.read_bytes(),
        result.json_path.read_bytes(),
        copy.deepcopy(result.data["power"]),
    )
    full = result.to_chip(library=library, output_dir=out / "chip")
    return result, full, before


def test_real_chip_passes_every_unwaived_check_and_preserves_macro(wrapped):
    macro, full, before = wrapped
    report = full.report
    assert report["clean"] and report["physical_checks_passed"]
    assert report["drawing_drc"]["violations"] == 0
    assert report["drawing_lvs"]["matched"] and report["drawing_lvs"]["strict_ports"]
    assert report["mask_drc"]["violations"] == 0
    assert report["mdp"]["metal_preservation"]["clean"]
    assert report["mpw_precheck"]["clean"]
    assert report["self_checks"]["connectivity"]["clean"]
    assert report["dc_current_check"]["reserved_margin_met"]
    assert report["drawing_audit"]["waiver_polygon_count"] == 0
    assert not report[
        "submission_ready"
    ]  # Real allocation/bond/ESD approval is external.
    assert report["mask_lvs"] == {
        "defined": False,
        "matched": None,
        "reason": "Inspected MPW workflow defines drawing LVS before MDP; no post-MDP LVS stage",
    }
    assert before == (
        macro.gds_path.read_bytes(),
        macro.json_path.read_bytes(),
        macro.data["power"],
    )
    assert {p["net"] for p in full.data["pad_map"]} == {
        p.name for p in macro.netlist.ports
    } | {"VDD", "VMID", "VSS"}
    assert (full.json_path.parent / "README.md").exists()


def test_frame_seal_is_an_exact_copy_of_pinned_master(wrapped):
    _, full, _ = wrapped
    ref, actual = db.Layout(), db.Layout()
    ref.read(str(PDK_ROOT / "libs.tech/klayout/libraries/TR-1um_frame_25x25.gds"))
    actual.read(str(full.gds_path))
    seal = next(
        actual.cell(i.cell_index)
        for i in actual.cell("OSS_FRAME_TEG").each_inst()
        if actual.cell(i.cell_index).name.startswith("OSS_EDGE_SEAL")
    )
    for info in ref.layer_infos():
        a = db.Region(ref.cell("OSS_EDGE_SEAL").begin_shapes_rec(ref.layer(info)))
        b = db.Region(seal.begin_shapes_rec(actual.layer(info)))
        assert (a ^ b).is_empty()
    assert full.report["drawing_audit"]["bbox_um"] == [-1250.0, -1250.0, 1250.0, 1250.0]


def test_verified_chip_cache_checks_inputs_and_outputs(wrapped, monkeypatch):
    _, full, _ = wrapped
    module = importlib.import_module("tritflow.pnr.chip")

    def recompute(*args, **kwargs):
        raise RuntimeError("native recomputation requested")

    monkeypatch.setattr(module, "_run", recompute)
    assert full.signoff()["cache_hit"]
    for path in (full.gds_path, Path(full.report["mdp"]["output_path"])):
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        try:
            with pytest.raises(RuntimeError, match="native recomputation requested"):
                full.signoff()
        finally:
            path.write_bytes(original)
    # A failed rerun may have replaced other reports in the tampered run.
    # Regenerate the complete proof before accepting another cache hit.
    monkeypatch.undo()
    assert not full.signoff(force=True)["cache_hit"]
    assert full.signoff()["cache_hit"]


def test_failed_mask_check_preserves_previous_canonical(wrapped, monkeypatch):
    macro, full, _ = wrapped
    module = importlib.import_module("tritflow.pnr.chip")
    original = module._drc

    def rejected(*args, **kwargs):
        report = original(*args, **kwargs)
        if args[5] == "mask_drc":
            report.update(clean=False, violations=1, categories={"injected failure": 1})
        return report

    monkeypatch.setattr(module, "_drc", rejected)
    before = full.gds_path.read_bytes()
    metadata = full.json_path.read_bytes()
    reference = full.gds_path.with_suffix(".cir").read_bytes()
    with pytest.raises(PhysicalVerificationError, match="Chip qualification failed"):
        chip(macro, output_dir=full.gds_path.parent, force_signoff=True)
    assert full.gds_path.read_bytes() == before
    assert full.json_path.read_bytes() == metadata
    assert full.gds_path.with_suffix(".cir").read_bytes() == reference
    assert full.gds_path.with_name(full.data["top"] + ".failed.gds").exists()


def test_mock_wrapper_and_oversize_macro_are_rejected_before_publication(tmp_path):
    result = place_and_route(
        chain(1), mock_library(), output_dir=tmp_path / "mock", run_pdk_drc=False
    )
    with pytest.raises(ValueError, match="real device cells"):
        result.to_chip()
    result.data["library"]["mock"] = False
    result.data["die"] = [3000.0, 3000.0]
    with pytest.raises(ValueError, match="does not fit"):
        result.to_chip(library=mock_library())
    assert not (tmp_path / "mock/chip").exists()
