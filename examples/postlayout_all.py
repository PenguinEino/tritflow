"""Validate real PNR outputs, retaining extraction, SPICE, waveforms and IR results.

Run from any directory. Input layouts must match the current cells/out library.
Use --rebuild-pnr for a standalone rerun after cell compaction; this calls PNR's
public API, with its normal DRC checks. --watch reruns when library/GDS inputs
change and waits for externally produced PNR revisions without accepting stale
results. A bounded --watch-seconds supports parallel stream handoffs.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tritflow.sim.postlayout import run_postlayout, file_hash


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--designs',nargs='+',default=['adder4','full_add','mac1','mul1'])
    parser.add_argument('--build-root',type=Path,default=ROOT/'build')
    parser.add_argument('--hold-ns',type=float,default=2000)
    parser.add_argument('--step-ns',type=float,default=2)
    parser.add_argument('--timeout',type=float,default=600)
    parser.add_argument('--rebuild-pnr',action='store_true')
    parser.add_argument('--watch',action='store_true')
    parser.add_argument('--watch-seconds',type=float,default=600)
    args=parser.parse_args(argv)
    deadline=time.monotonic()+args.watch_seconds
    completed={};failures={};attempted={}
    while True:
        for name in args.designs:
            directory=args.build_root/name
            files=[directory/f'{name}.gds',directory/f'{name}.pnr.json',directory/f'{name}.json']
            files += [ROOT/'cells/template.json']
            if files[2].is_file():
                used=sorted({i['cell'] for i in json.loads(files[2].read_text())['instances']})
                files += [ROOT/'cells/out'/cell/f'{cell}{suffix}' for cell in used
                          for suffix in ('.gds','.spice','.ext.spice','.abstract.json','.char.json')]
            signature=tuple((str(p),file_hash(p) if p.is_file() else None) for p in files)
            if completed.get(name)==signature or attempted.get(name)==signature: continue
            attempted[name]=signature
            try:
                if args.rebuild_pnr:
                    from tritflow.pnr import place_and_route
                    place_and_route(directory/f'{name}.json',output_dir=directory,seed=7)
                result=run_postlayout(directory,hold_s=args.hold_ns*1e-9,step_s=args.step_ns*1e-9,timeout=args.timeout)
                print(json.dumps({'design':name,**{k:result[k] for k in ('passed','lvs_matched','vector_count','pre_max_error_v','post_max_error_v')}}),flush=True)
                if result['passed']:
                    completed[name]=tuple((str(p),file_hash(p) if p.is_file() else None) for p in files);failures.pop(name,None)
                else: failures[name]='Analog checks failed; inspect postlayout/summary.json'
            except Exception as exc:
                failures[name]=str(exc)
                directory.joinpath('postlayout').mkdir(parents=True,exist_ok=True)
                error={'passed':False,'state':'failed','error':str(exc)}
                directory.joinpath('postlayout/error.json').write_text(json.dumps(error,indent=2)+'\n')
                summary_path=directory.joinpath('postlayout/summary.json')
                previous=json.loads(summary_path.read_text()) if summary_path.exists() else {}
                if previous.get('state')!='stale':
                    summary_path.write_text(json.dumps(error,indent=2)+'\n')
                print(f'{name}: {exc}',flush=True)
        if not args.watch or time.monotonic()>=deadline: break
        time.sleep(min(10,max(0,deadline-time.monotonic())))
    return 0 if len(completed)==len(args.designs) and not failures else 1


if __name__=='__main__': raise SystemExit(main())
