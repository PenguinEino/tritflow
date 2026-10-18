# Schematic geometry: phase 4 → phase 5

Wire length is in drawing pixels, not chip micrometres. A bend is a unique same-net degree-two orthogonal corner; T joins are excluded. Crossings count distinct different-net perpendicular intersections. Aspect is full canvas width / height; the real-C overlay includes its annotation table.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect | Min font pt @1000px |
|---|---:|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 3776 → 3648 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 5 | 2.66 → 2.54 | 4.7 → 9.0 |
| half_add-flat | 3776 → 3648 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 5 | 2.66 → 2.54 | 4.7 → 9.0 |
| full_add-hierarchical | 1360 → 1344 | 6 → 8 | 0.67 → 0.89 | 4 → 4 | 0 → 0 | 4.24 → 4.48 | 6.0 → 9.0 |
| full_add-flat | 9792 → 11072 | 38 → 30 | 2.00 → 1.58 | 7 → 5 | 11 → 12 | 2.17 → 3.66 | 3.4 → 9.0 |
| adder2-hierarchical | 496 → 512 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.51 → 1.58 | 10.5 → 10.0 |
| adder2-flat | 21704 → 24768 | 78 → 64 | 2.11 → 1.73 | 7 → 7 | 24 → 29 | 1.11 → 1.83 | 3.3 → 9.0 |
| adder4-hierarchical | 944 → 960 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 2.57 → 2.64 | 6.2 → 9.0 |
| adder4-flat | 46360 → 52224 | 158 → 132 | 2.16 → 1.81 | 7 → 7 | 62 → 63 | 2.26 → 0.90 | 1.6 → 9.0 |
| mul1-hierarchical | 1856 → 1808 | 8 → 8 | 1.33 → 1.33 | 2 → 2 | 2 → 2 | 2.84 → 2.64 | 6.9 → 9.0 |
| mul1-flat | 1856 → 1808 | 8 → 8 | 1.33 → 1.33 | 2 → 2 | 2 → 2 | 2.84 → 2.64 | 6.9 → 9.0 |
| mac1-hierarchical | 3488 → 3224 | 10 → 12 | 0.77 → 0.92 | 3 → 3 | 2 → 2 | 3.27 → 3.09 | 4.3 → 9.0 |
| mac1-flat | 12672 → 17696 | 46 → 56 | 1.70 → 2.07 | 7 → 8 | 12 → 16 | 3.18 → 2.14 | 2.1 → 9.0 |
| sign-hierarchical | 592 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 1.40 → 1.45 | 14.1 → 12.4 |
| sign-flat | 592 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 1.40 → 1.45 | 14.1 → 12.4 |
| compare2-hierarchical | 4224 → 2728 | 10 → 8 | 0.71 → 0.57 | 4 → 4 | 3 → 0 | 1.58 → 3.69 | 6.6 → 9.0 |
| compare2-flat | 4224 → 2728 | 10 → 8 | 0.71 → 0.57 | 4 → 4 | 3 → 0 | 1.58 → 3.69 | 6.6 → 9.0 |
| mul2-hierarchical | 5728 → 5648 | 24 → 24 | 2.00 → 2.00 | 4 → 4 | 7 → 7 | 2.52 → 2.55 | 4.3 → 9.0 |
| mul2-flat | 20904 → 29152 | 73 → 76 | 2.15 → 2.24 | 7 → 9 | 15 → 26 | 1.38 → 2.29 | 2.7 → 9.0 |
| minmax-hierarchical | 1360 → 1328 | 4 → 4 | 0.67 → 0.67 | 2 → 2 | 2 → 2 | 2.09 → 1.96 | 9.4 → 9.2 |
| minmax-flat | 1360 → 1328 | 4 → 4 | 0.67 → 0.67 | 2 → 2 | 2 → 2 | 2.09 → 1.96 | 9.4 → 9.2 |
| half_add-overlay | 3776 → 3648 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 5 | 2.35 → 2.14 | 4.7 → 9.0 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 | 6.9 → 9.0 |

A short jog is a leg shorter than one gate input pitch (32 px) between two degree-two corners. Terminal stubs and T joins are excluded; pin access uses the finer 8 px raster. Edge runs count positive overlap along any symbol/label keep-out boundary; perpendicular pin contact is allowed.

| Figure | Short jogs | Rotated gates | Symbol-edge runs | Clearance violations |
|---|---:|---:|---:|---:|
| half_add-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| half_add-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| full_add-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| full_add-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| adder2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| adder2-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| adder4-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| adder4-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| mul1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| mul1-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| mac1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| mac1-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| sign-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| sign-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| compare2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| compare2-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| mul2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| mul2-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| minmax-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| minmax-flat | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| half_add-overlay | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| legend | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
