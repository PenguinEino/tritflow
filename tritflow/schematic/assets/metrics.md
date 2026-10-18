# Schematic geometry: phase 2 → phase 3

Wire length is in drawing pixels, not chip micrometres. A bend is a unique same-net degree-two orthogonal corner; T joins are excluded. Crossings count distinct different-net perpendicular intersections. Aspect is full canvas width / height; the real-C overlay includes its annotation table.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect |
|---|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 2248 → 2200 | 11 → 9 | 1.22 → 1.00 | 2 → 2 | 5 → 5 | 1.68 → 1.68 |
| half_add-flat | 2248 → 2200 | 11 → 9 | 1.22 → 1.00 | 2 → 2 | 5 → 5 | 1.68 → 1.68 |
| full_add-hierarchical | 912 → 1072 | 12 → 8 | 1.33 → 0.89 | 4 → 4 | 0 → 0 | 1.69 → 1.85 |
| full_add-flat | 5096 → 5040 | 44 → 31 | 2.32 → 1.63 | 6 → 6 | 10 → 8 | 2.15 → 2.15 |
| adder2-hierarchical | 448 → 448 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.28 → 1.28 |
| adder2-flat | 11208 → 11152 | 94 → 69 | 2.54 → 1.86 | 7 → 8 | 23 → 16 | 1.13 → 1.13 |
| adder4-hierarchical | 864 → 864 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 2.12 → 2.12 |
| adder4-flat | 23944 → 23856 | 194 → 137 | 2.66 → 1.88 | 9 → 8 | 57 → 32 | 2.16 → 2.16 |
| mul1-hierarchical | 1152 → 1152 | 9 → 9 | 1.50 → 1.50 | 3 → 3 | 2 → 2 | 1.67 → 1.67 |
| mul1-flat | 1152 → 1152 | 9 → 9 | 1.50 → 1.50 | 3 → 3 | 2 → 2 | 1.67 → 1.67 |
| mac1-hierarchical | 2176 → 2176 | 12 → 12 | 0.92 → 0.92 | 3 → 3 | 3 → 3 | 2.32 → 2.32 |
| mac1-flat | 6944 → 6920 | 55 → 42 | 2.04 → 1.56 | 6 → 6 | 12 → 10 | 2.72 → 2.72 |
| sign-hierarchical | 312 → 312 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 0.83 → 0.83 |
| sign-flat | 312 → 312 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 0.83 → 0.83 |
| compare2-hierarchical | 3080 → 3048 | 15 → 9 | 1.07 → 0.64 | 4 → 4 | 3 → 3 | 1.27 → 1.27 |
| compare2-flat | 3080 → 3048 | 15 → 9 | 1.07 → 0.64 | 4 → 4 | 3 → 3 | 1.27 → 1.27 |
| mul2-hierarchical | 2808 → 2848 | 27 → 23 | 2.25 → 1.92 | 4 → 3 | 7 → 7 | 1.74 → 1.74 |
| mul2-flat | 13944 → 14032 | 84 → 71 | 2.47 → 2.09 | 7 → 7 | 24 → 21 | 1.47 → 1.47 |
| minmax-hierarchical | 768 → 768 | 5 → 5 | 0.83 → 0.83 | 3 → 3 | 2 → 2 | 1.23 → 1.23 |
| minmax-flat | 768 → 768 | 5 → 5 | 0.83 → 0.83 | 3 → 3 | 2 → 2 | 1.23 → 1.23 |
| half_add-overlay | 2248 → 2200 | 11 → 9 | 1.22 → 1.00 | 2 → 2 | 5 → 5 | 1.44 → 1.44 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 |

A short jog is a leg shorter than one gate input pitch (32 px) between two degree-two corners. Terminal stubs and T joins are excluded; pin access uses the finer 8 px raster. Edge runs count positive overlap along any symbol/label keep-out boundary; perpendicular pin contact is allowed.

| Figure | Short jogs | Rotated gates | Symbol-edge runs |
|---|---:|---:|---:|
| half_add-hierarchical | 1 → 0 | 0 → 0 | 0 → 0 |
| half_add-flat | 1 → 0 | 0 → 0 | 0 → 0 |
| full_add-hierarchical | 2 → 0 | 0 → 0 | 0 → 0 |
| full_add-flat | 4 → 0 | 2 → 0 | 0 → 0 |
| adder2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| adder2-flat | 9 → 0 | 4 → 0 | 0 → 0 |
| adder4-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| adder4-flat | 19 → 0 | 8 → 0 | 0 → 0 |
| mul1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| mul1-flat | 0 → 0 | 0 → 0 | 0 → 0 |
| mac1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| mac1-flat | 4 → 0 | 2 → 0 | 0 → 0 |
| sign-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| sign-flat | 0 → 0 | 0 → 0 | 0 → 0 |
| compare2-hierarchical | 3 → 0 | 0 → 0 | 0 → 0 |
| compare2-flat | 3 → 0 | 0 → 0 | 0 → 0 |
| mul2-hierarchical | 3 → 0 | 0 → 0 | 0 → 0 |
| mul2-flat | 5 → 0 | 2 → 0 | 0 → 0 |
| minmax-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| minmax-flat | 0 → 0 | 0 → 0 | 0 → 0 |
| half_add-overlay | 1 → 0 | 0 → 0 | 0 → 0 |
| legend | 0 → 0 | 0 → 0 | 0 → 0 |
