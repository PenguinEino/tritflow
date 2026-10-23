"""Record ternary-weight dot products through synthesis, real PNR, STA and SPICE.

The default command only reads the publication. Expensive computation requires
``python3 -B examples/dot_scaling.py --recompute``. All generated files stay in
results/dot_scaling; no shared cell publication or other stream is modified.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "notebook"))
RESULT = ROOT / "results/dot_scaling.json"
COMPANIONS = ROOT / "results/dot_scaling"
SIZES = (2, 4, 8, 16, 32)
CONDITIONS = dict(seed=0, load_f=100e-15, edge_s=1e-9, hold_s=1e-6,
                  step_s=2e-9, temperature_c=27, timeout_s=600,
                  supplies_v={"VDD": 5., "VMID": 0., "VSS": -5.})


def size_conditions(n, base=None):
    """Document the larger circuits' channel capacity and settling observation time."""
    conditions = dict(base or CONDITIONS)
    conditions["hold_s"] *= max(1, n / 8)
    conditions["pnr_options"] = (dict(channel_tracks=24, current_density_a_per_um=.0001335,
                                      ripup_passes=2, max_expansions=2) if n >= 16 else {})
    if n >= 32:
        conditions["pnr_options"]["current_density_a_per_um"] = .00007
    return conditions


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def output_width(n):
    """Smallest balanced-ternary word covering every integer in [-N, N]."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError("Dot products require an integer term count >= 2")
    width = 1
    while (3**width - 1) // 2 < n:
        width += 1
    return width


def dot_source(n):
    """Keep dot4's left-associative + expression, without constant weights."""
    width = output_width(n)
    inputs = ", ".join([*(f"w{i}" for i in range(n)), *(f"x{i}" for i in range(n))])
    expression = " + ".join(f"w{i}*x{i}" for i in range(n))
    return (f"module dot{n}(input trit {inputs}, output trit [{width-1}:0] y);\n"
            f"  assign y = {expression};\nendmodule\n")


def dot_oracle(n, inputs, outputs):
    """Integer multiply/sum and radix conversion, independent of mapped cells."""
    width = output_width(n)

    def expected(vector):
        values = dict(zip(inputs, vector, strict=True))
        total = sum(values[f"w{i}"] * values[f"x{i}"] for i in range(n))
        digits = {}
        for i in range(width):
            digit = (total + 1) % 3 - 1
            digits[f"y[{i}]"] = digit
            total = (total - digit) // 3
        if total:
            raise ValueError("The output word would truncate the dot product")
        return {pin: digits[pin] for pin in outputs}

    return expected


def vector_plan(n, inputs, outputs):
    """Fixed weights and a first-term edge that carries through every low digit.

    H=(3**(width-1)-1)/2 has all lower digits +1. With product 0 initially
    at term 0 and H other products +1, asserting term 0 changes H to H+1:
    all low output digits change +1 -> -1 and the top digit 0 -> +1.
    The negative case is symmetric. Term 0 traverses the entire source sum
    chain; neither the source nor its lowered network is rebalanced here.
    """
    width = output_width(n)
    weights = tuple((1, -1, 1, 1)[i % 4] for i in range(n))
    threshold = (3**(width - 1) - 1) // 2
    zero = [0] * n
    positive = [0] + [1] * threshold + [0] * (n - threshold - 1)
    asserted = positive.copy()
    asserted[0] = 1
    cases = [("zero", zero), ("positive_carry_setup", positive),
             ("positive_carry_assert", asserted), ("positive_carry_release", positive),
             ("return_zero", zero),
             ("negative_carry_setup", [-v for v in positive]),
             ("negative_carry_assert", [-v for v in asserted]),
             ("negative_carry_release", [-v for v in positive]),
             ("all_products_positive", [1] * n),
             ("all_products_negative", [-1] * n), ("final_zero", zero)]
    vectors, activations = [], []
    for _, products in cases:
        x = [p * w for p, w in zip(products, weights, strict=True)]
        values = {f"w{i}": w for i, w in enumerate(weights)}
        values.update({f"x{i}": v for i, v in enumerate(x)})
        vectors.append([values[name] for name in inputs])
        activations.append(x)
    expected = dot_oracle(n, inputs, outputs)
    return dict(input_order=inputs, output_order=outputs, weights=list(weights),
                activations=activations, vectors=vectors, labels=[label for label, _ in cases],
                expected=[expected(v) for v in vectors], carry_threshold=threshold,
                coverage="11 states in order; 10 directed pairs; both polarities of longest output-digit carry, "
                         "assert/release; zero and both all-product rails. Finite directed coverage, not a global worst-case proof.")


