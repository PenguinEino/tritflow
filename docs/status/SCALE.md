# SCALE — complete

2026-10-23. Required N=2,4,8,16 are complete and pass synthesis equivalence, PDK drawing DRC (0 violations), strict LVS, all transient ±0.5 V checks and independent DC checks. The juror-review additions are complete. Optional N=32 was attempted and failed routing; it is explicitly excluded from qualified curves.

## Deliverables and V3 integration

- `results/dot_scaling.json`: completed, hash-checked publication; `passed` applies to `required_sizes=[2,4,8,16]`. The unsuccessful N=32 record is in `optional_attempts`.
- `examples/dot_scaling.py`: recorded reader by default; explicit `--recompute --jobs 4` runs the full expanded campaign. `--review` adds/resumes the wire/power ablations using intact archived base evidence.
- `notebook/scale_views.py`: Japanese booktabs tables and paper-style Plotly figures, without physical-tool calls in any view.
- `results/dot_scaling/dotN/`: compressed HDL, gate JSON, GDS/PNR, actual PDK DRC/LVS evidence, extracted circuits, C estimates, vectors, timing reports, SPICE decks/logs/measurements and DC evidence.
- Seven standalone HTML/PNG previews under `results/dot_scaling/`: `scaling_table`, `synthesis_table`, `timing_table`, `power_table`, `layout_penalty_table`, `scaling_figure`, `power_figure`.
- Tests: `tests/test_dot_scaling.py`, `tests/test_scale_views.py`.

```python
from scale_views import (load_scaling, scaling_table, synthesis_table, timing_table,
                         power_table, layout_penalty_table, scaling_figure, power_figure)
data = load_scaling()  # recorded, verifies sources/PDK/evidence; no native tools
display(scaling_table(data))
display(power_table(data))
display(layout_penalty_table(data))
scaling_figure(data).show()
power_figure(data).show()
# Optional: display(synthesis_table(data)); display(timing_table(data))
# Expensive and explicit: data = load_scaling(recompute=True)
```

All table functions return IPython HTML; figure functions return Plotly Figure. Put the notebook directory on `sys.path`, as the existing notebook does.

## Logic and physical results

Every row uses synthesis/P&R seed 0. Weights remain variable HDL inputs during synthesis; only the electrical/timing experiments fix their values. Output widths are the minimum balanced-ternary widths covering [-N,N].

| N | INV | NAND | NANY | NOR | Total | Output trits | Equivalence |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 4 | 4 | 5 | 2 | 15 | 2 | 81 exhaustive |
| 4 | 13 | 8 | 21 | 4 | 46 | 2 | 6,561 exhaustive |
| 8 | 35 | 16 | 63 | 8 | 122 | 3 | 100,000 random, seed 0 |
| 16 | 92 | 32 | 175 | 16 | 315 | 4 | 100,000 random, seed 0 |

| N | Die (µm × µm) | Area (mm²) | Rows | HPWL before → after (mm) | Routed M1 + M2 (mm) | Signal / power vias | P&R incl. DRC (s) |
|---:|---|---:|---:|---:|---:|---:|---:|
| 2 | 612 × 870 | 0.532440 | 5 | 7.483 → 3.954 | 2.538 + 5.736 | 107 / 200 | 1.734 |
| 4 | 1692 × 1206 | 2.040552 | 6 | 40.083 → 24.299 | 17.778 + 22.665 | 329 / 600 | 2.978 |
| 8 | 2160 × 3054 | 6.596640 | 13 | 210.450 → 167.862 | 86.478 + 149.889 | 1146 / 1768 | 35.992 |
| 16 | 5508 × 3894 | 21.448152 | 13 | 890.294 → 832.897 | 682.752 + 547.629 | 3320 / 4888 | 48.554 |

HPWL is the placement cell-terminal estimate, excluding external ports. Routed length is drawn signal wire, not power rails. All four rows have actual PDK DRC=0 and strict device/port LVS match. Runtime is observed on the producer host, including concurrent independent sizes; it is not a universal runtime benchmark.

## Timing and layout penalty

Identical fixed-weight pairs, 100 fF/output, 1 ns edges, 2 ns maximum step, 27 °C. N≤8 holds are 1 µs; the successful N=16 sequence uses 1.25 µs. Delay is input-ramp start to final entry into ideal ±0.5 V, remaining in band through the entire hold. Initial DC dwell is checked but excluded from transition maxima.

