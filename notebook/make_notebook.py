"""Regenerate the concise, output-free submission notebook from reviewable cells."""

import json
from pathlib import Path
import textwrap


cells = []


def cell(kind, source):
    item = {"cell_type": kind, "id": f"tritflow-{len(cells):02d}", "metadata": {},
            "source": textwrap.dedent(source).strip()+"\n"}
    if kind == "code":
        item.update(execution_count=None, outputs=[])
    cells.append(item)


def md(source):
    cell("markdown", source)


def code(source):
    cell("code", source)


md("""
# TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb)

Draft for IEEE SSCS Code-a-Chip, ISSCC 2027. Audience: designers familiar with
CMOS, synthesis, P&R and SPICE. We follow a real three-rail circuit through the
flow, separating logical equivalence, physical connectivity and nominal analog
settling. Coverage and conditions are generated beside each result.

Colab shallow-clones [TritFlow](https://github.com/PenguinEino/tritflow) at
`colab-v0` into `/content/tritflow`, prints the resolved commit and installs
the package editably beside its committed cell/example/figure assets. Set
`TRITFLOW_REF` before the first cell to select another tag or branch. An existing
Colab checkout must match the requested ref and have no tracked edits.
**Release TODO — integrator:** create the `colab-v0` tag after committing this
notebook. Fresh Colab execution and the install-inclusive ten-minute budget
remain unverified.

The default run starts with a small adder, then closes the loop on every shared
example and one selected circuit. Coverage is reported beside each experiment.
Heavy stages use content-keyed JSON caches; `TRITFLOW_EXTENDED=1` enables extra
load/routing views. Cached reports are identified as cache hits and their
artifact hashes are checked. A cache is evidence of the recorded run, not a new
DRC/LVS execution. Clear `build/notebook/cache` to force recomputation.
""")
code(r'''
import os, sys, json, time, hashlib, subprocess, importlib.util
from pathlib import Path
started = time.monotonic()
try:
    IN_COLAB = importlib.util.find_spec("google.colab") is not None
except ModuleNotFoundError:
    IN_COLAB = False
SOURCE_URL = "https://github.com/PenguinEino/tritflow.git"
SOURCE_REF = os.environ.get("TRITFLOW_REF", "colab-v0")
def source_git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
if IN_COLAB:
    ROOT = Path("/content/tritflow")
    if not SOURCE_REF or SOURCE_REF.startswith("-") or any(c.isspace() for c in SOURCE_REF):
        raise ValueError("TRITFLOW_REF must name a Git tag or branch")
    if not ROOT.exists():
        subprocess.run(["git", "clone", "--depth", "1", "--single-branch", "--branch", SOURCE_REF,
                        SOURCE_URL, str(ROOT)], check=True)
    if not (ROOT/".git").is_dir():
        raise RuntimeError("/content/tritflow must be a git clone; use a fresh Colab runtime")
    if source_git("remote", "get-url", "origin").removesuffix(".git") != SOURCE_URL.removesuffix(".git"):
        raise RuntimeError("existing checkout has a different origin; use a fresh Colab runtime")
    SOURCE_COMMIT = source_git("rev-parse", "--verify", "HEAD^{commit}")
    requested_commit = source_git("rev-parse", "--verify", SOURCE_REF+"^{commit}")
    if SOURCE_COMMIT != requested_commit or source_git("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("existing checkout differs from TRITFLOW_REF; use a fresh Colab runtime")
    print(f"Source: {SOURCE_URL} ref={SOURCE_REF} commit={SOURCE_COMMIT}", flush=True)
    runtime = ROOT/"notebook/runtime.json"
    if not runtime.is_file():
        subprocess.run(["bash", str(ROOT/"notebook/colab_setup.sh"), "--source", str(ROOT)], check=True)
    os.environ.update(json.loads(runtime.read_text()))
else:
    candidates = [Path(os.environ.get("TRITFLOW_ROOT", ".")), Path.cwd(), Path.cwd().parent]
    ROOT = next((p.resolve() for p in candidates if (p/"pyproject.toml").is_file()
                 and (p/"tritflow").is_dir()), None)
    if ROOT is None:
        raise RuntimeError("run locally from the full checkout or set TRITFLOW_ROOT")
    SOURCE_COMMIT = source_git("rev-parse", "--verify", "HEAD^{commit}") if (ROOT/".git").exists() else "tracked-tree export (no .git)"
    print(f"Source: {ROOT} commit={SOURCE_COMMIT}")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/"notebook"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
''')
code('''
import numpy as np
from IPython.display import display, HTML, Image
from tritflow import flow, CELLS_DIR, PDK_ROOT, PASS_BAND, TRIT_VOLTS
from tritflow.sim import dc_transfer, input_vectors, subcircuits
from tritflow.viz.graph import color_nets, gate_graph, truth_table_html
from tritflow.viz.waves import waveform_figure, transfer_figure
from tritflow.viz.layout import render_gds, layout_figure, placement_animation, routing_progress
from cache import Cache, runtime_fingerprint
from schematics import schematic_gallery
from experiments import (complete_design, experiment_artifacts, assert_experiment,
                         load_edited, verify_publication_sources)
EXTENDED = os.environ.get("TRITFLOW_EXTENDED", "0") == "1"
BUILD = Path(os.environ.get("TRITFLOW_NOTEBOOK_BUILD", ROOT/"build/notebook")).resolve()
cache = Cache(BUILD/"cache", runtime_fingerprint(ROOT, PDK_ROOT))
def show(figure):
    if os.environ.get("TRITFLOW_NOTEBOOK_HEADLESS") == "1":
        figure.to_json()  # still validate every figure during local execution
    else:
        display(figure)
def table(rows):
    from html import escape
    display(HTML("<div style='overflow-x:auto'><table>"+"".join("<tr>"+"".join("<td style='padding:.3em .8em'>"+
        escape(str(v))+"</td>" for v in row)+"</tr>" for row in rows)+"</table></div>"))
''')
md('''
## 0. Start with the complete adder flow

A trit is −1, 0 or +1, represented by −5, 0 or +5 V. It is distinct from
Verilog's four-state logic. We first build a two-trit ripple adder from HDL,
route real cells into GDS, check DRC/LVS, and simulate extracted devices plus
estimated wire capacitance. Integer arithmetic supplies an independent oracle.
The logical test is exhaustive. The generated coverage table distinguishes it
from the representative analog sequence, which includes initialization and
return. The analog sequence covers neither all directed transitions nor PVT.
''')
code('''
d = flow.load(ROOT/"examples/adder.tv", "adder", {"N": 2})
net = d.synthesize(name="adder2_demo")
logical = d.truth_table()
inputs = [p.name for p in net.ports if p.dir == "input"]
outputs = [p.name for p in net.ports if p.dir == "output"]
vectors = [(-1,)*len(inputs), (0,)*len(inputs), (1,)*len(inputs),
           (1,-1,-1,1,0), (-1,1,1,-1,1), (-1,)*len(inputs)]
LOAD_F, HOLD_S, STEP_S, EDGE_S, TEMP_C = 100e-15, 1e-6, 2e-9, 1e-9, 27
PNR_ROWS, PNR_ANNEAL_STEPS = None, 600  # automatic near-square floorplan; placement effort
assert all(len(v) == len(inputs) for v in vectors)
assert len(logical[inputs[0]]) == 3**len(inputs)
def adder_reference(vector):
    v = dict(zip(inputs, vector, strict=True))
    remainder = sum((v[f"a[{i}]"] + v[f"b[{i}]"])*3**i for i in range(2)) + v["cin"]
    result = {}
    for i in range(2):
        result[f"sum[{i}]"] = (remainder+1)%3-1
        remainder = (remainder-result[f"sum[{i}]"])//3
    return {**result, "cout": remainder}
for row in zip(*(logical[name] for name in inputs)):
    assert adder_reference(row) == {k: int(v) for k,v in d.design.evaluate(dict(zip(inputs,row))).items()}
out = BUILD/"adder2_demo"
def complete_adder():
    lay = net.place_and_route(output_dir=out, seed=0, rows=PNR_ROWS, anneal_steps=PNR_ANNEAL_STEPS)
    drc = lay.drc()
    lvs = lay.lvs()
    assert drc["clean"] and lvs["matched"], (drc, lvs)
    extracted = lay.extract()
    post = extracted.simulate(vectors, load=LOAD_F, hold_s=HOLD_S, step_s=STEP_S, edge_s=EDGE_S,
                              temperature_c=TEMP_C, expected=adder_reference, timeout=180, workdir=out/"post")
    assert post["measurements"]["passed"], post["measurements"]
    return {**post, "stats": lay.stats, "drc": drc, "lvs": lvs,
            "extracted_spice": extracted.spice, "capacitance": extracted.capacitance}
demo = cache.run("adder2-complete", {"net": net.to_json(), "vectors": vectors, "load": LOAD_F,
                                   "hold": HOLD_S, "step": STEP_S, "edge": EDGE_S,
                                   "temperature_c":TEMP_C, "seed": 0,
                                   "rows":PNR_ROWS,"anneal_steps":PNR_ANNEAL_STEPS}, complete_adder,
    artifacts=lambda r: [out/"adder2_demo.gds", out/"adder2_demo.pnr.json",
                         r["drc"]["report_path"], r["lvs"]["report"], r["lvs"]["extracted"]])
lay = flow.load_layout(net, out)
assert demo["drc"]["clean"] and demo["lvs"]["matched"] and demo["measurements"]["passed"]
assert not lay.stats["library_mock"]
table([["Logical input states (exhaustive)", len(logical[inputs[0]])],
       ["Analog states / unique states", f"{len(vectors)} / {len(set(vectors))}"],
       ["Analog transitions (selected / possible)", f"{len(vectors)-1} / {3**len(inputs)*(3**len(inputs)-1)}"],
       ["Configured rails (trit: V)", TRIT_VOLTS], ["Level acceptance band (V)", PASS_BAND],
       ["Nominal temperature (°C)", TEMP_C],
       ["Output load (fF)", LOAD_F*1e15], ["Hold / ramp / max step (ns)",
        [HOLD_S*1e9,EDGE_S*1e9,STEP_S*1e9]],
       ["Cells", net.report()["cells"]], ["GDS", lay.gds_path],
       ["Die dimensions (µm)", lay.stats["die_size_um"]],
       ["Die aspect (long / short)", max(lay.stats["die_size_um"])/min(lay.stats["die_size_um"])],
       ["Die area (µm²)", lay.stats["die_area_um2"]], ["DRC violations", demo["drc"]["violations"]],
       ["LVS matched", demo["lvs"]["matched"]], ["Analog passed", demo["measurements"]["passed"]],
       ["Max error (V)", demo["measurements"]["max_error_v"]]])
show(color_nets(net, dict(zip(inputs, vectors[2]))))
show(waveform_figure(demo, outputs, title="Extracted two-trit adder: representative vectors"))
raster = cache.run("adder2-raster", {"gds":hashlib.sha256(lay.gds_path.read_bytes()).hexdigest()},
    lambda: {"png":str(render_gds(lay.gds_path, out/"adder2_demo.layout.png", top=net.top))},
    artifacts=lambda r: [r["png"]])
display(Image(filename=raster["png"], width=900))
show(layout_figure(lay.data, highlight_net="sum[0]", show_power=True))
''')
md('''
The raster is rendered from the actual GDS by KLayout. The interactive vector
view selects nets/cells and retains source hierarchy in hover. Presence of a
GDS file alone is not evidence of a clean check; the DRC/LVS reports are.
''')
md('''
## 1. Learn the gates

INV is −a, NAND is −min(a,b), NOR is −max(a,b), and NANY is the negative
saturated sum. Therefore min/max need an extra INV when mapped from a positive
HDL expression. At a=0, both min(a,−a) and max(a,−a) equal 0: Boolean
complementation laws cannot be used. The asserted truth table and historical
source drawings below connect these equations to the circuit topology. Their
hashes identify the exported sources; they do not qualify the new layout.
''')
code('''
gates = flow.loads("""module gates(input trit a,b,output trit inva,nandab,norab,nanyab);
 assign inva=~a; assign nandab=~(a&b); assign norab=~(a|b); assign nanyab=nany(a,b);
 endmodule""")
t = gates.truth_table()
assert np.array_equal(t["inva"], -t["a"])
assert np.array_equal(t["nandab"], -np.minimum(t["a"], t["b"]))
assert np.array_equal(t["norab"], -np.maximum(t["a"], t["b"]))
assert np.array_equal(t["nanyab"], -np.clip(t["a"]+t["b"],-1,1))
display(truth_table_html(gates.design))
for name in ["INV","NAND","NOR","NANY"]:
    body = subcircuits((CELLS_DIR/f"out/{name}/{name}.spice").read_text())[name.lower()]["body"]
    assert ("VMID" in body.upper()) == (name == "NANY"), name
display(HTML(schematic_gallery(ROOT/"notebook/assets/schematics")))
cell_spice = (CELLS_DIR/"out/NANY/NANY.ext.spice").read_text()
DC_FIXED_B, DC_STEP_V = 0, .1
curve = cache.run("nany-dc", {"fixed_B": DC_FIXED_B, "step_v": DC_STEP_V}, lambda:
    dc_transfer(cell_spice, "NANY", ["A","B"], ["Y"], "A",
                fixed_trits={"B":DC_FIXED_B}, step_v=DC_STEP_V))
show(transfer_figure(curve, "A", ["Y"],
                     title=f"NANY DC: B={DC_FIXED_B} trit ({TRIT_VOLTS[DC_FIXED_B]:g} V)"))
''')
md('''
The primitive crops retain instance W/L properties and omit obsolete free-text
sizing sidebars in the source drawings. Light/dark variants have opaque backing;
expand the provenance control to compare them. NANY's clamp uses VMID; the
other displayed primitive bodies do not, as checked against their SPICE above.

## 2. Size and characterize a cell

The table reads the published characterization, verifies its source/model
hashes, and checks its recorded pass flags. Conditions and tested loads are
shown from that data. Input capacitance is a biased AC driving-point measure,
including Miller response. Fanout method/scope are shown verbatim from the
record: these nominal tests do not establish PVT or arbitrary path timing.
''')
code('''
characters = {cell: json.loads((CELLS_DIR/f"out/{cell}/{cell}.char.json").read_text())
              for cell in ["INV","NAND","NOR","NANY","BUF"]}
rows = [["Cell", "Max DC error (mV)", "Max static rail |I| (µA)", "Input C (fF)", "Suggested fanout"]]
for cell, char in characters.items():
    assert hashlib.sha256((CELLS_DIR/f"out/{cell}/{cell}.ext.spice").read_bytes()).hexdigest() == char["source_sha256"]
    assert all(hashlib.sha256((PDK_ROOT/"libs.tech/spice/models"/name).read_bytes()).hexdigest() == value
               for name,value in char["model_sha256"].items()), cell
    assert char["passed"] and all(row["passed"] for row in char["dc"])
    assert len({tuple(row["input_trits"]) for row in char["dc"]}) == 3**len(char["inputs"])
    assert all(result["passed"] for result in char["transient"])
    rows.append([cell, 1e3*max(abs(v) for row in char["dc"] for v in row["error_v"].values()),
                 max(abs(i) for row in char["dc"] for i in row["rail_current_a"].values())*1e6,
                 char["input_capacitance"]["max_f"]*1e15, char["fanout"]["suggested_max"]])
table(rows)
table([["Cell", "Recorded conditions", "Tested loads (fF)", "Fanout evidence"]]+
      [[cell, char["conditions"], [r["load_f"]*1e15 for r in char["transient"]], char["fanout"]]
       for cell,char in characters.items()])
fanout_rows = [["Cell", "Measured receiver counts", "Chain depth", "Worst chain (ns)",
                "Driver at largest tested fanout (ns)", "Max level error (mV)"]]
for cell, char in characters.items():
    cascade = char["cascade"]
    assert cascade["source_sha256"] == char["source_sha256"]
    assert cascade["passed"] and cascade["chains_passed"] and all(c["passed"] for c in cascade["cases"])
    largest = max(cascade["fanouts_tested"])
    chain_times = [t for c in cascade["cases"] if c["mode"] == "chain"
                   for t in c["max_settling_s"].values() if t is not None]
    loaded_times = [c["max_settling_s"]["y0"] for c in cascade["cases"]
                    if c["mode"] == "fanout" and c["fanout"] == largest]
    fanout_rows.append([cell, cascade["fanouts_tested"], cascade["chain_depth"],
                       max(chain_times)*1e9, max(loaded_times)*1e9,
                       max(c["max_error_v"] for c in cascade["cases"])*1e3])
table(fanout_rows)
''')
md('''
Each receiver is a transistor-level load. The largest tested count is a measured
nominal bound, not an extrapolation to larger fanout or PVT. The chain checks
every intermediate output. Isolated-cell load sweeps and self-loading chains
answer different questions; their conditions are displayed separately above.

**SIM publication slot — W/L sweep:** `cells/out/sizing/` supplies cached
transfer/error/current data. When available, the code below reads SIM's public
`load_grid(cell)` and uses `sizing_figure(result)` to mark the adopted dimensions.
Missing or stale grids leave an explicit TODO. Full characterization is not
rerun by default. To compute new sparse device overrides, use
`sweep_dimensions(cell, candidates, *, sweep_pin="A", fixed_trits=None,
start_v=-5., stop_v=5., step_v=.1, temperature_c=27., pdk=None,
workdir=None, timeout=120.)`; W/L values are µm, not SPICE metre suffixes.
''')
code('''
from tritflow.sim.sizing import load_grid, sweep_dimensions
from tritflow.viz.scaling import sizing_figure
SIZING_INDEX = {"INV": None, "NANY": None}  # None selects adopted; set a candidate index to inspect it
for cell in ["INV", "NANY"]:
    if not (CELLS_DIR/f"out/sizing/{cell}.grid.json").is_file():
        print(f"TODO SIM: publish cells/out/sizing/{cell}.grid.json (W/L sweep)")
        continue
    try:
        grid = load_grid(cell)
    except RuntimeError as error:
        print(f"TODO SIM: refresh {cell} sizing grid: {error}")
        continue
    adopted = grid["rows"][grid["adopted_index"]]
    table([["Cell", "Candidates", "PASS", "Adopted dimensions (µm)", "Conditions"],
           [cell, len(grid["rows"]), sum(r["passed"] for r in grid["rows"]),
            adopted["dimensions"], grid["conditions"]]])
    show(sizing_figure(grid))
    index = grid["adopted_index"] if SIZING_INDEX[cell] is None else SIZING_INDEX[cell]
    candidate = grid["rows"][index]
    table([["Selected candidate",index], ["Dimensions (µm)",candidate["dimensions"]],
           ["PASS / solver error",[candidate["passed"],candidate["error"]]]])
    if candidate["transfer"] is not None:
        show(transfer_figure(candidate["transfer"],grid["conditions"]["sweep_pin"],["Y"],
                             title=f"{cell}: candidate {index}, adopted={candidate['is_adopted']}"))
''')
md('''

## 3. Read the standard-cell views

Every cell supplies GDS, source SPICE, extracted SPICE, a physical abstract and
characterization. Rails run VDD / cell body / VMID / VSS. Read actual dimensions
and obstructions from the template/abstract; compact cells may use internal M2
and V1 if declared as routing obstacles. R0 and left/right reflection preserve
rail polarity. Cell-local DRC/LVS and abutment qualification are distinct from
top-level routed checks. The table verifies the published report's artifact
hashes before showing its flags; chapter 0 checks the routed design. TIE drive
remains a load-dependent property.
''')
code('''
template = json.loads((CELLS_DIR/"template.json").read_text())
generation = json.loads((CELLS_DIR/"out/generation.json").read_text())
abstracts = {item["name"]:json.loads((CELLS_DIR/"out"/item["abstract"]).read_text())
             for item in json.loads((CELLS_DIR/"out/library.json").read_text())}
assert {a["height"] for a in abstracts.values()} == {template["height"]}
assert generation["height_um"] == template["height"]
print("Published library generation:", generation["id"])
table([["Cell", "Width × common height (µm)", "Area (µm²)", "Free full-height M2 tracks"]]+
      [[name, [a["width"],a["height"]], a["width"]*a["height"], a["free_M2_tracks"]["count"]]
       for name,a in abstracts.items()])
abstract = json.loads((CELLS_DIR/"out/NANY/NANY.abstract.json").read_text())
table([["Height (µm)", template["height"]], ["Grid (µm)", template["grid"]],
       ["NANY width (µm)", abstract["width"]], ["Rails", template["rails"]],
       ["Pin names", list(abstract["pins"])], ["Obstruction layers", list(abstract["obstructions"])]])
image = CELLS_DIR/"out/NANY/NANY.png"
if image.is_file():
    display(Image(filename=str(image), width=700))
qualification = CELLS_DIR/"out/verify_report.json"
if qualification.is_file():
    report = json.loads(qualification.read_text())
    assert report["passed"]
    for cell, artifacts in report["artifact_sha256"].items():
        for suffix, expected_hash in artifacts.items():
            assert hashlib.sha256((CELLS_DIR/f"out/{cell}/{cell}.{suffix}").read_bytes()).hexdigest() == expected_hash
    table([["Cell", "Recorded DRC clean", "Recorded LVS qualification", "LVS method"]]+[
        [name, result["drc"]["passed"], result["lvs"]["passed"],
         result["lvs"].get("method","strict device/port comparison")]
        for name,result in report["cells"].items()])
    if "FILL" in report["cells"]:
        print("FILL qualification:", report["cells"]["FILL"]["lvs"]["explanation"])
    print("Recorded qualification scope:", report["scope"])
else:
    print("TODO CELLS: publish the cell qualification report; no cell-clean claim is made here")
''')
md('''
## 4. Describe arithmetic in TritVerilog

The reference half adder shares intermediates. Two such blocks and carry
combination produce the full adder. Gate counts are computed below and asserted
against the authored hierarchy. Its invariant is a+b+cin = sum+3·cout. Generate loops
replicate that slice; bit i has integer weight 3ⁱ. Only parameters/indices use
integer arithmetic in HDL; signal arithmetic is implemented with gates.
''')
code('''
ha = flow.load(ROOT/"examples/half_add.tv", "half_add")
fa = flow.load(ROOT/"examples/full_add.tv", "full_add")
display(truth_table_html(ha.design))
display(truth_table_html(fa.design))
fa_table = fa.truth_table()
ha_table = ha.truth_table()
assert np.array_equal(ha_table["a"]+ha_table["b"], ha_table["sum"]+3*ha_table["carry"])
assert np.array_equal(fa_table["a"]+fa_table["b"]+fa_table["cin"],
                      fa_table["sum"]+3*fa_table["cout"])
ha_counts, fa_counts = ha.synthesize().report()["cells"], fa.synthesize().report()["cells"]
schematic_sources = json.loads((ROOT/"notebook/assets/schematics/manifest.json").read_text())["schematics"]
ha_symbols = schematic_sources["half_adder"]["instances_by_symbol"]
fa_symbols = schematic_sources["full_adder"]["instances_by_symbol"]
symbol_names = {"INV":"inverter", "NANY":"nany"}
assert ha_counts == {cell:ha_symbols[symbol] for cell,symbol in symbol_names.items()}
assert fa_counts == {cell:fa_symbols["half_adder"]*ha_counts[cell]+fa_symbols[symbol]
                     for cell,symbol in symbol_names.items()}
table([["Circuit", "Cells", "Exhaustive input states"],
       ["half_add",ha_counts,len(ha_table["sum"])], ["full_add",fa_counts,len(fa_table["sum"])]])
print((ROOT/"examples/adder.tv").read_text())
''')
md('''
## 5. Follow synthesis into cells

Constant folding, double-negation removal, common-expression sharing and dead
logic removal operate on the ternary DAG. Negated min/max fuse into NAND/NOR;
positive min/max use NAND/NOR followed by INV. Constants map to TIEP/TIEZ/TIEN.
Authored live primitives retain identity. BUF trees bound input-pin fanout;
separate output aliases also need physical drivers. The synthesis report shows
the equivalence mode and vector count actually used for this design.
''')
code('''
fa_net = fa.synthesize()
assert fa_net.report()["equivalence"]["passed"]
assert fa_net.report()["equivalence"]["vectors"] == len(fa_table["sum"])
show(gate_graph(fa_net))
show(color_nets(fa_net, {"a": 1, "b": 1, "cin": -1}))
table([["Report field", "Value"]]+[[k,v] for k,v in fa_net.report().items()])
from tritflow.synth import tritverilog
print(tritverilog(fa_net))
mapping_cases = [("~a",["INV"]), ("~(a&b)",["NAND"]), ("a&b",["NAND","INV"]),
                 ("~(a|b)",["NOR"]), ("a|b",["NOR","INV"]), ("nany(a,b)",["NANY"]),
                 ("1'tT",["TIEN"]), ("1't0",["TIEZ"]), ("1't1",["TIEP"])]
mapping_rows = [["HDL expression", "Computed cells"]]
for expr, expected_cells in mapping_cases:
    mapped = flow.loads(f"module mapping(input trit a,b,output trit y); assign y={expr}; endmodule").synthesize()
    assert sorted(inst.cell for inst in mapped.instances) == sorted(expected_cells)
    mapping_rows.append([expr, mapped.report()["cells"]])
table(mapping_rows)
''')
md('''
## 6. Place, route and inspect GDS

The physical flow starts from signal-order placement, seeks shorter connections
with seeded annealing, and routes with A* and rip-up/retry on a two-layer grid. M1 routes
use channels; M2 crosses cells while respecting declared obstructions. Three
supplies connect row rails to trunks. Independent checks inspect drawn metal
islands, widths/spaces and via enclosures before the official PDK deck runs.
Top-level device LVS compares the exported GDS to mapped-cell connectivity.
''')
code('''
table([["Metric", "Two-trit adder"]]+[[k,v] for k,v in lay.stats.items()])
table([["Requested rows (None = automatic)",PNR_ROWS], ["Annealing steps",PNR_ANNEAL_STEPS],
       ["Actual physical rows",len(lay.data["rows"])], ["Utilization",lay.stats["utilization"]]])
print("Placement snapshots:", len(lay.data["history"]))
print("Routing attempts:", lay.data["routing_attempts"])
assert all(check["clean"] for check in lay.data["checks"].values())
assert lay.stats["routed_nets"] == len(net.nets())
assert {p["orient"] for p in lay.data["placements"]} <= {"R0","MY"}
table([["Check", "Clean"]]+[[name,check["clean"]] for name,check in lay.data["checks"].items()])
table([["Initial / final cell-terminal HPWL (µm)",
        [lay.data["history"][i]["hpwl"] for i in (0,-1)]]])
show(placement_animation(lay.data))
if EXTENDED:
    show(routing_progress(lay.data))
RUN_FLOORPLAN_EXPERIMENT = False  # opt in after changing the controls below
EXPERIMENT_ROWS, EXPERIMENT_ANNEAL_STEPS, EXPERIMENT_SEED = None, 2400, 7
if RUN_FLOORPLAN_EXPERIMENT:
    folder = BUILD/"floorplan_experiment"
    def route_experiment():
        routed = net.place_and_route(output_dir=folder, rows=EXPERIMENT_ROWS,
                   anneal_steps=EXPERIMENT_ANNEAL_STEPS, seed=EXPERIMENT_SEED)
        drc, lvs = routed.drc(), routed.lvs()
        assert drc["clean"] and lvs["matched"]
        return {"stats":routed.stats, "drc":drc, "lvs":lvs}
    trial = cache.run("floorplan-experiment", {"net":net.to_json(),"rows":EXPERIMENT_ROWS,
                     "steps":EXPERIMENT_ANNEAL_STEPS,"seed":EXPERIMENT_SEED}, route_experiment,
                     artifacts=[folder/f"{net.top}.gds",folder/f"{net.top}.pnr.json"])
    assert trial["drc"]["clean"] and trial["lvs"]["matched"]
    table([["Measured floorplan experiment",trial["stats"]]])
    show(placement_animation(flow.load_layout(net,folder).data))
''')
md('''
The placement animation uses recorded snapshots and cell-terminal HPWL.
With extended experiments enabled, routing progress replays the successful
recorded pass. Neither animation substitutes for the geometry checks.
`rows=None` searches row counts and independently fed power spans for a compact,
near-square floorplan; the dimensions/aspect/utilization shown are measured.
A positive `rows` fixes the physical row count. `anneal_steps=0` retains initial
placement; more steps spend effort on swaps/moves/reflections. Change the
opt-in controls above to compare geometry and HPWL. Row/feed current constraints
remain active in every saved placement. More steps do not guarantee a better
route, and explicit row counts can reduce utilization.

## 7. Measure settled levels and wiring effects

Level pass means the sampled output lies in the configured band around its
ideal trit voltage. Overall sequence pass also requires a finite settling time.
Settling is the final entry into that band and remaining inside through the
segment end under sampled-waveform linear interpolation. The SIM API measures
from ramp **start**, including the configured input ramp. Finite timestep limits
resolution; initialization is excluded from maximum transition delay.

The extracted devices retain intrinsic/junction effects. Added top-net wire C
uses actual connected GDS area/perimeter with explicitly assumed coefficients;
it is not calibrated signoff PEX. Signal-wire resistance, coupling, local poly
RC and PVT/mismatch are outside this experiment. The four-design loop below
also estimates a separate rail-IR envelope from drawn power geometry and
characterized currents; it does not perturb the ideal supplies in SPICE.
''')
code('''
pre = cache.run("adder2-pre", {"net":net.to_json(),"vectors":vectors,"load":LOAD_F,
                             "hold":HOLD_S,"step":STEP_S,"edge":EDGE_S,"temperature_c":TEMP_C}, lambda:
    net.simulate(vectors, load=LOAD_F, expected=adder_reference, hold_s=HOLD_S,
                 step_s=STEP_S, edge_s=EDGE_S, temperature_c=TEMP_C, timeout=180))
assert pre["measurements"]["passed"]
assert pre["stimulus"]["vectors"] == demo["stimulus"]["vectors"]
assert pre["stimulus"]["hold_s"] == demo["stimulus"]["hold_s"]
assert pre["stimulus"]["step_s"] == demo["stimulus"]["step_s"]
show(waveform_figure(demo, outputs, pre=pre, title=f"Matched pre/post stimuli: {LOAD_F*1e15:g} fF per output"))
table([["Output", "Pre max settling (ns)", "Post max settling (ns)"]]+[
    [p, pre["measurements"]["max_settling_s"][p]*1e9,
     demo["measurements"]["max_settling_s"][p]*1e9] for p in outputs])
print("Wire-C assumptions:", demo["capacitance"]["assumptions"])
if EXTENDED:
    for load in [10e-15,1e-12]:
        loaded = cache.run(f"adder2-load-{load:g}", {"vectors":vectors,"load":load}, lambda:
            lay.extract().simulate(vectors, load=load, expected=adder_reference,
                                   hold_s=2e-6, step_s=2e-9, timeout=180))
        assert loaded["measurements"]["passed"], loaded["measurements"]
        print(load, loaded["measurements"]["passed"], loaded["measurements"]["max_settling_s"])
''')
md('''
The next loop regenerates all shared designs from committed HDL and cell views;
it consumes no pre-existing `build/` results. SIM supplies the vector plans and
independent radix-arithmetic oracles. Small circuits visit every input state;
the larger adder uses labeled carry assertion/release, overflow and cancellation
cases. Neither sequence exhausts directed transitions. Each physical result is
checked before matched pre/post simulation. Maxima can occur on different
transitions; the last timing column compares each transition with itself.
Sub-timestep differences do not establish a speedup.
''')
code('''
from tritflow.sim.postlayout import representative_vectors, arithmetic_oracle
FOUR_DESIGN_LOAD_F, FOUR_DESIGN_HOLD_S, FOUR_DESIGN_STEP_S = 10e-15, 500e-9, 2e-9
four_results = {}
physical_rows = [["Design", "Die (µm)", "Aspect", "Utilization", "DRC / LVS", "Input states visited / possible",
                  "Post max error (mV)", "Rail deviation / zero shift (mV)"]]
timing_rows = [["Design", "Output", "Pre max (ns)", "Post max (ns)", "Largest same-transition change (ns)"]]
for name, source_name, params in [("adder4","adder",{"N":4}), ("full_add","full_add",{}),
                                  ("mac1","mac1",{}), ("mul1","mul1",{})]:
    mapped = flow.load(ROOT/f"examples/{source_name}.tv", source_name, params).synthesize(name=name)
    pins = [p.name for p in mapped.ports if p.dir == "input"]
    planned, labels = representative_vectors(name, pins)
    oracle = arithmetic_oracle(name, pins)
    directory = BUILD/"four_designs"/name
    result = cache.run(f"four-{name}", {"net":mapped.to_json(),"vectors":planned,"labels":labels,
                       "expected":[oracle(v) for v in planned],"load_f":FOUR_DESIGN_LOAD_F,
                       "hold_s":FOUR_DESIGN_HOLD_S,"step_s":FOUR_DESIGN_STEP_S,
                       "rows":None,"anneal_steps":600,"seed":0},
        lambda: complete_design(mapped,directory,planned,oracle,load_f=FOUR_DESIGN_LOAD_F,
                   hold_s=FOUR_DESIGN_HOLD_S,step_s=FOUR_DESIGN_STEP_S),
        artifacts=lambda r: experiment_artifacts(r,directory,name))
    assert_experiment(result)
    assert result["post"]["stimulus"]["vectors"] == list(map(tuple,planned))
    stats, ir = result["stats"], result["ir"]
    rail = max(abs(v) for c in ir["cells"].values() for v in c["rail_deviation_v"].values())
    zero = max(abs(c["zero_level_shift_v"]) for c in ir["cells"].values() if c["zero_level_shift_v"] is not None)
    physical_rows.append([name,stats["die_size_um"],max(stats["die_size_um"])/min(stats["die_size_um"]),
                          stats["utilization"],[result["drc"]["clean"],result["lvs"]["matched"]],
                          f"{len(set(planned))} / {3**len(pins)}",result["post"]["measurements"]["max_error_v"]*1e3,
                          [rail*1e3,zero*1e3]])
    before, after = [result[mode]["measurements"] for mode in ("pre","post")]
    for pin in after["max_settling_s"]:
        changes = [b["outputs"][pin]["settling_s"]-a["outputs"][pin]["settling_s"]
                   for a,b in zip(before["rows"][1:],after["rows"][1:],strict=True)]
        timing_rows.append([name,pin,before["max_settling_s"][pin]*1e9,after["max_settling_s"][pin]*1e9,
                            max(changes)*1e9])
    four_results[name] = result
table(physical_rows)
table(timing_rows)
table([["Shared load (fF)",FOUR_DESIGN_LOAD_F*1e15], ["Hold / max step (ns)",
       [FOUR_DESIGN_HOLD_S*1e9,FOUR_DESIGN_STEP_S*1e9]],
       ["Input plan labels", {name:representative_vectors(name,
          r["post"]["stimulus"]["inputs"])[1] for name,r in four_results.items()}]])
FOUR_DESIGN_VIEW = "full_add"  # switch to adder4, mac1 or mul1
viewed = four_results[FOUR_DESIGN_VIEW]
show(waveform_figure(viewed["post"],pre=viewed["pre"],title=f"{FOUR_DESIGN_VIEW}: matched pre/post vectors"))
print("Wire-C assumptions:", viewed["capacitance"]["assumptions"])
print("IR assumptions (separate from ideal-rail SPICE):", viewed["ir"]["assumptions"])
''')
md('''
**SIM publication slots — width scaling and load boundary:** the following cell
reads `results/adder_scaling.json` and `results/full_add_load_sweep.json` when
SIM publishes them. Missing data stays a TODO; no interpolated or invented
measurements fill the gap. The precomputed readers/figures are fast. Producing
the full matrix or refining a failing load is an opt-in experiment, outside
default Run all: `run_scaling(sizes=range(1,7), *, jobs=1, destination=..., **kwargs)`
and `sweep_output_load(directory, *, loads_f=..., hold_s=500e-9, step_s=2e-9,
relative_resolution=.02, absolute_resolution_f=50e-15, timeout=600, destination=...)`.
The latter reports the first observed failure on its stated sequence/window;
it is not a universal or PVT-qualified maximum capacitance. Failed/unsettled
points retain their flags and null delays.
''')
code('''
from tritflow.sim.scaling import load_scaling
from tritflow.sim.load_sweep import load_sweep_results
from tritflow.viz.scaling import scaling_figure, load_sweep_figure
for filename, loader, figure in [("adder_scaling.json",load_scaling,scaling_figure),
                                  ("full_add_load_sweep.json",load_sweep_results,load_sweep_figure)]:
    published = ROOT/"results"/filename
    if not published.is_file():
        print(f"TODO SIM: publish results/{filename}; no scaling/boundary result claimed")
        continue
    result = loader(published)
    try:
        records = result["rows"] if filename == "adder_scaling.json" else [result]
        for record in records:
            verify_publication_sources(record,ROOT,PDK_ROOT)
    except RuntimeError as error:
        print(f"TODO SIM: refresh results/{filename}: {error}; no current result claimed")
        continue
    print("Published experiment:", filename, result.get("coverage",result.get("scope")))
    print("Limits / conditions:",result.get("limits",result.get("conditions")))
    if filename == "adder_scaling.json":
        table([["Width", "Recorded state", "PASS", "Error"]]+
              [[r["n"],r["state"],r["passed"],r["error"]] for r in result["rows"]])
    else:
        table([["Measured boundary (F)",result["boundary"]], ["Boundary found",result["boundary_found"]],
               ["Outputs / input-state count",[result["outputs"],len(result["vectors"])]]])
    show(figure(result))
''')
md('''
## 8. Your circuit: choose, edit and check

Choose a catalog key below: sign, signed two-trit comparison, exact two-trit
multiplication, or a min/max sorter. Each source has an independent integer
oracle. The generated table checks every input against both source and mapped
logic. The selected circuit then runs real P&R, DRC/LVS and extracted simulation
through the same chain. Editing HDL can intentionally fail the oracle; update
the mathematical specification only when you intend to change the function.
Initial internal-node Newton guesses use mapped trits and strict-LVS net
correspondence. They avoid nonphysical model operating-point roots; `.nodeset`
is unconstrained during the transient, with no `.ic`/`uic` or circuit changes.
Output acceptance still uses the independent arithmetic oracle. The actual
guesses are displayed with the result.

`~`, `&`, `|` and `nany` retain their ternary meanings. Here is a deliberately
broken expression, caught before any physical work. Located errors identify
the filename/line/column and the supported replacement operators.
''')
code('''
from tritflow.hdl import HDLError
broken = """module broken(input trit a,b,output trit y);
 assign y = a + b;
endmodule"""
try:
    flow.loads(broken,"broken",filename="your_circuit.tv")
except HDLError as error:
    print(error)
    print("Repair: use gates for signal arithmetic; e.g. nany(a,b) gives the negative saturated sum.")
else:
    raise AssertionError("unsupported signal arithmetic must be rejected")
''')
code('''
from examples.curated import DESIGNS
from tritflow.synth import evaluate_netlist
CHOICE = os.environ.get("TRITFLOW_CIRCUIT", "minmax")  # sign | compare2 | mul2 | minmax
table([["Choice", "Specification"]]+[[key,item.description] for key,item in DESIGNS.items()])
example = DESIGNS[CHOICE]
source = example.path.read_text()  # edit this string, or choose another catalog entry
print(source)
# Stage includes beside the edited text, preserving the committed source files.
custom_circuit = load_edited(example,source,BUILD/"your_circuit"/"source"/example.top)
custom = custom_circuit.synthesize()
truth = custom_circuit.truth_table()
pins = custom_circuit.design.inputs
planned = list(zip(*(truth[p] for p in pins)))
oracle = example.oracle(pins)
mapped_truth = evaluate_netlist(custom,{p:truth[p] for p in pins})
for i, vector in enumerate(planned):
    expected = oracle(vector)
    assert {p:int(truth[p][i]) for p in expected} == expected
    assert {p:int(mapped_truth[p][i]) for p in expected} == expected
display(truth_table_html(custom,max_rows=len(planned)))
show(color_nets(custom,dict(zip(pins,planned[-1]))))
custom_out = BUILD/"your_circuit"/example.top
custom_result = cache.run(f"your-{CHOICE}", {"source":source,"net":custom.to_json(),"vectors":planned,
                         "expected":[oracle(v) for v in planned],"load_f":10e-15,"hold_s":1e-6,
                         "step_s":2e-9,"rows":None,"anneal_steps":600,"seed":0,"initialize_internal":True},
    lambda: complete_design(custom,custom_out,planned,oracle,hold_s=1e-6,initialize_internal=True),
    artifacts=lambda r: experiment_artifacts(r,custom_out,example.top))
assert_experiment(custom_result)
assert {tuple(row["input_trits"]) for row in custom_result["post"]["measurements"]["rows"]} == set(planned)
table([["Independent arithmetic input states",len(planned)], ["Physical results",custom_result["stats"]],
       ["DRC clean / LVS matched",[custom_result["drc"]["clean"],custom_result["lvs"]["matched"]]],
       ["Initial Newton guesses (V)",custom_result["initial_nodeset_v"]]])
show(waveform_figure(custom_result["post"],title=f"{CHOICE}: all input states, selected sequence"))
''')
md('''
## 9. Connect the model to a future measurement

The exported drawings document the historical reference topology, not measured
silicon performance. Record actual device/package identity, measured supply
voltages, temperature, probe capacitance and stimulus skew. Compare
DC levels and final band-entry times with matched loads and stimulus edges.
Repeat with supply/temperature variation, then revise model assumptions from
measured discrepancies. The generated core is not a padframe or ESD-qualified
top, and nominal device simulation is not a lifetime qualification.

**TODO — integrator:** confirm the measurement schedule and hardware details;
replace draft placeholders, publish the `colab-v0` tag, and run this exact
notebook in a clean Colab runtime before submission. Record cold/warm runtimes
and keep total default Run all near ten minutes.

Sources: [OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um),
[reference cells and arithmetic](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic),
[official KLayout packages](https://www.klayout.de/build.html).
The setup pins the PDK commit and verifies SHA-256 archive/package downloads.
''')
code('''
print("Cache stages:", cache.events)
print(f"Run time including setup: {time.monotonic()-started:.1f} s")
print("Artifacts:", BUILD)
''')


if __name__ == "__main__":
    document = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
        "colab": {"name": "tritflow_tr1um.ipynb", "provenance": []}}, "cells": cells}
    Path(__file__).with_name("tritflow_tr1um.ipynb").write_text(json.dumps(document, indent=1)+"\n")
