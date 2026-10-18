"""Cell-local routing constraints, including reflection and certified free columns."""
from __future__ import annotations


def reflected_rect(cell, placement, rect):
    """Transform an abstract rectangle exactly like a GDS cell reference."""
    x0, y0, x1, y1 = rect
    if placement["orient"] == "MY":
        x0, x1 = cell.width-x1, cell.width-x0
    return [x0+placement["x"], y0+placement["y"], x1+placement["x"], y1+placement["y"]]


def free_m2_columns(cell):
    """Return certified local x columns, or None when only shapes constrain M2.

    Public extension: ``free_tracks: {"M2": [x, ...]}``. An explicit empty list
    forbids over-cell transit. The original metadata is retained in Library.
    ``routing.m2_free_tracks`` is accepted for cell generators using that key.
    """
    value = cell.free_tracks.get("M2") if isinstance(cell.free_tracks, dict) else cell.free_tracks
    if value is None:
        value = cell.routing.get("m2_free_tracks")
    if value is None:
        return None
    if isinstance(value, dict):
        value = value["x"]
    return tuple(float(x) for x in value)


def m2_obstacles(cell, placement, template):
    """Yield M2 keepouts; V1 cuts imply enclosed metal even in sparse abstracts.

    A free-column list constrains full-height over-cell transit. Shape keepouts
    remain authoritative inside those columns. V1 cuts carry their 1 µm metal
    enclosure before M2 spacing is applied by the maze.
    """
    for rect in cell.obstructions.get("M2", []):
        yield reflected_rect(cell, placement, rect)
    enclosure = template["rules"]["V1_enc_M2"]
    for x0, y0, x1, y1 in cell.obstructions.get("V1", []):
        yield reflected_rect(cell, placement, [x0-enclosure, y0-enclosure, x1+enclosure, y1+enclosure])
    columns = free_m2_columns(cell)
    if columns is not None:
        pitch = template["grid"]
        for index in range(round(cell.width/pitch)):
            x = pitch/2+index*pitch
            if not any(abs(x-free) < 1e-6 for free in columns):
                yield reflected_rect(cell, placement, [x, 0., x, cell.height])


def legal_pin_access(cell, pin, template):
    """Choose an advertised landing whose pad clears M2 and internal V1 cuts."""
    rules = template["rules"]
    half = (rules["V1"]+2*rules["V1_enc_M2"])/2
    gap = rules["M2_s"]
    obstacles = list(m2_obstacles(cell, {"x": 0., "y": 0., "orient": "R0"}, template))
    result = []
    for x, y in cell.pins[pin]["access"]:
        if all(x+half+gap <= x0+1e-7 or x-half-gap >= x1-1e-7 or
               y+half+gap <= y0+1e-7 or y-half-gap >= y1-1e-7
               for x0, y0, x1, y1 in obstacles):
            result.append([x, y])
    return result
