"""Notebook-sized experiments assembled only from public stream APIs."""

import json
from hashlib import sha256
from pathlib import Path
import shutil
import time

from tritflow import flow, TRIT_VOLTS
from tritflow.extract import estimate_ir_drop, reference_net_map
from tritflow.sim.spice import simulation_netlist
from tritflow.synth import write_artifacts, evaluate_netlist


def adder_demo_vectors(inputs, width=2):
    """Ordered rail-restoration and carry assert/release cases, never a truth tour.

    Digits in the case definitions are least-significant first. Return vectors
    in the actual elaborated port order rather than relying on bus ordering.
    """
    zero = [0]*width
    cases = [("zero", zero, zero, 0)]
    for bit in range(width):
        for sign, label in ((1,"positive"),(-1,"negative")):
            operand = zero.copy()
            operand[bit] = sign
            cases.append((f"{label}_digit_{bit}",operand,zero,0))
    for sign, label in ((1,"positive"),(-1,"negative")):
        for suffix, carry in (("setup",0),("carry_assert",sign),("carry_release",0)):
            cases.append((f"{label}_{suffix}",[sign]*width,zero,carry))
    cases.append(("return_zero",zero,zero,0))
    vectors = []
    for _, a, b, carry in cases:
        values = {f"a[{i}]":a[i] for i in range(width)} | {f"b[{i}]":b[i] for i in range(width)} | {"cin":carry}
        vectors.append(tuple(values[p] for p in inputs))
    return vectors, [label for label, *_ in cases]


def complete_design(net, directory, vectors, expected, *, load_f=10e-15,
                    hold_s=500e-9, step_s=2e-9, rows=None, anneal_steps=600, seed=0,
                    initialize_internal=False):
    """Real GDS + DRC/LVS + matched pre/post vectors + separate rail-IR envelope.

    ``expected`` is an independent integer oracle. The analog sequence is
    explicit: exhausting states does not exhaust directed transitions. IR uses
    nominal characterized currents and assumed sheet/via R, with ideal-rail
    SPICE kept separate. Every assertion applies on the producer path; callers
    must also assert cached flags before displaying them.
    """
    timings = {}
    def timed(name, action):
        start = time.perf_counter()
        value = action()
        timings[name] = time.perf_counter()-start
        return value
    write_artifacts(net, directory)
    lay = timed("pnr_including_drc", lambda: net.place_and_route(
        output_dir=directory, rows=rows, anneal_steps=anneal_steps, seed=seed))
    # PNR just ran the official deck on the published GDS. Reuse its actual
    # report here; no second identical DRC invocation is needed in this stage.
    drc = lay.data["checks"]["pdk_drc"]
    lvs = timed("strict_lvs", lay.lvs)
    assert drc["clean"] and lvs["matched"], (drc, lvs)
    device_only = lay.extract(wire_c=False)
    extracted = timed("wire_capacitance", lay.extract)
    added = [line for line in extracted.spice.splitlines() if line.startswith("Ctfwire")]
    assert len(added) == sum(row["capacitance_f"] > 0 for row in extracted.capacitance["nets"].values())
    # Only wire capacitors may distinguish this controlled experiment. The
    # original mapped-cell schematic remains the independent LVS reference.
    def intrinsic(text):
        return [line.strip() for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("*") and not line.startswith("Ctfwire")]
    assert intrinsic(device_only.spice) == intrinsic(extracted.spice)
    options = dict(load=load_f, hold_s=hold_s, step_s=step_s, expected=expected, timeout=300)
    guesses = {"pre": {}, "post": {}}
    if initialize_internal:
        # Soft Newton guesses address nonphysical BSIM operating-point roots.
        # They are never .ic/uic constraints and never replace the independent
        # arithmetic oracle or constrain any subsequent transient sample.
        pins = [p.name for p in net.ports if p.dir == "input"]
        ports = {p.name for p in net.ports}
        values = evaluate_netlist(net,dict(zip(pins,vectors[0],strict=True)),return_all=True)
        internal = {name:TRIT_VOLTS[int(value)] for name,value in values.items() if name not in ports}
        mapping = {name.lower():node for name,node in reference_net_map(lvs["report"],net.top).items()}
        for name, voltage in internal.items():
            node = mapping[name.lower()]
            node = simulation_netlist("\\"+node if node.startswith("$") else node)
            guesses["pre"]["xdut."+name] = voltage
            guesses["post"]["xdut."+node] = voltage
    # Both runs use the same extracted terminal orientation (including the
    # asymmetric F_RR intrinsic C); this isolates the added wire-C effect.
    guesses["pre"] = guesses["post"].copy()
    pre = timed("pre_ngspice", lambda: device_only.simulate(vectors, workdir=directory/"pre", nodeset=guesses["pre"], **options))
    post = timed("post_ngspice", lambda: extracted.simulate(vectors, workdir=directory/"post", nodeset=guesses["post"], **options))
    assert pre["measurements"]["passed"] and post["measurements"]["passed"], {
        mode:result["measurements"] for mode,result in (("pre",pre),("post",post))}
    assert pre["stimulus"]["vectors"] == post["stimulus"]["vectors"]
    assert pre["stimulus"]["hold_s"] == post["stimulus"]["hold_s"]
    cells = net.settings.cells
    used = {inst.cell for inst in net.instances}
    def read(relative):
        return json.loads((cells/relative).read_text())
    ir = estimate_ir_drop(lay.data, read("template.json"),
                         {c: read(f"out/{c}/{c}.abstract.json") for c in used},
                         {c: read(f"out/{c}/{c}.char.json") for c in used})
    return {"pre": pre, "post": post, "drc": drc, "lvs": lvs, "stats": lay.stats,
            "capacitance": extracted.capacitance, "ir": ir, "initial_nodeset_v": guesses,
            "timings_s": timings}


