# Static figure captions

## fig_flow

**TritFlow from HDL to extracted simulation** For run {paper_adder.run_id},
a {paper_adder.width}-trit adder described in {paper_adder.hdl_lines} top-level
HDL lines plus shared arithmetic
modules maps to {paper_adder.nany} NANY and {paper_adder.inv} INV cells, with
{paper_adder.equivalence_mode} source-to-cell equivalence.
The {paper_adder.die_um} µm layout uses two routing metals and three supply
rails, with {paper_adder.drc_items} drawing-DRC markers and LVS
{paper_adder.lvs_status}; the final panel shows the extracted sum and carry
waveforms with estimated wire capacitance.

## fig_gates

**DC behavior of the ternary logic cells** (a) Output voltage and (b) absolute
VDD current versus input A for the extracted INV, NAND, NOR and NANY cells at
{paper_gates.temperature_c} °C, with B held at each trit level where applicable.
At its middle input, INV draws {paper_gates.inv_current_ma} mA from VDD,
corresponding to {paper_gates.inv_power_mw} mW of signed total rail power;
shading marks the ±{levels.band_v} V output acceptance bands.

## fig_sizing

**Dimensions control middle-level accuracy and standing current** (a) INV
transfer curves for resistor lengths {paper_sizing.resistor_lengths_um} µm
at the adopted MOS dimensions; (b,c) worst discrete-state level error versus
maximum absolute rail current for {paper_sizing.inv_count} finite INV and
{paper_sizing.nany_count} finite NANY results.
Filled and open markers distinguish errors within and outside
±{levels.band_v} V, inverted triangles place errors below
{paper_sizing.error_floor_mv} mV at the display floor, and outer rings identify
the dimensions used in the reference design.

## fig_cell

**Adapting the reference NANY to a three-rail cell row** (a) The taped-out
reference layout occupies {paper_cell.original_die_um} µm; (b) the adapted
cell retains its circuit and device sizes in a {cell.width_um} ×
{cell.height_um} µm footprint, with the device groups and supply rails labelled.
(c) An abutted row of {paper_cell.row_count} logic cells carries VDD, VMID
and VSS continuously across the indicated cell boundaries.

## fig_synth

**Arithmetic expressed as ternary cells** (a) Shared half-adder and full-adder
HDL, (b) the mapped half adder with {arithmetic.ha_nany} NANY and
{arithmetic.ha_inv} INV cells, and (c) the full-adder hierarchy with
{arithmetic.fa_nany} NANY and {arithmetic.fa_inv} INV cells.
Net colors show settled negative, middle and positive trits for the illustrated
inputs; the sum and carry preserve the integer total in both examples.

## fig_pnr

**Placement and routing of the illustrated adder** (a) Initial placement in
signal order, (b) the annealed and routed {paper_adder.width}-trit layout
occupying {paper_adder.die_um} µm in run {paper_adder.run_id}, and (c) the
recorded cell-terminal HPWL.
Annealing reduces HPWL from {paper_pnr.initial_hpwl_mm} to
{paper_pnr.final_hpwl_mm} mm, a {paper_pnr.hpwl_reduction_pct}% reduction;
cell colors identify full-adder digits, while the routes distinguish
horizontal M1 in channels from vertical M2 over the cells.

## fig_postlayout

**Full-adder settling and the observed load boundary** (a) The full adder
in run {paper_post.run_id} visits {paper_post.states} input states with
{paper_post.hold_ns} ns intervals
and {paper_post.load_ff} fF per output; device-only and device-plus-wire-C
outputs meet the ±{levels.band_v} V criterion.
(b) On the transition with the largest post-wire sum settling, final band
entry changes from {paper_post.pre_sum_ns} to {paper_post.post_sum_ns} ns
when estimated wire capacitance is added to the same extracted devices.
(c) The equal-output-load sweep brackets an observed pass and failure between
{load.last_pass_pf} and {load.first_fail_pf} pF within its
{load.hold_ns} ns intervals.

## fig_scaling

**Ripple-adders generated from one parameterized HDL source** Adders of
width {paper_scaling.width_min}–{paper_scaling.width_max} trits are synthesized,
routed, drawing-DRC/LVS checked and simulated at {paper_scaling.load_ff} fF
per output under nominal models (run family {paper_scaling.run_id}).
(a) Fits to the recorded carry-endpoint settling give
{scaling.device_slope_ns} ns/trit for extracted devices alone and
{scaling.wired_slope_ns} ns/trit with estimated wire capacitance.
(b) The tested-state DC-power maxima give an effective
{scaling.power_per_cell_mw} mW per mapped cell for this adder mix;
(c) die area and cell count show the physical cost of increasing width.

## fig_sta

**Ternary static timing compared with extracted-circuit SPICE** Each point
compares an output's maximum over the same input-transition set, using
transition-class midpoint delays, propagated slew and one endpoint settling
tail; the line denotes equality and shading marks ±{sta.target_pct}%.
Across the example designs and adders of width
{paper_scaling.width_min}–{paper_scaling.width_max}, {sta.within_target} of
{sta.output_count} output maxima fall within this band, with
{sta.mape_pct}% mean absolute percentage error (routing realizations:
{sta.run_ids}).
The separate conservative envelope, not plotted here, averages
{sta.bound_mean_factor}× the measured maxima and is conservative on the saved
nominal cases, without constituting a certified analog bound.
