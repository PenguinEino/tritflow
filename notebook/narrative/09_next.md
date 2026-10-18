## 9. Next: compare the model with silicon

The reference-cell chip is expected in {history.delivery_month}. Measurement
will connect the divider and timing predictions to real devices: first DC
output levels and static rail currents, then settling with known stimulus
edges and loads. The recorded supply voltages, temperature and probe loading
will define a matching SPICE experiment.

<!-- figure: ch9 -->

The first comparison will sweep the input through the middle region and
measure the output and each rail current. Next, step between trit levels,
measure final entry into the same voltage bands, and repeat at several loads.
Record pad, package and instrument capacitance alongside the circuit load.
Supply and temperature sweeps can then show which discrepancies depend on
bias and which call for changes to the interconnect or device assumptions.

> **What this shows.** TritFlow provides the predictions, layouts and test
> stimuli for a matched measurement; the middle-level check uses the same
> ±{levels.band_v} V target band as the notebook.