| N | Output | STA, no wire C (ns) | STA, wire C (ns) | SPICE, wire C (ns) | STA error (%) | STA wire penalty (%) |
|---:|---|---:|---:|---:|---:|---:|
| 2 | y[1] | 56.227 | 62.939 | 79.983 | -21.309 | 11.937 |
| 2 | y[0] | 68.124 | 75.644 | 79.661 | -5.042 | 11.040 |
| 4 | y[1] | 106.126 | 122.455 | 128.579 | -4.763 | 15.386 |
| 4 | y[0] | 191.546 | 221.291 | 227.219 | -2.609 | 15.529 |
| 8 | y[2] | 363.316 | 462.167 | 432.272 | +6.916 | 27.208 |
| 8 | y[1] | 333.870 | 422.330 | 396.993 | +6.382 | 26.495 |
| 8 | y[0] | 348.286 | 437.037 | 440.210 | -0.721 | 25.482 |
| 16 | y[3] | 626.312 | 919.748 | 902.207 | +1.944 | 46.852 |
| 16 | y[2] | 596.866 | 880.450 | 868.561 | +1.369 | 47.512 |
| 16 | y[1] | 567.896 | 834.975 | 828.903 | +0.733 | 47.030 |
| 16 | y[0] | 576.166 | 839.321 | 828.619 | +1.291 | 45.673 |

Error is 100·(STA/SPICE−1). 10/11 output maxima lie within ±20%; mean absolute percent error is 4.825%. N=2 y[1] is the −21.309% outlier. This is finite matched-vector accuracy, not a global timing bound.

For **N=4 only**, both SPICE modes use exactly the same LVS-extracted intrinsic devices and terminal orientation; only added `Ctfwire*` elements are removed. Both modes pass. Device-only → wire-C SPICE:

- y[1]: 113.118 → 128.579 ns, +13.668%.
- y[0]: 199.688 → 227.219 ns, +13.787%.

The corresponding STA penalties are 15.386% and 15.529%. At N=16, STA wire penalties reach 45.7–47.5%. Fourteen NANY loads extend above the 2 pF table maximum (largest 2.862 pF); the public STA uses its documented linear load extension, below the 2× limit. Warnings remain in the recorded reports.

## Static and average supply power

Raw ngspice voltage-source current is positive into the source. Delivered supply power is `P = −Σ(Vrail·Irail) = −5·I(VDD) + 5·I(VSS)`; VMID is 0 V. The following currents are magnitudes at x=0 (raw VDD current is negative, raw VSS current positive). Both ±5 V sources are included.

| N | VDD / VSS current magnitudes at x=0 (mA) | Static x=0 (mW) | Time-average supply (mW) | Measured DC range (mW) | Static / cell (mW) | Average / cell (mW) | Hold (µs) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 5.041 / 5.041 | 50.410 | 21.720 | 4.072–50.410 | 3.361 | 1.448 | 1.00 |
| 4 | 16.348 / 16.348 | 163.479 | 85.797 | 29.511–163.479 | 3.554 | 1.865 | 1.00 |
| 8 | 45.208 / 45.208 | 452.082 | 229.513 | 86.922–452.082 | 3.706 | 1.881 | 1.00 |
| 16 | 120.019 / 120.019 | 1200.193 | 638.631 | 336.763–1200.193 | 3.810 | 2.027 | 1.25 |

- Static points are independent DC solves on the extracted circuit. x=0 is the measured maximum at every qualified N; this is a maximum over the documented states, not an exhaustive global power proof. The adder network mostly sits at the middle level and its resistive dividers draw current. Fixed ±1 weights mean not every internal MUL node is 0 V.
- The time-average is the trapezoidal integral of actual supply power on ngspice's nonuniform time grid over **all eleven holds**, including transitions and repeated states. It is not `mean_w` (the separately retained mean over unique DC states). `power.sequence` contains duration, energy, per-hold averages/energies, and raw mean rail currents.
- Per-cell denominator is mapped logic/buffer/tie instances; metal-only FILL is excluded. Static DC range per cell is also in JSON. Input-driver source power is outside the supply-only measurement.
- **Switching-only energy is not separated.** Resistive draw varies during transitions; subtracting a selected DC baseline would not uniquely identify switching energy. The JSON and Japanese table note explicitly say so.

## Conditions, decisions and interpretation

- Source is the unparenthesized `assign y = w0*x0 + ...;` expression used by dot4. The current lowering preserves left association with its public three-operand fusion; no manually balanced reduction tree or constant-weight resynthesis is substituted.
- Weights repeat (+1,−1,+1,+1). Eleven states / ten directed pairs cover zero, both full-product polarities and carry assertion/release in both signs. For output width D, H=(3^(D−1)−1)/2 other products are +1; changing product 0 from 0 to +1 changes H→H+1, every low digit +1→−1 and top 0→+1. The negative witness is symmetric. Term 0 traverses the source sum chain.
- STA receives exactly the same LVS-mapped full-GDS signal wire C as SPICE, including connected cell terminal metal once. The no-wire control zeroes only that wire-C term; intrinsic pin loads and the 100 fF test loads remain.
- Matched STA's symbolic initialization exceeded 1M nodes at N=8 with unconstrained weight inputs. Analysis-only logical TIE drivers now impose the actual fixed weights on the same weight nets; all original cells, pins and loads remain. Tests on N=2,4 reproduce original arrivals, paths, patterns and loads exactly. Physical/SPICE designs keep variable weight inputs.
- Default N=16 routing spent >5 min in maze search. A wider channel and tighter row-span current budget made it tractable: 24 tracks, requested current density 0.0001335 A/µm, 20% reserve retained, two rip-up passes, up to three floorplans. These choices are explicit in each row. Smaller N use public defaults.
- The first N=16 SPICE attempt with 2 µs holds timed out after 600 s and is retained in `spice_attempts`. STA maximum was 0.920 µs. The successful retry used 1.25 µs holds and a 900 s budget, kept the same vectors/load/ramp/step, and passed every full-window band check. Its observed runtime was 545.454 s; longest settling was 902.207 ns.
- Area grows faster than term count in this implementation: increasing arithmetic width, the current lowering, longer routes and fragmented power-feed banks all contribute. These points do not establish an optimal area law. Zero-activation static power grows from 50.4 mW to **1.200 W**; the per-cell draw remains about 3.36–3.81 mW. Reducing activity alone does not remove divider DC power.
- Nominal models only; ideal supplies, no rail IR in the transient, no signal-wire R, coupling or calibrated sign-off PEX. Area/perimeter wire-C coefficients remain explicit assumptions. DRC is the PDK drawing deck; this is not MPW mask/precheck sign-off. No binary-efficiency advantage is claimed.

