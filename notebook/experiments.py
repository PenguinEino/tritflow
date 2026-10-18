"""Notebook-sized experiments assembled only from public stream APIs."""

import json
from hashlib import sha256
from pathlib import Path
import shutil

from tritflow import flow
from tritflow.extract import estimate_ir_drop
from tritflow.synth import write_artifacts


def complete_design(net, directory, vectors, expected, *, load_f=10e-15,
                    hold_s=500e-9, step_s=2e-9, rows=None, anneal_steps=600, seed=0):
    """Real GDS + DRC/LVS + matched pre/post vectors + separate rail-IR envelope.

    ``expected`` is an independent integer oracle. The analog sequence is
    explicit: exhausting states does not exhaust directed transitions. IR uses
    nominal characterized currents and assumed sheet/via R, with ideal-rail
    SPICE kept separate. Every assertion applies on the producer path; callers
    must also assert cached flags before displaying them.
    """
    write_artifacts(net, directory)
    lay = net.place_and_route(output_dir=directory, rows=rows, anneal_steps=anneal_steps, seed=seed)
    drc, lvs = lay.drc(), lay.lvs()
    assert drc["clean"] and lvs["matched"], (drc, lvs)
    extracted = lay.extract()
    options = dict(load=load_f, hold_s=hold_s, step_s=step_s, expected=expected, timeout=300)
    pre = net.simulate(vectors, workdir=directory/"pre", **options)
    post = extracted.simulate(vectors, workdir=directory/"post", **options)
    assert pre["measurements"]["passed"] and post["measurements"]["passed"]
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
            "capacitance": extracted.capacitance, "ir": ir}


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
            current = Path(pdk)/"libs.tech"/original.split("/libs.tech/", 1)[1]
        else:
            anchor = next((s for s in ("tritflow", "examples", "cells") if f"/{s}/" in original), None)
            if anchor is None:
                raise RuntimeError(f"unrecognized publication source: {original}")
            current = Path(root)/anchor/original.split(f"/{anchor}/", 1)[1]
        if not current.is_file() or sha256(current.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"published result is stale relative to {current}")
