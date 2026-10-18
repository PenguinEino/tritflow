"""Content-keyed JSON caches for notebook stages, without pickle or stale flags."""

from __future__ import annotations

from hashlib import sha256
import gzip
import json
from pathlib import Path
import sys
import importlib.metadata
import shutil
import subprocess
import os

import numpy as np


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def runtime_fingerprint(root, pdk):
    """Include code, physical/electrical library views, PDK decks and models."""
    root, pdk = Path(root), Path(pdk)
    files = [*root.glob("tritflow/**/*.py"), *root.glob("cells/out/**/*.gds"),
             *root.glob("cells/out/**/*.spice"), *root.glob("cells/out/**/*.char.json"),
             root/"cells/template.json", root/"notebook/setup_pins.json",
             root/"notebook/tritflow_tr1um.ipynb", *root.glob("notebook/*.py"),
             *root.glob("examples/*.tv"), *root.glob("examples/*.py")]
    files += [p for folder in ["libs.tech/klayout/tech/drc", "libs.tech/klayout/tech/lvs",
                              "libs.tech/spice/models"] for p in (pdk/folder).rglob("*") if p.is_file()]
    digest = sha256(sys.version.encode())
    for package in ["numpy", "scipy", "klayout", "plotly", "lark"]:
        digest.update(f"{package}={importlib.metadata.version(package)}".encode())
    for binary in [shutil.which("ngspice"), os.environ.get("KLAYOUT_BINARY")
                   or shutil.which("klayout") or Path.home()/"bin/klayout/klayout"]:
        if binary and Path(binary).is_file():
            digest.update(Path(binary).read_bytes())
            run = subprocess.run([str(binary), "-v"], capture_output=True, text=True, timeout=15)
            digest.update((run.stdout+run.stderr).encode())
    for path in sorted(files):
        digest.update(str(path).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot cache {type(value).__name__}")


def _restore(value):
    """Restore native simulation arrays even inside a pre/post experiment pair."""
    if isinstance(value, list):
        return [_restore(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: _restore(item) for key, item in value.items()}
    for key in ("waveforms", "data"):
        if key in result and isinstance(result[key], dict):
            result[key] = {name: np.asarray(array) for name, array in result[key].items()}
    if "stimulus" in result:
        result["stimulus"]["vectors"] = [tuple(v) for v in result["stimulus"]["vectors"]]
    return result


class Cache:
    """Cache native dict results only when context/options/artifact hashes agree."""

    def __init__(self, directory, fingerprint):
        self.directory = Path(directory)
        self.fingerprint = fingerprint
        self.events = []

    def run(self, name, options, producer, *, artifacts=()):
        if not name or Path(name).name != name:
            raise ValueError("cache name must be one filename component")
        key = sha256(json.dumps([self.fingerprint, options], sort_keys=True, default=_json).encode()).hexdigest()
        path = self.directory/f"{name}.json.gz"
        if path.is_file():
            with gzip.open(path, "rt") as stream:
                saved = json.load(stream)
            if saved["key"] == key and all(Path(p).is_file() and file_hash(p) == h
                                           for p, h in saved["artifacts"].items()):
                self.events.append((name, "hit"))
                print(f"Cache hit: {name}")
                return _restore(saved["result"])
        print(f"Running: {name}")
        result = producer()
        paths = artifacts(result) if callable(artifacts) else artifacts
        hashes = {str(Path(p).resolve()): file_hash(p) for p in paths}
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        with gzip.open(temporary, "wt") as stream:
            json.dump({"key": key, "result": result, "artifacts": hashes}, stream, default=_json, allow_nan=False)
        temporary.replace(path)
        self.events.append((name, "run"))
        return result
