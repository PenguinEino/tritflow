## 2. Sizing sets the middle level

Sizing changes both sides of the divider. A stronger pull-down lowers the
middle output; a stronger pull-up raises it. Increasing both series resistors
reduces static current, while MOS asymmetry still affects the voltage.
Use the inverter sweep to see level accuracy and current together, then inspect
NANY with the same controls. The star marks the adopted reference dimensions.

**Predict first.** For the conducting MOS devices, take on-resistance as
inversely proportional to \(W/L\). Apply the divider from the previous chapter
before looking at the new SPICE curve.

\[
r_{\rm on}'\simeq r_{\rm on}
\frac{(W/L)_{\rm adopted}}{(W/L)'},\qquad
I'=\frac{V_{DD}-V_{SS}}{R_u'+R_d'},
\]
\[
\Delta V_Y\simeq
(V_{DD}-V_{SS})\frac{R_u\Delta R_d-R_d\Delta R_u}{(R_u+R_d)^2}.
\]

<!-- figure: ch2 -->

*Change MOS width, MOS length or resistor length across the measured grid.
Compare the predicted middle-level shift with the SPICE marker, then look at
the worst level error over the complete discrete input table.*

> **What this shows.** For the selected INV dimensions, the predicted
> middle-level shift is {sizing.predicted_shift_mv} mV and SPICE gives
> {sizing.spice_shift_mv} mV. Across all logical inputs, worst error is
> {sizing.max_error_mv} mV and maximum absolute rail current is
> {sizing.current_ua} µA; the adopted point gives
> {sizing.adopted_error_mv} mV and {sizing.adopted_current_ua} µA.

The sweep changes schematic dimensions; generating and checking a new physical
cell is a separate step. Next we inspect the library built from the adopted sizes.
