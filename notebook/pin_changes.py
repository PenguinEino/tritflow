"""Compare reported scientific numbers with the committed pre-migration values.

Adaptive transient arrays cannot be compared by sample index after a solver
change. Compare their reported endpoint/settling metrics, every timing arc and
DC sizing curve instead. Run times, hashes and producer metadata are excluded.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import zipfile


IGNORE = {"waveforms", "created_utc", "pdk_provenance", "provenance", "source_generation",
          "generation", "code_sha256", "measurement_code", "analysis_sha256", "model_sha256",
          "input_sha256", "sources_sha256", "artifacts_sha256", "native_sha256", "repository_sha256",
          "presentation_sha256", "timings_s", "cpu_times_s", "timings", "runtime_s", "elapsed_s"}


def scalar_leaves(value, path):
    """Report newly added or removed measured numbers without inventing a delta."""
    if isinstance(value, dict):
        for key, item in sorted(value.items()):
            if key not in IGNORE:
                yield from scalar_leaves(item, path+'/'+str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from scalar_leaves(item, path+'/'+str(index))
    elif isinstance(value, (int, float, bool)):
        yield path, value


def differences(before, after, path=""):
    """Keep every changed measured scalar, including pass/fail and null delays."""
    if isinstance(before,dict) and isinstance(after,dict):
        for key in sorted(before.keys() & after.keys()):
            if key not in IGNORE:
                yield from differences(before[key],after[key],path+"/"+str(key))
        for key in sorted((before.keys() ^ after.keys()) - IGNORE):
            added = key in after
            for label, value in scalar_leaves(after[key] if added else before[key],path+'/'+str(key)):
                yield {"path":label,"before":None if added else value,
                       "after":value if added else None,"delta":None,
                       "kind":"added" if added else "removed"}
    elif isinstance(before,list) and isinstance(after,list):
        if len(before) != len(after):
            yield {"path":path+"/length","before":len(before),"after":len(after)}
        for index,(a,b) in enumerate(zip(before,after)):
            yield from differences(a,b,path+"/"+str(index))
        for index in range(min(len(before),len(after)),max(len(before),len(after))):
            added = index < len(after)
            for label, value in scalar_leaves(after[index] if added else before[index],path+'/'+str(index)):
                yield {"path":label,"before":None if added else value,
                       "after":value if added else None,"delta":None,
                       "kind":"added" if added else "removed"}
    elif before != after and (isinstance(before,(int,float,bool)) or isinstance(after,(int,float,bool))):
        numeric = (type(before) in (int,float) and type(after) in (int,float))
        yield {"path":path,"before":before,"after":after,
               "delta":after-before if numeric else None}


def compare(root, baseline, destination):
    from tritflow.sim.tools import simulator_identity
    root = Path(root)
    baseline = Path(baseline)
    old = json.loads(baseline.read_text())
    commit_file = baseline.with_name('baseline_commit.txt')
    revision = (commit_file.read_text().strip() if commit_file.is_file() else
                subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip())
    records, missing = {}, []
    for name,before in old.items():
        if name.startswith("notebook/assets/four_designs.zip:"):
            design = name.rsplit(":",1)[-1]
            if design == "manifest":
                continue
            with zipfile.ZipFile(root/'notebook/assets/four_designs.zip') as archive:
                after = json.loads(archive.read(design+'/result.json'))
        else:
            path = root/name
            if not path.is_file():
                missing.append(name)
                continue
            after = json.loads(path.read_text())
        delta = list(differences(before,after))
        if delta:
            records[name] = delta
    published = subprocess.check_output(['git','-C',str(root),'ls-files','--cached','--others',
        '--exclude-standard','cells/out','results'],text=True).splitlines()
    added = sorted({name for name in published if name.endswith('.json') and name not in old})
    for name in added:
        after = json.loads((root/name).read_text())
        delta = list(differences({},after))
        if delta:
            records[name] = delta
    result = {"created_utc":datetime.now(timezone.utc).isoformat(),
              "baseline_commit":revision,
              "scope":__doc__,
              "simulator":json.loads((root/'results/environment.json').read_text())['simulator'],
              "comparison_runtime":simulator_identity(),
              "records_compared":len(old),"missing_current_records":missing,
              "added_current_records":added,
              "changed_records":len(records),"changed_values":sum(map(len,records.values())),
              "changes":records}
    text = json.dumps(result,indent=2,allow_nan=False)+"\n"
    if str(destination).endswith(".gz"):
        import gzip   # mtime=0 keeps the archived ledger byte-reproducible
        Path(destination).write_bytes(gzip.compress(text.encode(),compresslevel=9,mtime=0))
    else:
        Path(destination).write_text(text)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline",type=Path,default=Path("build/pin42/committed-baseline.json"))
    parser.add_argument("--output",type=Path,default=Path("notebook/assets/ngspice42_changes.json.gz"))
    args = parser.parse_args()
    report = compare(Path(__file__).resolve().parents[1],args.baseline,args.output)
    print({k:v for k,v in report.items() if k != "changes"})