def source_names(root=ROOT, pdk=None):
    """Only consumed implementations, published cell views, tables and PDK inputs."""
    from tritflow import PDK_ROOT
    pdk = Path(pdk or PDK_ROOT)
    relative = ["examples/dot_scaling.py", "notebook/cache.py", "notebook/setup_pins.json",
                "tritflow/__init__.py", "tritflow/netlist.py", "tritflow/flow.py",
                "tritflow/progress.py", "cells/template.json", "cells/out/all.spice"]
    for folder in ("hdl", "synth", "pnr", "sim", "extract", "sta"):
        excluded = {"__main__.py"}
        if folder == "pnr":
            excluded |= {"chip.py", "signoff.py", "batch.py"}
        if folder == "sim":
            excluded |= {"characterize.py", "scaling.py", "corners.py", "sizing.py", "publication.py",
                         "diagnose.py", "load_sweep.py", "cascade.py", "postlayout.py", "compare.py"}
        if folder == "sta":
            excluded |= {"characterize.py", "validate.py", "plot.py", "diagnose.py", "charge.py",
                         "metrics.py", "worst_audit.py"}
        relative += [str(path.relative_to(root)) for path in sorted((root / "tritflow" / folder).glob("*.py"))
                     if path.name not in excluded]
    # logical_nodeset and independent DC solves are called by this producer.
    relative += ["tritflow/sim/postlayout.py", "tritflow/sim/characterize.py"]
    relative += [str(p.relative_to(root)) for p in sorted((root / "cells/out").glob("*.json"))]
    for name in ("INV", "NAND", "NOR", "NANY", "BUF", "TIEP", "TIEZ", "TIEN", "FILL"):
        for suffix in ("gds", "spice", "ext.spice", "abstract.json", "char.json", "timing.json"):
            path = root / f"cells/out/{name}/{name}.{suffix}"
            if path.is_file():
                relative.append(str(path.relative_to(root)))
    relative += [str(p.relative_to(root)) for p in sorted((root / "results/sta/propagation/tables").glob("*.json"))]
    names = ["source/" + name for name in relative]
    for folder in ("libs.tech/spice/models", "libs.tech/klayout/tech/lvs", "libs.tech/klayout/tech/drc"):
        names += ["pdk/" + str(p.relative_to(pdk)) for p in sorted((pdk / folder).rglob("*")) if p.is_file()]
    names += ["pdk/" + str(p.relative_to(pdk)) for p in sorted((pdk / "openIP62/IP62/Technology/doc").glob("*.pdf"))]
    return sorted(set(names))


def provenance():
    """Relocatable content identities; Git revision alone never qualifies a run."""
    from cache import source_manifest
    from tritflow import PDK_ROOT
    from tritflow.sim.provenance import pdk_provenance
    from tritflow.sim.tools import simulator_identity

    klayout = Path(os.environ.get("KLAYOUT_BINARY") or shutil.which("klayout")
                   or Path.home() / "bin/klayout/klayout").resolve()
    revision = os.environ.get("TRITFLOW_SOURCE_COMMIT")
    if not revision:
        run = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)
        revision = run.stdout.strip() if run.returncode == 0 else None
    return dict(sources_sha256=source_manifest(ROOT, PDK_ROOT, names=source_names()),
                pdk=pdk_provenance(), simulator=simulator_identity(), source_commit=revision,
                klayout=dict(binary_sha256=sha256(klayout.read_bytes()).hexdigest(),
                             version=subprocess.check_output([str(klayout), "-v"], text=True).strip()),
                runtime=dict(hostname=platform.node(), python=sys.version, platform=platform.platform(), machine=platform.machine(),
                             packages={p: importlib.metadata.version(p) for p in ("numpy", "scipy", "klayout", "lark")}))


def verify_record(data, *, root=ROOT, pdk=None, artifacts=True):
    """Read recorded evidence without launching native tools or requiring work/."""
    from cache import file_hash, source_manifest
    from tritflow import PDK_ROOT
    saved = data["provenance"]["sources_sha256"]
    current = source_manifest(Path(root), Path(pdk or PDK_ROOT), names=saved)
    changed = [name for name in saved if saved[name] != current[name]]
    if changed:
        raise RuntimeError("Recorded dot scaling is stale: " + ", ".join(changed[:8]))
    if artifacts:
        for name, digest in data.get("evidence_sha256", {}).items():
            path = Path(root) / name
            if Path(name).is_absolute() or not path.resolve().is_relative_to(Path(root).resolve()):
                raise ValueError(f"Recorded evidence escapes the repository: {name}")
            if not path.is_file() or file_hash(path) != digest:
                raise RuntimeError(f"Recorded dot-scaling evidence is missing or changed: {name}")
    return data


