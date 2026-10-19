"""Visible method cells: the public TritFlow calls each chapter teaches.

Each snippet is what a reader would copy into their own work. Checks,
provenance and evidence tables run in the collapsed cell that follows it
(see stages.py), so the method stays short without weakening any assertion.
"""

OPENING = r'''
d = flow.load(ROOT/"examples/adder.tv", "adder", {"N": 2})        # 1. TritVerilog source
net = d.synthesize(name="adder2_demo")                           # 2. cells + exhaustive equivalence check
inputs = [p.name for p in net.ports if p.dir == "input"]
vectors, vector_labels = adder_demo_vectors(inputs)               #    three-level test sequence
lay = net.place_and_route(output_dir=out, seed=0, rows=PNR_ROWS, anneal_steps=PNR_ANNEAL_STEPS)  # 3. GDS
drc, lvs = lay.drc(), lay.lvs()                                  # 4. TR-1um DRC deck, strict LVS
guesses = logical_nodeset(net, lvs["report"], inputs, vectors[0])
post = lay.extract().simulate(vectors, load=LOAD_F, expected=adder_reference,
                              nodeset=guesses, **CONDITIONS)     # 5. extracted devices + wire C in ngspice
print(f"DRC clean: {drc['clean']} · LVS match: {lvs['matched']} · analog PASS: {post['measurements']['passed']}")
'''

GATES = r'''
from fig_gates import simulate, draw                      # the paper's own Fig. 2 script
from paperstyle import save as save_figure
gates = flow.load(ROOT/"examples/gates.tv", "gates")       # the definition shown above
t = gates.truth_table()                                    # all nine input pairs, ideal trits
curves = simulate(CELLS_DIR/"out")                         # ten ngspice DC sweeps of the extracted layouts
png = save_figure(draw(curves), "fig_gates", out=BUILD/"figures")
display(Image(filename=str(png), width=1000))              # Fig. 2, regenerated from your own run
v_a, v_y, i_ma = curves["INV"][0]
i0 = int(np.argmin(abs(v_a)))
print(f"A = 0 V:  Y = {1e3*v_y[i0]:.1f} mV,  supply current = {i_ma[i0]:.3f} mA")
'''

SIZING = r'''
from tritflow.sim.sizing import load_grid
sizing_grids = {cell: load_grid(cell) for cell in ("INV", "NANY")}  # precomputed W/L/R sweeps
gi = sizing_grids["INV"]
adopted = gi["rows"][gi["adopted_index"]]                           # the taped-out size
hand = divider(adopted["dimensions"], PDK_ROOT)                     # predict first ...
table([["INV at zero input", "Hand estimate", "SPICE"],
       ["Output (V)", hand["output_v"], zero_dc(adopted)["output_v"]["Y"]],
       ["Static power (mW)", hand["power_w"]*1e3, rail_power(zero_dc(adopted), gi["conditions"]["supplies_v"])*1e3]])
show(sizing_slider(gi, PDK_ROOT))                                   # ... then explore every simulated size
'''

CELLS = r'''
library = json.loads((CELLS_DIR/"out/library.json").read_text())
abstracts = {c["name"]: json.loads((CELLS_DIR/"out"/c["abstract"]).read_text()) for c in library}
print({name: f"{a['width']:g} × {a['height']:g} µm" for name, a in abstracts.items()})
mapping = device_mapping("NANY", selected="XCN1")       # LVS-matched schematic devices on the real GDS
show(highlight_devices(mapping, {"XCP1", "XCN1"},
                       title="NANY: Y → XCP1/XM6 → c1 → XCN1/XM7 → VMID, A=−1 B=+1"))
'''

ARITHMETIC = r'''
ha = flow.load(ROOT/"examples/half_add.tv", "half_add")
fa = flow.load(ROOT/"examples/full_add.tv", "full_add")
fa_table = fa.truth_table()                                     # all 27 input states
assert np.array_equal(fa_table["a"] + fa_table["b"] + fa_table["cin"], fa_table["sum"] + 3*fa_table["cout"])
ha_counts, fa_counts = ha.synthesize().report()["cells"], fa.synthesize().report()["cells"]
print("half_add:", ha_counts, "  full_add:", fa_counts)
'''

SYNTHESIS = r'''
fa_net = fa.synthesize()                         # rewrite → map to cells → equivalence check
print(fa_net.report()["equivalence"])
half_net = flow.load(ROOT/"examples/half_add.tv", "half_add").synthesize()
display(value_selector(half_net))                # click input trits; every net shows its settled value
'''

SCHEMATIC = r'''
sch = net.schematic(inputs={"a[0]": 1, "a[1]": 0, "b[0]": 1, "b[1]": 0, "cin": 0}, net_names=True,
                    title="Two-trit adder: mapped hierarchy and settled trits")
display(sch)                                     # the synthesized netlist, drawn as a schematic
'''

