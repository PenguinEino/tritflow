"""Bundled Xschem SVGs retain provenance, contrast, text and safe read-only export."""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import pytest


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT/"notebook/assets/schematics"
NS = "{http://www.w3.org/2000/svg}"


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/"notebook"/filename)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


exporter = module("tritflow_schematic_export", "export_schematics.py")
gallery = module("tritflow_schematic_gallery", "schematics.py")


def luminance(color):
    components = [int(color[i:i+2], 16)/255 for i in (1,3,5)]
    linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in components]
    return sum(a*b for a,b in zip(linear,[.2126,.7152,.0722]))


def test_assets_have_complete_drawings_and_high_contrast_variants():
    manifest = json.loads((ASSETS/"manifest.json").read_text())
    assert set(manifest["schematics"]) == set(exporter.EXPORTS)
    for entry in manifest["schematics"].values():
        assert len(entry["source_sha256"]) == 64
        for theme, record in entry["themes"].items():
            raw = (ASSETS/record["file"]).read_bytes()
            assert sha256(raw).hexdigest() == record["sha256"]
            root = ET.fromstring(raw)
            assert root.get("viewBox") and root.get("role") == "img"
            assert len(list(root.iter(NS+"path"))) >= 10
            assert len(list(root.iter(NS+"text"))) >= 10
            assert list(root.iter(NS+"rect"))[0].get("class") == "l0"
            assert not list(root.iter(NS+"image")), "SVG must not depend on external rasters"
            bg, fg = exporter.THEMES[theme]
            low, high = sorted([luminance(bg),luminance(fg)])
            assert (high+.05)/(low+.05) >= 7
            assert bg in raw.decode() and fg in raw.decode()


def test_gallery_verifies_assets_and_bundles_both_themes(tmp_path):
    html = gallery.schematic_gallery(ASSETS)
    assert html.count("<picture>") == len(exporter.EXPORTS)
    assert "prefers-color-scheme: dark" in html
    assert "data:image/svg+xml;base64," in html
    assert "Source SHA-256" in html
    shutil.copytree(ASSETS, tmp_path/"assets")
    p = tmp_path/"assets/INV.svg"
    p.write_text(p.read_text()+"<!-- altered -->")
    with pytest.raises(AssertionError, match="asset changed"):
        gallery.schematic_gallery(tmp_path/"assets")


def test_only_selected_primitive_expands_and_arithmetic_drawings_are_separate():
    html = gallery.schematic_gallery(ASSETS,names=["INV","NAND","NOR","NANY"],selected="NANY")
    assert html.count("<details open>") == 1
    assert "<details open><summary><strong>NANY" in html
    assert "half_adder" not in html and "full_adder" not in html
    assert "max-width:620px" in html
    arithmetic = gallery.schematic_gallery(ASSETS,names=["half_adder","full_adder"],selected="half_adder")
    assert arithmetic.count("<picture>") == 2 and arithmetic.count("<details open>") == 1


@pytest.mark.skipif(not shutil.which("xschem") or not (Path.home()/"balanced-ternary-logic/inverter.sch").is_file(),
                    reason="read-only reference and Xschem required")
def test_batch_reexport_is_deterministic_and_source_unchanged(tmp_path):
    source = Path.home()/"balanced-ternary-logic"
    files = [source/filename for filename,_ in exporter.EXPORTS.values()]
    before = {p: sha256(p.read_bytes()).hexdigest() for p in files}
    args = (source, Path.home()/"pdk/TR-1um-pinned", "/usr/local/share/xschem/xschem_library")
    first = exporter.export(*args, tmp_path/"one")
    second = exporter.export(*args, tmp_path/"two")
    assert first == second
    assert before == {p: sha256(p.read_bytes()).hexdigest() for p in files}
    assert {"reference", "pdk", "system"} == {p.split("/")[0] for p in first["dependencies"]}
    with pytest.raises(ValueError, match="read-only"):
        exporter.export(*args, source/"forbidden-export")
