"""Readable rounded tables preserve actual data and expandable native precision."""

import importlib.util
from pathlib import Path


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
