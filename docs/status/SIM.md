# SIM Phase 2 — in progress (2026-10-18)

Cascade/fanout and Plotly waveform/DC functions are implemented. All five compact
logic cells pass five-stage chains and actual fanout 1/2/4/8 across each receiver
pin / other-input bias. Current `.char.json` files now recommend 8 (largest
measured count, not extrapolated) and retain the earlier capacitance estimate.
Source hashes match the published 132 um cells. RR20 reference-chain replay
matches saved output checkpoints within 7.75e-8 V.

`full_add` compact PNR: strict LVS matches, all 27 pre/post input vectors PASS,
post includes GDS-derived wire C; maximum level error 43.34 mV. Worst SUM settles
100.57 ns pre / 110.07 ns post; COUT 90.62 / 101.57 ns. IR solution and standalone
Plotly pre/post HTML are in `build/full_add/postlayout/`.

`examples/postlayout_all.py` is watching for the remaining PNR files. It validates
embedded masters against current cells, snapshots consumed views, detects changed
inputs, rejects stale results and writes all evidence under each postlayout/.
The plan exhausts 27 full_add / 81 mac1 / 9 mul1 inputs; adder4 uses 20 documented
cases including both polarities of four-digit carry propagation and release.
Identical electrical experiments can reuse stored waveforms while LVS and IR
are rerun for changed metadata. PDK model hashes are part of the waveform cache.

Fixed two integration issues: PDK-purged unused power formals are restored only
when recursively proven unloaded; purged unconnected metal is accounted for
when identifying the LVS metal layers. Signal port mismatches remain errors.
Also tolerate decimal time roundoff of a few ulps at the final sample, while
rejecting real truncation. Current targeted tests pass; the previous complete
regression passed 30 tests before the final integration fixes. Final full-suite
results and all four design tables will replace this progress section.
No additional packages installed.

---

# SIM stream status

Complete, 2026-10-18. No blockers. No packages installed. No git-state changes.
Owned implementation paths only, plus the explicitly authorized cell `.char.json`
outputs. Reference checkout and PDK were read only.

## Delivered

- `tritflow.sim`: isolated batch ngspice runner with timeout/error handling,
  wrdata and real ASCII-raw numpy readers; arbitrary-subcircuit PWL benches;
  configurable edges, holds, loads, temperature and initial .nodeset guesses;
  exhaustive states and Euler tours of every directed input-vector transition;
  checkpoint error, inclusive ±0.5 V PASS, final band-entry settling and rail
  currents; DC sweep helper. Bit-blasted names such as `a[0]` work in both
  SPICE circuits and Nutmeg output expressions.
- `tritflow.sim.characterize`: independent DC operating points, rail currents,
  AC input capacitance at every trit bias, all directed transitions at
  10 fF / 100 fF / 1 pF, and nominal max-fanout suggestions. CLI and Python API.
- `tritflow.sim.compare_layout`: identical pre/post vectors and loads, with
  per-output, per-transition post-minus-pre settling differences. Unsettled
  transitions retain null differences.
- `tritflow.extract`: installed PDK KLayout extraction/LVS; GateNetlist reference
  generation; actual-GDS/LVS per-net metal capacitance or routed-PNR-geometry
  capacitance; safe in-subcircuit capacitor insertion with LVS net-name mapping;
  sparse rail nodal solver and a PNR/characterization adapter reporting per-cell
  rail voltages and estimated ternary-zero shift.
- Usage and scope: `tritflow/sim/README.md`, `tritflow/extract/README.md`.

## Verified results

Copied `~/balanced-ternary-logic/full_adder.gds` into the test workspace and ran
the official PDK deck against `full_adder.extracted`. All four hierarchical
circuits match (full_adder, half_adder, inverter, nany), no errors. A separate
negative test confirms a missing top output is rejected.

Fresh extracted full_adder, 27 input combinations, 10 fF per output, 200 ns hold,
1 ns edges and 0.5 ns maximum timestep: all PASS, maximum output error 0.04334 V.
SUM worst settling is 100.25 ns; COUT is 89.83 ns, measured from edge start.
Pre/post comparison passes on those same 27 inputs. Adding the estimated
actual-GDS top-net wire capacitances also passes all 27 inputs at 500 ns hold.
This additional test covers estimated substrate C, not calibrated signoff PEX.

