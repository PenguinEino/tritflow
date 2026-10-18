## 7. Does the layout still work?

Timing must say when an output becomes a valid trit. Here it is the time from
input-ramp start until the output enters the target's ±{levels.band_v} V band
and stays there through the input interval. Compare the same extracted devices
with and without estimated wire capacitance, then increase output load and
adder width. The carry path and static power give two predictions to test.

**Predict first.** Use a single full-adder slice to estimate a ripple path.
Let \(t_{c,1}\) be its carry settling and \(t_{e,1}\) its slower carry-or-sum
endpoint. Each added digit contributes another carry stage.

\[
t_{\rm hand}(N)=t_{e,1}+(N-1)t_{c,1}.
\]

For the all-zero input, count the mapped cells and sum their zero-input DC
powers. The rail currents retain SPICE's signed voltage-source convention.

\[
P_c(0)=-\sum_{r\in\{DD,MID,SS\}} V_r I_{r,c}(0),\qquad
P_{\rm hand}(N)=\sum_c n_c(N)P_c(0).
\]

<!-- figure: ch7 -->

*Move the load slider to the first observed failure, then choose an adder width
in the scaling panel. The prediction stays visible beside the measured points.*

> **What this shows.** At width {scaling.selected_n}, the carry-path estimate
> is {scaling.predicted_ns} ns and device-only SPICE gives
> {scaling.device_ns} ns; adding wire capacitance gives
> {scaling.wired_ns} ns. Across the displayed passing widths, the fitted
> slopes are {scaling.device_slope_ns} and {scaling.wired_slope_ns} ns/trit.
> Zero-state power is {scaling.predicted_power_mw} mW by cell summation and
> {scaling.zero_power_mw} mW by full-circuit DC simulation.

The static-power fit gives {scaling.power_per_cell_mw} mW per mapped cell
for this adder mix and the tested-state maxima. At width {scaling.selected_n},
the largest measured static power over {scaling.static_states} states is
{scaling.max_power_mw} mW. This current flows with the inputs held still;
reducing switching frequency alone does not remove it.

With {load.hold_ns} ns input intervals, the full-adder load test brackets an
observed pass and failure between {load.last_pass_pf} and
{load.first_fail_pf} pF per output. The separate DC rail calculation predicts
up to {scaling.rail_deviation_mv} mV rail deviation and
{scaling.zero_shift_mv} mV middle-level shift; its most heavily loaded branch
uses {scaling.current_utilization_pct}% of the width-scaled published DC limit.

These results cover the displayed input sequences and model conditions;
Appendix A collects their scope.
