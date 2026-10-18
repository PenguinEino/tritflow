# PNR stream — pinned PDK / phase 6

Only qualification against public PDK **5d963db9d44e192d37a0489c208bfccf2e2f690c**
at `~/pdk/TR-1um-pinned` is current. Native KLayout is 0.30.9; Python API is
0.30.6. Earlier dev-PDK results below are historical, not current qualification.

## In progress

Waiting for CELLS Phase 7 atomic publication before the final complete rerun.
Provisional pinned-deck campaigns already pass all 100 deterministic random
circuits, the four examples, and adders 1–6/8. The pinned strict-port mismatch
was resolved by SIM's label-only normalization using synthesis annotations;
PNR's isolated-input restoration now decodes/restores the same mapping, including
bracketed unused input names. No physical label is invented and no PDK rule or
strict-port setting is weakened.

The optional **`tritflow.pnr.chip(result, ...)` / `PnrResult.to_chip()`** builds
separate `build/<design>/chip/` artifacts. Provisional adder4 and full_add both
have **zero drawing DRC, strict LVS Match, MDP, zero mask DRC, and passing MPW
precheck**. Original macro GDS/PNR JSON are unchanged. The copied pinned
`OSS_FRAME_TEG` retains its exact seal ring and prohibited regions; its stock
pad bank is replaced by peripheral **real `OSS_PAD_TEG` masters**. Pins align
with macro ports to avoid detours. Adder4 has 23 pads (four each for VDD/VSS,
one VMID, fourteen signals); full_add has eight. All same-domain supply pads
must be bonded/probed. VMID has a separate bottom terminal; substrate/common
VSS remains −5 V. No 5 V two-rail ESD network is silently attached to the
accepted +5/0/−5 V domains.

Generator-side fixes found by full-chip verification: preserve the copied
63/1 prohibited side strips; honor 64 µm pad-opening separation; add real
40 µm × 14 µm lead-outs; keep ordinary TC outside pad enclosure regions;
apply 14 µm pad-to-metal spacing even to disjoint metal of the same net;
avoid large-pad centerline artifacts with distributed pad taps; use multiple
supply pads and 2.9 µm-pitch TC arrays to retain the DC reserve. No cell-internal
mask defect has been found. All native report items count, including warnings;
there are no waiver polygons or marker tricks.

Sizing reserves **20%** of OS00 p17 Tables I-3-1/I-3-3: stepped M1 500 µA/2 µm,
field M2 3.7 mA/3 µm, TC 780 µA/cut. Width scaling is an engineering
interpretation, not foundry lifetime EM signoff. Every real PNR result is
independently solved using SIM's characterized per-rail envelope and resistor
network. If any solved branch misses the reserve, row capacity tightens and
PNR reruns before publishing. The original `power` schema is retained; new
`assumptions` fields and `dc_current_check` are additive. SIM continues reading
`build/<design>/<top>.pnr.json`; chip metadata is a separate `.chip.json`.
Provisional chip worst utilizations: adder4 **79.01%** (M1), full_add **63.99%**.

The N=7 routing stress case exposed poor floorplan/seed combinations. A measured
passing run uses seed 19, `anneal_steps=3000`, `channel_tracks=16`, reaching
18 tracks automatically; 65.47 s with concurrent jobs, 2904 × 2634 µm. The
scale producer records these explicit options. For macros above 100 cells,
default adaptive routing now skips the two predictably undersized channel
trials while retaining their placement and seed offsets. N=6 remains below
60 s in the provisional pinned runs (26.96 s, including strict LVS).

## Real shuttle submission work

This wrapper requires a **full centered 2500 × 2500 µm allocation**; the prior
balanced-ternary macro's 1800 × 1000 µm shared slot cannot hold adder4. Obtain
organizer approval for the custom TEG pad map and allocation, complete the bond
map/package/probe plan (including every supply pad), agree VSS/common substrate
and die attach, and obtain the process/ESD decision for the accepted rail
span. Passive TEG pads provide no ESD network. Simulate package/probe loading
and supply impedance; the DC envelope does not qualify current crowding,
transients, temperature/lifetime derating or pad/bond reliability. Complete the
shuttle `info.yaml`, schematic/reference, licence and project metadata and run
its final CI on the final frozen revision. The code does not upload or submit.
The inspected MPW flow defines drawing LVS before MDP and no post-MDP LVS;
`mask_lvs` is explicitly undefined, not reported as a pass.

## Interface requests

- CELLS: publish the Phase 7 pinned generation journal; PNR will then rerun all
  final examples, fuzz/scaling, and full-chip evidence automatically.
- FRONTEND: optional notebook delegate `Layout.to_chip(**opts)` can forward to
  `self.result.to_chip(**opts)` and show `chip.report`, its pad map and GDS PNG.
  `ChipResult.signoff()` caches verified artifacts; `submission_ready` remains
  false until the external allocation/package/ESD approvals described above.
- SIM: encoded-port handoff is adopted. Power JSON keys are stable with the
  additive current-reserve fields above; no chip operation changes macro JSON.

Development tooling installed with the permitted user-pip flags: Black (and
its pip dependencies), used only to format PNR-owned new code; no runtime
package dependency or reference tree was changed.

# PNR stream — phase 5

## Done

The four shared designs are routed with the **132 µm compact cell library**.
All canonical GDS, PNR JSON, official DRC reports, strict LVS reports/extracted
SPICE, seed comparisons and notebook views are under `build/<design>/`.
The generated result/seed tables below are refreshed by `examples/pnr_all.py`.
Phase-1 `/tmp` artifacts are superseded by these project-local results.

