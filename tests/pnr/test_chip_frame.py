"""Stock-frame exceptions are recorded and cannot hide our waiver or metal edits."""

from hashlib import sha256
import importlib
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import klayout.db as db
import pytest

from tritflow import PDK_ROOT, ROOT
from tritflow.netlist import GateNetlist
from tritflow.pnr import PhysicalVerificationError, PnrResult
from tritflow.pnr.chip_frame import frame_integrity
from tritflow.pnr.chip_frame_audit import stock_frame_policy

ASSETS = ROOT / "notebook/assets/chip/dot4"


def read(name):
    return json.loads((ASSETS / name).read_text())


def frame_mask(tmp_path):
    with ZipFile(ASSETS / "evidence.zip") as archive:
        name = next(
            n for n in archive.namelist() if n.endswith("/stock_frame.ip62.gds")
        )
        path = tmp_path / "stock_frame.ip62.gds"
        path.write_bytes(archive.read(name))
    return path


def recorded_macro(tmp_path):
    """Reuse the qualified seed-0 macro; only rebuild its stock-frame wrapper."""
    macro = tmp_path / "macro"
    macro.mkdir()
    with ZipFile(ASSETS / "evidence.zip") as archive:
        for name in ("dot4.gds", "dot4.pnr.json"):
            (macro / name).write_bytes(archive.read(".work/macro/" + name))
    data = json.loads((macro / "dot4.pnr.json").read_text())
    return PnrResult(
        macro / "dot4.gds",
        macro / "dot4.pnr.json",
        data["stats"],
        data,
        GateNetlist.load(ASSETS / "dot4.json"),
    )


def test_stock_chip_rebuild_preserves_recorded_geometry(tmp_path):
    """Separate frame power code must reproduce the qualified drawing and mask."""
    result = recorded_macro(tmp_path)
    before_macro = result.gds_path.read_bytes(), result.json_path.read_bytes()
    full = result.to_chip(
        frame="OSS_FRAME", output_dir=tmp_path / "chip", force_signoff=True
    )
    assert full.report["clean"] and full.report["drawing_lvs"]["strict_ports"]
    expected = read("provenance.json")["published_artifacts_sha256"]
    assert sha256(full.gds_path.read_bytes()).hexdigest() == expected["tr_1um_dot4.gds"]
    assert full.gds_path.read_bytes() == (ASSETS / "tr_1um_dot4.gds").read_bytes()
    # The native MDP deck writes build timestamps; compare its GDS with only
    # those timestamps disabled. The published drawing above is byte-exact.
    masks = []
    for source in (Path(full.report["mdp"]["output_path"]), ASSETS / "tr_1um_dot4.ip62.gds"):
        layout = db.Layout()
        layout.read(str(source))
        options = db.SaveLayoutOptions()
        options.gds2_write_timestamps = False
        normalized = tmp_path / f"mask{len(masks)}.gds"
        layout.write(str(normalized), options)
        masks.append(normalized.read_bytes())
    assert masks[0] == masks[1]
    with ZipFile(ASSETS / "evidence.zip") as archive:
        recorded = json.loads(archive.read(".work/chip/tr_1um_dot4.chip.json"))
    assert full.data["power_header"] == recorded["power_header"]
    for key in ("rails", "straps", "vias", "pins"):
        assert full.data["power"][key] == recorded["power"][key]
    assert (result.gds_path.read_bytes(), result.json_path.read_bytes()) == before_macro


