"""Notebook-sized experiments assembled only from public stream APIs."""

import ast
import json
from hashlib import sha256
from pathlib import Path
import shutil
import time
import resource

from tritflow import flow
from tritflow.extract import estimate_ir_drop
from tritflow.synth import write_artifacts
from routing_identity import routing_files


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
                    initialize_internal=False, dataset='notebook'):
    """Real GDS + DRC/LVS + matched pre/post vectors + separate rail-IR envelope.

    ``expected`` is an independent integer oracle. The analog sequence is
    explicit: exhausting states does not exhaust directed transitions. IR uses
    nominal characterized currents and assumed sheet/via R, with ideal-rail
    SPICE kept separate. Every assertion applies on the producer path; callers
    must also assert cached flags before displaying them.
    """
    timings = {}
    cpu_times = {}
    def timed(name, action):
        start = time.perf_counter()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        process_before = time.process_time()
        value = action()
        timings[name] = time.perf_counter()-start
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu_times[name] = (time.process_time()-process_before +
                          after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime)
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
        return [" ".join(line.split()).upper() for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("*") and not line.startswith("Ctfwire")]
    assert intrinsic(device_only.spice) == intrinsic(extracted.spice)
    options = dict(load=load_f, hold_s=hold_s, step_s=step_s, expected=expected, timeout=600)
    guesses = {"pre": {}, "post": {}}
    if initialize_internal:
        # Soft Newton guesses address nonphysical BSIM operating-point roots.
        # They are never .ic/uic constraints and never replace the independent
        # arithmetic oracle or constrain any subsequent transient sample.
        from tritflow.sim.postlayout import logical_nodeset
        pins = [p.name for p in net.ports if p.dir == "input"]
        guesses["post"] = logical_nodeset(net,lvs["report"],pins,vectors[0])
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
            "timings_s": timings, "cpu_times_s": cpu_times,
            "routing":routing_files(directory/f'{net.top}.pnr.json',directory/f'{net.top}.gds',dataset)}


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


def schematic_extension_proof(path, expected):
    """Prove one optional display hook is the only change to recorded mapping.

    The complete recorded file SHA must be recovered by deleting the exact
    public SCHEM delegate, including at most its following blank line. No
    normalization of the remaining source is allowed. The delegate has no
    decorators, default expressions or annotations, and no class-time effects.
    This is compatibility with an old recorded run, never new qualification.
    """
    path = Path(path)
    if path.name != "mapping.py" or path.parent.name != "synth":
        return None
    raw = path.read_bytes()
    try:
        tree = ast.parse(raw)
    except SyntaxError:
        return None
    methods = [method for cls in tree.body if isinstance(cls,ast.ClassDef) and cls.name == "SynthesizedNetlist"
               for method in cls.body if isinstance(method,ast.FunctionDef) and method.name == "schematic"]
    if len(methods) != 1:
        return None
    method = methods[0]
    start, end = method.lineno-1, method.end_lineno
    if isinstance(method.body[0],ast.Expr) and isinstance(method.body[0].value,ast.Constant) and isinstance(method.body[0].value.value,str):
        method.body.pop(0)
    safe = ast.parse("def schematic(self, **options):\n from tritflow.schematic import draw\n return draw(self, **options)\n").body[0]
    if ast.dump(method,include_attributes=False) != ast.dump(safe,include_attributes=False):
        return None
    lines = raw.splitlines(keepends=True)
    ends = [end] + ([end+1] if end < len(lines) and not lines[end].strip() else [])
    if any(sha256(b"".join(lines[:start]+lines[stop:])).hexdigest() == expected for stop in ends):
        return {"path":str(path),"recorded_sha256":expected,"live_sha256":sha256(raw).hexdigest(),
                "proof":"Only the optional schematic(self, **options) display delegate was added; deleting it recovers the complete recorded source SHA. All mapping/report code bytes are identical. Recorded results, not new qualification."}
    return None


def verify_publication_sources(record, root, pdk):
    """Check a published run's sources after relocation, without needing build/.

    Raw ignored build artifacts are provenance of the recorded run, not inputs
    to plotting committed JSON. Code/library/HDL/PDK hashes must still agree.
    Returns disclosed compatibility proofs for an exact display-only extension;
    every other consumed byte must match. This does not rerun DRC/LVS.
    """
    sources = record.get("sources_sha256")
    if not sources:
        raise RuntimeError("published source fingerprints are missing")
    compatible = []
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
        if any(p.is_file() and sha256(p.read_bytes()).hexdigest() == expected for p in candidates):
            continue
        proof = next((proof for p in candidates if p.is_file()
                      and (proof := schematic_extension_proof(p,expected))),None)
        if proof:
            compatible.append(proof)
        else:
            raise RuntimeError(f"published result is stale relative to {original}")
    return compatible