- API and CLI: seeded placement, HPWL annealing/history, M1 horizontal channel
  routing, M2 vertical routing, rip-up/reordering, adaptive horizontal channels
  and vertical signal corridors, hierarchical GDS and geometric self-checks.
- Compact cells: retain `free_M2_tracks` metadata, honor actual M2/V1 obstruction
  rectangles and certified free columns, reflect all constraints with MY, and
  select an unobstructed advertised signal-pin access. No implicit assumption
  that cell interiors are M2-free remains.
- Four physical builds compared at **seeds 0, 7, 19**, **600 annealing steps**.
  Every seed is routed and checked by the unmodified PDK drawing-layer DRC and
  strict device-level LVS through the SIM stream's existing extraction API.
- `examples/pnr_all.py` detects changed cell publications, restarts a run when
  inputs change mid-build, and reuses results only when both input hashes and
  checked output hashes agree. Deleted/edited GDS or reports trigger rebuilding.
- `tritflow.viz.layout` provides the KLayout raster with embedded layer legend,
  Plotly net/instance selection, placement + HPWL animation, and routing replay.
  Figures are normal notebook-ready Plotly Figures; exported HTML embeds Plotly.

## Phase 5 — manufacturing qualification

The real local MPW flow was read from
`~/TR-1um_MPW_Sanken/.github/workflows/check.yml`,
`~/TR-1um_MPW_Sanken/scripts/pre_check.py`, and the user's previous
`~/balanced-ternary-logic/scripts/verify_half_adder_layout.py` /
`verify_full_adder_layout.py`. It runs drawing DRC, drawing LVS, MDP via
`run_mdp.drc`, then `run_IP62.drc`. The PDK's Python MDP wrapper and prior
submission pass `cellname` to the MDP deck; the template passes `top_cell`,
which that particular deck does not read. Both current PNR GDSs have one top;
our call explicitly uses the supported `cellname` argument.

Final actual results: adder4 46 and full_add 16 `WAR06: Floating SG Detected`
mask items, all traced through actual mask SG/CO/M1/V1/M2 to their external
input nets. No other mask violation class appears. These are counted as
failures. Drawing DRC and strict drawing LVS remain clean. The previous full
adder's `FULL_ADDER_POST_LAYOUT.md` records the same 16 external-input warnings.
The full-chip precheck rejects these unframed core macros: their boundaries
are not [-1250,-1250,1250,1250] µm and no OSS_FRAME/OSS_FRAME_TEG exists.
Qualification result: **FAIL for both standalone macros**. Actual checks,
provenance, diagnostics and the cached API are complete. Remaining manufacturing
blockers are full-chip frame and real input-I/O/protection integration. No PNR
metal-generation defect or cell-internal process-rule defect was found. The
phase-3 choice to keep the canonical outputs as compact core macros is retained;
a framed submission is a separate full-chip artifact requiring its I/O mapping.
No reference files or PDK rules were modified.

### Measured results and retained evidence

Native KLayout is **0.30.9**, matching the inspected MPW workflow; Python
`klayout.db` is **0.30.6**. The local PDK directory has no `.git` metadata;
each report therefore retains SHA-256 of every consumed deck/include, native
binary, GDS, cell reference/abstract and implementation file, plus byte copies
of the DRC/LVS rule trees. The inspected MPW template checkout is
`b3dab389ddaac1056c93bf5704230c6d2f52d5b2`.

| Design | Drawing DRC | Strict drawing LVS | MDP | Mask IP62 DRC | MPW precheck | Macro clean / submission ready | Native run / cached call |
|---|---:|---|---|---|---|---|---:|
| adder4 | 0 | Match | Generated | 46 × WAR06 | Failed die/frame | false / false | 7.81 s / 15.5 ms |
| full_add | 0 | Match | Generated | 16 × WAR06 | Failed die/frame | false / false | 4.94 s / 12.0 ms |

Every warning is unwaived and unvisited in the actual native reports. The API
also counts already visited items as failures, so opening/marking a report
cannot manufacture a pass. Layer 63/0 waiver polygon count is zero in drawing
and mask outputs. Independent flattened Region XOR proves **CO, M1, V1 and M2
are identical before and after MDP** for both designs (all XOR areas zero).

| Violation / precheck class | adder4 | full_add | Cause / ownership |
|---|---:|---:|---|
| `WAR06: Floating SG Detected` | 46 | 16 | Exposed primary-input gates lack an attached junction/pad path at standalone-core scope; full-chip I/O integration |
| Other mask DRC classes | 0 | 0 | No routing geometry or cell-internal process violations observed |
| Fixed MPW die boundary | 1740 × 1590 at (0,0) | 792 × 702 at (0,0) | Template requires centered 2500 × 2500 µm |
| Required frame cell | absent | absent | `OSS_FRAME` or `OSS_FRAME_TEG` must be present in a full-chip submission |

Gate-to-port counts from actual mask connectivity: adder4 has 4 warnings on
each `a[0..3]`, 6 on each `b[0..3]`, and 6 on `cin`; full_add has `a:4`,
`b:6`, `cin:6`. No marker is attributed to an internal/unmapped net. Labels
alone satisfy the drawing deck’s top-port handling; the IP62 antenna check
uses physical junction/pad connectivity. Exact marker boxes and net names
are in `floating_gate_attribution` in each sign-off JSON.

