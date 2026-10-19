"""Resolve the qualified circuit simulator independently of the shell PATH."""

from functools import lru_cache
import json
import os
from pathlib import Path
import re
import subprocess


NGSPICE_VERSION = "42"


@lru_cache(maxsize=8)
def _checked(binary, size, modified):
    result = subprocess.run([binary, "-v"], capture_output=True, text=True,
                            check=True, timeout=15)
    version = result.stdout + result.stderr
    if not re.search(r"\bngspice-42\s*:", version):
        raise RuntimeError(f"TritFlow requires Ubuntu ngspice-42 (42+ds-3build1), but {binary} reports:\n"
                           f"{version.strip()}\nRun notebook/install_ngspice.py; set NGSPICE_BINARY "
                           "to its official package wrapper. Other releases are unqualified.")
    return binary


def ngspice_binary(explicit=None):
    """Use an explicit path, setup's runtime.json, or the official local package.

    An ordinary PATH ngspice may be a different release with different DC
    source or convergence behavior. It must never silently supply evidence.
    """
    selected = explicit or os.environ.get("NGSPICE_BINARY")
    if not selected:
        config = Path(__file__).resolve().parents[2]/"notebook/runtime.json"
        if config.is_file():
            selected = json.loads(config.read_text()).get("NGSPICE_BINARY")
    binary = Path(selected or Path.home()/".local/opt/tritflow-ubuntu-24.04/bin/ngspice").expanduser()
    if not binary.is_absolute() or not binary.is_file():
        raise RuntimeError(f"Pinned Ubuntu ngspice-42 is missing at {binary}. Run "
                           "python3 notebook/install_ngspice.py, or run the Colab setup cell.")
    info = binary.stat()
    return _checked(str(binary.resolve()), info.st_size, info.st_mtime_ns)


def simulator_identity():
    """Include the actual binary in electrical cache keys and evidence records."""
    from hashlib import sha256
    binary = Path(ngspice_binary())
    payload = os.environ.get("NGSPICE_PAYLOAD")
    if not payload:
        config = Path(__file__).resolve().parents[2]/"notebook/runtime.json"
        if config.is_file():
            payload = json.loads(config.read_text()).get("NGSPICE_PAYLOAD")
    if not payload:
        local = Path.home()/".local/opt/tritflow-ubuntu-24.04/ngspice.json"
        if local.is_file() and json.loads(local.read_text()).get("NGSPICE_BINARY") == str(binary):
            payload = json.loads(local.read_text())["NGSPICE_PAYLOAD"]
    result = {"version": NGSPICE_VERSION,
              "binary_sha256": sha256(Path(payload or binary).read_bytes()).hexdigest()}
    if payload:
        result["runtime_sha256"] = sha256(binary.read_bytes()).hexdigest()
    return result
