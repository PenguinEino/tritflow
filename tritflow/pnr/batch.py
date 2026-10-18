"""Content-aware builds of the four shared physical-design demonstrations."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from tritflow import CELLS_DIR, ROOT, PDK_ROOT
from tritflow.netlist import GateNetlist
from . import Library, place_and_route

DESIGNS = ("adder4", "full_add", "mac1", "mul1")


def write_json(path, data):
    """Publish a complete record; a watch process never reads partial JSON."""
    path = Path(path)
    temporary = path.with_name(path.name+".new")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False)+"\n")
    temporary.replace(path)


def digest_files(paths):
    """Hash paths and contents, detecting changed views even with preserved mtimes."""
    result = {}
    for path in sorted({Path(p).resolve() for p in paths}):
        result[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def input_state(build_root, cells_root, designs, seeds, anneal_steps, views):
    cells_root = Path(cells_root)
    # Hash all published cell views and root publication/qualification files.
    # Independent comparison runs may write large scratch trees under out/;
    # those are not a new library publication. Their final root report is hashed.
    publication = cells_root/"out"
    files = [cells_root/"template.json"]
    files += [p for p in publication.iterdir() if p.is_file()]
    files += [p for directory in publication.iterdir()
              if directory.is_dir() and (directory/f"{directory.name}.abstract.json").exists()
              for p in directory.rglob("*") if p.is_file()]
    files += [Path(build_root)/name/f"{name}.json" for name in designs]
    files += [p for p in (ROOT/"tritflow/pnr").glob("*.py") if not p.name.startswith(("chip","signoff"))]
    files += [ROOT/"tritflow/viz/layout.py", ROOT/"tritflow/extract/lvs.py",
              ROOT/"tritflow/extract/capacitance.py", ROOT/"examples/pnr_all.py"]
    files += [p for group in ("drc", "lvs")
              for p in (PDK_ROOT/"libs.tech/klayout/tech"/group).rglob("*") if p.is_file()]
    files += [ROOT/"notebook/setup_pins.json", ROOT/"tritflow/extract/technology.py"]
    state = {"files": digest_files(files), "designs": list(designs), "seeds": list(seeds),
             "anneal_steps": anneal_steps, "views": views}
    state["fingerprint"] = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    return state


def checked_artifacts(build_root, designs, views):
    """The cache also certifies outputs, so deleting/editing a GDS triggers rebuild."""
    paths = []
    for name in designs:
        out = Path(build_root)/name
        paths += [out/f"{name}{suffix}" for suffix in
                  (".gds", ".pnr.json", ".net_parasitics.json", ".drc.lyrdb", ".lvs.summary.json", ".pnr.summary.json", ".seed_comparison.json")]
        paths += [p for p in (out/"pnr_seeds").rglob("*") if p.is_file()]
        paths += [out/"lvs"/f"{name}.ext.spice", out/"lvs"/f"{name}.lvsdb"]
        if views:
            paths += [out/f"{name}{suffix}" for suffix in
                      (".layout.png", ".layout.html", ".placement.html", ".routing.html", ".capacitance.html")]
    return digest_files(paths)


def _lvs(result, netlist, cell_subckts, directory):
    from .lvs import strict_lvs
    started = time.perf_counter()
    library = Library.load(result.data["library"]["source"])
    report = strict_lvs(result.gds_path, result.data, netlist, library, directory, cell_subckts)
    summary = {key: value for key, value in report.items() if key != "log"}
    path = result.json_path.with_name(f"{netlist.top}.lvs.summary.json")
    write_json(path, summary)
    result.data["checks"]["lvs"] = {"clean": report["matched"], "summary_path": str(path),
                                   "report_path": report["report"], "errors": report["errors"]}
    timing = result.stats["runtime_s"]
    timing["lvs"] = time.perf_counter()-started
    timing["with_lvs"] = timing["total"]+timing["lvs"]
    if not report["matched"]:
        write_json(result.json_path, result.data)
        raise RuntimeError(f"{netlist.top}: strict LVS mismatch; inspect {path}")
    result.data["net_parasitics"] = result.net_parasitics(lvs_report=report["report"])
    write_json(result.json_path, result.data)
    return summary


def build_design(name, build_root, library, seeds, anneal_steps, *, views=True):
    """Compare verified seeds, preferring compact dies and short drawn routes."""
    from tritflow.viz.layout import save_layout_views
    out = Path(build_root)/name
    netlist = GateNetlist.load(out/f"{name}.json")
    subckts = (Path(library.source)/"out/all.spice").read_text()
    trials = []
    for seed in seeds:
        trial_dir = out/"pnr_seeds"/f"seed{seed}"
        print(f"{name}: seed {seed} — placement, routing, DRC, LVS", flush=True)
        try:
            result = place_and_route(netlist, library, output_dir=trial_dir,
                                     seed=seed, anneal_steps=anneal_steps)
            lvs = _lvs(result, netlist, subckts, trial_dir/"lvs")
            trial = {"seed": seed, "passed": True, **result.stats,
                     "pdk_drc_violations": result.data["checks"]["pdk_drc"]["violations"],
                     "lvs_matched": lvs["matched"], "json_path": str(result.json_path)}
        except Exception as error:
            trial = {"seed": seed, "passed": False, "error": str(error), "directory": str(trial_dir)}
            print(f"{name}: seed {seed} failed: {error}", flush=True)
        trials.append(trial)
        write_json(out/f"{name}.seed_comparison.json", trials)
    passing = [trial for trial in trials if trial["passed"]]
    if not passing:
        raise RuntimeError(f"{name}: all seeds failed; inspect {out/name}.seed_comparison.json")
    best = min(passing, key=lambda trial: (
        trial["aspect_ratio"] > 1.5, trial["utilization"] < .45, trial["die_area_um2"],
        sum(trial["wirelength_um"].values()), trial["hpwl_after_um"], trial["seed"]))
    # Regenerate at the canonical location: report paths and self-check evidence
    # refer to build/<design>/ rather than a copied seed directory or /tmp.
    print(f"{name}: publishing seed {best['seed']} to {out}", flush=True)
    result = place_and_route(netlist, library, output_dir=out, seed=best["seed"], anneal_steps=anneal_steps)
    lvs = _lvs(result, netlist, subckts, out/"lvs")
    view_start = time.perf_counter()
    figures = save_layout_views(result) if views else {}
    view_seconds = time.perf_counter()-view_start
    summary = {"design": name, "selected_seed": best["seed"],
               "selection": "DRC/LVS pass, aspect <= 1.5, utilization >= 45%, then minimum die area, drawn signal wirelength, HPWL, seed",
               "stats": result.stats, "checks": result.data["checks"], "seed_comparison": trials,
               "gds_path": str(result.gds_path), "json_path": str(result.json_path),
               "views": {key: str(path) for key, path in figures.items()},
               "lvs": lvs, "view_runtime_s": view_seconds,
               "canonical_runtime_with_views_s": result.stats["runtime_s"]["with_lvs"]+view_seconds}
    write_json(out/f"{name}.pnr.summary.json", summary)
    return summary


def update_status(build_root, cells_root, results, fingerprint):
    """Refresh only the owned generated result tables for canonical project builds."""
    if (Path(build_root).resolve() != (ROOT/"build").resolve() or
            Path(cells_root).resolve() != CELLS_DIR.resolve() or
            {result["design"] for result in results} != set(DESIGNS)):
        return
    height = json.loads((Path(cells_root)/"template.json").read_text())["height"]
    lines = ["<!-- PNR_RESULTS_BEGIN -->", "## Current verified build results", "",
             f"Published template height: **{height:g} µm**. Input content fingerprint: `{fingerprint}`.", "",
             "All outputs and reports are under `build/<design>/`. Utilization is placed cell area / die area; wirelength and signal via counts exclude the separately reported power geometry.", "",
             "| Design | Seed | Die (µm) | Aspect | Utilization | M1 (µm) | M2 (µm) | Signal / power vias | PDK DRC | Strict LVS | PNR / +LVS (s) |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|"]
    for result in results:
        stats, checks = result["stats"], result["checks"]
        width, height = stats["die_size_um"]
        lines.append(f"| {result['design']} | {result['selected_seed']} | {width:g} × {height:g} | "
                     f"{stats['aspect_ratio']:.3f} | {stats['utilization']:.2%} | {stats['wirelength_um']['M1']:g} | {stats['wirelength_um']['M2']:g} | "
                     f"{stats['via_count']} / {stats['power_via_count']} | {checks['pdk_drc']['violations']} violations | "
                     f"{'Match' if checks['lvs']['clean'] else 'FAILED'} | "
                     f"{stats['runtime_s']['total']:.2f} / {stats['runtime_s']['with_lvs']:.2f} |")
    baseline_path = Path(build_root)/"pnr_phase2_baseline.json"
    if baseline_path.exists():
        baseline = {r["design"]: r for r in json.loads(baseline_path.read_text())}
        lines += ["", "## Phase 2 → phase 3", "",
                  "Before artifacts are preserved in each design's `phase2/`; cell library and input netlists are unchanged.", "",
                  "| Design | Die before → after (µm) | Aspect before → after | Utilization before → after | Die area reduction | Signal length before → after (µm) |",
                  "|---|---:|---:|---:|---:|---:|"]
        for result in results:
            before, after = baseline[result["design"]]["stats"], result["stats"]
            bw, bh = before["die_size_um"]
            aw, ah = after["die_size_um"]
            lines.append(f"| {result['design']} | {bw:g} × {bh:g} → {aw:g} × {ah:g} | "
                         f"{max(bw,bh)/min(bw,bh):.3f} → {after['aspect_ratio']:.3f} | "
                         f"{before['utilization']:.2%} → {after['utilization']:.2%} | "
                         f"{1-after['die_area_um2']/before['die_area_um2']:.2%} | "
                         f"{sum(before['wirelength_um'].values()):g} → {sum(after['wirelength_um'].values()):g} |")
    lines += ["", "## Placement seed comparison", "",
              "Cell-terminal HPWL excludes external ports. Each before/after pair uses the same final floorplan. Seed selection prefers aspect ≤1.5 and utilization ≥45%, then smallest die area and drawn signal wirelength; HPWL and seed break ties. All reported runtimes are measured on this machine, include PDK DRC, and exclude seed-search overhead.", "",
              "| Design | Seed | HPWL before (µm) | HPWL after (µm) | Reduction | PNR / +LVS (s) | DRC / LVS |",
              "|---|---:|---:|---:|---:|---:|---|"]
    for result in results:
        for trial in result["seed_comparison"]:
            if trial["passed"]:
                lines.append(f"| {result['design']} | {trial['seed']} | {trial['hpwl_before_um']:g} | "
                             f"{trial['hpwl_after_um']:g} | {trial['hpwl_improvement_pct']:.2f}% | "
                             f"{trial['runtime_s']['total']:.2f} / {trial['runtime_s']['with_lvs']:.2f} | clean / Match |")
            else:
                lines.append(f"| {result['design']} | {trial['seed']} | — | — | — | — | FAILED; see seed comparison JSON |")
    lines += ["", "Machine-readable results: `build/pnr_summary.json`, `build/pnr_manifest.json`, and each design's `.pnr.summary.json` / `.seed_comparison.json`.", "<!-- PNR_RESULTS_END -->"]
    block = "\n".join(lines)+"\n"
    path = ROOT/"docs/status/PNR.md"
    text = path.read_text()
    start, end = "<!-- PNR_RESULTS_BEGIN -->", "<!-- PNR_RESULTS_END -->"
    if start in text and end in text:
        first, remainder = text.split(start, 1)
        _, last = remainder.split(end, 1)
        text = first+block+last.lstrip("\n")
    else:
        text += "\n"+block
    path.write_text(text)


def run_all(build_root=ROOT/"build", cells_root=CELLS_DIR, *, designs=DESIGNS,
            seeds=(0, 7, 19), anneal_steps=600, views=True, force=False, max_restarts=5):
    """Rebuild changed inputs; restart all designs if cells change during the run."""
    build_root, cells_root = Path(build_root).resolve(), Path(cells_root).resolve()
    manifest_path = build_root/"pnr_manifest.json"
    for attempt in range(max_restarts+1):
        before = input_state(build_root, cells_root, designs, seeds, anneal_steps, views)
        if not force and manifest_path.exists():
            previous = json.loads(manifest_path.read_text())
            if previous.get("inputs", {}).get("fingerprint") == before["fingerprint"]:
                try:
                    if previous["outputs"] == checked_artifacts(build_root, designs, views):
                        print("PNR inputs and checked artifacts unchanged; all designs are current.", flush=True)
                        update_status(build_root, cells_root, previous["results"], before["fingerprint"])
                        return previous["results"]
                except FileNotFoundError:
                    pass
        try:
            library = Library.load(cells_root)
            results = [build_design(name, build_root, library, seeds, anneal_steps, views=views) for name in designs]
        except Exception:
            after = input_state(build_root, cells_root, designs, seeds, anneal_steps, views)
            if before["fingerprint"] == after["fingerprint"] or attempt == max_restarts:
                raise
            print("Cell/source inputs changed during a failed build; retrying with the new publication.", flush=True)
            continue
        after = input_state(build_root, cells_root, designs, seeds, anneal_steps, views)
        if before["fingerprint"] != after["fingerprint"]:
            if attempt == max_restarts:
                raise RuntimeError("Inputs kept changing; re-run after the cell publication settles")
            print("Cell/source inputs changed during the run; rebuilding all designs automatically.", flush=True)
            continue
        write_json(build_root/"pnr_summary.json", {"library_height_um": library.template["height"],
                   "input_fingerprint": after["fingerprint"], "results": results})
        write_json(manifest_path, {"inputs": after, "outputs": checked_artifacts(build_root, designs, views), "results": results})
        update_status(build_root, cells_root, results, after["fingerprint"])
        return results
    raise AssertionError("unreachable")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, default=ROOT/"build")
    parser.add_argument("--cells-root", type=Path, default=CELLS_DIR)
    parser.add_argument("--designs", nargs="+", choices=DESIGNS, default=list(DESIGNS))
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 7, 19])
    parser.add_argument("--anneal-steps", type=int, default=600)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-views", action="store_true")
    parser.add_argument("--watch", action="store_true", help="poll cell publications and automatically rebuild changed inputs")
    parser.add_argument("--poll-seconds", type=float, default=5.)
    args = parser.parse_args(argv)
    if args.poll_seconds <= 0:
        parser.error("--poll-seconds must be positive")
    if any(not (args.build_root/name/f"{name}.json").exists() for name in args.designs):
        subprocess.run([sys.executable, str(ROOT/"examples/build_all.py"), "--output-root", str(args.build_root)], check=True, cwd=ROOT)
    last = None
    while True:
        try:
            state = input_state(args.build_root, args.cells_root, args.designs, args.seeds, args.anneal_steps, not args.no_views)
            if state["fingerprint"] != last or args.force:
                # A second snapshot avoids loading a library midway through a fast
                # multi-file publication. An active build also checks before/after.
                if args.watch:
                    time.sleep(min(args.poll_seconds, 5.))
                    if input_state(args.build_root, args.cells_root, args.designs, args.seeds, args.anneal_steps, not args.no_views)["fingerprint"] != state["fingerprint"]:
                        continue
                run_all(args.build_root, args.cells_root, designs=args.designs, seeds=tuple(dict.fromkeys(args.seeds)),
                        anneal_steps=args.anneal_steps, views=not args.no_views, force=args.force)
                last = input_state(args.build_root, args.cells_root, args.designs, args.seeds, args.anneal_steps, not args.no_views)["fingerprint"]
                args.force = False
        except (OSError, ValueError, RuntimeError) as error:
            if not args.watch:
                raise
            print(f"Waiting for a consistent cell publication: {error}", flush=True)
        if not args.watch:
            return 0
        time.sleep(min(args.poll_seconds, 60.))


if __name__ == "__main__":
    raise SystemExit(main())