**Separate fixed-bias diagnostic:**
`build/full_add/signoff/input_bias_diagnostic/summary.json` records drawing
DRC **0**, strict device LVS **Match**, and mask DRC **0**. Its parent ties
all three DUT inputs to the existing VDD feed, reproducing the earlier
submission’s diagnostic method. The original functional GDS is unchanged.
This fixed-input fixture establishes the source of WAR06; functional macro
qualification retains its 16 warnings until real I/O integration.

**Mask-level LVS:** neither the actual MPW workflow nor the prior submission
check script defines a post-MDP LVS stage. The available legacy
`libs.tech/klayout/tech/lvs/IP62/run.lvs` was additionally probed on a copied
full_add mask: it exits **1 before extraction**, because its relative include
points to missing `lvs/drc/00_Layers.drc`. It has no modern headless I/O
parameter setup. No deck was repaired or substituted to claim mask LVS.
Probe command/log: `build/full_add/signoff/legacy_mask_lvs_probe/probe.json`
and `probe.log`. `mask_lvs.matched` is null; it is explicitly not a pass.

Canonical summaries:

- `build/adder4/signoff/signoff.summary.json`.
- `build/full_add/signoff/signoff.summary.json`.

Each summary points to `signoff/runs/<fingerprint>/`: input drawing snapshot,
mask GDS, both complete DRC databases/logs, strict drawing LVS database and
extracted/reference SPICE, MPW precheck log and copied unmodified rules. The
initial raw MDP/IP62 discovery is retained in `signoff/discovery/`.

### Public API and verification

```python
from tritflow.pnr import place_and_route

lay = place_and_route("build/full_add/full_add.json", output_dir="build/full_add")
checks = lay.signoff(mpw_template="/home/ishi-kai/TR-1um_MPW_Sanken")
print(checks["clean"], checks["submission_ready"], checks["mask_drc"]["categories"])
# A second identical call reuses the hashed result; force=True reruns checks.
```

`mpw_template` is optional: without one, macro qualification still runs, and
`submission_ready` remains false because full-chip precheck was not proven.
`PnrResult` retains its gate reference for immediate calls; reopening a saved
result uses adjacent `<top>.json`, or accepts `netlist=...` explicitly.
Other options: `output_dir`, `library`, `pdk_root`, `klayout_binary`, `timeout`
and `force`. Missing mask output, tool failure and timeout raise with a log
path. Physical-check failures return an explicit false result with all native
evidence, consistent with the existing DRC/LVS report APIs. Canonical drawing
GDS, PNR JSON and its power section are never rewritten by sign-off.

Tests exercise actual INV mask warnings and net attribution, result reuse
without invoking a native tool, invalidation after GDS/rule/reference/report
changes, a missing MDP output despite exit 0, visited-warning rejection, mock
library rejection and a clear missing-reference error. Final combined run: **36 passed in 67.67 s**. `compileall` and owned-path
`git diff --check` pass. Repeated canonical sign-off calls confirmed cache
reuse, unchanged input/output hashes and all native warning items still
unvisited. No background PNR processes remain.

**Interface requests for FRONTEND/integrator:** the owned public
`PnrResult.signoff()` and `tritflow.pnr.signoff(result, ...)` are implemented.
To expose the requested method on FRONTEND's `tritflow.flow.Layout` wrapper,
add this delegate in that owned file (PNR does not edit it):

```python
def signoff(self, *, output_dir=None, **kwargs):
    from tritflow.pnr import Library
    return self.result.signoff(
        netlist=self.netlist, library=Library.load(self.settings.cells),
        output_dir=output_dir,
        **{"pdk_root": self.settings.pdk,
           "klayout_binary": self.settings.klayout, **kwargs})
```

The helper caches on disk, including failed physical-check results, only while
all consumed inputs and every generated report/GDS/rule snapshot hash agree.
Report fields are `clean` (macro qualification) and `submission_ready`
(additionally requires a successful supplied MPW-template precheck). Both
are false for the current macros. No successful mask-LVS result is claimed:
the inspected workflow does not define that step.

**Interface requests for CELLS:** none from current evidence. Every floating
SG marker is electrically attributed to an external input; none is an
unmapped internal cell gate. Frame/real I/O integration must preserve the
three supply domains and resolve those exposed-input connections before a
full-chip re-run. Current PNR outputs and power JSON are unchanged.

## Phase 4 — robustness

`examples/fuzz_pnr.py` generates deterministic reader-style TritVerilog, runs
the public HDL/synthesis APIs (including source-to-gate equivalence), then
real-cell placement/routing, flattened-GDS connectivity, own metal DRC,
unmodified PDK DRC and strict device LVS. Corrected 100-design campaigns pass;
the final frozen-input campaign and scale table are recorded below. All
output stays under `build/`. No packages were installed.

Reproduce from the checkout:

```
python3 examples/fuzz_pnr.py --count 100 --scale --jobs 2
python3 examples/fuzz_pnr.py --count 100 --scale --jobs 2 --resume
python3 examples/fuzz_pnr.py --seeds 74 79 --jobs 1
python3 examples/fuzz_pnr.py --count 0 --scale --output-root build/pnr_scale
```

Seeds 0–99 vary 2–12 input trits, 1–19 authored logic levels, widths 1–6,
outputs 1–6, reconvergent paths, shared inputs, all min/max/nany/neg operators,
all three constants, output aliases, entirely constant outputs and fanout
limits 2/3/4/8. Every fifth case retains six output branches for larger live
DAGs. Synthesis equivalence is exhaustive for these input sizes. The actual
mapped circuit sizes and coverage are in the final result table below.

