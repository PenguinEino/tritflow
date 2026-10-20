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
import time
from hashlib import sha256
from pathlib import Path


SETUP_SCHEMA = "3"
MINIMUM_VERSIONS = {"numpy":"1.26.4", "scipy":"1.11.4", "matplotlib":"3.8.4", "plotly":"5.24.1"}
RESTART = ("Restart the runtime once (Runtime → Restart session), then run setup and imports again. "
           "Do not reinstall NumPy/SciPy in the live kernel. If this persists, disconnect/delete "
           "the old runtime and connect a fresh one.")


def setup_identity(root):
    """Invalidate a setup marker when a consumed lock or installer changes."""
    digest = sha256()
    for name in ("setup_pins.json", "requirements-colab.txt", "native_runtime.py",
                 "ubuntu-24.04-lock.json", "setup_colab.py", "font_runtime.py", "fonts-lock.json"):
        digest.update((Path(root)/"notebook"/name).read_bytes())
    return digest.hexdigest()


def _release(version):
    match = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", version)
    if not match:
        raise RuntimeError(f"Cannot interpret installed package version {version!r}")
    return tuple(int(value or 0) for value in match.groups())


def check_minimum_versions(packages=None):
    """Inspect installed metadata without importing or changing any package."""
    versions = {}
    for name, minimum in MINIMUM_VERSIONS.items():
        if packages is not None and name not in packages:
            continue
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
        if os.environ.get('TRITFLOW_FONT_ROOT'):
            from font_runtime import register_fonts
            register_fonts(os.environ['TRITFLOW_FONT_ROOT'])
        numpy.testing.assert_allclose(linalg.solve([[2.0]], [4.0]), [2.0])
    except Exception as error:
        raise RuntimeError(f"Scientific Python import/BLAS check failed: {type(error).__name__}: {error}. "
                           + RESTART) from error
    print("Python: " + ", ".join(f"{k} {v}" for k,v in versions.items()))
    return versions


def step(message):
    """Say what the notebook is doing now, so a long cell is never silent."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def print_tool_versions():
    """Print the actual executables used for PDK decks and circuit simulation."""
    from tritflow.sim.tools import ngspice_binary
    versions = {}
    for name, binary in (("KLayout",os.environ.get("KLAYOUT_BINARY") or shutil.which("klayout")),
                         ("ngspice",ngspice_binary())):
        if not binary:
            raise RuntimeError(f"{name} is missing. Run the setup cell successfully first.")
        result = subprocess.run([str(binary), "-v"],capture_output=True,text=True,check=True,timeout=15)
        versions[name] = (result.stdout+result.stderr).strip()
        # ngspice prints a banner; its "** ngspice-NN" line names the release.
        release = next((line.strip("* ").strip() for line in versions[name].splitlines()
                        if line.strip("* ").lower().startswith(name.lower())), versions[name].splitlines()[0])
        print(f"{name}: {release} ({binary})")
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
        started = time.monotonic()
        step(f"▶ {title}")
        yield
        self.completed.add(name)
        step(f"✓ {title} ({time.monotonic()-started:.1f} s)")