def _files(folder, paths):
    from cache import file_hash
    return {str(Path(p).relative_to(folder)): file_hash(p) for p in paths}


def _cached(folder, name, key, action, artifacts):
    """Resume complete stages only when options, inputs and artifact bytes agree."""
    from cache import file_hash
    path = folder / f"{name}.cache.json"
    if path.is_file():
        saved = json.loads(path.read_text())
        if saved["key"] == key and all((folder / p).is_file() and file_hash(folder / p) == h
                                       for p, h in saved["artifacts_sha256"].items()):
            print(f"{folder.name}: reuse {name}", flush=True)
            return saved["value"]
    print(f"{folder.name}: {name}", flush=True)
    started = time.perf_counter()
    value = action()
    value["elapsed_s"] = time.perf_counter() - started
    files = artifacts(value) if callable(artifacts) else artifacts
    _save(path, dict(key=key, value=value, artifacts_sha256=_files(folder, files)))
    return value


def _power_rows(rows, labels, cells, supplies):
    """Delivered rail power uses ngspice source-current signs, including VSS."""
    result = []
    for row, label in zip(rows, labels, strict=True):
        currents = row["rail_current_a"]
        power = -sum(supplies[rail] * current for rail, current in currents.items())
        result.append(dict(label=label, input_trits=row["input_trits"], passed=row["passed"],
                           rail_current_a=currents, supply_current_a={r: -v for r, v in currents.items()},
                           static_power_w=power, power_per_cell_w=power / cells,
                           rail_current_per_cell_a={r: v / cells for r, v in currents.items()}))
    return result


def fixed_weight_timing(net, plan, logical_caps, conditions):
    """Apply fixed weights to STA without changing a physical gate or its load.

    The matched-event engine initializes a symbolic load report. Leaving weight
    inputs unconstrained there creates an unnecessary 2N-input decision diagram
    even though no weight changes in any pair. For this analysis only, replace
    those primary input drivers by ideal logical TIE sources on the same nets.
    No synthesis/constant propagation is run: every original cell, pin, net and
    load remains. The virtual TIEs never transition and contribute no path delay.
    This is exactly the fixed-weight constraint used in the analog experiment.
    """
    from tritflow.netlist import GateNetlist, Instance
    from tritflow.sta import analyze

    fixed = {f"w{i}": value for i, value in enumerate(plan["weights"])}
    tie = {-1: "TIEN", 0: "TIEZ", 1: "TIEP"}
    constrained = GateNetlist(net.top, [p for p in net.ports if p.name not in fixed],
                             [Instance(f"_sta_weight_{i}", tie[value], {"Y": name})
                              for i, (name, value) in enumerate(fixed.items())] + net.instances)
    states = [{name: value for name, value in zip(plan["input_order"], vector, strict=True) if name not in fixed}
              for vector in plan["vectors"]]
    report = analyze(constrained, vector_pairs=list(zip(states, states[1:])), wire_caps=logical_caps,
                     output_load_f=conditions["load_f"], input_transition_s=conditions["edge_s"])
    for pattern in report.patterns.values():
        for phase in ("before", "after"):
            if phase in pattern:
                pattern[phase].update(fixed)
    report.provenance["fixed_weight_constraint"] = fixed
    report.assumptions.append("Analysis-only ideal logical TIE drivers impose fixed weights on the original weight nets; "
                              "no original cell, connection or load is removed or remapped. Physical/SPICE design has variable weight inputs.")
    return report