Each source has its own directory `build/pnr_fuzz/fuzz_<seed>/`, with `.tv`,
synthesis JSON/gate source/SPICE/equivalence report, canonical GDS/PNR JSON,
PDK DRC database/log, strict LVS database/extracted/reference SPICE, worker log
and `fuzz.result.json`. `summary.json` tracks progress and sets
`inputs_stable=true` only after the final library/tool hash agrees. A changed
publication fails certification; rerun after it settles. Resume requires both
matching source/tool/library hashes and unchanged GDS/JSON/DRC/LVS artifact
hashes. Changing annealing effort invalidates reuse. Each worker is a separate
process with a timeout; its entire process group is reaped on exit/timeout.
There is no daemon or watcher.

### Failure classes and fixes

1. **Unloaded boundary inputs disappear from device extraction.** The original
   discovery pass completed 100 designs with 55 strict-LVS rejections of this
   class; it was a diagnostic run during implementation, not a fixed-version
   success-rate benchmark. Pads existed and DRC/connectivity were clean, but
   the PDK removes standalone metal nets and the strict top-port comparison
   reported missing inputs. In one minimal alias/TIEZ case, those unused
   formals also made the native comparator mispair supplies. Original failing
   sources and metadata are preserved as `first_failure.tv/.json`; the initial
   run is `build/pnr_fuzz/discovery.summary.json`.

   **Fix:** new public `tritflow.pnr.strict_lvs` independently proves each
   unloaded input from the drawn GDS: exactly its M2 pad island, no V1,
   the correct actual top-level TXM2 label, and clean drawn connectivity.
   Only those empty formals are removed from the device reference before
   invoking the unmodified strict PDK comparator. Every device and loaded
   port must match. Proven formals are restored in extracted SPICE and the
   complete physical port set is checked again. The full-port reference and
   pre-restoration extracted file remain beside the native report. A missing
   or mislabeled loaded/unloaded pad cannot be excused by this procedure.
   Regression tests cover the minimal TIEZ/NOR/aliased-BUF circuit and deletion
   of an actual unused-pad label while leaving its JSON unchanged.

2. **A failed verification could leave a newly written canonical GDS.** This
   was identified while exercising failure UX, rather than as a random DRC
   defect. **Fix:** export to `<top>.candidate.gds`; publish `<top>.gds` and
   canonical PNR JSON only after all requested geometry/PDK checks pass.
   Failures raise `PhysicalVerificationError`, move geometry to
   `<top>.failed.gds`, and write `<top>.pnr.failure.json`. An earlier successful
   canonical GDS/JSON remains intact; its failure marker makes the new failed
   attempt explicit. Tests inject both an unenclosed V1 (own check) and a tiny
   N-well (actual PDK device DRC), verify exceptions, and compare the old good
   artifacts byte for byte. No failed GDS is returned as a `PnrResult`.

3. **Routing exhaustion gave a generic maze error.** **Fix:** `RoutingFailure`
   carries `failed_nets`, `region_um`, `blocking_nets` and a readable message.
   A failed connection window is reported with x/y bounds in µm and nearby
   occupied nets where applicable, plus `rows`/`channel_tracks` and pin-access
   guidance. Outer retries retain diagnostic fields and write all attempts to
   `<top>.pnr.failure.json`. A real, intentionally enclosed M2 pin pocket is
   tested without a mocked router. Reproducer evidence lives under
   `build/pnr_failure_demo/`; it emits no GDS:

   > Routing failed for nets z: no legal maze path; exhausted 1 floorplan
   > attempts. Congested connection region: x=63..156 µm, y=3..111 µm.
   > Try more rows (rows=...) or channel tracks (channel_tracks=...);
   > check cell pin-access obstructions.

No random-case metal-connectivity or PDK DRC defect remains in the verified
corpus. This is measured fuzz coverage, not an assertion that all possible
reader circuits will route. Exhausted routing and invalid layouts fail loudly.
The power section and its geometry/current schema are unchanged from phase 3.

### Scale methodology

Scale runs synthesize adders at N=6/8 using the actual HA/FA source. `mul2`
is a functioning two-trit multiplier: four one-trit multipliers and two full
adders combine the four partial products into four output trits. A regression
checks its arithmetic against integer multiplication for all 81 input vectors;
its synthesis equivalence checks all 81 vectors as well. Generated standalone
HDL and all physical/verification outputs are under
`build/adder6/`, `build/adder8/`, `build/mul2/`.

Wall time is measured separately for synthesis, PNR (including GDS, connectivity,
own DRC and official PDK DRC), and LVS. Peak memory is sampled every 100 ms as
the sum of worker/descendant RSS from `/proc`, in MiB. It includes Python and
the live KLayout subprocess; shared pages can be counted twice. It excludes
the small parent monitor and other concurrent workers. It is sampled process-
tree RSS, rather than a claim of exact physical RAM or PSS. Timings are on this
machine under concurrent stream/test load. No figures are included in fuzz
run time; all native physical verification is included.

### Final phase-4 evidence

**103/103 passed:** 100 random HDL designs plus adder6, adder8 and mul2. The final frozen-input campaign took **173.18 s** with two bounded workers. All sources and checked output hashes were independently revalidated after the run; native LVS circuit statuses are Match for every case.

Tool/library content fingerprint: `518d49bef7f8b4b1127ff7b0e5b0bb0c4b0e5d2c8182e51a54629f7e24e50fd1`. `inputs_stable=true`. Authoritative campaign: `build/pnr_fuzz/certified_campaign.summary.json`; progress/latest results: `build/pnr_fuzz/summary.json`.