def experiment_artifacts(result, directory, top):
    """Files whose deletion/edit invalidates a cached physical/analog result."""
    return [directory/f"{top}.json", directory/f"{top}.gds", directory/f"{top}.pnr.json",
            result["drc"]["report_path"], result["lvs"]["report"], result["lvs"]["extracted"],
            *[directory/mode/name for mode in ("pre", "post") for name in ("tb.spice", "ngspice.log")]]


def assert_experiment(result):
    """Check saved or fresh outcomes alike, never treating a cache hit as PASS."""
    assert result["drc"]["clean"] and result["lvs"]["matched"]
    assert result["pre"]["measurements"]["passed"] and result["post"]["measurements"]["passed"]
    assert result["pre"]["stimulus"]["vectors"] == result["post"]["stimulus"]["vectors"]
    assert not result["stats"]["library_mock"]


def load_edited(example, source, directory):
    """Stage editable HDL with its shared includes; never overwrite examples."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for dependency in example.path.parent.glob("*.tv"):
        shutil.copy2(dependency, directory/dependency.name)
    edited = directory/example.path.name
    edited.write_text(source)
    return flow.load(edited, example.top)


def verify_publication_sources(record, root, pdk):
    """Check a published run's sources after relocation, without needing build/.

    Raw ignored build artifacts are provenance of the recorded run, not inputs
    to plotting committed JSON. Code/library/HDL/PDK hashes must still agree.
    This does not assert that the recorded DRC/LVS has been rerun locally.
    """
    sources = record.get("sources_sha256")
    if not sources:
        raise RuntimeError("published source fingerprints are missing")
    for original, expected in sources.items():
        if "/build/" in original:
            continue
        if "/libs.tech/" in original:
            candidates = [Path(pdk)/"libs.tech"/original.rsplit("/libs.tech/", 1)[1]]
        elif "/openIP62/" in original:
            candidates = [Path(pdk)/"openIP62"/original.rsplit("/openIP62/", 1)[1]]
        else:
            # A checkout itself can be named tritflow; package subdirectories
            # can be named cells. Resolve against existing content, rather than
            # treating either occurrence as an unambiguous repository boundary.
            candidates = [Path(root)/anchor/original.rsplit(f"/{anchor}/", 1)[1]
                          for anchor in ("tritflow", "examples", "cells") if f"/{anchor}/" in original]
            if not candidates:
                raise RuntimeError(f"unrecognized publication source: {original}")
        if not any(p.is_file() and sha256(p.read_bytes()).hexdigest() == expected for p in candidates):
            raise RuntimeError(f"published result is stale relative to {original}")
