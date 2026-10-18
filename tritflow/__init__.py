"""TritFlow: balanced-ternary HDL -> GDS flow for the OpenSUSI TR-1um PDK."""

from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent
CELLS_DIR = ROOT / "cells"
# The flow is qualified against the public PDK commit pinned in notebook/setup_pins.json.
_PINNED = Path.home() / "pdk" / "TR-1um-pinned"
PDK_ROOT = Path(os.environ.get("TR1UM_PDK", _PINNED if _PINNED.is_dir() else Path.home() / "pdk" / "TR-1um"))

VDD, VMID, VSS = 5.0, 0.0, -5.0
TRIT_VOLTS = {-1: VSS, 0: VMID, 1: VDD}
PASS_BAND = 0.5  # |V - ideal| must be <= this at a check point
RAILS = ("VDD", "VMID", "VSS")