PNR = r'''
png = render_gds(lay.gds_path, out/"adder2_demo.layout.png", top=net.top)   # KLayout render of the GDS
display(Image(filename=str(png), width=760))
s = lay.stats
print(f"{s['instance_count']} cells in {s['row_count']} rows · die {s['die_size_um'][0]:.0f} × {s['die_size_um'][1]:.0f} µm"
      f" · utilization {100*s['utilization']:.0f} % · annealing shortened HPWL by {s['hpwl_improvement_pct']:.0f} %")
'''

PRE = r'''
pre = lay.extract(wire_c=False).simulate(vectors, load=LOAD_F, expected=adder_reference,
                                         nodeset=guesses, **CONDITIONS)    # same devices, no wire C
for pin, t_post in post["measurements"]["max_settling_s"].items():
    print(f"{pin:7s} devices only {1e9*pre['measurements']['max_settling_s'][pin]:6.1f} ns"
          f"  →  with wire C {1e9*t_post:6.1f} ns")
wire_report = lay.result.net_parasitics()                                 # routed wire C per logical net
routed_sch = sch.annotate(parasitics=wire_report, title="Same schematic: settled trits and routed wire C (fF)")
display(routed_sch)
'''

STA = r'''
from tritflow.sta import analyze
states = [dict(zip(inputs, v)) for v in vectors]
wire_caps = {name: e["wire_capacitance_f"] for name, e in wire_report["nets"].items()}
timing = analyze(net, vector_pairs=list(zip(states, states[1:])), wire_caps=wire_caps,
                 output_load_f=LOAD_F, input_transition_s=EDGE_S)    # milliseconds, no SPICE
for pin, t_sta in timing.arrival.items():
    print(f"{pin:7s} STA {1e9*t_sta:6.1f} ns   SPICE {1e9*post['measurements']['max_settling_s'][pin]:6.1f} ns")
'''

CUSTOM = r'''
custom_circuit = load_edited(example, source, BUILD/"your_circuit"/"source"/example.top)
custom = custom_circuit.synthesize()                                     # your HDL → cells
display(custom.schematic(net_names=True, title=f"{custom.top}: schematic of the edited HDL"))
'''

CUSTOM_LAYOUT = r'''
custom_out = BUILD/"your_circuit"/example.top
custom_lay = custom.place_and_route(output_dir=custom_out, seed=0, anneal_steps=600)   # → GDS
print("DRC clean:", custom_lay.drc()["clean"], "· LVS match:", custom_lay.lvs()["matched"])
display(Image(filename=str(render_gds(custom_lay.gds_path, custom_out/f"{custom.top}.layout.png",
                                      top=custom.top)), width=760))
'''

SHUTTLE = r'''
chip = json.loads((ROOT/"notebook/assets/chip/adder4/signoff.json").read_text())   # recorded run, adder4 seed 7
display(Image(filename=str(ROOT/"notebook/assets/chip/adder4/tr_1um_adder4.png"), width=640))
table([["Check", "Result"]] + [[k, chip[k]] for k in
      ("drawing_drc", "drawing_lvs", "mask_drc", "mpw_precheck", "submission_ready", "reason")])
# Reproduce locally with KLayout and the OpenSUSI MPW template (see docs/status/PNR.md):
#   full = macro.to_chip(); full.signoff()
'''

EDIT = r'''
# Your circuit: edit this TritVerilog, then run the cells below.
# This first edit writes min(a, b) through De Morgan, as -max(-a, -b).
source = """
module minmax(input  trit a, b,
              output trit lo, hi);
  assign lo = ~((~a) | (~b));   // min(a, b)
  assign hi = a | b;            // max(a, b)
endmodule
"""
'''

BROKEN = r'''
from tritflow.hdl import HDLError
broken = """
module broken(input trit a, b, output trit y);
  assign y = a + b;   // '+' on signals is not a gate
endmodule
"""
try:
    flow.loads(broken, "broken", filename="your_circuit.tv")
except HDLError as error:
    print(error)
    print("Repair: use gates for signal arithmetic; e.g. nany(a, b) gives the negative saturated sum.")
else:
    raise AssertionError("unsupported signal arithmetic must be rejected")
'''

PICK = r'''
from examples.curated import DESIGNS
from tritflow.synth import evaluate_netlist
CHOICE = os.environ.get("TRITFLOW_CIRCUIT", "minmax")   # or: sign | compare2 | mul2
example = DESIGNS[CHOICE]                                # its independent arithmetic reference
if CHOICE != "minmax":
    source = example.path.read_text()
print(example.description)
'''