## N=32 optional attempt

Synthesis passed 100,000 random input vectors, seed 0: INV=196, NAND=64, NANY=383, NOR=32 (675 cells), 4 output trits. A 24-track start with requested current density 0.000070 A/µm was needed for the power-span capacity. Seed 0 then exhausted three floorplans (24/26/28 tracks), two rip-up passes each. Failing nets were `_n164`, `_n201`, `w26`; the last congested region was x=0..417 µm, y=15..7035 µm. No canonical qualified GDS, DRC/LVS result, timing point or SPICE result is claimed. The source/gate/failure JSON evidence and exact reason are retained in `optional_attempts` and `dot32/`.

## Provenance and execution host

All final numerical rows were produced on `strata-ubuntu` (5090 server, Ubuntu 24.04 amd64), using only `~/tritflow-sim`. Independent sizes ran with `--jobs 4`; review tasks also ran independently. No unrelated service, including strata, was stopped. No extra packages were installed on either host.

- PDK: public pinned `5d963db9d44e192d37a0489c208bfccf2e2f690c`; models/decks/document hashes are recorded.
- Python 3.12.3; NumPy 2.1.3, SciPy 1.16.3, KLayout Python/CLI 0.30.6, Lark 1.3.1.
- ngspice-42 payload SHA256: `820658317b0b54035208da41936fd6871ce924036e5ea4113a4168b821b7fc45`.
- KLayout ELF SHA256: `b2cbe3e00d6b61a40fc9141f634697776041d443a1851b372b32b35073602523`. Original launch-wrapper hashes and KLayout shared-library/loader hashes are also retained in `native_binary_hashes.json`.
- `build/setupmem` disappeared after reboot. The integrator explicitly authorized the existing `runtime/native` cache. `remote_environment.json` preserves original/resolved runtime paths; `review_environment.json` records the additional launch.
- Original producer SHA256: `de282436dc55eaf7f8b577d9546591339d1510918e56db0125bfeb7ba1672c56`; its byte-exact source is `producer_before_juror.py`. Review producer SHA256: `4b277db44efd8d01592cc329f074f470e542f7d901cb81dea9b49759fc717e9f`.
- Base-stage cache configuration hashes remain historical. The successful N=16 SPICE retry has its own final conditions, prior timeout conditions and complete `spice_provenance`; review analyses have separate complete provenance. No old stage is relabeled as a fresh run of new source.
- The recorded reader checks both source identities, every unchanged base dependency, PDK inputs, the original producer snapshot, and 135 evidence hashes. It needs no recording-host binaries or ignored raw work directory. Plots run afresh from verified numbers.

## Validation / how to run

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B examples/dot_scaling.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q -p no:cacheprovider \
  --basetemp=results/dot_scaling/work/pytest_final \
  tests/test_dot_scaling.py tests/test_scale_views.py
PYTHONDONTWRITEBYTECODE=1 python3 -B notebook/scale_views.py
```

**33 tests passed** (1.78 s). They cover arithmetic/oracle/range and equivalence mode, both carry witnesses, fixed-weight STA equivalence, unavailable/unsettled timing handling, source/evidence integrity, identical wire C in STA/SPICE, actual level/settling values, per-cell/source-sign power arithmetic, time integration, no-tool recorded reads, explicit recompute, Japanese tables and plotting units/missing data. Seven views were rendered with headless Chrome; final PNG visual inspection is recorded below.

Final visual inspection completed for all seven PNGs: four-size data and all eleven output rows are present; Japanese fonts, units, three table rules, legends, 1.25 µs hold, time-average power and wire-C ablation labels render correctly. No clipped columns, overlapping labels or substituted missing timing points were found. Previews are 1800 px wide (headless Chrome, 1.5× scale); figures are standalone HTML as well.

## In progress / blockers / interface requests

- Required implementation and numerical work: none remaining.
- Blockers: none. N=32 is a disclosed optional routing limit, not a qualified result.
- Interface requests: none. V3 can use the existing APIs above; `layout_penalty_table` is the added review view.
- No commits or pushes; other streams' files were not edited.
