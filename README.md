# TritFlow: balanced-ternary HDL to GDS

TritFlow turns a Verilog-like balanced-ternary HDL into a layout on the open [OpenSUSI TR-1um PDK](https://github.com/OpenSUSI/TR-1um). The notebook follows synthesis, standard cells, two-metal placement and routing, PDK DRC/LVS, and extracted ngspice simulation, using −5/0/+5 V for the three trit values. It develops a four-term dot product, compares recorded area, timing and power across sizes, and includes an editable HDL experiment.

**English** [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/main/notebook/v3/tritflow_en.ipynb)

**日本語** [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/main/notebook/v3/tritflow_ja.ipynb)

Choose **Runtime → Run all** in Colab. Setup installs the pinned tools and PDK; larger scaling studies and the framed chip are recorded results. Wire capacitance is estimated from geometry. The notebook states the measurement conditions and limits.

Repository layout:

- `notebook/v3/`: English/Japanese notebooks, narratives and their builder.
- `notebook/`: shared interactive views, setup, runtime locks and bundled assets.
- `tritflow/`, `cells/`, `examples/`: the design library, generated standard cells and HDL examples.
- `results/`, `figures/`: recorded dot-product results, STA characterization and notebook figures.
- `tests/`, `notebook/tests/`: library and notebook regression tests.
- `submission/`: reviewer-package builder and payload; `docs/`: design contracts and development notes.

From a local checkout on Ubuntu 24.04:

```sh
python3 -m pip install --user --break-system-packages -e . jupyter
bash notebook/colab_setup.sh --source "$PWD"
python3 notebook/v3/make_notebook.py --lang en
TRITFLOW_ROOT="$PWD" jupyter execute --timeout=1200 \
  --output=tritflow_en_executed.ipynb notebook/v3/tritflow_en.ipynb
```

Use `--lang ja` and `tritflow_ja.ipynb` for Japanese. See the [notebook guide](notebook/README.md) for local execution, pinned runtimes and tests. Generated flow artifacts live under `build/`.

TritFlow is licensed under [Apache-2.0](LICENSE). [NOTICE](NOTICE) credits the PDK and original taped-out circuits; the separately fetched PDK retains its own license and notices.
