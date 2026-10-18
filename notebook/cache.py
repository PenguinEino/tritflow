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
import time

import numpy as np


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def source_fingerprint(root, pdk):
    """Hash consumed code/views/publication identity, using relative filenames.

    Pin access, obstructions and free tracks can change without changing a
    transistor or GDS byte. They and the manifest/publication barrier therefore
    participate explicitly. Relocating an identical checkout/PDK is harmless.
    """
    root, pdk = Path(root), Path(pdk)
    # Scope is the notebook's runtime API, not independent library generators,
    # STA, chip packaging or campaign publication tools. Their published data
    # is still hashed below. Optional signoff has its own PNR fingerprint.
    def consumed(path):
        relative = path.relative_to(root/"tritflow")
        package, name = relative.parts[0], relative.name
        if package == "sta" or name == "__main__.py":
            return False
        if package == "cells":
            return name in {"__init__.py", "circuits.py"}  # sizing ID/dimension table
        if package == "pnr" and (name.startswith(("chip", "signoff")) or name == "batch.py"):
            return False
        return not (package == "sim" and name in {"diagnose.py", "publication.py", "corners.py"})
    code = [p for p in root.glob("tritflow/**/*.py") if consumed(p)]
    files = [*code, *root.glob("cells/out/**/*.gds"),
             *root.glob("cells/out/**/*.spice"), *root.glob("cells/out/**/*.char.json"),
             *root.glob("cells/out/**/*.abstract.json"), *root.glob("cells/out/*.json"),
             *root.glob("cells/out/**/*.pcells.json"),
             root/"cells/template.json", root/"notebook/setup_pins.json",
             root/"notebook/tritflow_tr1um.ipynb", *root.glob("notebook/*.py"),
             *root.glob("examples/*.tv"), *root.glob("examples/curated.py")]
    pdk_files = [p for folder in ["libs.tech/klayout/tech/drc", "libs.tech/klayout/tech/lvs",
                                "libs.tech/spice/models"] for p in (pdk/folder).rglob("*") if p.is_file()]
    digest = sha256()
    for origin, base, paths in (("source", root, files), ("pdk", pdk, pdk_files)):
        for path in sorted(set(paths)):
            digest.update(f"{origin}/{path.relative_to(base)}".encode()+b"\0")
            raw = path.read_bytes()
            digest.update(len(raw).to_bytes(8, "big"))
            digest.update(raw)
    return digest.hexdigest()


def runtime_fingerprint(root, pdk):
    """Local reuse additionally requires the same interpreter/packages/binaries."""
    digest = sha256((source_fingerprint(root,pdk)+sys.version).encode())
    for package in ["numpy", "scipy", "klayout", "plotly", "lark"]:
        digest.update(f"{package}={importlib.metadata.version(package)}".encode())
    for binary in [shutil.which("ngspice"), os.environ.get("KLAYOUT_BINARY")
                   or shutil.which("klayout") or Path.home()/"bin/klayout/klayout"]:
        if binary and Path(binary).is_file():
            digest.update(Path(binary).read_bytes())
            run = subprocess.run([str(binary), "-v"], capture_output=True, text=True, timeout=15)
            digest.update((run.stdout+run.stderr).encode())
    return digest.hexdigest()


def _json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot cache {type(value).__name__}")


def restore_result(value):
    """Restore native simulation arrays even inside a pre/post experiment pair."""
    if isinstance(value, list):
        return [restore_result(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: restore_result(item) for key, item in value.items()}
    for key in ("waveforms", "data"):
        if key in result and isinstance(result[key], dict):
            result[key] = {name: np.asarray(array) for name, array in result[key].items()}
    if "stimulus" in result:
        result["stimulus"]["vectors"] = [tuple(v) for v in result["stimulus"]["vectors"]]
    return result


class Cache:
    """Cache native dict results only when context/options/artifact hashes agree."""

    def __init__(self, directory, fingerprint, *, force=False):
        self.directory = Path(directory)
        self.fingerprint = fingerprint
        self.events = []
        self.timings = []
        self.force = force

    def run(self, name, options, producer, *, artifacts=()):
        if not name or Path(name).name != name:
            raise ValueError("cache name must be one filename component")
        key = sha256(json.dumps([self.fingerprint, options], sort_keys=True, default=_json).encode()).hexdigest()
        path = self.directory/f"{name}.json.gz"
        started = time.perf_counter()
        if path.is_file() and not self.force:
            with gzip.open(path, "rt") as stream:
                saved = json.load(stream)
            if saved["key"] == key and all(Path(p).is_file() and file_hash(p) == h
                                           for p, h in saved["artifacts"].items()):
                self.events.append((name, "hit"))
                self.timings.append({"stage":name, "state":"hit", "elapsed_s":time.perf_counter()-started})
                print(f"Cache hit: {name}")
                return restore_result(saved["result"])
        print(f"Running: {name}")
        result = producer()
        paths = artifacts(result) if callable(artifacts) else artifacts
        hashes = {str(Path(p).resolve()): file_hash(p) for p in paths}
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        with gzip.open(temporary, "wt") as stream:
            json.dump({"key": key, "fingerprint":self.fingerprint, "options":options,
                       "result": result, "artifacts": hashes}, stream, default=_json, allow_nan=False)
        temporary.replace(path)
        self.events.append((name, "run"))
        self.timings.append({"stage":name, "state":"run", "elapsed_s":time.perf_counter()-started})
        return result
