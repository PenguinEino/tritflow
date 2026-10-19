"""Executable notebook stages, separate from the editorial reading path.

All physical/electrical work uses public stream APIs. Scientific assertions
remain active even where verbose displays are collapsed.
"""

SETUP = r'''
_TRITFLOW_SETUP_READY = False
globals().pop("_tf_cells", None)
import os, sys, json, time, hashlib, subprocess, importlib.util
from pathlib import Path
started = time.monotonic()
try:
    IN_COLAB = importlib.util.find_spec("google.colab") is not None
except ModuleNotFoundError:
    IN_COLAB = False
SOURCE_URL = "https://github.com/PenguinEino/tritflow.git"
SOURCE_REF = os.environ.get("TRITFLOW_REF", "839adbf19f7590221d18d171adaaddb95c8fd27a")
def source_git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
if IN_COLAB:
    ROOT = Path("/content/tritflow")
    import re
    if not re.fullmatch(r"[0-9a-f]{40}", SOURCE_REF):
        raise ValueError("TRITFLOW_REF must be an immutable full 40-character Git commit")
    if not ROOT.exists():
        subprocess.run(["git", "clone", "--no-checkout", "--depth", "1", "--filter=blob:none",
                        SOURCE_URL, str(ROOT)], check=True)
        subprocess.run(["git", "-C", str(ROOT), "fetch", "--depth", "1", "origin", SOURCE_REF], check=True)
        subprocess.run(["git", "-C", str(ROOT), "switch", "--detach", SOURCE_REF], check=True)
    if not (ROOT/".git").is_dir():
        raise RuntimeError("/content/tritflow must be a git clone; use a fresh Colab runtime")
    if source_git("remote", "get-url", "origin").removesuffix(".git") != SOURCE_URL.removesuffix(".git"):
        raise RuntimeError("existing checkout has a different origin; use a fresh Colab runtime")
    SOURCE_COMMIT = source_git("rev-parse", "--verify", "HEAD^{commit}")
    requested_commit = source_git("rev-parse", "--verify", SOURCE_REF+"^{commit}")
    if SOURCE_COMMIT != requested_commit or source_git("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("existing checkout differs from TRITFLOW_REF; use a fresh Colab runtime")
    print(f"Source: {SOURCE_URL} ref={SOURCE_REF} commit={SOURCE_COMMIT}", flush=True)
    if not (ROOT/"notebook/runtime_support.py").is_file():
        raise RuntimeError("TRITFLOW_REF predates this notebook's setup. Select its matching immutable release with TRITFLOW_REF in a fresh runtime.")
    sys.path.insert(0, str(ROOT/"notebook"))
    from runtime_support import SETUP_SCHEMA, setup_identity
    if SETUP_SCHEMA != "3":
        raise RuntimeError("The selected source commit predates the pinned runtime. Use the final submission commit with TRITFLOW_REF.")
    runtime = ROOT/"notebook/runtime.json"
    if (not runtime.is_file()
            or json.loads(runtime.read_text()).get("TRITFLOW_SETUP_SCHEMA") != SETUP_SCHEMA
            or json.loads(runtime.read_text()).get("TRITFLOW_SETUP_SHA256") != setup_identity(ROOT)):
        subprocess.run(["bash", str(ROOT/"notebook/colab_setup.sh"), "--source", str(ROOT)], check=True)
    os.environ.update(json.loads(runtime.read_text()))
    sys.path.insert(0, os.environ["TRITFLOW_PYTHON_TARGET"])
else:
    candidates = [Path(os.environ.get("TRITFLOW_ROOT", ".")), Path.cwd(), Path.cwd().parent]
    ROOT = next((p.resolve() for p in candidates if (p/"pyproject.toml").is_file()
                 and (p/"tritflow").is_dir()), None)
    if ROOT is None:
        raise RuntimeError("run locally from the full checkout or set TRITFLOW_ROOT")
    SOURCE_COMMIT = source_git("rev-parse", "--verify", "HEAD^{commit}") if (ROOT/".git").exists() else "tracked-tree export (no .git)"
    print(f"Source: {ROOT} commit={SOURCE_COMMIT}")
runtime = ROOT/"notebook/runtime.json"
if not IN_COLAB and runtime.is_file():
    os.environ.update(json.loads(runtime.read_text()))
    sys.path.insert(0, os.environ["TRITFLOW_PYTHON_TARGET"])
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/"notebook"))
sys.path.append(str(ROOT/"figures"))   # the paper's figure scripts, reused by method cells
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from runtime_support import check_runtime, print_tool_versions
check_runtime()
print_tool_versions()
_TRITFLOW_SETUP_READY = True
'''

