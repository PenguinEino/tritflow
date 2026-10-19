"""Content-keyed JSON caches for notebook stages, without pickle or stale flags."""

from __future__ import annotations

from hashlib import sha256
from tritflow.sim.tools import ngspice_binary

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


def source_manifest(root, pdk, *, names=None):
    """Content hashes of cached physical/electrical experiment inputs.

    A recorded filename set prevents an uncalled module added by another stream
    from invalidating a completed experiment. Changed/deleted inputs still fail.
    Published data readers and plotting run afresh; the GDS raster has its own
    renderer key. Cell pin access/obstructions and publication identity are
    explicit inputs, independent of whether GDS/SPICE bytes also changed.
    """
    root, pdk = Path(root), Path(pdk)
    if names is None:
        def consumed(path):
            relative = path.relative_to(root/"tritflow")
            package, name = relative.parts[0], relative.name
            if len(relative.parts)>1 and package not in {"hdl","synth","pnr","sim","extract"}:
                return False
            if name == "__main__.py": return False
            if package == "pnr" and (name.startswith(("chip","signoff")) or name == "batch.py"):
                return False
            return not (package == "sim" and name in {
                "diagnose.py","publication.py","corners.py","sizing.py","scaling.py","load_sweep.py"})
        files = [p for p in root.glob("tritflow/**/*.py") if consumed(p)]
        files += [root/"cells/template.json", *root.glob("cells/out/*.json"),root/"cells/out/all.spice",
                  root/"notebook/setup_pins.json",root/"notebook/tritflow_tr1um.ipynb",
                  *root.glob("notebook/*.py"),*root.glob("examples/*.tv"),*root.glob("examples/curated.py")]
        library=json.loads((root/"cells/out/library.json").read_text())
        entries=library.get("cells",library) if isinstance(library,dict) else library
        cells=list(entries) if isinstance(entries,dict) else [e if isinstance(e,str) else e["name"] for e in entries]
        for cell in cells:
            files += [p for suffix in ("gds","spice","ext.spice","abstract.json","char.json","pcells.json")
                      if (p:=root/f"cells/out/{cell}/{cell}.{suffix}").is_file()]
        models=[p for folder in ("libs.tech/klayout/tech/drc","libs.tech/klayout/tech/lvs","libs.tech/spice/models")
                for p in (pdk/folder).rglob("*") if p.is_file()]
        models += list((pdk/"openIP62/IP62/Technology/doc").glob("*.pdf"))
        names=[f"source/{p.relative_to(root)}" for p in files]+[f"pdk/{p.relative_to(pdk)}" for p in models]
    result={}
    for label in sorted(set(names)):
        origin,relative=label.split("/",1)
        if origin not in {"source","pdk"} or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"invalid recorded source path: {label}")
        base=root if origin=="source" else pdk
        path=base/relative
        if not path.resolve().is_relative_to(base.resolve()):
            raise ValueError(f"recorded source escapes its root: {label}")
        result[label]=notebook_hash(path) if path.suffix == ".ipynb" else file_hash(path)
    return result


def notebook_hash(path):
    """Notebook identity without its own source pin.

    The released notebook names the implementation commit it clones, which is
    only known after that commit exists; the pin line must not invalidate the
    experiments recorded for that very commit.
    """
    import re
    text = re.sub(r'SOURCE_REF = os\.environ\.get\(\\"TRITFLOW_REF\\", \\"[^"\\]*\\"\)',
                  'SOURCE_REF = <pinned>', Path(path).read_text())
    return sha256(text.encode()).hexdigest()


def source_fingerprint(root, pdk, *, names=None):
    return sha256(json.dumps(source_manifest(root,pdk,names=names),sort_keys=True).encode()).hexdigest()


def runtime_fingerprint(root, pdk, *, names=None):
    """Local reuse additionally requires the same interpreter/packages/binaries."""
    digest = sha256((source_fingerprint(root,pdk,names=names)+sys.version).encode())
    for package in ["numpy", "scipy", "klayout", "plotly", "lark"]:
        digest.update(f"{package}={importlib.metadata.version(package)}".encode())
    from tritflow.sim.tools import simulator_identity
    digest.update(json.dumps(simulator_identity(),sort_keys=True).encode())
    for binary in [ngspice_binary(), os.environ.get("KLAYOUT_BINARY")
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

    def __init__(self, directory, fingerprint, *, force=False, sources=None):
        self.directory = Path(directory)
        self.fingerprint = fingerprint
        self.events = []
        self.timings = []
        self.force = force
        self.sources = sources

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
                       "result": result, "artifacts": hashes, "sources":self.sources}, stream, default=_json, allow_nan=False)
        temporary.replace(path)
        self.events.append((name, "run"))
        self.timings.append({"stage":name, "state":"run", "elapsed_s":time.perf_counter()-started})
        return result
