# Prediction calculations for FRONTEND

This file specifies calculations, not new simulation APIs. Render only the
short equations and computed comparisons already placed in chapters 1, 2 and
7. Compute each prediction before revealing the comparison trace. Preserve
full precision internally and use the same display rounding as measured data.
Every numerical input must pass the source checks in placeholders.md.

## Chapter 1 — the inverter at its middle input

Use INV at A=VMID, with MP bulk/source at VDD and MN bulk/source at VSS.
The canonical connectivity is `tritflow.cells.circuits.circuits()['INV']`;
actual dimensions come from
`tritflow.sim.sizing.published_dimensions('INV')[1]`, keys MP, MN, RP, RN.
Do not infer dimensions from legacy free-text schematic annotations.

The simplest square-law approximation uses

\[
C_{ox}=\frac{\epsilon_{ox}}{t_{ox}},\qquad
r_{p,n}\simeq
\left[\mu_{p,n}C_{ox}\frac{W_{p,n}}{L_{p,n}}
\left(|V_{GS,p,n}|-|V_{T,p,n}|\right)\right]^{-1},
\]
\[
R_u=R_{RP}+r_p,\quad R_d=R_{RN}+r_n,\quad
I_h=\frac{V_{DD}-V_{SS}}{R_u+R_d},\quad V_h=V_{SS}+I_hR_d,
\quad P_h=(V_{DD}-V_{SS})I_h.
\]

| Variable | Exact source and conversion |
|---|---|
| VDD, VMID, VSS | `tritflow.VDD`, `.VMID`, `.VSS`; cross-check grid `$.conditions.supplies_v`. |
| Wp, Lp, Wn, Ln | `published_dimensions('INV')[1]`, `['MP'/'MN']['w_um'/'l_um']`; multiply lengths by 1e-6 for SI; W/L is dimensionless. |
| Resistor W, L | Same call, RP/RN dimensions; the published sweep keeps each RR width in its supported model branch. |
| μp, μn | `$TR1UM_PDK/libs.tech/spice/models/models_IP62_mos_v2.lib`, model `PMOS_mst`/`NMOS_mst`, parameter `u0`, in m²/(V·s). |
| tox | Same two model blocks, parameter `tox`, in metres; use each device's value. |
| VTp, VTn | Same blocks, `vth0`, including the nominal `vthMP`/`vthMN` offsets from `ip62_models`; these offsets are not statistical corners. |
| εox | `3.9 * scipy.constants.epsilon_0` in F/m, an explicitly assumed SiO₂ permittivity; not a fitted device parameter. |
| VGS magnitudes | `abs(VMID-VDD)` for MP and `abs(VMID-VSS)` for MN; these are source-referenced overdrives, not the full rail span. |
| RRP, RRN | Correct `F_RR` width branch in `models_IP62_res_v5.lib`, using each resistor's L in µm and the zero-bias geometry term described below. |
| SPICE output/current | `load_grid('INV')['rows'][adopted_index]['dc']`, row with `input_trits == [0]`, `output_v.Y` and signed `rail_current_a`. This is source-level DC, matching the schematic-dimension estimate. |

For the adopted RR width, the model has a dedicated branch
`.elseif (w == 2.8u)`. Extract its geometry polynomial coefficients from that
branch, not from the unrelated `F_RS` or the wider RR branches:

\[
R_0(L_\mu)=aL_\mu^2+bL_\mu+c.
\]

Here a, b, c are the coefficients in the model expression beginning
`(-0.1716*((l*10**6)**2)+486.5*(l*10**6)-3605.5)`; those digits identify the
source expression, not copied notebook results. FRONTEND should parse this
expression's three signed coefficients and evaluate it for RP and RN. The hand
estimate keeps the nominal-temperature, zero-bias term. The full model adds
temperature, well-bias and voltage-gradient corrections in SPICE. This choice
is explicit so the hand calculation remains independent of a fitted DC current.

Reject nonpositive R or MOS overdrive. Outside a valid conducting INV bias,
show “divider approximation not applicable”; do not extend this equation to
the off branch at the rail inputs or the NANY clamp. The input slider still
uses the measured transfer curve at those points. A predicted middle-level
offset need not match SPICE's sign: the simple model intentionally omits
mobility degradation and bias-dependent RR asymmetry.

Compute measured power from `-sum(Vrail*Irail)` over all three supplies.
Never sum absolute rail currents and multiply by the rail span: that counts
the same through-current twice. DC rows, not late transient samples, supply
static-power comparisons.