IMPORTS = r'''
globals().pop("_tf_cells", None)
if not globals().get("_TRITFLOW_SETUP_READY", False):
    raise RuntimeError("Run the first setup cell successfully, then rerun the imports cell. If setup requested a restart, restart once first.")
from runtime_support import CellState
import numpy as np
from IPython.display import display, HTML, Image
from tritflow import flow, CELLS_DIR, PDK_ROOT, PASS_BAND, TRIT_VOLTS
from tritflow.sim import dc_transfer, input_vectors, subcircuits
from tritflow.viz.graph import truth_table_html
from tritflow.viz.waves import waveform_figure, waveform_scope
from tritflow.viz.layout import render_gds, placement_animation, routing_progress
from tritflow.viz.cell import device_mapping
from tritflow.sim.provenance import pdk_provenance
from tritflow.sim.postlayout import logical_nodeset
from cache import Cache, runtime_fingerprint, source_manifest
from campaign import RecordedCampaign
from schematics import schematic_gallery
from experiments import (complete_design, experiment_artifacts, assert_experiment,
                         load_edited, verify_publication_sources, adder_demo_vectors)
EXTENDED = os.environ.get("TRITFLOW_EXTENDED", "0") == "1"
BUILD = Path(os.environ.get("TRITFLOW_NOTEBOOK_BUILD", ROOT/"build/notebook")).resolve()
qualified_pdk = pdk_provenance(PDK_ROOT)
assert qualified_pdk["qualified_commit"] == json.loads((ROOT/"notebook/setup_pins.json").read_text())["pdk_commit"]
native_sources = source_manifest(ROOT,PDK_ROOT)
cache = Cache(BUILD/"cache", runtime_fingerprint(ROOT, PDK_ROOT,names=native_sources),
              force=os.environ.get("TRITFLOW_FORCE_RUN", "0") == "1",sources=native_sources)
recorded_campaign = RecordedCampaign(ROOT/"notebook/assets/four_designs.zip",ROOT,PDK_ROOT,
                                     enabled=not cache.force)
renderer_sha256 = hashlib.sha256((ROOT/"tritflow/viz/layout.py").read_bytes()).hexdigest()
from presentation import show, table, evidence, gds_download

from IPython.display import Markdown, Code
from editorial import context, context_identity, render as render_narrative, dimensions
from paper_evidence import load_paper
from learning import sizing_slider, value_selector, highlight_devices, cell_cards
from predictions import divider, zero_dc, rail_power
from presentation import details_html, details_svg
from routing_identity import routing_label, archive_routing
paper = load_paper(ROOT)
narrative_values = context(ROOT)
assert context_identity(narrative_values) == NARRATIVE_CONTEXT_SHA256, "Published figure measurements changed; regenerate the notebook before running."
'''

OPENING_INPUTS = r'''
LOAD_F, HOLD_S, STEP_S, EDGE_S, TEMP_C = 100e-15, 1e-6, 2e-9, 1e-9, 27
PNR_ROWS, PNR_ANNEAL_STEPS = None, 600  # automatic near-square floorplan; placement effort
CONDITIONS = dict(hold_s=HOLD_S, step_s=STEP_S, edge_s=EDGE_S, temperature_c=TEMP_C, timeout=600)
out = BUILD/"adder2_demo"
def adder_reference(vector):
    """Independent balanced-ternary integer oracle; `inputs` comes from the method cell."""
    v = dict(zip(inputs, vector, strict=True))
    remainder = sum((v[f"a[{i}]"] + v[f"b[{i}]"])*3**i for i in range(2)) + v["cin"]
    result = {}
    for i in range(2):
        result[f"sum[{i}]"] = (remainder+1)%3-1
        remainder = (remainder-result[f"sum[{i}]"])//3
    return {**result, "cout": remainder}
'''

