# Notebook figures

V3 uses two static figures: the full-adder overview (`fig_flow_v2`, English and Japanese) and the first circuit's flow map (`fig_flow_map_ja`). The retained filenames keep the notebook's published asset URLs stable. Their PDF, PNG and SVG outputs are in `out/`; `paperstyle.py` is shared with the schematic palette tests.

```sh
PYTHONPATH=. python3 figures/make_all.py
python3 notebook/v3/make_figures.py
```

The flow map producer executes the small first circuit. The full-adder overview reads native artifacts under `build/full_add/`, so first generate that design with the library's example flow. The second command translates the flow-map SVG into the English asset under `notebook/v3/assets/`. Xschem tables and compact schematics have separate producers under `notebook/v3/`.
