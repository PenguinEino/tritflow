"""A changed cell publication invalidates all physical-design evidence."""
import json
import os
import shutil

import pytest

from tritflow import CELLS_DIR, ROOT
from tritflow.pnr import batch


def test_fingerprint_detects_preserved_mtime_and_extra_cell_views(tmp_path):
    cells = tmp_path/"cells"
    (cells/"out").mkdir(parents=True)
    (cells/"template.json").write_text('{}')
    view = cells/"out/INV.gds"
    view.write_bytes(b"first drawing")
    out = tmp_path/"build/mul1"
    out.mkdir(parents=True)
    (out/"mul1.json").write_text('{}')
    before = batch.input_state(tmp_path/"build", cells, ("mul1",), (7,), 60, False)
    stamp = view.stat()
    view.write_bytes(b"other drawing")
    os.utime(view, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    after = batch.input_state(tmp_path/"build", cells, ("mul1",), (7,), 60, False)
    assert before["fingerprint"] != after["fingerprint"]
    (cells/"out/new.abstract.json").write_text('{}')
    assert batch.input_state(tmp_path/"build", cells, ("mul1",), (7,), 60, False)["fingerprint"] != after["fingerprint"]


def test_cached_build_and_mid_run_publication_restart(tmp_path, monkeypatch):
    if not (CELLS_DIR/"out/library.json").exists():
        pytest.skip("Real cell library not published")
    # Copy only the views consumed by PNR/LVS, never modify the shared library.
    cells = tmp_path/"cells"
    (cells/"out").mkdir(parents=True)
    shutil.copy2(CELLS_DIR/"template.json", cells/"template.json")
    for filename in ("library.json", "all.spice"):
        shutil.copy2(CELLS_DIR/"out"/filename, cells/"out"/filename)
    for directory in (CELLS_DIR/"out").iterdir():
        if directory.is_dir() and (directory/f"{directory.name}.abstract.json").exists():
            target = cells/"out"/directory.name
            target.mkdir()
            for suffix in ("gds", "abstract.json", "char.json"):
                source = directory/f"{directory.name}.{suffix}"
                if source.exists():
                    shutil.copy2(source, target/source.name)
    out = tmp_path/"build/mul1"
    out.mkdir(parents=True)
    from tritflow.hdl import load
    from tritflow.synth import synthesize
    netlist = synthesize(load(ROOT/"examples/mul1.tv", top="mul1"))
    netlist.save(out/"mul1.json")
    original = batch.build_design
    calls = []
    def publishing(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(args[0])
        if len(calls) == 1:
            # Model a publication finishing while a design was being checked.
            (cells/"out/publication.json").write_text('{"generation": 2}')
        return result
    monkeypatch.setattr(batch, "build_design", publishing)
    results = batch.run_all(tmp_path/"build", cells, designs=("mul1",), seeds=(7,), anneal_steps=60, views=False)
    assert calls == ["mul1", "mul1"]
    assert results[0]["checks"]["lvs"]["clean"]
    manifest = json.loads((tmp_path/"build/pnr_manifest.json").read_text())
    assert "publication.json" in " ".join(manifest["inputs"]["files"])
    batch.run_all(tmp_path/"build", cells, designs=("mul1",), seeds=(7,), anneal_steps=60, views=False)
    assert len(calls) == 2  # Valid unchanged evidence is reused.
    (out/"mul1.gds").unlink()
    batch.run_all(tmp_path/"build", cells, designs=("mul1",), seeds=(7,), anneal_steps=60, views=False)
    assert len(calls) == 3  # Missing checked output never counts as cached success.