OPENING = r'''
logical = d.truth_table()
outputs = [p.name for p in net.ports if p.dir == "output"]
assert all(len(v) == len(inputs) for v in vectors)
assert len(logical[inputs[0]]) == 3**len(inputs)
expected_sequence = [adder_reference(v) for v in vectors]
assert all({r[p] for r in expected_sequence} == {-1,0,1} for p in outputs)
assert all(a != b for a,b in zip(vectors,vectors[1:]))
for row in zip(*(logical[name] for name in inputs)):
    assert adder_reference(row) == {k: int(v) for k,v in d.design.evaluate(dict(zip(inputs,row))).items()}
assert drc["clean"] and lvs["matched"], (drc, lvs)
assert post["measurements"]["passed"], post["measurements"]
demo = {**post, "stats": lay.stats, "drc": drc, "lvs": lvs, "initial_nodeset_v": guesses}
assert not lay.stats["library_mock"]
assert all({row["outputs"][p]["ideal_trit"] for row in demo["measurements"]["rows"]} == {-1,0,1}
           and demo["measurements"]["max_settling_s"][p] > 0 for p in outputs)
table([["Live adder", "Cells", "Die (µm)", "DRC markers", "Strict LVS", "Analog"],
       [net.top,net.report()["total_cells"],dimensions(lay.stats["die_size_um"]),
        demo["drc"]["violations"],demo["lvs"]["matched"],demo["measurements"]["passed"]]])
print(f"Independent integer oracle: {len(logical[inputs[0]])} exhaustive states; extracted sequence: {len(set(vectors))} selected states.")
'''

GATES = r'''
assert np.array_equal(t["inva"], -t["a"])
assert np.array_equal(t["nandab"], -np.minimum(t["a"], t["b"]))
assert np.array_equal(t["norab"], -np.maximum(t["a"], t["b"]))
assert np.array_equal(t["nanyab"], -np.clip(t["a"]+t["b"],-1,1))
for name in ["INV","NAND","NOR","NANY"]:
    body = subcircuits((CELLS_DIR/f"out/{name}/{name}.spice").read_text())[name.lower()]["body"]
    assert ("VMID" in body.upper()) == (name == "NANY"), name
# The regenerated figure uses the same public DC call and zero-input sample as the paper.
assert {cell: sorted(c) for cell, c in curves.items()} == {"INV": [0], "NAND": [-1, 0, 1], "NOR": [-1, 0, 1], "NANY": [-1, 0, 1]}
assert abs(v_a[i0]) < 1e-9
assert abs(v_y[i0]-paper["inv_dc"]["output_v"]) < 1e-8
# The held input really is held: at A = +5 V, NAND gives +5 V for B = −1 and −5 V for B = +1.
assert curves["NAND"][-1][1][-1] > 4.5 and curves["NAND"][1][1][-1] < -4.5
details_html("Taped-out INV schematic and exported source",schematic_gallery(
    ROOT/"notebook/assets/schematics",names=["INV"],selected="INV"))
'''

CHARACTERIZATION = r'''
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
characterization_rows = rows
evidence("Full-precision DC checkpoints", {cell:char["dc"] for cell,char in characters.items()})
table([["Cell", "Recorded conditions", "Tested loads (fF)", "Fanout evidence"]]+
      [[cell, char["conditions"], [r["load_f"]*1e15 for r in char["transient"]], char["fanout"]]
       for cell,char in characters.items()], details="Characterization conditions and complete fanout evidence")
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

'''

SIZING = r'''
# Hold MOS sizes fixed: these are actual simulated RR candidates.
rr_candidates = sorted((r for r in gi["rows"] if r["dc"] and
    all(r["dimensions"][k] == adopted["dimensions"][k] for k in ("MP","MN"))),
    key=lambda r:r["dimensions"]["RP"]["l_um"])
table([["Common RR length (µm)","Worst level error (mV)","Max |rail I| (µA)","Reference"]]+[
    [r["dimensions"]["RP"]["l_um"],r["max_error_v"]*1e3,r["max_static_current_a"]*1e6,
     "taped out" if r["is_adopted"] else ""] for r in rr_candidates])
'''

