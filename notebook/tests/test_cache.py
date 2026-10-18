"""Caches never reuse stale options, library context, or modified artifacts."""

import importlib.util
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
