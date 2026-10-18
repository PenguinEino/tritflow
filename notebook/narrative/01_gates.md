## 1. Three levels from ordinary CMOS

The middle output level comes from conducting transistor and resistor branches.
At a zero input, the inverter connects its output toward both supply rails;
the balance sets the voltage and draws current even with constant inputs.
NANY adds paths to VMID that clamp the output for opposite input trits.
Follow the selected schematic alongside its transfer curve.

The gate functions are

\[
\operatorname{INV}(a)=-a,\qquad
\operatorname{NAND}(a,b)=-\min(a,b),\qquad
\operatorname{NOR}(a,b)=-\max(a,b),\qquad
\operatorname{NANY}(a,b)=-\operatorname{clamp}(a+b,-1,1).
\]

**Predict first.** Select INV and set its input to the middle voltage. Replace
each conducting MOS with an on-resistance and keep the series resistors.
Call the complete upper and lower branch resistances \(R_u\) and \(R_d\).

\[
I_{\rm hand}=\frac{V_{DD}-V_{SS}}{R_u+R_d},\qquad
V_{Y,\rm hand}=V_{SS}+I_{\rm hand}R_d,
\]
\[
P_{\rm hand}=(V_{DD}-V_{SS})I_{\rm hand}.
\]

Equal branch resistances predict the middle voltage. The displayed estimate
uses device dimensions and the PDK's nominal model parameters; SPICE then
includes the nonlinear devices.

<!-- figure: ch1 -->

*Move the input-voltage slider. The marker follows output voltage and supply
current; the truth table identifies the nearby logical input state.*

> **What this shows.** At the middle input, the divider estimate gives
> {divider.output_v} V and {divider.power_mw} mW; SPICE gives
> {divider.spice_output_v} V and {divider.spice_power_mw} mW.
> The static current is the cost of establishing this resistive midpoint.

At \(a=0\), both \(\min(a,-a)\) and \(\max(a,-a)\) equal zero.
That example is enough to reject Boolean complementation as a synthesis rule.
