# Schematic geometry: phase 3 → phase 4

Wire length is in drawing pixels, not chip micrometres. A bend is a unique same-net degree-two orthogonal corner; T joins are excluded. Crossings count distinct different-net perpendicular intersections. Aspect is full canvas width / height; the real-C overlay includes its annotation table.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect |
|---|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 2200 → 3776 | 9 → 8 | 1.00 → 0.89 | 2 → 2 | 5 → 5 | 1.68 → 2.66 |
| half_add-flat | 2200 → 3776 | 9 → 8 | 1.00 → 0.89 | 2 → 2 | 5 → 5 | 1.68 → 2.66 |
| full_add-hierarchical | 1072 → 1360 | 8 → 6 | 0.89 → 0.67 | 4 → 4 | 0 → 0 | 1.85 → 4.24 |
| full_add-flat | 5040 → 9792 | 31 → 38 | 1.63 → 2.00 | 6 → 7 | 8 → 11 | 2.15 → 2.17 |
| adder2-hierarchical | 448 → 496 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.28 → 1.51 |
| adder2-flat | 11152 → 21704 | 69 → 78 | 1.86 → 2.11 | 8 → 7 | 16 → 24 | 1.13 → 1.11 |
| adder4-hierarchical | 864 → 944 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 2.12 → 2.57 |
| adder4-flat | 23856 → 46360 | 137 → 158 | 1.88 → 2.16 | 8 → 7 | 32 → 62 | 2.16 → 2.26 |
| mul1-hierarchical | 1152 → 1856 | 9 → 8 | 1.50 → 1.33 | 3 → 2 | 2 → 2 | 1.67 → 2.84 |
| mul1-flat | 1152 → 1856 | 9 → 8 | 1.50 → 1.33 | 3 → 2 | 2 → 2 | 1.67 → 2.84 |
| mac1-hierarchical | 2176 → 3488 | 12 → 10 | 0.92 → 0.77 | 3 → 3 | 3 → 2 | 2.32 → 3.27 |
| mac1-flat | 6920 → 12672 | 42 → 46 | 1.56 → 1.70 | 6 → 7 | 10 → 12 | 2.72 → 3.18 |
| sign-hierarchical | 312 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 0.83 → 1.40 |
| sign-flat | 312 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 0.83 → 1.40 |
| compare2-hierarchical | 3048 → 4224 | 9 → 10 | 0.64 → 0.71 | 4 → 4 | 3 → 3 | 1.27 → 1.58 |
| compare2-flat | 3048 → 4224 | 9 → 10 | 0.64 → 0.71 | 4 → 4 | 3 → 3 | 1.27 → 1.58 |
| mul2-hierarchical | 2848 → 5728 | 23 → 24 | 1.92 → 2.00 | 3 → 4 | 7 → 7 | 1.74 → 2.52 |
| mul2-flat | 14032 → 20904 | 71 → 73 | 2.09 → 2.15 | 7 → 7 | 21 → 15 | 1.47 → 1.38 |
| minmax-hierarchical | 768 → 1360 | 5 → 4 | 0.83 → 0.67 | 3 → 2 | 2 → 2 | 1.23 → 2.09 |
| minmax-flat | 768 → 1360 | 5 → 4 | 0.83 → 0.67 | 3 → 2 | 2 → 2 | 1.23 → 2.09 |
| half_add-overlay | 2200 → 3776 | 9 → 8 | 1.00 → 0.89 | 2 → 2 | 5 → 5 | 1.44 → 2.35 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 |

A short jog is a leg shorter than one gate input pitch (32 px) between two degree-two corners. Terminal stubs and T joins are excluded; pin access uses the finer 8 px raster. Edge runs count positive overlap along any symbol/label keep-out boundary; perpendicular pin contact is allowed.

| Figure | Short jogs | Rotated gates | Symbol-edge runs | Clearance violations |
|---|---:|---:|---:|---:|
| half_add-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 27 → 0 |
| half_add-flat | 0 → 0 | 0 → 0 | 0 → 0 | 27 → 0 |
| full_add-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 16 → 0 |
| full_add-flat | 0 → 0 | 0 → 0 | 0 → 0 | 93 → 0 |
| adder2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| adder2-flat | 0 → 0 | 0 → 0 | 0 → 0 | 195 → 0 |
| adder4-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| adder4-flat | 0 → 0 | 0 → 0 | 0 → 0 | 381 → 0 |
| mul1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 26 → 0 |
| mul1-flat | 0 → 0 | 0 → 0 | 0 → 0 | 26 → 0 |
| mac1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 37 → 0 |
| mac1-flat | 0 → 0 | 0 → 0 | 0 → 0 | 124 → 0 |
| sign-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 4 → 0 |
| sign-flat | 0 → 0 | 0 → 0 | 0 → 0 | 4 → 0 |
| compare2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 23 → 0 |
| compare2-flat | 0 → 0 | 0 → 0 | 0 → 0 | 23 → 0 |
| mul2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 72 → 0 |
| mul2-flat | 0 → 0 | 0 → 0 | 0 → 0 | 206 → 0 |
| minmax-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 18 → 0 |
| minmax-flat | 0 → 0 | 0 → 0 | 0 → 0 | 18 → 0 |
| half_add-overlay | 0 → 0 | 0 → 0 | 0 → 0 | 27 → 0 |
| legend | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