## Chapter 2 — a change of W/L or resistor length

Use the same nominal INV model inputs as chapter 1. For grid row j, read
`grid['rows'][j]['dimensions']`; row `grid['adopted_index']` is the baseline.
Hold the zero-input gate voltages fixed while changing dimensions.

\[
r_{p,n}'=r_{p,n}\frac{(W/L)_{p,n}}{(W/L)'_{p,n}},\quad
R_u'=R_0(L_{RP}')+r_p',\quad R_d'=R_0(L_{RN}')+r_n',
\]
\[
V_h'=V_{SS}+\frac{(V_{DD}-V_{SS})R_d'}{R_u'+R_d'},\qquad
\Delta V_h=V_h'-V_h,\qquad I_h'=\frac{V_{DD}-V_{SS}}{R_u'+R_d'},
\]
\[
\Delta V_h\simeq (V_{DD}-V_{SS})
\frac{R_u\Delta R_d-R_d\Delta R_u}{(R_u+R_d)^2}.
\]

Use the full primed divider for the displayed number at large grid steps;
the derivative in the chapter explains direction for small changes. Compare
with the difference of zero-input DC `output_v.Y` between row j and baseline.
This is a middle-level shift, distinct from `max_error_v`, which covers every
discrete input state. Report `max_static_current_a` explicitly as maximum
absolute rail current; use the zero-input signed rail sum for the optional
power comparison. Mark failed rows and retain missing metrics as missing.

The baseline marker means “dimensions used in the reference design”; a temporary
sizing row does not update physical abstracts or validate a new cell. NANY's
grid may be explored with the same measured panels, but the simple INV divider
prediction is shown only when INV is selected.

## Chapter 7 — predict width scaling from one slice

Load and validate `results/adder_scaling.json`. Let `one` be the complete,
passing row with `n == 1`. Use its device-only measurements, so wire length in
wider layouts has not already been fitted into the estimate.

\[
t_{c,1}=\texttt{one.carry.pre.endpoint\_max\_settling\_s.cout},\quad
t_{e,1}=\texttt{one.carry.pre.max\_settling\_s},\qquad
t_h(N)=t_{e,1}+(N-1)t_{c,1}.
\]

Each row's `carry.pre.max_settling_s` and `carry.post.max_settling_s` is the
maximum of cout and the most significant sum output over the recorded full-length
carry assertion/release cases of both polarities. Compare those same endpoints
with the estimate, not an unrelated maximum over every output/state. Use only
the one-slice row for prediction; the all-width OLS slopes are a separate
description of the measured points. The standalone slice includes its input
ramp and external output load; repeating that stage is an approximation, not
an STA calculation. Keep its assumptions in the figure hover and Appendix A.

For zero-state power, synthesize the selected width with
`flow.load(ROOT/'examples/adder.tv', 'adder', {'N': N}).synthesize()` and
count instances by cell type. Read each used cell's `.char.json`, select its
all-zero input row (an empty input vector for ties), and form

\[
P_c(0)=-\sum_r V_r I_{r,c}(0),\qquad
P_h(N)=\sum_c n_c(N)P_c(0).
\]

Dimensions, extraction hashes, supplies and model hashes must match the chosen
scaling result. Check that all ideal internal nets in the all-zero adder are
zero with `evaluate_netlist(net, zero_inputs, return_all=True)`; the zero-bias
cell sum is valid for this network because INV and NANY preserve zero.
If a future adder includes nonzero ties or internal states, evaluate those
states and select their actual cell DC rows instead.

The measured zero-state comparator is the all-zero `input_trits` row in the
scaling artifact `postlayout/static.json`, field `static_power_w`. Locate it
from the row's `artifacts_sha256` path ending `/postlayout/static.json`, verify
the digest, then read it. The default location is
`build/adder_scaling/adder<N>/postlayout/static.json`. This native file must be
included in the recorded experiment or exposed as a compact verified table to
make that comparison portable. If unavailable, use the maximum/mean fields
only with their own labels; never relabel a tested-state maximum as zero-state
power. This is an integration request, not an existing new JSON field.

The macro power fit uses `fit_scaling(result)['static_power']['slope']` and
applies to this adder mix and tested-state maximum only. Rail-current utilization
comes from the selected row's `em_check.max_utilization`, not the power-fit
slope. Display wire-C assumptions and the separate ideal-supply/rail-network
models in Appendix A/B. Optional STA or corner comparisons can join this
figure only with current, complete evidence; the required story needs neither.
