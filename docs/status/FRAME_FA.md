# FRAME_FA status — 2026-10-29

## Done

Built Fig. 1's existing `build/full_add/full_add.gds` in the unchanged stock
`OSS_FRAME`. Native drawing DRC, strict drawing LVS, MDP, mask DRC, copied
Sanken MPW precheck, frame/macro integrity and DC current checks all pass.
All writes are confined to `figures/full_add_chip/` and this file. No commit/push.

## Decisions

- Reuse the original 16-cell, 876 × 702 µm macro without rebuilding it.
- Keep the stock three core-VDD ANA feeders (P01/P02/P15), VMID on P13,
  common −5 V ESD/core VSS on P08, and separate +5 V ESD_VDD on P16.
- Inputs a/b/cin use P06/P05/P04 in increasing macro-pin height; outputs
  sum/cout use P11/P12. This keeps the five signal routes short and ordered.
- P03/P07/P09/P10/P14 remain independent, unbonded ANA terminals, named
  NC03/NC07/NC09/NC10/NC14. Their stock ESD devices remain connected to
  ESD_VDD/VSS; none drives the core. Include each in the strict LVS reference.
- The small macro's default VDD distribution bar does not reach the three
  fixed stock feeders. Extend its M2 bar endpoints to x = ±620 µm and the
  VMID bar's right endpoint to x = 654 µm, allowing VMID to escape on M2
  beyond the VDD feeder. The macro geometry is untouched.
  Runtime substitutions live in the local build script; library sources stay intact.
- Stock waivers and the independently measured stock-logo MDP delta follow
  the binding FRAME policy; no new exceptions are permitted.

## Pad map

| Pad | Stock pin | Net | Center (µm) |
|---|---|---|---|
| P01 | P1 | VDD | −200, 1040 |
| P02 | P2 | VDD | −600, 1040 |
| P03 | P3 | NC03 | −1040, 600 |
| P04 | P4 | cin | −1040, 200 |
| P05 | P5 | b | −1040, −200 |
| P06 | P6 | a | −1040, −600 |
| P07 | P7 | NC07 | −600, −1040 |
| P08 | VSS | VSS | −200, −1040 |
| P09 | P9 | NC09 | 200, −1040 |
| P10 | P10 | NC10 | 600, −1040 |
| P11 | P11 | sum | 1040, −600 |
| P12 | P12 | cout | 1040, −200 |
| P13 | P13 | VMID | 1040, 200 |
| P14 | P14 | NC14 | 1040, 600 |
| P15 | P15 | VDD | 600, 1040 |
| P16 | VDD | ESD_VDD | 200, 1040 |

All pads except P08/P16 are `OSS_ESD_5V_ANA`. Leave NC pads unbonded;
strict LVS checks their independent terminals and original ESD devices.
Connect all three core-VDD pads at +5 V; VMID is 0 V; common ESD/core
VSS/substrate is −5 V. Apply separate ESD_VDD (+5 V) before or together
with core VDD. No NC pad connects to a core input.

## Checks run

- PDK `5d963db9d44e192d37a0489c208bfccf2e2f690c`, from
  `~/pdk/TR-1um-pinned`; KLayout `~/bin/klayout/klayout`; ngspice
  `~/.local/opt/tritflow-ubuntu-24.04/bin/ngspice`.
- **Native drawing DRC: 0 items. Strict drawing LVS: match**, including
  `OSS_FRAME`, all ESD pad types and NC terminals. No formal ports restored.
- **Native MDP and mask DRC: pass; mask DRC 0 items.** Exactly the two
  stock 63/0 waiver polygons remain (union 63400 µm²); own count/area zero.
  Independent frame-only MDP reproduces **0.001508 µm² M2 XOR** in the logo.
  No additional XOR or overlap with our geometry. CO/M1/V1 XOR zero.
