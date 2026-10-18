# Schematic geometry: phase 5 → phase 6

Wire length is in drawing pixels, not chip micrometres. A bend is a unique same-net degree-two orthogonal corner; T joins are excluded. Crossings count distinct different-net perpendicular intersections. Aspect is full canvas width / height; the real-C overlay includes its annotation table.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect | Min font pt @1000px |
|---|---:|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 3648 → 3104 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 2 | 2.54 → 2.54 | 9.0 → 11.0 |
| half_add-flat | 3648 → 3104 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 2 | 2.54 → 2.54 | 9.0 → 11.0 |
| full_add-hierarchical | 1344 → 1344 | 8 → 8 | 0.89 → 0.89 | 4 → 4 | 0 → 0 | 4.48 → 4.48 | 9.0 → 11.0 |
| full_add-flat | 11072 → 10192 | 30 → 30 | 1.58 → 1.58 | 5 → 5 | 12 → 6 | 3.66 → 3.61 | 9.0 → 9.0 |
| adder2-hierarchical | 512 → 480 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.58 → 1.51 | 10.0 → 17.2 |
| adder2-flat | 24768 → 23040 | 64 → 64 | 1.73 → 1.73 | 7 → 7 | 29 → 17 | 1.83 → 1.80 | 9.0 → 9.0 |
| adder4-hierarchical | 960 → 864 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 2.64 → 2.42 | 9.0 → 11.0 |
| adder4-flat | 52224 → 48800 | 132 → 132 | 1.81 → 1.81 | 7 → 7 | 63 → 39 | 0.90 → 0.89 | 9.0 → 9.0 |
| mul1-hierarchical | 1808 → 1808 | 8 → 8 | 1.33 → 1.33 | 2 → 2 | 2 → 2 | 2.64 → 2.64 | 9.0 → 11.1 |
| mul1-flat | 1808 → 1808 | 8 → 8 | 1.33 → 1.33 | 2 → 2 | 2 → 2 | 2.64 → 2.64 | 9.0 → 11.1 |
| mac1-hierarchical | 3224 → 3224 | 12 → 12 | 0.92 → 0.92 | 3 → 3 | 2 → 2 | 3.09 → 3.09 | 9.0 → 11.0 |
| mac1-flat | 17696 → 16912 | 56 → 56 | 2.07 → 2.07 | 8 → 8 | 16 → 10 | 2.14 → 2.07 | 9.0 → 9.0 |
| sign-hierarchical | 592 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 1.45 → 1.45 | 12.4 → 20.2 |
| sign-flat | 592 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 1.45 → 1.45 | 12.4 → 20.2 |
| compare2-hierarchical | 2728 → 2728 | 8 → 8 | 0.57 → 0.57 | 4 → 4 | 0 → 0 | 3.69 → 3.75 | 9.0 → 11.0 |
| compare2-flat | 2728 → 2728 | 8 → 8 | 0.57 → 0.57 | 4 → 4 | 0 → 0 | 3.69 → 3.75 | 9.0 → 11.0 |
| mul2-hierarchical | 5648 → 5648 | 24 → 24 | 2.00 → 2.00 | 4 → 4 | 7 → 7 | 2.55 → 2.55 | 9.0 → 11.0 |
| mul2-flat | 29152 → 28384 | 76 → 74 | 2.24 → 2.18 | 9 → 9 | 26 → 19 | 2.29 → 2.32 | 9.0 → 9.0 |
| minmax-hierarchical | 1328 → 1328 | 4 → 4 | 0.67 → 0.67 | 2 → 2 | 2 → 2 | 1.96 → 1.96 | 9.2 → 14.9 |
| minmax-flat | 1328 → 1328 | 4 → 4 | 0.67 → 0.67 | 2 → 2 | 2 → 2 | 1.96 → 1.96 | 9.2 → 14.9 |
| half_add-overlay | 3648 → 3104 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 2 | 2.14 → 2.07 | 9.0 → 11.0 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 | 9.0 → 11.0 |

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