def test_stock_chip_uses_sixteen_real_pads_and_separate_esd_vdd():
    report, pads = read("signoff.json"), read("pad_map.json")
    assert report["clean"] and not report["submission_ready"]
    assert pads == report["pad_map"] and len(pads) == report["pad_count"] == 16
    assert [p["pad"] for p in pads] == [f"P{i:02d}" for i in range(1, 17)]
    assert sum(p["master"] == "OSS_ESD_5V_ANA" for p in pads) == 14
    assert pads[7]["net"] == "VSS" and pads[7]["master"] == "OSS_ESD_5V_VSS"
    assert pads[15]["net"] == "ESD_VDD" and pads[15]["master"] == "OSS_ESD_5V_VDD"
    assert [p["pad"] for p in pads if p["net"] == "VDD"] == ["P01", "P02", "P15"]
    assert sum(p["net"] == "VMID" for p in pads) == 1
    assert {p["net"] for p in pads if p["type"] == "signal"} == set(
        report["port_directions"]
    )
    actual = db.Layout()
    actual.read(str(ASSETS / "tr_1um_dot4.gds"))
    assert [c.name for c in actual.top_cells()] == ["tr_1um_dot4"]
    assert actual.dbu == 0.001
    assert str(actual.top_cell().dbbox()) == "(-1250,-1250;1250,1250)"
    assert actual.cell("OSS_FRAME") is not None and actual.cell("OSS_FRAME_TEG") is None
    assert frame_integrity(
        ASSETS / "tr_1um_dot4.gds",
        PDK_ROOT / "libs.tech/klayout/libraries/TR-1um_frame_25x25.gds",
    )["clean"]


def test_native_zero_items_accept_only_the_documented_stock_exceptions():
    native = read("native_signoff.json")
    assert native["drawing_drc"]["violations"] == native["mask_drc"]["violations"] == 0
    assert native["physical_checks_passed"] and native["clean"]
    assert native["drawing_lvs"]["matched"] and native["drawing_lvs"]["strict_ports"]
    assert {p["layout"] for p in native["drawing_lvs"]["circuits"]} >= {
        "OSS_FRAME",
        "OSS_ESD_5V_ANA",
        "OSS_ESD_5V_VDD",
        "OSS_ESD_5V_VSS",
    }
    assert (
        native["mpw_precheck"]["clean"]
        and "mpw_template" in native["mpw_precheck"]["command"][1]
    )
    policy = native["stock_frame_policy"]
    assert policy["clean"]
    assert policy["stock_waivers"]["stock_polygon_count"] == 2
    assert policy["stock_waivers"]["stock_union_area_um2"] == 63400
    assert policy["stock_waivers"]["own_polygon_count"] == 0
    assert policy["stock_waivers"]["own_union_area_um2"] == 0
    metal = policy["metal_preservation"]
    assert metal["clean"]
    assert metal["stock_frame_only_xor_area_um2"]["M2"] == 0.001508
    assert all(v == 0 for v in metal["outside_stock_frame_xor_area_um2"].values())
    assert all(v == 0 for v in metal["delta_over_own_geometry_um2"].values())
    assert not native["mdp"]["full_die_metal_preservation"]["clean"]


def test_every_supply_has_reserve_including_ring_pad_cut_and_esd_leakage():
    report = read("native_signoff.json")["dc_current_check"]
    assert (
        report["defined"]
        and report["reserved_margin_met"]
        and report["max_utilization"] <= 0.8
    )
    assert report["imported_model_geometry_verified"]
    assert set(report["per_supply"]) == {"VDD", "VMID", "VSS", "ESD_VDD"}
    assert all(v["reserve"] >= 0.2 for v in report["per_supply"].values())
    assert len(report["pad_cut_checks"]) == 6
    assert all(v["reserve"] >= 0.2 for v in report["pad_cut_checks"])
    assert report["esd_leakage"]["passed"] and report["esd_leakage"]["biases_v"] == [
        -5,
        0,
        5,
    ]
    assert report["esd_leakage"]["max_total_absolute_current_a"] < 1e-6
    assert report["esd_leakage"]["conservative_budget_a_per_supply"] >= 1e-6


