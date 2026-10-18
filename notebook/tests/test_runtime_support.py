"""A preloaded scientific stack and failed notebook cells get useful recovery."""

import importlib.metadata
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"notebook"))
import runtime_support as runtime


def test_colab_pins_only_the_two_notebook_owned_packages():
    lines=[line.strip() for line in (ROOT/"notebook/requirements-colab.txt").read_text().splitlines()
           if line.strip() and not line.startswith("#")]
    assert {line.split("==")[0] for line in lines} == {"klayout","lark"}


def test_preloaded_version_change_requests_one_restart_before_importing(monkeypatch):
    monkeypatch.setattr(runtime.importlib.metadata,"version",lambda name:"9.0.0")
    monkeypatch.setitem(sys.modules,"numpy",SimpleNamespace(__version__="2.0.2"))
    monkeypatch.setattr(runtime.importlib,"import_module",lambda name:pytest.fail("must stop before importing"))
    with pytest.raises(RuntimeError,match="2.0.2 is loaded, but 9.0.0 is installed.*Restart the runtime once"):
        runtime.check_runtime()


def test_original_mixed_numpy_import_error_has_restart_guidance(monkeypatch):
    versions=dict(runtime.MINIMUM_VERSIONS)
    monkeypatch.setattr(runtime,"check_minimum_versions",lambda:versions)
    for name in (*versions,"klayout","lark"):
        monkeypatch.delitem(sys.modules,name,raising=False)
    def mixed(name):
        if name == "numpy.testing":
            raise AttributeError("numpy._core._multiarray_umath lacks _blas_supports_fpe")
        return SimpleNamespace()
    monkeypatch.setattr(runtime.importlib,"import_module",mixed)
    with pytest.raises(RuntimeError,match="_blas_supports_fpe.*Restart the runtime once"):
        runtime.check_runtime()


def test_old_or_missing_host_stack_is_not_automatically_upgraded(monkeypatch):
    monkeypatch.setattr(runtime.importlib.metadata,"version",lambda name:"1.0.0")
    with pytest.raises(RuntimeError,match="older than required"):
        runtime.check_minimum_versions()
    def absent(name): raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(runtime.importlib.metadata,"version",absent)
    with pytest.raises(RuntimeError,match="current standard Colab"):
        runtime.check_minimum_versions()


def test_failed_rerun_blocks_stale_downstream_results():
    state=runtime.CellState({"demo":"Chapter 0","pnr":"Chapter 6"})
    with state.running("demo","Chapter 0"): pass
    with state.running("pnr","Chapter 6",requires=["demo"]): pass
    with pytest.raises(ValueError):
        with state.running("demo","Chapter 0"):
            raise ValueError("SPICE failed after setting some globals")
    assert not state.completed
    with pytest.raises(RuntimeError,match="first run Chapter 0 successfully"):
        with state.running("pnr","Chapter 6",requires=["demo"]):
            pytest.fail("must not touch stale lay/demo globals")


def test_every_chapter_cell_without_setup_fails_with_recovery_not_nameerror():
    document=json.loads((ROOT/"notebook/tritflow_tr1um.ipynb").read_text())
    code=[c for c in document["cells"] if c["cell_type"] == "code"]
    for cell in code[1:]:
        with pytest.raises(RuntimeError,match="setup.*(successfully|restart)"):
            exec(compile(cell["source"],cell["id"],"exec"),{})


def test_physical_views_reject_partial_opening_globals_before_any_work():
    document=json.loads((ROOT/"notebook/tritflow_tr1um.ipynb").read_text())
    code=[c for c in document["cells"] if c["cell_type"] == "code"]
    titles={c["id"]:c.get("metadata",{}).get("tritflow",{}).get("title",c["id"]) for c in code}
    views=[c for c in code if 'Full physical statistics' in c["source"] or 'pre = cache.run("adder2-pre"' in c["source"]]
    assert len(views) == 2
    for cell in views:
        namespace={"_tf_cells":runtime.CellState(titles),"lay":object(),"demo":{"partial":True}}
        with pytest.raises(RuntimeError,match="first run Chapter 0"):
            exec(compile(cell["source"],cell["id"],"exec"),namespace)
