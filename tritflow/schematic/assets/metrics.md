# Schematic geometry: original → revised

Wire length is in drawing pixels, not chip micrometres. A bend is a unique same-net degree-two orthogonal corner; T joins are excluded. Crossings count distinct different-net perpendicular intersections. Aspect is full canvas width / height; the real-C overlay includes its annotation table.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect |
|---|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 5152 → 2248 | 25 → 11 | 2.78 → 1.22 | 8 → 2 | 4 → 5 | 4.87 → 1.68 |
| half_add-flat | 5152 → 2248 | 25 → 11 | 2.78 → 1.22 | 8 → 2 | 4 → 5 | 4.87 → 1.68 |
| full_add-hierarchical | 3360 → 912 | 20 → 12 | 2.22 → 1.33 | 4 → 4 | 0 → 0 | 3.75 → 1.69 |
| full_add-flat | 14112 → 5096 | 69 → 44 | 3.63 → 2.32 | 12 → 6 | 10 → 10 | 6.87 → 2.15 |
| adder2-hierarchical | 4272 → 448 | 26 → 0 | 2.89 → 0.00 | 6 → 0 | 5 → 0 | 1.95 → 1.28 |
| adder2-flat | 39240 → 11208 | 162 → 94 | 4.38 → 2.54 | 20 → 7 | 29 → 23 | 6.66 → 1.13 |
| adder4-hierarchical | 16112 → 864 | 78 → 0 | 4.59 → 0.00 | 10 → 0 | 27 → 0 | 2.17 → 2.12 |
| adder4-flat | 130632 → 23944 | 471 → 194 | 6.45 → 2.66 | 36 → 9 | 85 → 57 | 6.83 → 2.16 |
| mul1-hierarchical | 1920 → 1152 | 14 → 9 | 2.33 → 1.50 | 4 → 3 | 2 → 2 | 3.15 → 1.67 |
| mul1-flat | 1920 → 1152 | 14 → 9 | 2.33 → 1.50 | 4 → 3 | 2 → 2 | 3.15 → 1.67 |
| mac1-hierarchical | 8304 → 2176 | 43 → 12 | 3.31 → 0.92 | 6 → 3 | 4 → 3 | 3.26 → 2.32 |
| mac1-flat | 34216 → 6944 | 134 → 55 | 4.96 → 2.04 | 22 → 6 | 17 → 12 | 8.33 → 2.72 |
| sign-hierarchical | 848 → 312 | 4 → 2 | 1.33 → 0.67 | 2 → 2 | 0 → 0 | 1.92 → 0.83 |
| sign-flat | 848 → 312 | 4 → 2 | 1.33 → 0.67 | 2 → 2 | 0 → 0 | 1.92 → 0.83 |
| compare2-hierarchical | 4848 → 3080 | 24 → 15 | 1.71 → 1.07 | 4 → 4 | 5 → 3 | 4.62 → 1.27 |
| compare2-flat | 4848 → 3080 | 24 → 15 | 1.71 → 1.07 | 4 → 4 | 5 → 3 | 4.62 → 1.27 |
| mul2-hierarchical | 6048 → 2808 | 30 → 27 | 2.50 → 2.25 | 4 → 4 | 9 → 7 | 1.88 → 1.74 |
| mul2-flat | 28080 → 13944 | 116 → 84 | 3.41 → 2.47 | 16 → 7 | 23 → 24 | 3.19 → 1.47 |
| minmax-hierarchical | 1520 → 768 | 6 → 5 | 1.00 → 0.83 | 2 → 3 | 2 → 2 | 2.50 → 1.23 |
| minmax-flat | 1520 → 768 | 6 → 5 | 1.00 → 0.83 | 2 → 3 | 2 → 2 | 2.50 → 1.23 |
| half_add-overlay | 5152 → 2248 | 25 → 11 | 2.78 → 1.22 | 8 → 2 | 4 → 5 | 4.87 → 1.44 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 |