The random corpus maps to **1–79 cells**, mapped depth **1–23**, and covers INV/NAND/NOR/NANY/BUF/TIEP/TIEZ/TIEN. All input counts 2–12 and fanout limits 2/3/4/8 occur. Source/gate equivalence checks a total of **7,174,422 exhaustive vectors**. Isolated-input proof is exercised in **81 designs**. There are zero outstanding synthesis, routing, connectivity, DRC or LVS failures in this corpus.

Random-design source-to-LVS time ranges **1.76–4.75 s** per design; sampled peak process-tree RSS ranges **547.3–566.4 MiB**.

| Scale design | Cells | Die (µm) | Utilization | PNR incl. DRC (s) | PNR + LVS (s) | Source → LVS (s) | Peak tree RSS (MiB) | PDK DRC / LVS |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| adder6 | 96 | 2460 × 1782 | 43.14% | 7.93 | 9.06 | 9.18 | 576.9 | 0 / Match |
| adder8 | 128 | 2796 × 2454 | 36.75% | 40.01 | 41.07 | 41.17 | 601.4 | 0 / Match |
| mul2 | 49 | 1680 × 1206 | 45.66% | 2.97 | 4.03 | 4.06 | 556.9 | 0 / Match |

| Scale design | Rows / spans | Tracks/channel | M1 / M2 signal length (µm) | Signal / power vias | HPWL before → after (µm) |
|---|---:|---:|---:|---:|---:|
| adder6 | 9 / 3 | 8 | 80898 / 79964.5 | 887 / 1944 | 153658 → 98407.5 |
| adder8 | 11 / 3 | 12 | 172416 / 133689 | 1279 / 3168 | 231814 → 172083 |
| mul2 | 6 / 2 | 8 | 29754 / 25475 | 383 / 600 | 54009.5 → 32969.5 |

N=6 is well within the requested ~60 s. N=8 takes longer because its maze
router exhausts eight-/ten-track attempts before succeeding with twelve
tracks and two side bypass columns; those failed attempts are retained in
its PNR JSON. All scale runs use default 600-step placement effort and seed 7.

The final combined PNR/owned-layout-view regression run is **32 passed in
38.77 s**. It includes actual PDK device-DRC rejection, geometric fault
injection, isolated-pad label deletion, genuine blocked routing, multiplier
arithmetic, prior compact-cell constraints and the 200-instance mock DAG.
The four original canonical designs and all twelve seed candidates were also
rebuilt under phase 4 and remain clean; their refreshed tables appear below.
PNR implementation/verification is complete, with no PNR blockers. The notebook
wrapper hookup below is an interface handoff under the ownership rules.
No PNR watcher or background worker remains running.

**Interface request for FRONTEND/integrator (files only):** notebook
`tritflow.flow.Layout.lvs()` still calls raw `tritflow.extract.extract_layout`.
To carry the unused-input correction into chapter 8, call the newly public
`tritflow.pnr.strict_lvs` instead, preserving existing report caching:

```python
from tritflow.pnr import Library, strict_lvs
report = strict_lvs(self.gds_path, self.data, self.netlist,
                    Library.load(self.settings.cells),
                    output_dir or self.gds_path.parent / "lvs",
                    (self.settings.cells / "out/all.spice").read_text(),
                    **{"pdk": self.settings.pdk,
                       "executable": self.settings.klayout, **kwargs})
```

This helper proves every unloaded input is an actual isolated, labeled M2
pad with no V1 before excluding that empty formal from device comparison;
all active devices and loaded ports still undergo the unmodified strict PDK
comparison. It then restores the physically proven unused formals in the
extracted SPICE and checks the full port set. Raw extraction alone still
rejects valid unused inputs. PNR does not modify the FRONTEND/SIM owned files.

## Decisions and physical scope

**Routing constraints.** CELLS publishes `free_M2_tracks: {x, count, wire_width,
clearance}` in each abstract. The loader normalizes that to `Cell.free_tracks.M2`
and preserves the metadata in PNR JSON. Explicit M2 obstructions remain
mandatory even on a declared free column. Internal V1 cuts imply their M2
metal enclosure before spacing is applied; neither signal wire nor new landing
may occupy that metal. `free_tracks.M2` and `routing.m2_free_tracks` are also
accepted for explicit/mock libraries. An absent free-column list uses shape
constraints alone; an empty list forbids full-height over-cell transit.

M2/V1 obstruction boundaries and interior points are included in the maze's y
coordinates. This prevents compressed vertical graph edges from jumping over
an obstacle between channel or pin coordinates. Via cuts are 1.4 µm with 1 µm
metal enclosure; signal landings are 3.4 µm square. Signal M1/M2 wires use
1.8/3.0 µm widths, with conservative 3.4 µm M2 occupancy reservations.

**Compact pin escapes and MY.** NANY/NAND/NOR A and B share a column at
different y coordinates. The lower pin escapes downward, the upper upward.
Those mandatory M2 stubs and first channel landings, plus boundary-port
landings, are reserved before routing. Rows initially alternate R0/MY; annealing
also flips individual instances. This can share vertical pin-access columns
between rows while preserving supply polarity. All abstract constraints are
reflected with each cell. The selected adder contains both orientations.

**Floorplan and route capacity.** Automatic sizing enumerates physical row counts
and independently fed spans per row, including actual power-bank widths and
channel height in its area/aspect objective. It prefers aspect ≤1.5, then
minimum die area. Cell rows remain separated by horizontal routing channels.
Full_add/mac1/mul1 start with four tracks per channel; adder4 starts with eight.
Eight deterministic rip-up/reorder passes precede channel expansion by two
tracks (compact library). Only failed attempts add an extra side bypass track.
The selected four designs require no added side bypass tracks. The compact
NANY's three advertised full-height M2 tracks remain binding throughout.

