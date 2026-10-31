"""The published GDS, pin table and raw PDK evidence must describe one chip."""

from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import klayout.db as db
import pytest

import reuse

ASSETS = Path(__file__).resolve().parents[2] / "notebook/assets/chip/dot4"


def read(name):
    return json.loads((ASSETS / name).read_text())


def test_recorded_top_has_clean_native_decks_strict_ports_and_real_pads():
    report = read("signoff.json")
    assert report["clean"] and report["physical_checks_passed"]
    assert report["drawing_drc"]["violations"] == report["mask_drc"]["violations"] == 0
    assert report["drawing_lvs"] == {"matched": True, "strict_ports": True}
    assert report["mpw_precheck"]["clean"]
    assert report["mdp"]["metal_preservation"]["clean"]
    assert report["dc_current_reserved_margin_met"]
    assert report["dc_current_max_utilization"] <= 0.8
    assert report["drawing_audit"]["stock_waivers"]["stock_polygon_count"] == 2
    assert report["drawing_audit"]["stock_waivers"]["own_polygon_count"] == 0
    assert report["mask_lvs"]["matched"] is None
    assert not report["submission_ready"]
    assert report["pad_map"] == read("pad_map.json")
    assert len(report["pad_map"]) == report["pad_count"] == 16
    assert {p["net"] for p in report["pad_map"]} == set(report["port_directions"]) | {
        "VDD",
        "VMID",
        "VSS",
        "ESD_VDD",
    }
    assert report["frame"]["cell"] == "OSS_FRAME"
    for name, key in (
        ("tr_1um_dot4.gds", "gds_sha256"),
        ("tr_1um_dot4.ip62.gds", "mask_gds_sha256"),
    ):
        assert sha256((ASSETS / name).read_bytes()).hexdigest() == report[key]
    layout = db.Layout()
    layout.read(str(ASSETS / "tr_1um_dot4.gds"))
    assert layout.dbu == 0.001
    assert [cell.name for cell in layout.top_cells()] == ["tr_1um_dot4"]
    box = layout.top_cell().dbbox()
    assert [box.left, box.bottom, box.right, box.top] == [-1250, -1250, 1250, 1250]


def test_archived_native_reports_are_empty_and_published_artifacts_are_hashed():
    provenance = read("provenance.json")
    for name, expected in provenance["source_sha256"].items():
        path = ASSETS.parents[3] / name
        assert sha256(path.read_bytes()).hexdigest() == expected, name
    for name, expected in provenance["published_artifacts_sha256"].items():
        assert sha256((ASSETS / name).read_bytes()).hexdigest() == expected, name
    with ZipFile(ASSETS / "evidence.zip") as archive:
        names = archive.namelist()
        for kind in ("drawing_drc", "mask_drc"):
            reports = [n for n in names if n.endswith(kind + ".lyrdb")]
            assert len(reports) == 1
            assert ET.fromstring(archive.read(reports[0])).findall("./items/item") == []
        assert any(n.endswith("dot4.lvsdb") for n in names)
        assert any(n.endswith("tr_1um_dot4.ext.spice") for n in names)
        assert any(n.endswith("mpw_precheck.log") for n in names)
        for name, expected in provenance["pdk_rule_sha256"].items():
            matches = [n for n in names if n.endswith("/pdk/" + name)]
            assert len(matches) == 1
            assert sha256(archive.read(matches[0])).hexdigest() == expected


def test_shuttle_view_rejects_a_changed_gds_before_display(tmp_path):
    (tmp_path / "signoff.json").write_text(json.dumps(read("signoff.json")))
    (tmp_path / "tr_1um_dot4.gds").write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash"):
        reuse.shuttle_view(tmp_path)
