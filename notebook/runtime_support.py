"""Colab compatibility and explicit notebook-cell prerequisites.

The host owns its scientific Python stack. Replacing an imported NumPy wheel
can leave Python modules and native extensions from different releases alive
in one kernel; importing more modules cannot repair that state.
"""

from contextlib import contextmanager
import importlib
import importlib.metadata
import os
import re
import shutil
import subprocess
import sys


SETUP_SCHEMA = "2"
MINIMUM_VERSIONS = {"numpy":"1.26", "scipy":"1.11", "matplotlib":"3.8", "plotly":"5.18"}
RESTART = ("Restart the runtime once (Runtime → Restart session), then run setup and imports again. "
           "Do not reinstall NumPy/SciPy in the live kernel. If this persists, disconnect/delete "
           "the old runtime and connect a fresh one.")


def _release(version):
    match = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", version)
    if not match:
        raise RuntimeError(f"Cannot interpret installed package version {version!r}")
    return tuple(int(value or 0) for value in match.groups())


def check_minimum_versions():
    """Inspect installed metadata without importing or changing any package."""
    versions = {}
    for name, minimum in MINIMUM_VERSIONS.items():
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise RuntimeError(f"{name}>={minimum} is required. Use a current standard Colab runtime.") from error
        if _release(versions[name]) < _release(minimum):
            raise RuntimeError(f"{name} {versions[name]} is older than required {minimum}. "
                               "Use a current standard Colab runtime; do not upgrade an imported scientific stack.")
    return versions


def check_runtime():
    """Reject mixed live/disk releases; smoke-test the formerly failing imports."""
    versions = check_minimum_versions()
    for name in (*versions, "klayout", "lark"):
        loaded = getattr(sys.modules.get(name), "__version__", None)
        if loaded is not None:
            installed = importlib.metadata.version(name)
            if loaded != installed:
                raise RuntimeError(f"{name} {loaded} is loaded, but {installed} is installed. {RESTART}")
    try:
        numpy = importlib.import_module("numpy")
        importlib.import_module("numpy.testing")
        linalg = importlib.import_module("scipy.linalg")
        importlib.import_module("matplotlib")
        importlib.import_module("plotly")
        numpy.testing.assert_allclose(linalg.solve([[2.0]], [4.0]), [2.0])
    except Exception as error:
        raise RuntimeError(f"Scientific Python import/BLAS check failed: {type(error).__name__}: {error}. "
                           + RESTART) from error
    print("Scientific Python (host versions preserved): " + ", ".join(f"{k}={v}" for k,v in versions.items()))
    return versions


def print_tool_versions():
    """Print the actual executables used for PDK decks and circuit simulation."""
    versions = {}
    for name, binary in (("KLayout",os.environ.get("KLAYOUT_BINARY") or shutil.which("klayout")),
                         ("ngspice",shutil.which("ngspice"))):
        if not binary:
            raise RuntimeError(f"{name} is missing. Run the setup cell successfully first.")
        result = subprocess.run([str(binary), "-v"],capture_output=True,text=True,check=True,timeout=15)
        versions[name] = (result.stdout+result.stderr).strip()
        print(f"{name} executable: {binary}\n{versions[name]}")
    return versions


class CellState:
    """A failed/rerun prerequisite invalidates downstream completion markers."""

    def __init__(self, titles=None):
        self.completed = set()
        self.dependencies = {}
        self.titles = dict(titles or {})

    @contextmanager
    def running(self, name, title, *, requires=()):
        self.dependencies[name] = set(requires)
        self.titles[name] = title
        invalid = {name}
        while True:
            affected = {cell for cell,deps in self.dependencies.items() if deps & invalid} - invalid
            if not affected:
                break
            invalid |= affected
        self.completed -= invalid
        missing = set(requires) - self.completed
        if missing:
            labels = ", ".join(self.titles.get(item,item) for item in sorted(missing))
            raise RuntimeError(f"{title}: first run {labels} successfully, then rerun this cell. "
                               "Results from a failed or partially rerun cell cannot be used.")
        yield
        self.completed.add(name)
