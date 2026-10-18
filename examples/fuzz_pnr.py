"""Deterministic TritVerilog → synthesis → verified physical-layout stress runs.

Run ``python3 examples/fuzz_pnr.py --count 100 --jobs 2``. Each design runs in
an isolated, measured process; all source, synthesis, GDS, DRC and strict LVS
evidence stays under build/pnr_fuzz/. ``--resume`` reuses only passing results
with matching source/tool/library hashes. ``--count 0 --scale`` measures the
6/8-trit adders and an actual two-trit multiplier under build/<design>/.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+".new")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")
    temporary.replace(path)


def random_source(seed):
    """Create acyclic expressions with reconvergence, shared fanout and ties."""
    rng = random.Random(seed)
    inputs, depth, width = 2+seed % 11, 1+(seed//3) % 12, 1+(seed//7) % 5
    outputs = 1+seed % 5
    top = f"fuzz_{seed:05d}"
    lines = [f"module {top}(input trit [{inputs-1}:0] a, output trit [{outputs-1}:0] z);"]
    pool = [f"a[{i}]" for i in range(inputs)]
    levels, operations = [], []
    for level in range(depth):
        current = []
        for column in range(width):
            name = f"w{level}_{column}"
            # Hot sources exercise synthesis's BUF trees; recent levels create
            # long paths, while arbitrary old nodes create reconvergent paths.
            recent = levels[-1] if levels else pool
            a = rng.choice(recent if rng.random() < .7 else pool)
            b = rng.choice(pool if rng.random() < .65 else ["a[0]"])
            if rng.random() < .18:
                b = rng.choice(["1'tT", "1't0", "1't1"])
            op = rng.choice(("min", "max", "nany", "neg"))
            expression = {"min": f"({a} & {b})", "max": f"({a} | {b})",
                          "nany": f"nany({a}, {b})", "neg": f"~{a}"}[op]
            lines += [f"  wire trit {name};", f"  assign {name} = {expression};"]
            current.append(name); operations.append(op)
        levels.append(current); pool.extend(current)
    for index in range(outputs):
        value = rng.choice(levels[-1])
        if seed % 17 == 0:
            value = ("1'tT", "1't0", "1't1")[index % 3]
        elif seed % 19 == 0:
            value = f"a[{index % inputs}]"
        lines.append(f"  assign z[{index}] = {value};")
    lines.append("endmodule")
    return "\n".join(lines)+"\n", dict(seed=seed, inputs=inputs, depth=depth,
        width=width, outputs=outputs, authored_operations=sorted(set(operations)),
        fanout_limit=(2, 3, 4, 8)[seed % 4])


def scale_sources():
    """Return standalone HDL including the real HA/FA and one-trit multiplier."""
    fa = (ROOT/"examples/full_add.tv").read_text().replace('`include "half_add.tv"',
        (ROOT/"examples/half_add.tv").read_text())
    adder = (ROOT/"examples/adder.tv").read_text().replace('`include "full_add.tv"', fa)
    sources = {}
    for n in (6, 8):
        name = f"adder{n}"
        sources[name] = adder.replace("module adder #", f"module {name} #").replace(
            "parameter N = 4", f"parameter N = {n}")
    sources["mul2"] = fa+"\n"+(ROOT/"examples/mul1.tv").read_text()+"""