**Placement.** Default effort is 600 annealing steps, seed 0. Swaps, moves and
MY flips minimize cell-terminal HPWL with a weak row-width penalty. Each
(row, span) has a hard current limit, every span has a fixed physical width,
and each span's aggregate current remains within the feed-bank envelope.
These constraints apply to the initial packing, every candidate and every
saved history frame. Cells are centered in their span on the 6 µm grid.
History HPWL is recomputed on the final routing-channel coordinates, so each
before/after pair compares identical floorplan dimensions. HPWL excludes
external ports; drawn wirelength includes their routes.

**Power / SIM compatibility.** Missing characterization uses 100 µA per logic
cell and zero intrinsic current for FILL/TIE. SIM's `max_static_current_a` and
`dc[*].rail_current_a` override defaults. The conservative 0.00025 A/µm width
scaling and immutable 4 µm lower cell rails previously limited adder4 to four
cells per row and forced sixteen rows. Internal vertical M2 banks now subdivide
long rows into independently fed spans. Adder4 uses eight physical rows with
two spans each and three banks (left/internal/right); the other designs need
only the two end banks. Each span still has the same two-ended current limit.
Internal banks are sized for half the aggregate load of each adjacent span;
an outer bank supplies half of its single neighboring span. The maximum
initial span load is reserved throughout annealing, so bank sizing stays valid.
Parallel unslotted trunks remain ≤42 µm. A 6.4 µm minimum trunk fits two V1
cuts at each 4 µm rail crossing; via arrays use the available rail/trunk widths.

SIM continues reading `build/<design>/<top>.pnr.json`. The `power.straps`,
`power.rails`, `power.vias`, `power.pins`, current maps, assumptions and
`ir_drop` records preserve their existing fields and units. Geometry lists
remain the authority for IR extraction. Additions are `feed_banks`,
`span_width`, `span_gap`, `span_current_limit_a`, and each strap's `bank` index;
`side` additionally accepts `internal`. Legacy trunk/stride fields describe
the outer banks only; internal banks can contain more parallel trunks.
Placements/history additionally carry `span`; `row` still means physical row.
No SIM source files or processes were changed. A file-based compatibility
check with SIM's existing `estimate_ir_drop` is retained separately as
`<design>.pnr.ir_compatibility.json`.

The PDK's local `openIP62/IP62/Technology/doc/OS00_リファレンスマニュアル_rev1.1.pdf`,
I.3.1/I.3.2, specifies M1(2 µm) 900 µA flat / 500 µA stepped, M2(3 µm) 3.7 mA,
and V1 780 µA/cut. Default `current_density_a_per_um=0.00025` uses the lower
stepped-M1 value with **assumed linear width scaling** for both metals; this is
not EM sign-off. Two-ended load sharing is a sizing approximation. PNR's IR
estimate assumes 0.05 Ω/square, groups parallel trunks at their mean x, and
omits via/package resistance. Divider zero shift uses equal pull-up/down
conductance for INV/NAND/NOR/BUF; NANY reports its VMID envelope. SIM's separate
geometry-based solver includes every drawn via and its assumed resistance.

**Verification.** Connectivity unions flattened drawn M1/V1/M2 islands and
checks every expected signal/power terminal and route. Direct-metal mock TIE
aliases are intentional; real RR ties retain separate metal nodes across their
resistor. Own routing DRC checks widths, spacing, wide-M1 spacing, fixed V1 cuts
and enclosure. The complete PDK deck runs without waived regions, disabled
warnings or skipped antenna rules; external TXM1/TXM2 labels are at the top
hierarchy because the deck reads top-cell labels for external gates. Official
report item counts, not process exit codes alone, determine DRC pass/fail.
An independent per-layer Region XOR of every used cell master in the archived
phase-2 and canonical phase-3 GDSs is empty for all four designs; area gains
come from the floorplan/routing changes with identical cell geometry.

Strict LVS compares the GDS against the GateNetlist plus `cells/out/all.spice`.
It establishes device/interconnect connectivity, not post-layout timing or
exhaustive transistor-level arithmetic correctness. Those remain SIM's scope.

## Reproduction and automatic updates

```
python3 examples/build_all.py
python3 examples/pnr_all.py
python3 examples/pnr_all.py --watch
```

The default designs are `adder4 full_add mac1 mul1`; default seeds are `0 7 19`.
Use `--force` to rebuild unchanged inputs, `--seeds ...`, `--anneal-steps ...`,
`--designs ...`, `--build-root ...`, or `--no-views` as needed. A missing shared
netlist invokes FRONTEND's build script. No git-state changes are performed.

The runner hashes the template, root publication/qualification files, every
published cell directory (including GDS/abstract/characterization/SPICE), the
four netlists and PNR/visualization/extraction entrypoint code. CELLS' independent
comparison scratch trees do not define a new cell publication; their final
root report does invalidate the cache. Watch mode polls every five seconds,
debounces changes, and reloads a changed publication. Every active build also
compares before/after fingerprints and restarts all designs if they differ.
Canonical results and seed evidence are hashed; missing/altered artifacts never
count as a cached pass. The actual batch observed publication changes and
restarted all four designs; the final run completed on a stable publication. The runner refreshes only the result-table block in this
status file for full canonical project builds. Custom/test builds leave it alone.

