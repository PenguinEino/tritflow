"""Caches never reuse stale options, library context, or modified artifacts."""

import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
import pytest


spec = importlib.util.spec_from_file_location("tritflow_cache", Path(__file__).resolve().parents[1]/"cache.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_cache_hits_and_invalidation(tmp_path):
    artifact = tmp_path/"design.gds"
    artifact.write_bytes(b"gds-1")
    calls = []

    def run():
        calls.append(1)
        return {"waveforms": {"time": np.arange(3)}, "stimulus": {"vectors": [(-1,), (0,)]}}

    cache = module.Cache(tmp_path/"cache", "source-and-pdk-A")
    options = {"load": 10e-15}
    cache.run("post", options, run, artifacts=[artifact])
    result = cache.run("post", options, run, artifacts=[artifact])
    assert len(calls) == 1 and isinstance(result["waveforms"]["time"], np.ndarray)
    assert result["stimulus"]["vectors"] == [(-1,), (0,)]
    artifact.write_bytes(b"gds-2")
    cache.run("post", options, run, artifacts=[artifact])
    assert len(calls) == 2
    cache.run("post", {"load": 100e-15}, run, artifacts=[artifact])
    assert len(calls) == 3
    other = module.Cache(tmp_path/"cache", "source-and-pdk-B")
    other.run("post", {"load": 100e-15}, run, artifacts=[artifact])
    assert len(calls) == 4


def test_failure_does_not_publish_cache_and_names_are_bounded(tmp_path):
    cache = module.Cache(tmp_path, "context")
    with pytest.raises(ValueError, match="filename"):
        cache.run("../outside", {}, lambda: {})
    def fail():
        raise RuntimeError("SPICE failed")
    with pytest.raises(RuntimeError, match="SPICE failed"):
        cache.run("post", {}, fail)
    assert not list(tmp_path.glob("*.gz"))


def test_cached_pre_post_pair_keeps_native_waveform_arrays(tmp_path):
    cache = module.Cache(tmp_path, "pair")
    simulated = {"waveforms": {"time": np.arange(3)*1e-9},
                 "stimulus": {"vectors": [(-1,), (0,)]}}
    cache.run("pair", {}, lambda: {"pre": simulated, "post": simulated})
    result = cache.run("pair", {}, lambda: pytest.fail("must reuse measured pair"))
    for mode in ("pre", "post"):
        assert isinstance(result[mode]["waveforms"]["time"], np.ndarray)
        np.testing.assert_array_equal(result[mode]["waveforms"]["time"]*1e9, np.arange(3))
        assert result[mode]["stimulus"]["vectors"] == [(-1,), (0,)]


def test_real_abstract_pin_obstruction_manifest_and_publication_invalidate(tmp_path):
    """Change only published metadata, retaining identical cell GDS/SPICE."""
    from tritflow import PDK_ROOT
    root = Path(__file__).resolve().parents[2]
    clone = tmp_path/"source"
    for directory in ("cells", "notebook", "tritflow", "examples"):
        (clone/directory).mkdir(parents=True)
    shutil.copy2(root/"cells/template.json", clone/"cells/template.json")
    shutil.copytree(root/"cells/out/INV", clone/"cells/out/INV")
    for name in ("library.json", "generation.json"):
        shutil.copy2(root/f"cells/out/{name}", clone/f"cells/out/{name}")
    for name in ("setup_pins.json", "tritflow_tr1um.ipynb"):
        shutil.copy2(root/f"notebook/{name}", clone/f"notebook/{name}")
    def fingerprint(): return module.runtime_fingerprint(clone, PDK_ROOT)
    initial = fingerprint()
    artifact = clone/"cells/out/INV/INV.abstract.json"
    original = artifact.read_bytes()
    value = json.loads(original)
    value["pins"]["A"]["access"][0][0] += 6
    artifact.write_text(json.dumps(value))
    pin_changed = fingerprint()
    assert pin_changed != initial
    artifact.write_bytes(original)
    assert fingerprint() == initial
    value = json.loads(original)
    value["obstructions"].setdefault("M2", []).append([3,3,6,6])
    artifact.write_text(json.dumps(value))
    assert fingerprint() not in {initial, pin_changed}
    artifact.write_bytes(original)
    for name in ("library.json", "generation.json"):
        path = clone/f"cells/out/{name}"
        raw = path.read_bytes()
        path.write_bytes(raw+b"\n")
        assert fingerprint() != initial
        path.write_bytes(raw)
    relocated = tmp_path/"relocated"
    shutil.copytree(clone, relocated)
    assert module.runtime_fingerprint(relocated, PDK_ROOT) == initial


def test_force_reruns_valid_cache_and_records_actual_stage_times(tmp_path):
    calls = []
    cache = module.Cache(tmp_path, "fixed", force=True)
    for _ in range(2): cache.run("stage", {}, lambda: calls.append(1) or {})
    assert len(calls) == 2
    assert cache.events == [("stage","run")]*2
    assert all(r["state"] == "run" and r["elapsed_s"] > 0 for r in cache.timings)
