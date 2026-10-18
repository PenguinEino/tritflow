"""Portable recorded experiments, with native evidence and consumed-input hashes.

Unlike a local execution cache, a publication is explicitly a recorded run on
its stated tool versions. Reading it never claims that local tools ran again.
Only completed, current local Cache results may be published. A single small
ZIP keeps native DRC/LVS/GDS evidence alongside compressed waveform/measurement
JSON; no ignored build tree is needed to read or validate it.
"""

from datetime import datetime, timezone
from hashlib import sha256
import gzip
import importlib.metadata
import json
from pathlib import Path
import platform
import os
import shutil
import subprocess
import zipfile

from cache import source_fingerprint, source_manifest, runtime_fingerprint, restore_result
from experiments import assert_experiment


DESIGNS = ("adder4","full_add","mac1","mul1")


def options_hash(options):
    return sha256(json.dumps(options,sort_keys=True).encode()).hexdigest()


def _relocate(value, replacements):
    if isinstance(value,dict):
        return {k:_relocate(v,replacements) for k,v in value.items()}
    if isinstance(value,list):
        return [_relocate(v,replacements) for v in value]
    if isinstance(value,str):
        for old,new in replacements.items(): value = value.replace(old,new)
    return value


def publish_campaign(cache_dir, destination, root, pdk, *, designs=DESIGNS):
    """Publish only current verified local runs; never rewrite their native files."""
    cache_dir, destination, root, pdk = map(Path,(cache_dir,destination,root,pdk))
    with gzip.open(cache_dir/f"four-{designs[0]}.json.gz","rt") as stream:
        first=json.load(stream)
    inputs=first.get("sources")
    if not inputs or source_manifest(root,pdk,names=inputs) != inputs:
        raise ValueError("capture input manifest is missing or changed; recompute before publishing")
    sources = source_fingerprint(root,pdk,names=inputs)
    runtime = runtime_fingerprint(root,pdk,names=inputs)
    manifest = {"schema_version":1,"created_utc":datetime.now(timezone.utc).isoformat(),
        "source_fingerprint":sources,"source_files":inputs,"recorded_runtime_fingerprint":runtime,
        "tools":{p:importlib.metadata.version(p) for p in ("numpy","scipy","klayout","lark")},
        "python":platform.python_version(),"records":{},"files":{},
        "scope":"Recorded PNR/DRC/strict-LVS and identical extracted devices ± wire C; not new local checks."}
    binary=os.environ.get("KLAYOUT_BINARY") or shutil.which("klayout") or Path.home()/"bin/klayout/klayout"
    manifest["tools"].update(
        klayout_binary=subprocess.check_output([str(binary),"-v"],text=True).strip(),
        ngspice=subprocess.check_output(["ngspice","-v"],text=True).strip())
    data = {}
    for name in designs:
        with gzip.open(cache_dir/f"four-{name}.json.gz","rt") as stream: saved=json.load(stream)
        if saved.get("fingerprint") != runtime or saved.get("sources") != inputs:
            raise ValueError(f"{name}: capture context changed; recompute before publishing")
        key=sha256(json.dumps([runtime,saved["options"]],sort_keys=True).encode()).hexdigest()
        if saved["key"] != key:
            raise ValueError(f"{name}: recorded options differ from the execution cache key")
        result = saved["result"]
        assert_experiment(restore_result(result))
        directory = Path(result["lvs"]["report"]).parent.parent
        for original,expected in saved["artifacts"].items():
            path=Path(original)
            if not path.is_file() or sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError(f"{name}: native capture artifact changed: {path}")
        # Keep full native proof, including reference SPICE, normalized input
        # snapshot and tool log. Waveforms are already in the result JSON.
        paths = {Path(p) for p in saved["artifacts"]}
        paths.update(p for p in (directory/"lvs").rglob("*") if p.is_file())
        for path in sorted(paths):
            if not path.is_relative_to(directory):
                raise ValueError(f"evidence outside experiment directory: {path}")
            data[f"{name}/{path.relative_to(directory)}"] = path.read_bytes()
        record = f"{name}/result.json"
        replacements={str(directory):f"recorded:{name}",str(root):"$TRITFLOW_ROOT",str(pdk):"$TR1UM_PDK"}
        data[record] = (json.dumps(_relocate(result,replacements),allow_nan=False)+"\n").encode()
        manifest["records"][name] = {"result":record,"options_sha256":options_hash(saved["options"])}
    if runtime_fingerprint(root,pdk,names=inputs) != runtime:
        raise RuntimeError("source/tool publication changed during campaign export")
    manifest["files"] = {name:sha256(raw).hexdigest() for name,raw in data.items()}
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix(".tmp")
    with zipfile.ZipFile(temporary,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,raw in sorted(data.items()): archive.writestr(name,raw)
        archive.writestr("manifest.json",json.dumps(manifest,indent=2)+"\n")
    temporary.replace(destination)
    return manifest


class RecordedCampaign:
    """Read checked-in evidence; return None for a stale source/options revision.

    Native bytes are hashed before any flags are displayed. Tool differences
    are disclosed by the recorded manifest, never adopted as a local cache key.
    No archive member is extracted, so paths inside reports are provenance only.
    """

    def __init__(self, path, root, pdk, *, enabled=True):
        self.path=Path(path)
        self.manifest=None
        self.records={}
        if not enabled or not self.path.is_file(): return
        with zipfile.ZipFile(self.path) as archive:
            manifest=json.loads(archive.read("manifest.json"))
            inputs=manifest.get("source_files")
            if not inputs: return
            try:
                if source_manifest(root,pdk,names=inputs) != inputs: return
            except FileNotFoundError:
                return
            if set(archive.namelist()) != {"manifest.json",*manifest["files"]}:
                raise ValueError("recorded campaign member list differs from its manifest")
            for name,expected in manifest["files"].items():
                if sha256(archive.read(name)).hexdigest() != expected:
                    raise ValueError(f"recorded native evidence hash mismatch: {name}")
            self.records={name:json.loads(archive.read(row["result"])) for name,row in manifest["records"].items()}
            self.manifest=manifest

    def get(self, name, options):
        if self.manifest is None or name not in self.records: return None
        if self.manifest["records"][name]["options_sha256"] != options_hash(options): return None
        result=restore_result(self.records[name])
        assert_experiment(result)
        return result


def main():
    import argparse
    from tritflow import ROOT, PDK_ROOT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache",type=Path,help="cache from a successful full fresh notebook run")
    parser.add_argument("--output",type=Path,default=ROOT/"notebook/assets/four_designs.zip")
    args=parser.parse_args()
    manifest=publish_campaign(args.cache,args.output,ROOT,PDK_ROOT)
    print(json.dumps({"archive":str(args.output),"bytes":args.output.stat().st_size,
                     "records":list(manifest["records"]),"native_files":len(manifest["files"])},indent=2))


if __name__ == "__main__": main()
