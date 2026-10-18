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

Draft for IEEE SSCS Code-a-Chip, ISSCC 2027. Audience: designers familiar with
CMOS, synthesis, P&R and SPICE. We follow a real three-rail circuit through the
flow, separating logical equivalence, physical connectivity and nominal analog
settling. Coverage and conditions are generated beside each result.

**Draft TODO — integrator:** publish a source archive containing this package,
`cells/`, `examples/` and `notebook/`; set `TRITFLOW_ARCHIVE_URL` and its
`TRITFLOW_ARCHIVE_SHA256` for a standalone Colab launch. Alternatively upload
the checkout to `/content/tritflow`. This checkout has no publication remote.
The setup script is complete for an available checkout; fresh Colab execution
and the total install-inclusive ten-minute budget remain unverified.

The default run uses a small adder and representative analog vectors. Heavy
stages use content-keyed JSON caches; `TRITFLOW_EXTENDED=1` enables additional
P&R/load experiments. Cached reports are identified as cache hits and their
artifact hashes are checked. A cache is evidence of the recorded run, not a new
DRC/LVS execution. Clear `build/notebook/cache` to force recomputation.
""")
code(r'''
import os, sys, json, time, hashlib, tarfile, tempfile, subprocess, importlib.util
from pathlib import Path
from urllib.request import urlretrieve
started = time.monotonic()
try:
    IN_COLAB = importlib.util.find_spec("google.colab") is not None
except ModuleNotFoundError:
    IN_COLAB = False
candidates = [Path(os.environ.get("TRITFLOW_ROOT", ".")), Path.cwd(), Path.cwd().parent,
              Path("/content/tritflow")]
ROOT = next((p.resolve() for p in candidates if (p/"pyproject.toml").is_file()
             and (p/"tritflow").is_dir()), None)
if ROOT is None:
    url = os.environ.get("TRITFLOW_ARCHIVE_URL", "")
    checksum = os.environ.get("TRITFLOW_ARCHIVE_SHA256", "")
    if not url or len(checksum) != 64:
        raise RuntimeError("TODO INTEGRATOR: configure the pinned source archive URL/SHA256, "
                           "or upload the full checkout to /content/tritflow")
    target = Path("/content/tritflow-source")
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        archive = Path(folder)/"source.tar.gz"
        urlretrieve(url, archive)
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == checksum, "source archive SHA256"
        with tarfile.open(archive) as stream:
            stream.extractall(target, filter="data")
    roots = [p.parent for p in target.rglob("pyproject.toml") if (p.parent/"tritflow").is_dir()]
    assert len(roots) == 1, "archive must contain exactly one TritFlow checkout"
    ROOT = roots[0]
if IN_COLAB:
    runtime = ROOT/"notebook/runtime.json"
    if not runtime.is_file():
        subprocess.run(["bash", str(ROOT/"notebook/colab_setup.sh"), "--source", str(ROOT)], check=True)
    os.environ.update(json.loads(runtime.read_text()))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/"notebook"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
print("Source:", ROOT)
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
    lay = net.place_and_route(output_dir=out, seed=0, anneal_steps=80)
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
                                   "temperature_c":TEMP_C, "seed": 0, "anneal": 80}, complete_adder,
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
''')
md('''
**TODO — SIM sizing experiment:** expose the requested `sweep_dimensions(...)`
API (signature/schema in `docs/status/FRONTEND.md`) and mark
the taped-out dimensions on its transfer/error/current curves. This draft reads
the real characterized dimensions and does not replace them with synthetic
sizing results. Full characterization is deliberately not rerun by default.

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
if EXTENDED:
    larger = flow.load(ROOT/"examples/adder.tv", "adder", {"N":4}).synthesize(name="adder4_experiment")
    folder = BUILD/"adder4_experiment"
    def larger_route():
        routed = larger.place_and_route(output_dir=folder, seed=0)
        return routed.stats
    stats4 = cache.run("adder4-route", {"net":larger.to_json()}, larger_route,
                      artifacts=[folder/"adder4_experiment.gds",folder/"adder4_experiment.pnr.json"])
    table([["N=4",stats4]])
''')
md('''
The placement animation uses recorded snapshots and cell-terminal HPWL.
With extended experiments enabled, routing progress replays the successful
recorded pass. Neither animation substitutes for the geometry checks.

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
RC and PVT/mismatch are outside this experiment. No rail-IR result is presented
here; its separate experiment remains in the result-matrix TODO below.
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
**TODO — final result matrix:** add cache-qualified N=1/2/4 area/settling sweeps,
load sweeps and per-cell IR results before submission. Exhaust all inputs only
for circuits whose analog sweep is budgeted; label larger patterns as sampled.
The default two-trit run must not be described as exhaustive analog coverage.

## 8. Edit a circuit and rerun the chain

Change the expression below. `~`, `&`, `|` and `nany` have their ternary gate
meanings; `+` on signal trits is rejected. This small example reruns the same
mapped-cell, physical and post-layout interfaces with all nine input states.
''')
code('''
source = """module experiment(input trit a,b,output trit y);
 assign y = nany(a,b);
 endmodule"""
custom = flow.loads(source, "experiment").synthesize()
display(truth_table_html(custom))
show(color_nets(custom, {"a":-1,"b":1}))
custom_out = BUILD/"experiment"
def run_custom():
    routed = custom.place_and_route(output_dir=custom_out, seed=0, anneal_steps=30)
    assert routed.drc()["clean"] and routed.lvs()["matched"]
    result = routed.extract().simulate(input_vectors(2), load=100e-15, hold_s=500e-9, step_s=2e-9)
    assert result["measurements"]["passed"]
    return result
custom_post = cache.run("editable-experiment", {"source":source,"load":100e-15}, run_custom,
    artifacts=[custom_out/"experiment.gds",custom_out/"experiment.pnr.json"])
assert custom_post["measurements"]["passed"]
assert {tuple(row["input_trits"]) for row in custom_post["measurements"]["rows"]} == set(input_vectors(2))
show(waveform_figure(custom_post, ["y"], title=f"Edited circuit: {len(custom_post['measurements']['rows'])} input states"))
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
replace draft placeholders, publish the source archive pin, and run this exact
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