CELLS = r'''
template = json.loads((CELLS_DIR/"template.json").read_text())
generation = json.loads((CELLS_DIR/"out/generation.json").read_text())
assert {a["height"] for a in abstracts.values()} == {template["height"]}
assert generation["height_um"] == template["height"]

cell_dimension_rows = ([["Cell", "Width × common height (µm)", "Area (µm²)", "Free full-height M2 tracks"]]+
      [[name, [a["width"],a["height"]], a["width"]*a["height"], a["free_M2_tracks"]["count"]]
       for name,a in abstracts.items()])
abstract = json.loads((CELLS_DIR/"out/NANY/NANY.abstract.json").read_text())
# Highlight both conducting devices of the zero-level clamp. These are device
# outlines, not an invented extracted current-density or wire-current map.
clamp_devices = {"XCP1","XCN1"}
clamp_body = subcircuits((CELLS_DIR/"out/NANY/NANY.spice").read_text())["nany"]["body"]
clamp_terminals = {fields[0]:fields[1:5] for fields in map(str.split,clamp_body.splitlines()) if fields}
assert clamp_terminals["XCP1"] == ["c1","A","Y","VDD"]
assert clamp_terminals["XCN1"] == ["c1","B","VMID","VSS"]
clamp_character = json.loads((CELLS_DIR/"out/NANY/NANY.char.json").read_text())
assert hashlib.sha256((CELLS_DIR/"out/NANY/NANY.ext.spice").read_bytes()).hexdigest() == clamp_character["source_sha256"]
clamp_dc = next(r for r in clamp_character["dc"] if r["input_trits"] == [-1,1])
assert clamp_dc["passed"] and abs(clamp_dc["output_v"]["Y"]) <= PASS_BAND
assert clamp_devices <= {r["name"] for r in mapping.rows}
evidence("Device correspondence and W/L",mapping.rows)

qualification = CELLS_DIR/"out/verify_report.json"
if qualification.is_file():
    report = json.loads(qualification.read_text())
    assert report["passed"]
    assert all(hashlib.sha256((PDK_ROOT/name).read_bytes()).hexdigest() == value
               for name,value in report["deck_sha256"].items()), "cell qualification uses a different PDK"
    for cell, artifacts in report["artifact_sha256"].items():
        for suffix, expected_hash in artifacts.items():
            assert hashlib.sha256((CELLS_DIR/f"out/{cell}/{cell}.{suffix}").read_bytes()).hexdigest() == expected_hash
    cell_qualification_rows = ([["Cell", "Recorded DRC clean", "Recorded LVS qualification", "LVS method"]]+[
        [name, result["drc"]["passed"], result["lvs"]["passed"],
         result["lvs"].get("method","strict device/port comparison")]
        for name,result in report["cells"].items()])
    if "FILL" in report["cells"]:
        evidence("FILL qualification", report["cells"]["FILL"]["lvs"]["explanation"])
    evidence("Recorded qualification scope", report["scope"])
else:
    raise FileNotFoundError("Required pinned-PDK cell qualification: "+str(qualification))
'''

ARITHMETIC = r'''
details_html("Half-adder exhaustive truth table",truth_table_html(ha.design))
details_html("Full-adder exhaustive truth table",truth_table_html(fa.design))
ha_table = ha.truth_table()
assert np.array_equal(ha_table["a"]+ha_table["b"], ha_table["sum"]+3*ha_table["carry"])
schematic_sources = json.loads((ROOT/"notebook/assets/schematics/manifest.json").read_text())["schematics"]
ha_symbols = schematic_sources["half_adder"]["instances_by_symbol"]
fa_symbols = schematic_sources["full_adder"]["instances_by_symbol"]
symbol_names = {"INV":"inverter", "NANY":"nany"}
assert ha_counts == {cell:ha_symbols[symbol] for cell,symbol in symbol_names.items()}
assert fa_counts == {cell:fa_symbols["half_adder"]*ha_counts[cell]+fa_symbols[symbol]
                     for cell,symbol in symbol_names.items()}
table([["Circuit", "Cells", "Exhaustive input states"],
       ["half_add",ha_counts,len(ha_table["sum"])], ["full_add",fa_counts,len(fa_table["sum"])]])
evidence("Ripple-adder HDL", (ROOT/"examples/adder.tv").read_text())
'''

