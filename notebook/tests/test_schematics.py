"""V3 compact drawings remain native SVGs with all source devices visible."""

import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "notebook/assets/schematics"
NS = "{http://www.w3.org/2000/svg}"
spec = importlib.util.spec_from_file_location("compact_verification", ASSETS / "verify_compact.py")
verification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verification)


@pytest.mark.parametrize("cell,device_count", [("INV", 4), ("NAND", 6), ("NOR", 6), ("NANY", 10)])
def test_compact_drawings_include_all_devices_and_native_embedded_symbols(cell, device_count):
    drawing = ET.fromstring((ASSETS / f"{cell}.compact.svg").read_bytes())
    assert drawing.get("viewBox") and drawing.get("role") == "img"
    assert len(list(drawing.iter(NS + "path"))) >= 10
    assert not list(drawing.iter(NS + "image"))
    assert not list(drawing.iter(NS + "foreignObject"))
    labels = " ".join(drawing.itertext())
    instances, embedded = verification.components((ASSETS / "src" / f"{cell.lower()}.sch").read_text())
    devices = [instance for instance in instances.values()
               if Path(instance["symbol"]).stem in verification.DEVICES]
    assert len(devices) == device_count
    assert set(embedded) == {instance["symbol"] for instance in devices}
    assert "w=" in labels and "l=" in labels