module mul2(input trit [1:0] a, b, output trit [3:0] p);
  wire trit q01, q10, q11, c1;
  mul1 m00(.a(a[0]), .b(b[0]), .p(p[0]));
  mul1 m01(.a(a[0]), .b(b[1]), .p(q01));
  mul1 m10(.a(a[1]), .b(b[0]), .p(q10));
  mul1 m11(.a(a[1]), .b(b[1]), .p(q11));
  full_add add1(.a(q01), .b(q10), .cin(1't0), .sum(p[1]), .cout(c1));
  full_add add2(.a(q11), .b(c1), .cin(1't0), .sum(p[2]), .cout(p[3]));
endmodule
"""
    return sources


def fingerprint():
    """Content hashes of the consumed physical views and implementation."""
    paths = [Path(__file__), ROOT/"cells/template.json", ROOT/"cells/out/all.spice",
             ROOT/"cells/out/library.json"]
    for package in ("pnr", "hdl", "synth", "extract"):
        paths += list((ROOT/f"tritflow/{package}").glob("*.py"))
    paths += [p for p in (ROOT/"cells/out").glob("*/*")
              if p.is_file() and p.name.endswith((".gds", ".abstract.json", ".char.json"))]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(set(paths))}
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def worker(job):
    """Perform all checks without weakening reference ports or PDK rules."""
    from tritflow.hdl import load
    from tritflow.synth import synthesize, write_artifacts
    from tritflow.pnr import place_and_route
    from tritflow.pnr.batch import _lvs
    out = Path(job["directory"])
    started = time.perf_counter()
    report = {"name": job["name"], "parameters": job["parameters"],
              "fingerprint": job["fingerprint"], "source_sha256": job["source_sha256"]}
    stage = "synthesis"
    try:
        net = synthesize(load(out/f"{job['name']}.tv", top=job["name"]),
                         seed=job["seed"], fanout_limit=job["parameters"].get("fanout_limit", 4))
        write_artifacts(net, out)
        report["synthesis"] = net.report()
        report["synthesis_runtime_s"] = time.perf_counter()-started
        stage = "pnr"
        result = place_and_route(net, output_dir=out, seed=job["seed"],
                                 anneal_steps=job["anneal_steps"])
        stage = "lvs"
        _lvs(result, net, (ROOT/"cells/out/all.spice").read_text(), out/"lvs")
        report.update(passed=True, stats=result.stats, checks=result.data["checks"])
    except Exception as error:
        report.update(passed=False, stage=stage, error_class=type(error).__name__,
                      error=str(error), traceback=traceback.format_exc())
    report["total_runtime_s"] = time.perf_counter()-started
    write_json(out/"fuzz.result.json", report)
    return 0 if report["passed"] else 1


def tree_rss_kib(pid):
    """Sum resident pages over this worker and its currently living descendants."""
    total, stack = 0, [pid]
    while stack:
        current = stack.pop()
        try:
            fields = Path(f"/proc/{current}/statm").read_text().split()
            total += int(fields[1])*os.sysconf("SC_PAGE_SIZE")//1024
            stack += [int(p) for p in Path(f"/proc/{current}/task/{current}/children").read_text().split()]
        except (OSError, ValueError, IndexError):
            pass  # A short-lived DRC/LVS subprocess may exit between reads.
    return total


def run_job(job, resume, timeout):
    """Bound the entire process group; even a timed-out run leaves no children."""
    out = Path(job["directory"])
    result_path = out/"fuzz.result.json"
    if resume and result_path.exists():
        previous = json.loads(result_path.read_text())
        if (previous.get("passed") and previous.get("fingerprint") == job["fingerprint"]
                and previous.get("source_sha256") == job["source_sha256"]):
            return previous
    write_json(out/"fuzz.job.json", job)
    peak, started = 0, time.perf_counter()
    with (out/"worker.log").open("w") as log:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
            "--worker", str(out/"fuzz.job.json")], cwd=ROOT, stdout=log, stderr=log,
            start_new_session=True)
        timed_out = False
        try:
            while process.poll() is None:
                peak = max(peak, tree_rss_kib(process.pid))
                if time.perf_counter()-started > timeout:
                    timed_out = True
                    break
                time.sleep(.1)
        finally:
            # Also reap a deck subprocess if Python raised/exited unexpectedly.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    if timed_out or not result_path.exists():
        result = dict(name=job["name"], passed=False, stage="worker",
            error_class="Timeout" if timed_out else "WorkerExit",
            error=f"worker exit {process.returncode}; see {out/'worker.log'}",
            total_runtime_s=time.perf_counter()-started, fingerprint=job["fingerprint"],
            source_sha256=job["source_sha256"], parameters=job["parameters"])
    else:
        result = json.loads(result_path.read_text())
    result["peak_process_tree_rss_mib"] = peak/1024
    write_json(result_path, result)
    if not result["passed"] and not (out/"first_failure.json").exists():
        write_json(out/"first_failure.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--seeds", nargs="+", type=int)
    parser.add_argument("--output-root", type=Path, default=ROOT/"build/pnr_fuzz")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--anneal-steps", type=int, default=600)
    parser.add_argument("--timeout", type=float, default=180.)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--scale", action="store_true")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        return worker(json.loads(args.worker.read_text()))
    if args.count < 0 or args.jobs < 1 or args.timeout <= 0:
        parser.error("count must be nonnegative; jobs and timeout must be positive")
    stamp, jobs = fingerprint(), []
    sources = []
    for seed in (args.seeds if args.seeds is not None else range(args.start_seed, args.start_seed+args.count)):
        source, parameters = random_source(seed)
        sources.append((f"fuzz_{seed:05d}", source, parameters, args.output_root, seed))
    if args.scale:
        sources += [(name, source, {"scale": True}, ROOT/"build", 7)
                    for name, source in scale_sources().items()]
    for name, source, parameters, root, seed in sources:
        out = (root/name).resolve(); out.mkdir(parents=True, exist_ok=True)
        (out/f"{name}.tv").write_text(source)
        jobs.append(dict(name=name, directory=str(out), parameters=parameters, seed=seed,
            anneal_steps=args.anneal_steps, fingerprint=stamp,
            source_sha256=hashlib.sha256(source.encode()).hexdigest()))
    args.output_root.mkdir(parents=True, exist_ok=True)
    results = []
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_job, job, args.resume, args.timeout) for job in jobs]
        for future in as_completed(futures):
            result = future.result(); results.append(result)
            print(f"{len(results)}/{len(jobs)} {result['name']}: " +
                  (f"PASS {result['total_runtime_s']:.2f}s {result['peak_process_tree_rss_mib']:.1f} MiB" if result["passed"]
                   else f"FAIL {result['stage']} {result['error_class']}: {result['error'][:250]}"), flush=True)
            write_json(args.output_root/"summary.json", dict(fingerprint=stamp,
                completed=len(results), passed=sum(r["passed"] for r in results),
                failed=sum(not r["passed"] for r in results),
                wall_time_s=time.perf_counter()-started,
                cases=sorted(results, key=lambda r: r["name"])))
    if fingerprint() != stamp:
        raise RuntimeError("Cell or tool inputs changed during fuzzing; rerun to certify the new publication")
    return int(any(not result["passed"] for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
