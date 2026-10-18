# TritFlow

A balanced-ternary HDL → synthesis → place & route → GDS → DRC/LVS → post-layout ngspice
flow on the open [OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um) PDK, built around a
standard-cell library derived from taped-out ternary cells
([opensusi-tr10-balanced-ternary-logic](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic)).

Prepared for the IEEE SSCS Code-a-Chip Travel Grant (ISSCC 2027). Work in progress.

- Notebook: [`notebook/tritflow_tr1um.ipynb`](notebook/tritflow_tr1um.ipynb)
- Colab setup: [`notebook/colab_setup.sh`](notebook/colab_setup.sh)
- Cells: [`cells/`](cells/) · Examples: [`examples/`](examples/)

Logic values −1 / 0 / +1 are −5 / 0 / +5 V with VDD = +5 V, VMID = 0 V, VSS = −5 V.

License: Apache-2.0.
