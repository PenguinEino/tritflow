"""Read circuit results from the executed notebook kernel, without rerunning EDA."""

# This self-contained cell is also safe to rerun from the submitted notebook.
# It does not depend on the builder being present in the pinned runtime.
CAPTURE_CODE = r'''
import importlib.metadata as _metadata
import json as _json
import platform as _platform
import subprocess as _subprocess
from IPython.display import display as _display

def _submission_evidence(namespace):
    """Record logic coverage, routed dimensions and nominal analog checks."""
    result = {"schema_version": 1, "designs": {}}
    for name, label in (("net", "first"), ("full_add_rtl", "full_add"),
                        ("mul", "mul"), ("dot4", "dot4")):
        circuit = namespace.get(name)
        if circuit is None:
            continue
        row = {"report": circuit.report(), "equivalence": dict(circuit.equivalence)}
        layout = namespace.get("dot4_layout" if name == "dot4" else "lay") if name in ("net", "dot4") else None
        if layout is not None:
            row["layout"] = dict(layout.stats)
            for key, variable in (("drc", "dot4_drc" if name == "dot4" else "drc"),
                                  ("lvs", "dot4_lvs" if name == "dot4" else "lvs")):
                check = namespace.get(variable)
                if check is not None:
                    row[key] = {k: check[k] for k in
                                ("clean", "violations", "matched", "strict_ports", "scope")
                                if k in check}
            post = namespace.get("dot4_post" if name == "dot4" else "post")
            if post is not None:
                row["measurements"] = post["measurements"]
                row["stimulus"] = post["stimulus"]
        if name == "dot4" and "dot4_timing" in namespace:
            row["sta_arrival_s"] = dict(namespace["dot4_timing"].arrival)
        result["designs"][label] = row
    # An optional future chapter can provide an explicit summary. Its rendered
    # tables are independently retained by the builder even without this key.
    if "submission_results" in namespace:
        result["evaluation"] = namespace["submission_results"]
    result["runtime"] = {"python": _platform.python_version(), "packages": {}}
    for package in ("numpy", "scipy", "plotly", "klayout", "lark", "matplotlib"):
        result["runtime"]["packages"][package] = _metadata.version(package)
    result["runtime"]["tools"] = namespace.get("tools", {})
    from tritflow import PDK_ROOT as _pdk_root
    from tritflow.sim.provenance import pdk_provenance as _pdk_provenance
    result["pdk"] = _pdk_provenance(_pdk_root)
    result["source_ref"] = namespace.get("SOURCE_REF")
    result["runtime_commit_at_end"] = _subprocess.check_output(
        ["git", "-C", str(namespace["ROOT"]), "rev-parse", "HEAD"], text=True).strip()
    result["runtime_commit"] = namespace.get("_submission_runtime_commit_at_start", result["runtime_commit_at_end"])
    result["tracked_working_changes_at_execution"] = _subprocess.check_output(
        ["git", "-C", str(namespace["ROOT"]), "diff", "--name-only", "HEAD"], text=True).splitlines()
    result["untracked_runtime_sources_at_execution"] = _subprocess.check_output(
        ["git", "-C", str(namespace["ROOT"]), "ls-files", "--others", "--exclude-standard",
         "tritflow", "notebook", "cells", "examples", "results"], text=True).splitlines()
    # Reject NaN/Infinity: a failed measurement must never become a result.
    return _json.loads(_json.dumps(result, allow_nan=False, default=str))

_display({"application/json": _submission_evidence(globals()),
          "text/plain": "Submission evidence: executed logic, layout, verification and timing results."}, raw=True)
'''.strip()


SETUP_CODE = r'''
import os as _os
import shutil as _shutil
import subprocess as _subprocess
from pathlib import Path as _Path
import plotly.io as _pio
_submission_runtime_commit_at_start = _subprocess.check_output(
    ["git", "-C", _os.environ["TRITFLOW_ROOT"], "rev-parse", "HEAD"], text=True).strip()
_pio.renderers.default = "png"
_pio.defaults.default_width = 1100
_pio.defaults.default_scale = 1
_pio.defaults.mathjax = None
# The source-level sizing helper otherwise writes disposable rows into cells/.
# Copy its published read-only records and redirect only its cache location.
import tritflow.sim.sizing as _sizing
_cache = _Path(_os.environ["TRITFLOW_SUBMISSION_WORKDIR"])/"sizing"
_cache.mkdir(parents=True, exist_ok=True)
for _record in _sizing.CACHE.glob("*.json"):
    _shutil.copyfile(_record, _cache/_record.name)
_sizing.CACHE = _cache
'''.strip()