SYNTHESIS = r'''
assert fa_net.report()["equivalence"]["passed"]
assert fa_net.report()["equivalence"]["vectors"] == len(fa_table["sum"])
table([["Report field", "Value"]]+[[k,v] for k,v in fa_net.report().items()],details="Full synthesis report")
from tritflow.synth import tritverilog
evidence("Gate-level TritVerilog", tritverilog(fa_net))
mapping_cases = [("~a",["INV"]), ("~(a&b)",["NAND"]), ("a&b",["NAND","INV"]),
                 ("~(a|b)",["NOR"]), ("a|b",["NOR","INV"]), ("nany(a,b)",["NANY"]),
                 ("1'tT",["TIEN"]), ("1't0",["TIEZ"]), ("1't1",["TIEP"])]
mapping_rows = [["HDL expression", "Computed cells"]]
for expr, expected_cells in mapping_cases:
    mapped = flow.loads(f"module mapping(input trit a,b,output trit y); assign y={expr}; endmodule").synthesize()
    assert sorted(inst.cell for inst in mapped.instances) == sorted(expected_cells)
    mapping_rows.append([expr, mapped.report()["cells"]])
table(mapping_rows,details="Expression-to-cell mapping checks")
'''


PNR = r'''
table([["Metric", "Two-trit adder"]]+[[k,v] for k,v in lay.stats.items()],details="Full physical statistics")
assert all(check["clean"] for check in lay.data["checks"].values())
assert lay.stats["routed_nets"] == len(net.nets())
assert {p["orient"] for p in lay.data["placements"]} <= {"R0","MY"}
evidence("Live adder physical checks",lay.data["checks"])
table([["Initial / final cell-terminal HPWL (µm)",
        [lay.data["history"][i]["hpwl"] for i in (0,-1)]]])
if EXTENDED:
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
'''

PRE = r'''
assert pre["measurements"]["passed"]
assert pre["stimulus"]["vectors"] == demo["stimulus"]["vectors"]
assert pre["stimulus"]["hold_s"] == demo["stimulus"]["hold_s"]
assert pre["stimulus"]["step_s"] == demo["stimulus"]["step_s"]
assert routed_sch.scene is sch.scene
evidence("Schematic wire-C scope (excludes receiving-pin C)",wire_report["assumptions"])
if EXTENDED:
    for load in [10e-15,1e-12]:
        loaded = cache.run(f"adder2-load-{load:g}", {"vectors":vectors,"load":load}, lambda:
            lay.extract().simulate(vectors, load=load, expected=adder_reference,
                                   hold_s=2e-6, step_s=2e-9, timeout=180))
        assert loaded["measurements"]["passed"], loaded["measurements"]
        print(load, loaded["measurements"]["passed"], loaded["measurements"]["max_settling_s"])
'''

