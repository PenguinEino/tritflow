# Add TritFlow: balanced-ternary HDL to GDS on OpenSUSI TR-1um

This submission adds an educational IC-design notebook under
`ISSCC27/submitted_notebooks/TritFlow/`. TritFlow turns a Verilog-like
description of signed ternary arithmetic into standard cells, routed GDS,
PDK drawing-DRC/LVS results and extracted ngspice waveforms on
[OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um).

The opening example follows a {paper_adder.width}-trit adder from
{paper_adder.hdl_lines} top-level HDL lines plus shared arithmetic modules
to {paper_adder.cells} cells and a {paper_adder.die_um} µm layout, with
{paper_adder.drc_items} drawing-DRC markers and LVS {paper_adder.lvs_status}.
Readers then connect the middle voltage to the transistor/resistor branches,
compare hand estimates with SPICE, inspect synthesis and routing, and edit
a circuit to repeat the flow.

## Contribution

The notebook connects the analog behavior of a ternary gate to the complete
digital implementation flow. The library adapts the author's taped-out cell
designs into abuttable three-rail cells. Synthesis checks source-to-cell logic;
LVS checks extracted connectivity; the analog test uses an independent
arithmetic reference and explicit voltage bands.

The static figures show DC transfer and current, sizing tradeoffs, cell
adaptation, value-colored arithmetic, placement progress, extracted settling
and width scaling. The measured adder series gives
{scaling.device_slope_ns} ns/trit for extracted devices alone and
{scaling.wired_slope_ns} ns/trit with estimated wire capacitance, and an
effective {scaling.power_per_cell_mw} mW per cell for tested-state DC-power
maxima. These results make the physical cost of the resistive middle level
visible alongside the arithmetic.

## Review and reproduction

The submitted notebook and supporting files are confined to
[`ISSCC27/submitted_notebooks/TritFlow/`](ISSCC27/submitted_notebooks/TritFlow/),
following the [official submission instructions](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io#program-logistics).
The [public source repository](https://github.com/PenguinEino/tritflow) contains
the Python package, HDL examples, cell library, result data and figure scripts;
the notebook fetches that implementation at its selected revision.

- Notebook: [TritFlow](ISSCC27/submitted_notebooks/TritFlow/tritflow_tr1um.ipynb)
- Colab: [open and run]({release.colab_url})
- Submitted-source revision: {release.source_commit}
- Pinned public PDK: {evidence.pdk_commit}
- Package execution: {release.capture_status}
- Automated checks: {evidence.tests}
- Clean-Colab verification: {evidence.colab_status}

Saved results retain their input coverage and conditions. The opening adder
and selected editable circuit execute in a fresh session; larger experiments
are labelled as recorded results, with instructions to recompute them.

The source cells were taped out in {history.tapeout_year}; silicon is expected
in {history.delivery_month} and has not yet been measured. Wire capacitance
is a geometry estimate, and the nominal simulation results do not establish
full interconnect, PVT, ESD or manufacturing qualification.

## Author

- Name: Einosuke Okazaki (岡崎 英之介)
- Affiliation: Information and Communication Engineering Course, Department of Monozukuri
  Engineering, Tokyo Metropolitan College of Industrial Technology (KOSEN), Tokyo, Japan
- Status: Fifth-year student (final year of the five-year KOSEN engineering programme, which
  combines upper-secondary and the first two years of tertiary education)
- Email: einosukeokazaki@gmail.com
- GitHub: PenguinEino

The submission includes the Apache-2.0 license and NOTICE. The author's
derived historical schematic illustrations use the same license; the PDK
and other dependencies retain their own attribution.