Source-schematic fixtures first qualified INV and NANY while CELLS was working.
The published characterization files now use actual CELLS `.ext.spice` outputs,
with matching source SHA256 and a PDK model-file SHA256 manifest. All logic-cell
DC states and directed transitions pass at each load:

| Cell | Max DC error (mV) | Max input C (fF) | Max rail current (uA) | Settling at 10 fF / 100 fF / 1 pF (ns) | Suggested fanout |
|---|---:|---:|---:|---|---:|
| INV | 39.542 | 114.426 | 407.166 | 4.852 / 7.508 / 38.126 | 4 |
| NAND | 102.661 | 206.132 | 435.377 | 8.221 / 10.718 / 40.595 | 4 |
| NOR | 158.997 | 277.988 | 434.207 | 21.805 / 24.003 / 50.223 | 3 |
| NANY | 44.600 | 394.061 | 421.361 | 16.627 / 19.655 / 50.813 | 2 |
| BUF | 35.237 | 114.426 | 814.302 | 7.704 / 9.873 / 39.453 | 4 |

INV/BUF use all 6 directed transitions; NAND/NOR/NANY use all 72. TIEP/TIEZ/TIEN
also pass their single DC state and loaded initialization; no input transitions
exist for ties, so their max transition settling and fanout are null.

IR solver tests cover an analytic two-resistor loaded ladder (including KCL),
dual-ended supply, sparse synthetic PNR geometry, three separate supplies,
M1/M2 via connections, signed current direction, divider midpoint shift,
NANY VMID shift, and floating-rail rejection.

## Decisions and limits

- Parse each actual `.subckt` declaration: legacy extracted pin order differs
  from the new contracted cells. GateNetlist reference generation strictly
  requires the new contract's signal pins followed by VDD/VMID/VSS.
- The installed deck can report success with a missing top port despite its
  strict-port message. The wrapper additionally compares top pin-name sets,
  case-insensitively. Any difference fails LVS. Process exit zero alone is
  insufficient; comparison statuses, database errors and deck message are checked.
- Extraction without a reference returns `matched=null`, `report=null` because
  the PDK writes no connectivity database in its netlist-only mode.
- ngspice runs without user startup files, in isolated temporary directories,
  using absolute model includes, ideal +5/0/-5 V rails and nominal 27 C.
  Default 1e12 ohm shunts aid convergence. .nodeset supplies initial DC guesses,
  never forced transient voltages. Artifacts are retained only with workdir.
- Check levels 1 ns before each segment end. Measure settling from input ramp
  START through the final band crossing, then require staying in band through
  segment end. Linear interpolation is limited by simulator timestep. The
  initialization segment is excluded from maximum transition delay.
- Transient tail current samples are estimates. Characterization uses separate
  true DC operating points for static rail current. SPICE current sign is
  positive INTO the ideal source: normally VDD is negative, VSS positive.
- Input capacitance: -Im(I(Vin))/(2*pi*1 MHz), one input driven with 1 V AC,
  other inputs/rails AC grounded, output unloaded, at every trit bias. This is
  biased in-circuit driving-point C including Miller response. Fanout is the
  heuristic min(4, floor(largest tested passing load / maximum measured C));
  it is not a multi-cell-path or PVT qualification.
- PDK models and OS00 reference manual provide no calibrated interconnect R/C
  coefficients found during this work; OS00 explicitly lists parasitic extraction
  as unavailable. C assumes SiO2 epsilon_r=3.9, effective M1/M2 heights 1/2 um:
  area coefficients 0.03453/0.01727 fF/um²; fringe 0.02 fF/um perimeter.
  Sheet R defaults to assumed 0.05 ohm/square (roughly assumed aluminum rho
  2.5e-8 ohm*m / 0.5 um thickness), via R to assumed 0.05 ohm. All are overridable.
