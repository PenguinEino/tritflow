# TritFlow notebook v3

The submission notebooks are [English](v3/tritflow_en.ipynb) and [Japanese](v3/tritflow_ja.ipynb). Both use the same code cells in `v3/make_notebook.py`; their Markdown sources live in `v3/narrative_en/` and `v3/narrative/`.

## Build and run

Run from the repository root. Full native setup supports Ubuntu 24.04 amd64; the simulator-only installer also supports arm64. KLayout must include Ruby for the PDK DRC/LVS decks. The setup downloads exact packages into a private runtime and fetches the pinned public PDK; it does not replace the host's preloaded NumPy or Matplotlib.

```sh
python3 -m pip install --user --break-system-packages -e . jupyter
bash notebook/colab_setup.sh --source "$PWD"
python3 notebook/v3/make_notebook.py --lang en
python3 notebook/v3/make_notebook.py --lang ja
TRITFLOW_ROOT="$PWD" jupyter execute --timeout=1200 \
  --output=tritflow_en_executed.ipynb notebook/v3/tritflow_en.ipynb
TRITFLOW_ROOT="$PWD" jupyter execute --timeout=1200 \
  --output=tritflow_ja_executed.ipynb notebook/v3/tritflow_ja.ipynb
```

The bootstrap finds a local checkout through `TRITFLOW_ROOT` and reads `notebook/runtime.json` when setup created it. Local execution does not clone or reset the source. `TRITFLOW_NOTEBOOK_BUILD` selects an artifact directory (default `build/notebook`). To use an existing qualified PDK and simulator, set `TR1UM_PDK` and the absolute `NGSPICE_BINARY` instead. `install_ngspice.py` can install the pinned ngspice-42 wrapper separately. Runtime locks and the Docker route are explained in [dependencies.md](dependencies.md).

Each generated notebook records an immutable `SOURCE_REF` for Colab. After merging changes, the integrator must publish a compatible implementation commit and rebuild both notebooks with `--ref <full-commit>`. An uncommitted local run verifies working-tree changes without publishing that source pin.

## Files and recorded inputs

- `live.py`, `style.py`, `views.py`, `inverter_views.py`, `cell_views.py` and `pnr_views.py` provide the shared controls and progress displays. `localization.py` handles presentation text.
- `v3/setup_cell.py`, `v3/make_tables.py` and `v3/compact_schematics.py` build the setup cell, static tables and compact Xschem figures. Table generation requires Xschem and the pinned PDK symbols.
- `assets/schematics/` holds the four compact circuit drawings, their editable sources and an electrical equivalence verifier. `export_schematics.py` supplies their SVG theme.
- `scale_views.py` reads `results/dot_scaling.json`; `examples/dot_scaling.py` checks its consumed source and artifact hashes. Its companion directory includes native evidence and a checked producer snapshot. `cache.py` supplies the hashed manifest reader.
- `reuse.py` runs edited HDL through verification and displays the recorded `assets/chip/dot4/` top. The shuttle directory includes build/verify scripts, GDS, reports, the original producer snapshot and native evidence.
- `cells/out/` supplies cell views, characterization and sizing grids. `results/sta/propagation/` supplies the STA propagation tables and their characterization runs.

Recorded evidence is not a fresh physical run. Editing a consumed implementation or model invalidates its reader checks; do not alter hashes to make a changed result appear current. Recomputing the scaling campaign is optional and can take substantially longer than the normal notebook execution.

## Verification

```sh
python3 notebook/validate_notebook.py --language en
python3 notebook/validate_notebook.py --language ja
python3 notebook/qualify_notebook.py --output build/qualification
python3 -m pytest tests notebook/tests
python3 -m pytest notebook/v3/test_language.py
python3 -m pytest submission/tests
```

The qualifier executes both editions in fresh kernels and writes notebooks and reports below the selected output directory. It does not install dependencies or claim a real-Colab run. The [submission guide](../submission/README.md) describes saved-output packaging and final release checks.