FOUR = r'''
from tritflow.sim.postlayout import representative_vectors, arithmetic_oracle
FOUR_DESIGN_LOAD_F, FOUR_DESIGN_HOLD_S, FOUR_DESIGN_STEP_S = 10e-15, 500e-9, 2e-9
four_results = {}
physical_rows = [["Design", "Routing realization", "Die (µm)", "Aspect", "Utilization", "DRC / LVS", "Input states visited / possible",
                  "Post max error (mV)", "Rail deviation / zero shift (mV)"]]
timing_rows = [["Design", "Routing realization", "Output", "Device-only max (ns)", "+ wire-C max (ns)", "Largest same-transition change (ns)"]]
four_run_labels = {}
for name, source_name, params in [("adder4","adder",{"N":4}), ("full_add","full_add",{}),
                                  ("mac1","mac1",{}), ("mul1","mul1",{})]:
    mapped = flow.load(ROOT/f"examples/{source_name}.tv", source_name, params).synthesize(name=name)
    pins = [p.name for p in mapped.ports if p.dir == "input"]
    planned, labels = representative_vectors(name, pins)
    oracle = arithmetic_oracle(name, pins)
    directory = BUILD/"four_designs"/name
    options = {"net":mapped.to_json(),"vectors":planned,"labels":labels,
               "expected":[oracle(v) for v in planned],"load_f":FOUR_DESIGN_LOAD_F,
               "hold_s":FOUR_DESIGN_HOLD_S,"step_s":FOUR_DESIGN_STEP_S,
               "rows":None,"anneal_steps":600,"seed":0,"initialize_internal":True}
    lookup_started = time.monotonic()
    result = None if cache.force else recorded_campaign.get(name,options)
    if result is not None:
        cache.events.append((f"four-{name}","recorded"))
        cache.timings.append({"stage":f"four-{name}","state":"recorded",
                              "elapsed_s":time.monotonic()-lookup_started})
        print(f"Recorded {name}: retained native checks; see Appendix B")
    else:
        result = cache.run(f"four-{name}",options,
            lambda: complete_design(mapped,directory,planned,oracle,load_f=FOUR_DESIGN_LOAD_F,
                       hold_s=FOUR_DESIGN_HOLD_S,step_s=FOUR_DESIGN_STEP_S,initialize_internal=True,dataset='four-design'),
            artifacts=lambda r: experiment_artifacts(r,directory,name))
    assert_experiment(result)
    state = 'recorded' if cache.events[-1][1] == 'recorded' else ('fresh' if cache.events[-1][1] == 'run' else 'local reuse')
    if state == 'recorded':
        assert result['routing'] == archive_routing(ROOT/'notebook/assets/four_designs.zip')[name]
    run_label = routing_label(result['routing'],state=state,digest=True)
    four_run_labels[name] = run_label
    assert result["post"]["stimulus"]["vectors"] == list(map(tuple,planned))
    stats, ir = result["stats"], result["ir"]
    rail = max(abs(v) for c in ir["cells"].values() for v in c["rail_deviation_v"].values())
    zero = max(abs(c["zero_level_shift_v"]) for c in ir["cells"].values() if c["zero_level_shift_v"] is not None)
    physical_rows.append([name,run_label,stats["die_size_um"],max(stats["die_size_um"])/min(stats["die_size_um"]),
                          stats["utilization"],[result["drc"]["clean"],result["lvs"]["matched"]],
                          f"{len(set(planned))} / {3**len(pins)}",result["post"]["measurements"]["max_error_v"]*1e3,
                          [rail*1e3,zero*1e3]])
    before, after = [result[mode]["measurements"] for mode in ("pre","post")]
    for pin in after["max_settling_s"]:
        changes = [b["outputs"][pin]["settling_s"]-a["outputs"][pin]["settling_s"]
                   for a,b in zip(before["rows"][1:],after["rows"][1:],strict=True)]
        timing_rows.append([name,run_label,pin,before["max_settling_s"][pin]*1e9,after["max_settling_s"][pin]*1e9,
                            max(changes)*1e9])
    four_results[name] = result


if recorded_campaign.manifest:
    evidence("Recorded four-design producer tools (not local requalification)",
             recorded_campaign.manifest["tools"])
table([["Shared load (fF)",FOUR_DESIGN_LOAD_F*1e15], ["Hold / max step (ns)",
       [FOUR_DESIGN_HOLD_S*1e9,FOUR_DESIGN_STEP_S*1e9]],
       ["Input plan labels", {name:representative_vectors(name,
          r["post"]["stimulus"]["inputs"])[1] for name,r in four_results.items()}]],details="Four-design stimulus conditions and labels")
'''

