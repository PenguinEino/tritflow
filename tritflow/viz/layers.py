"""TR-1um drawing layers as the notebook and figures show them.

Colors follow the PDK's KLayout properties (TR-1um.lyp); contacts, vias and M2
are darkened so they read on a white page. Hatches stand in for KLayout's
dither patterns.
"""

# ((layer, datatype), name, color, hatch, fill opacity), drawn in this order.
LAYER_STYLE = (
    ((140, 0), "N-well", "#00aa00", None, 0.10),
    ((3, 1), "P diffusion", "#ff00ff", "dots", 0.0),
    ((3, 2), "N diffusion", "#00aa00", "dots", 0.0),
    ((3, 3), "Diffusion resistor", "#ffae00", "back", 0.0),
    ((8, 1), "Gate poly", "#ff7c25", "fwd", 0.0),
    ((8, 2), "Resistor poly", "#c050c0", "back", 0.0),
    ((11, 0), "Contact", "#3a3f45", "cross", 0.0),
    ((13, 0), "M1", "#0080ff", "fwd", 0.15),
    ((19, 0), "V1", "#3a3f45", "cross", 0.0),
    ((20, 0), "M2", "#8c8c8c", "back", 0.12),
)
WIRE_WIDTH = {"M1": 1.8, "M2": 3.0}
VIA_SIZE = 1.4

# The same hatches as matplotlib patterns, for static figures.
MATPLOTLIB_HATCH = {"fwd": "////", "back": "\\\\\\\\", "dots": "...", "cross": "xx", None: None}
