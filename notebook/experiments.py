"""Notebook-sized experiments assembled only from public stream APIs."""

import json

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