PUBLISHED = r'''
from tritflow.sim.scaling import load_scaling
from tritflow.sim.load_sweep import load_sweep_results
from tritflow.viz.scaling import scaling_figure, load_sweep_figure, scaling_fit_figure
for filename, loader, figure in [("adder_scaling.json",load_scaling,scaling_figure),
                                  ("full_add_load_sweep.json",load_sweep_results,load_sweep_figure)]:
    published = ROOT/"results"/filename
    result = loader(published)
    records = result["rows"] if filename == "adder_scaling.json" else [result]
    compatible_sources = []
    for record in records:
        compatible_sources.extend(verify_publication_sources(record,ROOT,PDK_ROOT))
    if compatible_sources:
        evidence("Recorded-source compatibility: exact optional schematic delegate only",compatible_sources)
    evidence("Published experiment scope: "+filename,result.get("coverage",result.get("scope")))
    evidence("Published limits / conditions",result.get("limits",result.get("conditions")))
    if filename == "adder_scaling.json":
        table([["Width", "Routing realization", "Recorded state", "PASS", "Error"]]+
              [[r["n"],f"width-sweep/adder{r['n']} · seed {r['seed']}",r["state"],r["passed"],r["error"]] for r in result["rows"]])
    else:
        table([["Measured boundary (F)",result["boundary"]], ["Boundary found",result["boundary_found"]],
               ["Outputs / input-state count",[result["outputs"],len(result["vectors"])]]])
    if EXTENDED:
        show(figure(result))
    if filename == "adder_scaling.json":
        if EXTENDED:
            show(scaling_fit_figure(result))
'''


CUSTOM_CHECK = r'''
truth = custom_circuit.truth_table()
pins = custom_circuit.design.inputs
planned = list(zip(*(truth[p] for p in pins)))
oracle = example.oracle(pins)
mapped_truth = evaluate_netlist(custom,{p:truth[p] for p in pins})
for i, vector in enumerate(planned):
    expected = oracle(vector)
    source_actual = {p:int(truth[p][i]) for p in expected}
    mapped_actual = {p:int(mapped_truth[p][i]) for p in expected}
    if source_actual != expected or mapped_actual != expected:
        raise AssertionError(f"Independent reference disagreement at {dict(zip(pins,vector))}: "
                             f"expected {expected}, HDL {source_actual}, cells {mapped_actual}. "
                             "Check your edit; change the arithmetic reference only if you intend a different function.")
details_html("Edited-circuit exhaustive truth table",truth_table_html(custom,max_rows=len(planned)))
'''

CUSTOM = r'''
custom_result = cache.run(f"your-{CHOICE}", {"source":source,"net":custom.to_json(),"vectors":planned,
                         "expected":[oracle(v) for v in planned],"load_f":10e-15,"hold_s":1e-6,
                         "step_s":2e-9,"rows":None,"anneal_steps":600,"seed":0,"initialize_internal":True},
    lambda: complete_design(custom,custom_out,planned,oracle,hold_s=1e-6,initialize_internal=True),
    artifacts=lambda r: experiment_artifacts(r,custom_out,example.top))
assert_experiment(custom_result)
assert {tuple(row["input_trits"]) for row in custom_result["post"]["measurements"]["rows"]} == set(planned)
table([["Independent arithmetic input states",len(planned)], ["Physical results",custom_result["stats"]],
       ["DRC clean / LVS matched",[custom_result["drc"]["clean"],custom_result["lvs"]["matched"]]],
       ["Initial Newton guesses (V)",custom_result["initial_nodeset_v"]]],details="Selected circuit physical evidence and Newton guesses")

show(waveform_scope(custom_result["post"],title=f"{CHOICE}: post-layout transient, every input state"))
custom_values = {"custom.name":custom.top,"custom.logic_states":len(planned),
    "custom.cells":custom.report()["total_cells"],"custom.die_um":dimensions(custom_result["stats"]["die_size_um"]),
    "custom.drc_items":custom_result["drc"]["violations"],"custom.lvs_status":"Match",
    "custom.analog_states":len(set(planned)),"custom.analog_status":"PASS"}
custom_takeaway = (ROOT/"notebook/narrative/08_your_circuit.md").read_text().split("> **What this shows.**",1)[1]
display(Markdown(render_narrative("> **What this shows.**"+custom_takeaway,{**narrative_values,**custom_values})))
'''

