# tr_1um_adder4

Centered 2500 × 2500 µm OpenSUSI TEG allocation. The pinned seal ring is unchanged;
the copied pad bank is replaced by genuine OSS_PAD_TEG peripheral pads.
Drawing DRC, strict LVS, MDP and mask DRC reports are in signoff/.

VDD = +5 V; VMID = 0 V; VSS/common substrate = −5 V.
Bond or probe **every supply pad** in its domain; the current reserve assumes all are powered.
The original macro and its power JSON are unchanged.

| Pad | Net | X (µm) | Y (µm) |
|---|---|---:|---:|
| P01 | VDD | -890 | 1100 |
| P02 | VDD | -280 | 1100 |
| P03 | VDD | 280 | 1100 |
| P04 | VDD | 890 | 1100 |
| P05 | VSS | -700 | 1100 |
| P06 | VSS | -130 | 1100 |
| P07 | VSS | 488 | 1100 |
| P08 | VSS | 730 | 1100 |
| P09 | VMID | 0 | -1100 |
| P10 | a[3] | -1020 | -786 |
| P11 | a[2] | -1020 | -594 |
| P12 | a[1] | -1020 | -402 |
| P13 | a[0] | -1020 | -210 |
| P14 | b[3] | -1020 | -18 |
| P15 | b[2] | -1020 | 174 |
| P16 | b[1] | -1020 | 366 |
| P17 | b[0] | -1020 | 558 |
| P18 | cin | -1020 | 750 |
| P19 | sum[3] | 1020 | -786 |
| P20 | sum[2] | 1020 | -594 |
| P21 | sum[1] | 1020 | -402 |
| P22 | sum[0] | 1020 | -210 |
| P23 | cout | 1020 | -18 |

Before a real submission:

- Obtain the organizer's allocation and approval for this custom pad/probe map; it is not the stock 16-pin package.
- Agree the bond diagram, die attach/common substrate at VSS, all supply bonds and external VMID reference.
- Obtain process/ESD approval for the accepted ±5 V operating condition. These passive TEG pads add no ESD network.
- Simulate the full chip with package/probe loading and supply impedances; DC width/cut reserve is not lifetime EM signoff.
- Complete the shuttle info.yaml, project licence/metadata and schematic/reference package, using this top name and final PDK revision; run the organizer's final CI.
- Review the complete mask GDS and electrical results with the shuttle owner. No submission/upload is performed by TritFlow.

The inspected MPW flow specifies drawing LVS before MDP, and no post-MDP LVS stage.