def test_our_waiver_is_rejected_even_when_hidden_inside_a_stock_waiver(tmp_path):
    layout = db.Layout()
    layout.read(str(ASSETS / "tr_1um_dot4.gds"))
    layout.top_cell().shapes(layout.layer(63, 0)).insert(
        db.Box(-1130000, -1130000, -930000, -930000)
    )
    altered = tmp_path / "our_waiver.gds"
    layout.write(str(altered))
    policy = stock_frame_policy(
        altered,
        ASSETS / "tr_1um_dot4.ip62.gds",
        "tr_1um_dot4",
        PDK_ROOT / "libs.tech/klayout/libraries/TR-1um_frame_25x25.gds",
        frame_mask(tmp_path),
    )
    assert not policy["clean"] and not policy["stock_waivers"]["clean"]
    assert policy["stock_waivers"]["own_polygon_count"] == 1
    # A union-area-only audit would have missed this duplicate polygon.
    region = db.Region(layout.top_cell().begin_shapes_rec(layout.layer(63, 0)))
    assert region.merged().area() * layout.dbu**2 == 63400


def test_extra_mask_metal_inside_the_frame_bbox_is_rejected(tmp_path):
    mask = db.Layout()
    mask.read(str(ASSETS / "tr_1um_dot4.ip62.gds"))
    top, layer = mask.top_cell(), mask.layer(20, 0)
    metal = db.Region(top.begin_shapes_rec(layer))
    patch = next(
        db.Box(x, -880000, x + 4000, -876000)
        for x in range(-700000, 700001, 20000)
        if (metal & db.Region(db.Box(x, -880000, x + 4000, -876000))).is_empty()
    )
    top.shapes(layer).insert(patch)
    altered = tmp_path / "changed_mask.gds"
    mask.write(str(altered))
    policy = stock_frame_policy(
        ASSETS / "tr_1um_dot4.gds",
        altered,
        "tr_1um_dot4",
        PDK_ROOT / "libs.tech/klayout/libraries/TR-1um_frame_25x25.gds",
        frame_mask(tmp_path),
    )
    assert not policy["metal_preservation"]["clean"]
    assert policy["metal_preservation"]["outside_stock_frame_xor_area_um2"]["M2"] == 16


def test_native_failed_own_waiver_check_preserves_previous_exports(
    tmp_path, monkeypatch
):
    """Run real decks: inherited markers cannot authorize one of our own."""
    result = recorded_macro(tmp_path)
    output = tmp_path / "chip"
    output.mkdir()
    previous = {
        name: ("previous " + name).encode()
        for name in ("tr_1um_dot4.gds", "tr_1um_dot4.chip.json", "tr_1um_dot4.cir")
    }
    for name, contents in previous.items():
        (output / name).write_bytes(contents)
    before_macro = result.gds_path.read_bytes(), result.json_path.read_bytes()
    module = importlib.import_module("tritflow.pnr.chip")
    original = module.chip_signoff

    def add_our_waiver(wrapped, **options):
        layout = db.Layout()
        layout.read(str(wrapped.gds_path))
        layout.top_cell().shapes(layout.layer(63, 0)).insert(
            db.Box(-1130000, -1130000, -930000, -930000)
        )
        layout.write(str(wrapped.gds_path))
        return original(wrapped, **options)

    monkeypatch.setattr(module, "chip_signoff", add_our_waiver)
    with pytest.raises(
        PhysicalVerificationError, match="Stock-frame qualification failed"
    ):
        result.to_chip(frame="OSS_FRAME", output_dir=output, force_signoff=True)
    for name, contents in previous.items():
        assert (output / name).read_bytes() == contents
    assert (result.gds_path.read_bytes(), result.json_path.read_bytes()) == before_macro
    report = json.loads((output / "signoff/signoff.summary.json").read_text())
    assert report["drawing_lvs"]["matched"] and not report["clean"]
    assert report["drawing_drc"]["violations"] == report["mask_drc"]["violations"] == 0
    assert report["stock_frame_policy"]["stock_waivers"]["own_polygon_count"] == 1
    assert (output / "tr_1um_dot4.failed.gds").exists()