FINAL = r'''

table(characterization_rows,details="Cell DC / capacitance / fanout summary")
table(fanout_rows,details="Transistor-level cascade and fanout tests")
table(cell_dimension_rows,details="All standard-cell dimensions and pin-access tracks")
table(cell_qualification_rows,details="Cell drawing-DRC and LVS qualification")
table(physical_rows,details="Four-design physical and arithmetic checks (retained or fresh as below)")
table(timing_rows,details="Four-design identical-device timing comparison")
evidence("Cell ordered-pair/orientation abutments",report["abutment"])
for name,grid in sizing_grids.items():
    evidence(name+" sizing status including unavailable points",[
        {"index":i,"dimensions":r["dimensions"],"passed":r["passed"],"error":r["error"]}
        for i,r in enumerate(grid["rows"]) if not r["passed"]])
evidence("Live adder acceptance, sequence and initialized Newton guesses",{
    "logic":net.report()["equivalence"],"labels":vector_labels,"vectors":vectors,
    "measurements":demo["measurements"],"nodeset":demo["initial_nodeset_v"],
    "conditions":{"load_f":LOAD_F,"hold_s":HOLD_S,"edge_s":EDGE_S,"step_s":STEP_S,"temperature_c":TEMP_C}})
evidence("Native paper-figure inputs and committed image/data hashes",paper)
table([["Routing realization", "PNR SHA-256", "GDS SHA-256"]]+
      [[routing_label(r),r['pnr_sha256'],r['gds_sha256']]
       for r in (paper['paper_pnr']['routing'],paper['paper_post']['routing'])]+
      [[four_run_labels[name],r['routing']['pnr_sha256'],r['routing']['gds_sha256']]
       for name,r in four_results.items()],details="Native identities for each paper and four-design routing realization")
assert (runtime_fingerprint(ROOT,PDK_ROOT,names=native_sources) == cache.fingerprint and
        source_manifest(ROOT,PDK_ROOT,names=native_sources) == native_sources), "consumed sources changed during Run all; rerun after publication settles"
load_paper(ROOT)  # measurements remain strict; illustration changes only warn
table([["Stage", "Fresh / local cache / recorded", "Wall time this run (s)"]]+[
    [r["stage"],r["state"],round(r["elapsed_s"],3)] for r in sorted(cache.timings,key=lambda r:r["elapsed_s"],reverse=True)])
table([["Design", "Routing realization", "Measured producer phase", "Wall time (s)", "Process + child CPU time (s)"]]+[
    [name,four_run_labels[name],stage,round(seconds,3),round(result["cpu_times_s"][stage],3)] for name,result in four_results.items()
    for stage,seconds in result["timings_s"].items()],details="Physical and pre/post-SPICE runtime breakdown (producer evidence)")
print("Cache stages:")
for name,state in cache.events:
    print(f"  {name}: {state}")
print(f"Run time including setup: {time.monotonic()-started:.1f} s")
print("Artifacts:", BUILD)
'''



STA = r'''
rows = [[pin, t*1e9, post["measurements"]["max_settling_s"][pin]*1e9,
         100*(t/post["measurements"]["max_settling_s"][pin]-1)] for pin, t in timing.arrival.items()]
table([["Output", "STA (ns)", "Post-layout SPICE (ns)", "Difference (%)"]]+rows)
assert set(timing.arrival) == set(post["measurements"]["max_settling_s"])
evidence("STA critical path and assumptions", {"critical_output": timing.critical_output,
         "critical_path": timing.critical_path, "assumptions": timing.assumptions})
'''

SHUTTLE = r'''
assert chip["physical_checks_passed"] and chip["drawing_drc"]["clean"] and chip["mask_drc"]["clean"]
assert chip["drawing_lvs"]["matched"] and chip["drawing_lvs"]["strict_ports"]
assert hashlib.sha256((ROOT/"notebook/assets/chip/adder4/tr_1um_adder4.gds").read_bytes()).hexdigest() == chip["gds_sha256"]
details_html("Pad map and remaining submission steps",
             "<pre style='white-space:pre-wrap'>"+(ROOT/"notebook/assets/chip/adder4/README.md").read_text()+"</pre>")
'''