No watcher is running. `--watch` is an opt-in foreground script the integrator
can start and interrupt; a normal run exits after verification. Restart a watcher
after PNR Python implementation changes; cell/template/characterization
publications reload without restarting it. No watcher PID file is retained.

Each `build/<design>/` contains:

- `<design>.gds`, `.pnr.json`, `.pnr.summary.json`, `.seed_comparison.json`.
- `<design>.drc.lyrdb`, `.drc.log`, `.lvs.summary.json`; `lvs/` contains strict
  LVS databases, extracted SPICE, reference SPICE and the unmodified deck log.
- `pnr_seeds/seed{0,7,19}/` retains each candidate's physical and LVS evidence.
- `<design>.layout.png` and `.layout.html`, `.placement.html`, `.routing.html`.

## Public floorplan / placement controls

`place_and_route(..., rows=None, anneal_steps=600)` exposes the two notebook
controls. `rows=None` automatically sizes a near-square die; a positive integer
fixes its physical row count and adapts its power spans. `anneal_steps=0` keeps
initial placement, 600 is the fast default, and 2400 gives more optimization.
The CLI also accepts `--rows K --anneal-steps N`. Fixed rows can reduce
utilization; the API honors that explicit choice.

```python
from tritflow.pnr import place_and_route
from tritflow.viz.layout import placement_animation

r = place_and_route("build/adder4/adder4.json",
                    output_dir="build/adder4/notebook_rows10_steps2400",
                    rows=10, anneal_steps=2400, seed=7)
print(r.stats["die_size_um"], r.stats["utilization"], r.stats["runtime_s"])
placement_animation(r).show()
```

Controlled adder4 measurements (seed 7, same cells/netlist, every candidate
PDK-DRC clean and strict-LVS matched):

