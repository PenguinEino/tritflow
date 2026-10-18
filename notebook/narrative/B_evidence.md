## Appendix B. Verification evidence and how to rerun

Each result below links its HDL, library, PDK and native reports. A recorded
result retains the tools and conditions of the run that created it. Reading a
saved report does not execute a new physical or electrical check.

<!-- figure: appendix-b; generated evidence tables -->

| Check | Result from the selected evidence |
|---|---|
| Source identity | {evidence.source_commit} |
| Qualified PDK | {evidence.pdk_commit} |
| Tools used in this session | {evidence.tools} |
| Cell qualification | {evidence.cell_checks} |
| Sizing candidates and unavailable results | {evidence.sizing_checks} |
| Row abutment | {evidence.abutment_checks} |
| Selected adder | {evidence.adder_checks} |
| Width sweep | {evidence.width_checks} |
| Load sweep | {evidence.load_checks} |
| Random-design routing checks | {evidence.routing_checks} |
| Automated regression | {evidence.tests} |
| Colab verification | {evidence.colab_status} |

Use the routing realization below to distinguish paper figures from the
four-design results; a circuit name alone does not identify its layout.

| Figure or result set | Routing realization |
|---|---|
| Paper adder overview and placement | {paper_adder.run_id} |
| Paper full-adder waveform and load sweep | {paper_post.run_id} |
| Paper width sweep | {paper_scaling.run_id} |
| Four-design archive: adder4 | {archive.adder_run_id} |
| Four-design archive: full_add | {archive.full_add_run_id} |
| Four-design archive: mac1 | {archive.mac1_run_id} |
| Four-design archive: mul1 | {archive.mul1_run_id} |

The detailed physical and timing tables repeat that identifier in a
**Routing realization** column on every design/output row. The paper and
archived full adders use different routes, so their sum-settling values are
separate measurements even at the same external load and input interval.

For each analog experiment, the expanded table gives the actual input order,
unique states visited, possible states, interval, edge time, maximum timestep,
temperature, external load, initialized segment and pass criteria. Per-output
band errors and settling times accompany the waveforms. Initialization is
excluded from transition maxima. Soft Newton starting guesses, when used,
are listed with the circuit; they do not constrain the transient.

**Run the notebook.** Open the Colab badge and select **Runtime → Run all**.
The setup cell prints the resolved source revision and installed tools.
The default session runs the opening adder and selected editable circuit;
larger sizing, width and load sweeps can read their recorded data. The closing
table labels fresh calculations, local reuse and recorded experiments, with
wall time for each stage. The measured runtime for this session is
{evidence.session_seconds} s including setup. The clean-Colab result above
states whether an installation-inclusive Run all has completed successfully.

<details>
<summary>Repeat the calculations</summary>

Set `TRITFLOW_FORCE_RUN=1` before running to recompute expensive notebook stages,
including the shared-design examples. This bypasses both the local result
cache and the recorded shared-design archive. The variable does not regenerate
the separate cell-characterization, sizing, width or load publications.
`TRITFLOW_EXTENDED=1` enables the additional notebook experiments.
The build directory is selected by `TRITFLOW_NOTEBOOK_BUILD`.

From a full checkout with the pinned PDK and tools installed, these commands
regenerate the larger simulation experiments and check their results:

```sh
python3 -m tritflow.sim.sizing
python3 examples/postlayout_all.py
python3 examples/adder_scaling.py --jobs 1
python3 -m tritflow.sim.publication
python3 -m pytest tests/sim tests/extract -q
```

`tritflow.sim.load_sweep.sweep_output_load(directory, destination=...)` repeats
the full-adder load experiment against the generated physical design.
`tritflow.sim.scaling.run_scaling(...)` selects widths and a destination for a
new scaling experiment. Existing inputs and native outputs are checked before
reuse; remove the corresponding experiment output or choose a new destination
to require fresh computation. Failed or missing measurements stay visible.

Run the HDL, synthesis and physical regressions separately when changing those
parts of the flow. Native DRC/LVS reports, SPICE decks, simulator logs and
waveforms are retained beside each generated design.

</details>

<details>
<summary>Sources and licenses</summary>

[TritFlow](https://github.com/PenguinEino/tritflow), the
[author's reference ternary circuits](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic)
and [OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um) provide the design
sources. KLayout packages come from the
[official distribution](https://www.klayout.de/build.html).
The submission includes its Apache-2.0 license and NOTICE; the derived
historical schematic illustrations are released by their author under the
same license. The PDK retains its own license and attribution.

</details>