def run_size(n, identity, *, conditions=None, directory=COMPANIONS):
    """One seed-0 physical/electrical sample; a timeout is an explicit missing value."""
    import numpy as np
    from tritflow import flow
    from tritflow.extract import reference_net_map
    from tritflow.sim.characterize import dc_operating_points
    from tritflow.sim.postlayout import logical_nodeset
    from tritflow.sim.runner import SimulationError
    from tritflow.synth import write_artifacts

    conditions = size_conditions(n, conditions)
    folder = Path(directory) / "work" / f"dot{n}"
    folder.mkdir(parents=True, exist_ok=True)
    key = _hash(dict(identity=identity, conditions=conditions, n=n))
    source = dot_source(n)
    (folder / f"dot{n}.tv").write_text(source)
    started = time.perf_counter()
    record = dict(n=n, top=f"dot{n}", state="running", passed=False, configuration_sha256=key,
                  conditions=conditions, output_trits=output_width(n),
                  producer=dict(hostname=identity["runtime"]["hostname"], machine=identity["runtime"]["machine"],
                                platform=identity["runtime"]["platform"], simulator=identity["simulator"],
                                klayout=identity["klayout"]))
    _save(folder / "record.json", record)
    try:
        print(f"dot{n}: synthesis", flush=True)
        before = time.perf_counter()
        net = flow.loads(source).synthesize(seed=conditions["seed"])
        write_artifacts(net, folder)
        record["synthesis"] = net.report() | {"elapsed_s": time.perf_counter() - before}
        inputs = [p.name for p in net.ports if p.dir == "input"]
        outputs = [p.name for p in net.ports if p.dir == "output"]
        plan = vector_plan(n, inputs, outputs)
        record["vector_plan"] = plan
        expected = dot_oracle(n, inputs, outputs)
        _save(folder / "vectors.json", plan)

        def physical():
            lay = net.place_and_route(output_dir=folder, seed=conditions["seed"], **conditions["pnr_options"])
            return dict(stats=lay.stats, drc=lay.data["checks"]["pdk_drc"])

        physical_result = _cached(folder, "pnr", key, physical,
                                 [folder / f"dot{n}.gds", folder / f"dot{n}.pnr.json", folder / f"dot{n}.drc.lyrdb"])
        record["pnr"] = physical_result
        lay = flow.load_layout(net, folder)

        def extraction():
            lvs = lay.lvs()
            if not lvs["matched"]:
                raise RuntimeError(f"LVS mismatch: {lvs}")
            extracted = lay.extract()
            (folder / "postlayout.spice").write_text(extracted.spice)
            _save(folder / "capacitance.json", extracted.capacitance)
            return dict(lvs=lvs, capacitance=extracted.capacitance)

        extracted = _cached(folder, "extraction", key, extraction,
                            lambda value: [folder / "postlayout.spice", folder / "capacitance.json",
                                           Path(value["lvs"]["report"]), Path(value["lvs"]["extracted"])])
        record["lvs"] = extracted["lvs"]
        caps = extracted["capacitance"]
        mapping = reference_net_map(record["lvs"]["report"], net.top)
        missing = net.nets() - mapping.keys()
        if missing:
            raise RuntimeError(f"Missing extracted-net mapping: {sorted(missing)}")
        logical_caps = {name: caps["nets"][mapping[name]]["capacitance_f"] for name in sorted(net.nets())}
        record["wire_capacitance"] = dict(total_signal_f=sum(logical_caps.values()),
                                          logical_nets_f=logical_caps,
                                          parameters=caps.get("parameters"),
                                          assumptions=caps.get("assumptions"),
                                          parameter_origin=caps.get("parameter_origin"))
        def timing():
            report = fixed_weight_timing(net, plan, logical_caps, conditions)
            report.save(folder / "sta.json")
            return report.to_dict()

        record["sta"] = _cached(folder, "sta", key, timing, [folder / "sta.json"])
        circuit = (folder / "postlayout.spice").read_text()

        def transient():
            from tritflow.sim import simulate
            result = simulate(circuit, net.top, inputs, outputs, plan["vectors"], expected,
                              loads_f=conditions["load_f"], hold_s=conditions["hold_s"],
                              edge_s=conditions["edge_s"], step_s=conditions["step_s"],
                              temperature_c=conditions["temperature_c"], supplies_v=conditions["supplies_v"],
                              nodeset=logical_nodeset(net, record["lvs"]["report"], inputs, plan["vectors"][0]),
                              timeout=conditions["timeout_s"], workdir=folder / "post")
            np.savez_compressed(folder / "post/waveforms.npz", **result["waveforms"])
            _save(folder / "post/measurements.json", result["measurements"])
            # Keep a compressed numerical waveform and the exact simulator deck.
            (folder / "post/waveform.txt").unlink()
            return dict(state="simulated", passed=result["measurements"]["passed"],
                        measurements=result["measurements"])

        try:
            spice = _cached(folder, "spice", key, transient,
                            [folder / f"post/{name}" for name in ("measurements.json", "waveforms.npz", "tb.spice", "ngspice.log")])
        except SimulationError as error:
            if "timeout" not in str(error):
                raise
            spice = dict(state="not_simulated", passed=None, reason=str(error),
                         elapsed_s=conditions["timeout_s"], measurements=None)
        record["spice"] = spice
        record["timing_comparison"] = compare_timing(record["sta"]["arrival"], spice)

        # Independent DC solves distinguish quiescent draw from transition current.
        unique = list(dict.fromkeys(tuple(v) for v in plan["vectors"]))
        labels = [plan["labels"][plan["vectors"].index(list(v))] for v in unique]

        def static():
            dc = dc_operating_points(circuit, net.top, inputs, outputs, unique, expected,
                                     pdk=net.settings.pdk, temperature_c=conditions["temperature_c"],
                                     supplies_v=conditions["supplies_v"],
                                     timeout=conditions["timeout_s"], workdir=folder / "dc",
                                     nodeset=lambda v: logical_nodeset(net, record["lvs"]["report"], inputs, v))
            rows = _power_rows(dc, labels, len(net.instances), conditions["supplies_v"])
            _save(folder / "static.json", rows)
            return dict(rows=rows, passed=all(r["passed"] for r in rows))

        static_result = _cached(folder, "static", key, static,
                                lambda value: [folder / "static.json", *sorted((folder / "dc").rglob("tb.spice")),
                                               *sorted((folder / "dc").rglob("ngspice.log"))])
        static_rows = static_result["rows"]
        powers = [r["static_power_w"] for r in static_rows]
        record["power"] = static_result | dict(zero=static_rows[0], minimum_w=min(powers), maximum_w=max(powers),
                                               mean_w=sum(powers) / len(powers),
                                               zero_is_measured_maximum=static_rows[0]["static_power_w"] >= max(powers) - 1e-12,
                                               current_range_a={rail: [min(r["rail_current_a"][rail] for r in static_rows),
                                                                       max(r["rail_current_a"][rail] for r in static_rows)]
                                                                for rail in ("VDD", "VMID", "VSS")},
                                               minimum_per_cell_w=min(powers) / len(net.instances),
                                               maximum_per_cell_w=max(powers) / len(net.instances),
                                               scope="Independent DC operating points for unique simulated states; weights fixed. "
                                                     "Per-cell denominator is mapped logic/buffer/tie instances, excluding metal-only FILL. "
                                                     "Raw source currents use ngspice signs; P=-sum(Vrail*Irail). Finite-state spread, not an exhaustive power bound.")
        record.update(state="complete", passed=(spice["passed"] is True and static_result["passed"] is True
                                                  and record["pnr"]["drc"]["clean"] is True
                                                  and record["lvs"]["matched"] is True))
    except Exception as error:
        record.update(state="failed", error=f"{type(error).__name__}: {error}")
        print(f"dot{n}: {record['error']}", flush=True)
    record["elapsed_s"] = time.perf_counter() - started
    _save(folder / "record.json", record)
    return record


