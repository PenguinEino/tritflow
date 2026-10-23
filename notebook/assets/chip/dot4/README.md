# tr_1um_dot4

Centered 2500 × 2500 µm OpenSUSI TEG allocation. The pinned seal ring is unchanged;
the copied pad bank is replaced by genuine OSS_PAD_TEG peripheral pads.
Drawing DRC, strict LVS, MDP and mask DRC reports are in signoff/.

VDD = +5 V; VMID = 0 V; VSS/common substrate = −5 V.
Bond or probe **every supply pad** in its domain; the current reserve assumes all are powered.
The original macro and its power JSON are unchanged.

| Pad | Net | X (µm) | Y (µm) |
|---|---|---:|---:|
| P01 | VDD | -890 | 1100 |
| P02 | VDD | -78 | 1100 |
| P03 | VDD | 890 | 1100 |
| P04 | VSS | -700 | 1100 |
| P05 | VSS | 140 | 1100 |
| P06 | VSS | 732 | 1100 |
| P07 | VMID | 0 | -1100 |
| P08 | w0 | -1020 | -594 |
| P09 | x3 | -1020 | -444 |
| P10 | w1 | -1020 | -294 |
| P11 | w2 | -1020 | -144 |
| P12 | w3 | -1020 | 6 |
| P13 | x0 | -1020 | 174 |
| P14 | x1 | -1020 | 366 |
| P15 | x2 | -1020 | 558 |
| P16 | y[1] | 1020 | -594 |
| P17 | y[0] | 1020 | -402 |

Before a real submission:

- Obtain the organizer's allocation and approval for this custom pad/probe map; it is not the stock 16-pin package.
- Agree the bond diagram, die attach/common substrate at VSS, all supply bonds and external VMID reference.
- Obtain process/ESD approval for the accepted ±5 V operating condition. These passive TEG pads add no ESD network.
- Simulate the full chip with package/probe loading and supply impedances; DC width/cut reserve is not lifetime EM signoff.
- Complete the shuttle info.yaml, project licence/metadata and schematic/reference package, using this top name and final PDK revision; run the organizer's final CI.
- Review the complete mask GDS and electrical results with the shuttle owner. No submission/upload is performed by TritFlow.

The inspected MPW flow specifies drawing LVS before MDP, and no post-MDP LVS stage.

## Recorded notebook snapshot

The macro is the programmable chapter 3–5 dot4 (46 cells), with eight independent input trits and two output trits. The editable fixed-weight example is separate (`dot4_fixed.tv`, 31 cells).

`signoff.json` and `provenance.json` describe this snapshot; `evidence.zip` contains the original macro, chip JSON/reference, copied rule decks, native reports/logs, extracted SPICE, drawing and mask GDS. The frame is an unchanged pinned seal ring with genuine peripheral OSS_PAD_TEG probe pads.

Rebuild with `TR1UM_PDK=~/pdk/TR-1um-pinned python3 notebook/assets/chip/dot4/build.py --mpw-template ~/TR-1um_MPW_Sanken`. All generated files remain in this directory.

Notebook view: `from reuse import shuttle_view; shuttle_view()`. This opens the recorded GDS and the pad table without rerunning qualification.

The English edition adds presentation labels to `notebook/reuse.py`. The exact source used for this recorded chip is retained as `reuse_before_english.py`. In `provenance.json`, `producer_source_sha256` retains the original source hashes; `source_sha256` verifies the packaged sources, including both that archive and the translated helper. The language tests compare their Python syntax trees after removing language lookups. No GDS, circuit, model, pad map or native verification evidence was regenerated for this presentation change.
