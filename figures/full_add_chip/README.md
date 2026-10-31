# Full adder in the stock OSS_FRAME

`tr_1um_full_add.gds` is the Fig. 1 full adder from
`build/full_add/full_add.gds`, centered in the unmodified 2500 × 2500 µm
`OSS_FRAME`. The macro is 876 × 702 µm, with 11 NANY and 5 INV cells.
Its original layout is imported without rebuilding or rerouting the macro.

The 16 stock pads comprise 14 ANA pads and the dedicated ESD VDD/VSS pads.
Core VDD is +5 V on P01/P02/P15; connect all three. VMID is 0 V on P13.
ESD VSS, core VSS and substrate share −5 V through P08. ESD_VDD is a
separate +5 V terminal on P16, applied before or together with core VDD.

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

Leave the five NC pads unbonded. Each remains an independent ANA terminal
with its original ESD devices; it has no core connection. Explicit NC top
ports in the schematic reference let strict LVS check these pad nodes too.
This avoids unnecessary routes and does not leave a core gate input floating.

The local runtime adapter extends the core VDD bar to the three fixed pad
feeders and the VMID bar beyond the VDD feeder to permit its M2 escape.
All other wrapper routing, frame geometry, native decks and verification
functions are reused from the dot4 stock-frame flow. No library source changes
are required. The copied P&R record's old-worktree library path is rebased
locally to this worktree's `cells/`.

## Qualification results

Pinned PDK commit: `5d963db9d44e192d37a0489c208bfccf2e2f690c`.

| Check actually run | Result |
|---|---|
| Native drawing DRC | 0 items |
| Strict drawing LVS, including ESD and all five NC terminals | Match; no restored ports |
| Native MDP | Completed; no changes to our metal |
| Native mask DRC | 0 items |
| Independent stock-frame geometry/text comparison | Exact match |
| Imported full-adder geometry/text comparison | Exact match on every layer |
| Drawn-metal connectivity | Pass |
| Copied Sanken MPW precheck | Pass, exit 0 |
| DC current reserve | Pass; minimum 41.3022%, target 20% |
| Pinned-model ESD DC sweep, −5/0/+5 V at 27 °C | Pass; maximum summed absolute current 0.542608 nA |
| Existing `tests/pnr` regression suite | 49 passed in 248.57 s |

The zero-item DRC reports honor only the two organizer-owned 63/0 waiver
polygons (union 63400 µm²). No TritFlow waiver geometry exists. An independent
frame-only MDP run reproduces the 0.001508 µm² M2 delta in the stock logo;
the chip has exactly zero additional conductor delta or delta overlapping
our macro/wrapper geometry. Full-die CO/M1/V1 XOR is zero. The raw full-die
M2 delta remains recorded in the summary.

| Supply | Core current envelope | Minimum conductor reserve |
|---|---|---|
| VDD | 6.670803 mA | 64.8896% |
| VSS | 6.670803 mA | 41.3022% |
| VMID | 0.110049 nA | 99.8718% |
| ESD_VDD | 1 µA leakage budget | 99.7778% |

The solver includes a 1 µA auxiliary leakage budget per supply path and
verifies all modeled conductors/cuts against actual GDS. The three non-supply
pad biases conservatively cover the five unused ANA pads too; they do not
predict the voltage of a floating pad.

Suggested caption: “The same full adder in the stock OSS_FRAME (2.5 mm square,
16 pads); drawing DRC: 0 items with stock waivers, strict ESD-inclusive LVS:
match.”

## Reproduction

Run from the repository root; all generated files stay in this directory:

```bash
export PYTHONDONTWRITEBYTECODE=1
export TR1UM_PDK="$HOME/pdk/TR-1um-pinned"
export NGSPICE_BINARY="$HOME/.local/opt/tritflow-ubuntu-24.04/bin/ngspice"
python3 -B figures/full_add_chip/build.py --mpw-template "$HOME/TR-1um_MPW_Sanken"
python3 -B -m pytest tests/pnr -q \
  -o cache_dir=figures/full_add_chip/.pytest_cache \
  --basetemp=figures/full_add_chip/.pytest-tmp
```

`summary.json` is the figure-caption source of truth. `native_signoff.json`
contains the detailed native check results and hashes. `evidence.zip` packages
the build script and the `.work/macro/` and `.work/chip/` evidence. Scratch `.work/` retains
the copied macro, chip metadata, native DRC/LVS databases, copied pinned decks,
independent frame-only MDP run and local copy of the Sanken precheck template.
`verification.json` records the final hash/archive audit, independent native
DRC item counts and confirmation of all five NC ports in the extracted netlist.

Post-MDP LVS is not defined by the inspected stock workflow and is not claimed.
DC checks use the existing conservative rail envelopes and conductor/cut width
scaling, not a lifetime EM rating. No full-chip transient/ESD-stress simulation
is claimed. Organizer slot allocation, final bond diagram and final CI remain
separate from these local checks.