def compare_timing(arrival, spice):
    """Matched vector-set maxima; a failed/unsettled output never becomes zero."""
    measured = spice.get("measurements")
    rows = []
    for output, predicted in arrival.items():
        samples = [r["outputs"][output] for r in measured["rows"][1:]] if measured else []
        observed = max((r["settling_s"] for r in samples), default=None) if samples and all(
            r["settling_s"] is not None for r in samples) else None
        rows.append(dict(output=output, sta_s=predicted, spice_s=observed,
                         passed=all(r["passed"] for r in samples) and observed is not None if samples else None,
                         signed_error_percent=100 * (predicted / observed - 1) if observed else None,
                         error_s=predicted - observed if observed is not None else None))
    return rows


def _publish_evidence(row, directory):
    """Small portable evidence accompanies JSON; raw local stages stay in work/."""
    import gzip
    n = row["n"]
    folder = directory / "work" / f"dot{n}"
    destination = directory / f"dot{n}"
    destination.mkdir(parents=True, exist_ok=True)
    paths = []
    for relative in (f"dot{n}.tv", f"dot{n}.json", f"dot{n}.gds", f"dot{n}.pnr.json", f"dot{n}.drc.lyrdb", f"dot{n}.drc.log",
                     f"dot{n}.pnr.failure.json",
                     "postlayout.spice", "capacitance.json", "vectors.json", "sta.json", "static.json",
                     "post/measurements.json", "post/tb.spice", "post/ngspice.log", "lvs/lvs.json"):
        source = folder / relative
        if source.is_file():
            target = destination / (relative.replace("/", "_") + ".gz")
            # Deterministic gzip: avoid timestamps and local file names.
            target.write_bytes(gzip.compress(source.read_bytes(), mtime=0))
            paths.append(target)
    if row.get("lvs"):
        for name in ("report", "extracted"):
            source = Path(row["lvs"][name])
            target = destination / f"lvs_{name}{source.suffix}.gz"
            target.write_bytes(gzip.compress(source.read_bytes(), mtime=0))
            paths.append(target)
    for source in sorted((folder / "dc").rglob("*")):
        if source.is_file() and source.name in {"tb.spice", "ngspice.log"}:
            relative = source.relative_to(folder)
            target = destination / (str(relative).replace("/", "_") + ".gz")
            target.write_bytes(gzip.compress(source.read_bytes(), mtime=0))
            paths.append(target)
    return paths


