## Appendix A. What the results establish

Logical equivalence, physical connectivity and analog settling answer different
questions. The tables in Appendix B identify the checks actually run and the
conditions of each result.

| Topic | Scope |
|---|---|
| Silicon | The reference cells were taped out. Silicon has not yet been measured. Adapted standard-cell layouts and generated designs are simulation and layout results. |
| Operating conditions | Results use nominal models and the displayed supplies, temperature, input ramps and loads unless an explicitly labelled sweep says otherwise. No statistical mismatch or general PVT guarantee follows. |
| Logic | The HDL describes combinational ternary circuits. It has no sequential logic, `x`/`z` semantics or general signal arithmetic operators. Equivalence is exhaustive or sampled as stated for each design. |
| Analog coverage | Visiting all input states in one sequence does not test every directed transition or input skew. Larger circuits use labelled carry and arithmetic patterns. Static maxima cover only their listed DC states. |
| Timing | Settling means final band entry through the recorded interval, measured from input-ramp start. Sampling and interpolation limit resolution. An unsettled output has no finite reported delay. A longer interval may change a load pass/fail result. |
| Wire model | Device extraction uses the PDK LVS deck. Added wire capacitance is a per-net lumped estimate from connected metal area and perimeter with assumed coefficients, not calibrated parasitic extraction. Signal-wire resistance, coupling, distributed poly RC and package effects are absent from the main comparison. |
| Device comparison | Equal intrinsic devices establish circuit identity. The metal-capacitance comparison adds geometry-dependent loading; neither comparison establishes full interconnect-RC or silicon equivalence. |
| Hand estimates | The divider uses approximate on-resistances and a simplified resistor model. The ripple estimate repeats a standalone carry stage; the DC cell sum uses the all-zero bias. These are explanatory predictions, not bounds on arbitrary inputs or paths. |
| Poly resistance | Optional poly-resistance studies are sensitivity calculations with an assumed gate-poly sheet resistance. Device-resistor and MOS diffusion parameters are not substitutes for a calibrated gate-poly model. |
| Power delivery | Divider cells consume static power. The rail-resistance network uses characterized current envelopes and assumed metal/via resistance; it is separate from the ideal-supply SPICE waveforms. Width-scaled published DC limits and reserved margin do not establish lifetime, transient, pad, bond or current-crowding qualification. |
| Manufacturing | Drawing DRC and strict LVS concern the reported core. Mask preparation, mask DRC, padframe, ESD, package and shuttle acceptance require their own evidence. An optional chip wrapper is identified separately; passing its geometry checks alone does not grant shuttle approval. |

The physical-library and experiment files in Appendix B keep the assumptions
and the tested input plans available for reuse.