- GDS C uses merged top-net metal including connected cell pin metal. Local
  child-only internal nets are outside the top-level estimate. The PNR alternative
  measures routed wires/pins only. Do not add both estimates together. No coupling,
  shielding, via C or signal-wire R is claimed.
- IR uses Manhattan centerlines, cell-center taps on template rail y coordinates,
  fixed supply pads and constant nominal-bias currents. No package/thermal model,
  finite-width current spreading, overlapping parallel conductor correction or
  current-versus-local-voltage iteration. Missing supply connections raise errors.
  Without explicit per-instance vectors, currents are independent per-rail maxima,
  an envelope that may not occur for any common input pattern. INV/NAND/NOR zero
  shift assumes equal pull-up/down conductance; NANY reports local VMID shift.

## Characterization JSON schema (version 1)

`cells/out/<CELL>/<CELL>.char.json`:

- `schema_version`, `cell`, `top`, `inputs`, `output`, `created_utc`,
  `source_sha256`, `model_sha256`, `conditions` (supplies_v, temperature_c,
  band_v, edge_s, hold_s, step_s), `passed`.
- `dc[]`: `input_trits`, `output_v`, signed `error_v`, `rail_current_a`
  keyed by VDD/VMID/VSS, `passed`. `max_static_current_a` is the maximum absolute
  rail current across these rows, usable directly for conservative PNR sizing.
- `input_capacitance`: method, frequency_hz, max_f, and rows with input_trits,
  pin, capacitance_f.
- `transient[]`: load_f, passed, max_error_v, max_settling_s (per output),
  unsettled, sample_step_s, rows. First row is initialization; remaining rows
  cover each directed transition exactly once. Each row includes input_trits,
  previous_trits, check_s, rail_current_a, passed and outputs. Each output gives
  ideal_trit, voltage_v, error_v, passed, settling_s. Unsettled times are null.
  A null maximum with no transitions is distinguished by unsettled=0.
- `fanout`: suggested_max, tested_load_f, method, scope. JSON has no NaN/Infinity.

## Interface requests / information for other streams

No shared-contract changes requested.

- FRONTEND/PNR: nominal suggestions are INV/NAND/BUF=4, NOR=3, NANY=2. The
  full measured characterization is in the cell JSON, with assumptions above.
- PNR can consume `max_static_current_a`; signed per-vector currents are in
  `dc[*].rail_current_a`. IR needs `power.rails/straps/vias/pins` plus placements,
  template and abstracts, matching the current PNR power producer.
- PDK `openIP62/IP62/Technology/doc/OS00_リファレンスマニュアル_rev1.1.pdf`,
  section I.3.1, gives permissible wire currents M1(2 um): 900 uA;
  M2(3 um): 3.7 mA. Section I.3.2 gives step M1(2 um): 500 uA and
  TC(1.4 um square): 780 uA per via (instantaneous ceiling 7.8 mA per via).
  These documented ratings are separate from assumed interconnect R/C values.

## Reproduction

```
python3 -m pytest tests/sim
python3 -m pytest tests/extract
python3 -m pytest tests/sim tests/extract
python3 -m tritflow.sim.characterize INV
python3 -m tritflow.sim.characterize NANY
```

Requires the project's installed numpy/scipy/klayout, ngspice, KLayout binary and
TR-1um PDK (`$TR1UM_PDK`, default `~/pdk/TR-1um`). The full-adder integration test
also needs `~/balanced-ternary-logic`; it copies the GDS/reference to a temp folder
and never writes the original. In an environment missing these external tools or
reference data, affected integration tests explicitly skip; they ran here.

Final results: **23 tests passed, no skips**: SIM 15/15 in 23.38 s and
extraction 8/8 in 93.37 s. The earlier combined regression also passed before
the bit-blasted-port test was added. After merging geometry during LVS metal-layer
identification, the wire-C tests passed again and actual full-adder GDS extraction
still identifies all 12 top nets with unchanged capacitance values.
`compileall` and `git diff --check` on owned paths pass. Additional actual-cell
GateNetlist simulation with `a[0]` / `y[0]` also passes.