def run_scaling(sizes=SIZES, *, directory=COMPANIONS, result=RESULT, conditions=None, jobs=1):
    """Recompute/resume every requested N, then atomically publish one campaign."""
    from cache import file_hash, source_manifest
    from tritflow import PDK_ROOT

    sizes = list(sizes)
    if not sizes or len(set(sizes)) != len(sizes):
        raise ValueError("Choose a nonempty, unique set of term counts")
    for n in sizes:
        output_width(n)
    if isinstance(jobs, bool) or not isinstance(jobs, int) or jobs < 1:
        raise ValueError("jobs must be a positive integer")
    conditions = dict(conditions or CONDITIONS)
    directory, result = Path(directory), Path(result)
    identity = provenance()
    def samples():
        if jobs == 1:
            for n in sizes:
                yield run_size(n, identity, conditions=conditions, directory=directory)
        else:
            from concurrent.futures import ProcessPoolExecutor, as_completed
            with ProcessPoolExecutor(max_workers=min(jobs, len(sizes))) as pool:
                futures = [pool.submit(run_size, n, identity, conditions=conditions, directory=directory) for n in sizes]
                for future in as_completed(futures):
                    yield future.result()

    rows, evidence = [], []
    for row in samples():
        rows.append(row)
        rows.sort(key=lambda sample: sizes.index(sample["n"]))
        evidence += _publish_evidence(row, directory)
        data = dict(schema_version=1, experiment="ternary-weight dot product, variable 1-trit weights and activations",
                    generated_utc=datetime.now(timezone.utc).isoformat(), provenance=identity,
                    conditions=conditions, requested_sizes=sizes, rows=rows,
                    passed=all(row["passed"] for row in rows) and len(rows) == len(sizes),
                    complete=len(rows) == len(sizes),
                    measurement="1 ns ramp start to final entry into the ideal ±0.5 V band through the full segment; "
                                "2 ns maximum timestep; independent integer dot-product oracle; nominal 27 °C.",
                    limits="Finite fixed-weight vector pairs; matched STA is not a global timing bound. "
                           "Ideal ±5/0 V supply sources. No rail IR, signal wire R, PVT sweep, or calibrated sign-off PEX. "
                           "Wire C is area/perimeter based with published estimator assumptions. "
                           "Drawing-deck DRC and strict device/port LVS do not establish MPW mask sign-off. "
                           "Source expression is left associative and is lowered by the public synthesizer; no manual balancing.",
                    evidence_sha256={str(p.relative_to(ROOT)): file_hash(p) for p in evidence})
        current = source_manifest(ROOT, PDK_ROOT, names=identity["sources_sha256"])
        if current != identity["sources_sha256"]:
            data.update(complete=False, passed=False, stale=True)
            _save(result, data)
            raise RuntimeError("Consumed sources changed during dot scaling; rerun in a fresh process")
        _save(result, data)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recompute", action="store_true", help="explicitly run synthesis/PNR/DRC/LVS/STA/ngspice")
    parser.add_argument("--sizes", nargs="+", type=int, default=list(SIZES))
    parser.add_argument("--timeout", type=float, default=CONDITIONS["timeout_s"])
    parser.add_argument("--jobs", type=int, default=1, help="independent sizes in separate processes")
    args = parser.parse_args()
    if args.recompute:
        data = run_scaling(args.sizes, conditions=CONDITIONS | {"timeout_s": args.timeout}, jobs=args.jobs)
    else:
        data = verify_record(json.loads(RESULT.read_text()))
    for row in data["rows"]:
        print(f"N={row['n']}: {row['state']}; cells={row.get('synthesis', {}).get('total_cells')}; "
              f"SPICE={row.get('spice', {}).get('state', 'not reached')}; passed={row['passed']}")
    return 0 if data["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