| Rows requested | Steps | Actual rows / spans | Die (µm) | Utilization | HPWL before → after (µm) | Signal length (µm) | PNR / +LVS (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Auto | 0 | 8 / 2 | 1752 × 1698 | 42.38% | 76903.5 → 76903.5 | 116083 | 8.70 / 9.61 |
| Auto | 600 | 8 / 2 | 1740 × 1590 | 45.57% | 74515.5 → 47968.5 | 79949 | 3.20 / 4.04 |
| Auto | 2400 | 8 / 2 | 1740 × 1590 | 45.57% | 74515.5 → 31296 | 65938 | 3.35 / 4.21 |
| 10 | 600 | 10 / 2 | 1518 × 1974 | 42.08% | 94653 → 52837.5 | 87766 | 3.70 / 4.67 |

Raw records and DRC/LVS evidence: `build/adder4/floorplan_comparison.json` and
`build/adder4/floorplan_comparison/`. Zero effort needed two more channel tracks;
its HPWL therefore uses those wider final channel coordinates for both frames.
All tested adder4 API runs finish below 10 s including strict LVS. Canonical
PNR timings below include library discovery, placement, routing, GDS export,
geometry checks and the PDK DRC. `+LVS` adds extraction/comparison; view rendering
is separate in each summary JSON. No phase-2 runtime was archived, so the
comparison makes no phase-2 speedup claim.

Canonical PNR + strict LVS + all four exported notebook views took adder4 5.68 s, full_add 2.28 s, mac1 2.65 s, mul1 1.89 s.
Timings are wall-clock measurements on this machine; concurrent stream/test
activity affects them. The slowest adder4 seed in the final batch is 4.87 s including LVS.

SIM compatibility checks on the canonical JSONs completed with every cell
connected to all three supply pads. Maximum rail deviations from SIM's
geometry-based solver are adder4 13.54 mV, full_add 7.27 mV, mac1 9.86 mV,
mul1 2.17 mV under its independent per-rail worst-current envelope.

## Notebook figures

```python
import json
from IPython.display import Image, display
from tritflow.viz.layout import (
    render_gds, layout_figure, placement_animation, routing_progress)

record = "build/adder4/adder4.pnr.json"
data = json.load(open(record))
display(Image(filename=str(render_gds("build/adder4/adder4.gds"))))
layout_figure(record, highlight_net="sum[0]",
              highlight_instance=data["placements"][0]["inst"],
              show_power=True).show()
placement_animation(record).show()
routing_progress(record).show()
```

The raster uses `klayout.lay.LayoutView` with the actual GDS hierarchy, correct
PDK drawing layers, hollow boundaries/well outlines, and an embedded legend.
It requires no display server and never modifies the GDS. The vector view has
working HTML net and instance dropdowns; instance hover shows cell type, source
hierarchy, orientation and physical dimensions. Wire thickness in this view is
schematic in pixels; use the GDS raster/JSON for physical metal widths.

Placement frames replay the actual saved positions with a linked HPWL cursor.
Routing frames replay the recorded order of the **successful routing pass**;
failed/ripped-up passes and widening attempts are retained in `routing_attempts`
instead of being presented as final-route geometry. Signal and supply routes
are separately identified in the record. `save_layout_views(result)` exports
all four artifacts beside a `PnrResult` in one call.

## Tests and dependencies

```
python3 -m pytest tests/pnr tests/viz/test_layout.py -q
python3 -m compileall -q tritflow/pnr tritflow/viz/layout.py examples/pnr_all.py
```

Phase-3 combined run: **27 passed in 60.16 s**. Final phase-4 combined run:
**32 passed in 38.77 s**. This includes the original
synthetic suite and real four-trit adder, actual obstructed/mirrored mock GDS
through the full PDK deck, V1-implied metal, free-column metadata, alternative
pin access, portable raster/HTML, net/hierarchy selection, linked animation
frames, content changes with preserved mtimes, mid-build publication restart,
cache reuse, rebuilding a deleted checked GDS, and current/width/feed-envelope compliance of
every saved placement snapshot, plus the public row/annealing controls. A subsequent unchanged-input batch invocation
returned immediately with all checked artifacts current. `git diff --check`
and `compileall` on owned paths pass. The final actual GDS PNGs were visually
inspected, including the compact adder and mixed NAND/NOR/INV multiplier.

Extra packages installed: **none**. Uses existing klayout.db/lay 0.30.6, Plotly,
Pillow, numpy, matplotlib, the KLayout executable and the local PDK.

## Interface requests / ownership

No shared-contract changes requested. PNR JSON adds dimensions/hierarchy,
`routing_order`, `routing_progress`, corridor counts, library metadata and HPWL
statistics while preserving contracted placements/wires/vias/pins/power/history.
Own changes are confined to PNR paths, the explicitly assigned visualization
and test files, `examples/pnr_all.py`, and generated `build/` outputs.

<!-- PNR_RESULTS_BEGIN -->
## Current verified build results

Published template height: **132 µm**. Input content fingerprint: `b02fc563be6ad53bcd9ec00f0f0368822353c7c8ca646d6d88455c803c72eb8d`.

All outputs and reports are under `build/<design>/`. Utilization is placed cell area / die area; wirelength and signal via counts exclude the separately reported power geometry.

| Design | Seed | Die (µm) | Aspect | Utilization | M1 (µm) | M2 (µm) | Signal / power vias | PDK DRC | Strict LVS | PNR / +LVS (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| adder4 | 7 | 1692 × 1590 | 1.064 | 46.87% | 47274 | 43333 | 551 / 800 | 0 violations | Match | 6.08 / 7.23 |
| full_add | 19 | 876 × 702 | 1.248 | 51.26% | 6300 | 6200.5 | 125 / 240 | 0 violations | Match | 2.01 / 3.14 |
| mac1 | 0 | 876 × 1038 | 1.185 | 47.21% | 7782 | 9195.5 | 167 / 360 | 0 violations | Match | 1.79 / 2.97 |
| mul1 | 0 | 420 × 366 | 1.148 | 46.37% | 822 | 1022.5 | 25 / 80 | 0 violations | Match | 1.33 / 2.60 |

## Phase 2 → phase 3

Before artifacts are preserved in each design's `phase2/`; cell library and input netlists are unchanged.

| Design | Die before → after (µm) | Aspect before → after | Utilization before → after | Die area reduction | Signal length before → after (µm) |
|---|---:|---:|---:|---:|---:|
| adder4 | 1176 × 3534 → 1692 × 1590 | 3.005 → 1.064 | 30.34% → 46.87% | 35.27% | 91254 → 90607 |
| full_add | 924 × 942 → 876 × 702 | 1.019 → 1.248 | 36.21% → 51.26% | 29.35% | 11817.5 → 12500.5 |
| mac1 | 912 × 1374 → 876 × 1038 | 1.507 → 1.185 | 34.26% → 47.21% | 27.44% | 17899.5 → 16977.5 |
| mul1 | 612 × 510 → 420 × 366 | 1.200 → 1.148 | 22.84% → 46.37% | 50.75% | 2106.5 → 1844.5 |

## Placement seed comparison

Cell-terminal HPWL excludes external ports. Each before/after pair uses the same final floorplan. Seed selection prefers aspect ≤1.5 and utilization ≥45%, then smallest die area and drawn signal wirelength; HPWL and seed break ties. All reported runtimes are measured on this machine, include PDK DRC, and exclude seed-search overhead.

| Design | Seed | HPWL before (µm) | HPWL after (µm) | Reduction | PNR / +LVS (s) | DRC / LVS |
|---|---:|---:|---:|---:|---:|---|
| adder4 | 0 | 82552.5 | 53907 | 34.70% | 35.00 / 36.72 | clean / Match |
| adder4 | 7 | 72040.5 | 48070.5 | 33.27% | 6.90 / 8.83 | clean / Match |
| adder4 | 19 | 77296.5 | 53035.5 | 31.39% | 16.04 / 17.18 | clean / Match |
| full_add | 0 | 9135 | 5088 | 44.30% | 1.72 / 2.92 | clean / Match |
| full_add | 7 | 9831 | 5376 | 45.32% | 2.85 / 3.95 | clean / Match |
| full_add | 19 | 9135 | 4680 | 48.77% | 2.16 / 3.20 | clean / Match |
| mac1 | 0 | 16659.5 | 7353 | 55.86% | 1.89 / 3.40 | clean / Match |
| mac1 | 7 | 16659.5 | 8070.5 | 51.56% | 2.36 / 3.42 | clean / Match |
| mac1 | 19 | 18171.5 | 10235 | 43.68% | 3.29 / 4.43 | clean / Match |
| mul1 | 0 | 1420.5 | 494.5 | 65.19% | 1.36 / 2.59 | clean / Match |
| mul1 | 7 | 1420.5 | 494.5 | 65.19% | 1.24 / 2.26 | clean / Match |
| mul1 | 19 | 1420.5 | 588.5 | 58.57% | 1.21 / 2.29 | clean / Match |

Machine-readable results: `build/pnr_summary.json`, `build/pnr_manifest.json`, and each design's `.pnr.summary.json` / `.seed_comparison.json`.
<!-- PNR_RESULTS_END -->