- **Original stock frame: exact match** across all geometry and transformed
  labels. **Imported full_add: exact match** by the same per-layer/text test.
  Source GDS and both source JSON files remain byte-identical. The copied
  P&R record alone has its stale `/home/ishi-kai/code-a-chip/cells` path rebased
  to this worktree; its original bytes are retained in the evidence archive.
- **Drawn-metal connectivity: pass. Sanken MPW precheck: pass (exit 0)**,
  run in a copied template under the owned output directory.
- **DC reserve: pass, minimum 41.3022%, requirement 20%.** VDD/VSS core
  envelopes are 6.670803 mA; VMID is 0.110049 nA. Per-supply reserves:
  VDD 64.8896%, VSS 41.3022%, VMID 99.8718%, ESD_VDD 99.7778%.
- **ESD DC ngspice sweep: pass** at −5/0/+5 V, 27 °C. Maximum summed
  absolute current is 0.542608 nA, covered by the 1 µA auxiliary budget.
  The existing ten non-supply ANA bias sweeps cover five signal and five
  spare pads; they do not solve an unbonded pad's floating voltage.
- Rendered and visually inspected `tr_1um_full_add.png`: centered macro,
  complete stock frame, all sixteen pad openings and short ordered signal routes.
- **P&R regression: 49 passed in 248.57 s.** Full `tests/pnr` suite, no skips
  or failures, with cache and temporary outputs under the owned directory.
- Final evidence audit passed: 86 native input hashes, 70 native artifact
  hashes, all 86 ZIP entries and the original macro-file hashes verified.
  Recounted both native DRC databases (zero items) and checked all 14 extracted
  top ports, including NC03/NC07/NC09/NC10/NC14. `verification.json` records it.
- Final build reproduces the first clean drawing **byte-for-byte**. Native
  signoff runtime is 34.13 s. GDS SHA-256:
  `d5337058a01f284d833f01329f6bc99218427a58b9eca6bde4ba0b0c030ac9a3`.
  Source full-adder GDS SHA-256:
  `3f51bddf7aaa2706b8f8fe85d6f3aa75917fbc4daac7fa291b492c1d29199241`.

## In progress

None. Complete before the 2026-10-29 17:00 JST stop time.

## Files written

Under `figures/full_add_chip/`: `build.py`, `.gitignore`, `README.md`,
`tr_1um_full_add.gds`, `tr_1um_full_add.ip62.gds`, `tr_1um_full_add.cir`,
`tr_1um_full_add.png`, `summary.json`, `native_signoff.json`, `pad_map.json`,
`evidence.zip`, `verification.json`, `build.log`, `pytest.log`, ignored `.work/`
and test scratch.
The only other written path is this status file. No packages installed.

## Reproduction

```bash
export PYTHONDONTWRITEBYTECODE=1
export TR1UM_PDK="$HOME/pdk/TR-1um-pinned"
export NGSPICE_BINARY="$HOME/.local/opt/tritflow-ubuntu-24.04/bin/ngspice"
python3 -B figures/full_add_chip/build.py --mpw-template "$HOME/TR-1um_MPW_Sanken"
python3 -B -m pytest tests/pnr -q \
  -o cache_dir=figures/full_add_chip/.pytest_cache \
  --basetemp=figures/full_add_chip/.pytest-tmp
```

## Blockers / limitations / interface requests

No physical-check blocker. Fig. 1 integration belongs to the integrator:
use `figures/full_add_chip/tr_1um_full_add.gds` with top `tr_1um_full_add`
and replace the dot4 wording. This stream did not edit the figure script.
Caption facts come from `summary.json`; a short caption may quote drawing
DRC 0 (stock waivers only) and strict ESD-inclusive LVS match.

No post-MDP LVS is defined by the inspected workflow; none is claimed.
No full-chip transient or ESD-stress simulation was run. DC limits retain
the existing envelope/width-scaling assumptions rather than lifetime EM
qualification. `submission_ready=false`: organizer slot allocation, final
bond diagram and final CI remain outside this figure artifact's scope.
