"""Composable edge measurements on a particular directed ternary level change.

Midpoints are relative to the *old and new levels*, so a -1→0 transition
crosses -2.5 V and a -1→+1 transition crosses 0 V. The last directional
crossing is used; multiple crossings are recorded rather than hidden.
"""
from __future__ import annotations

import numpy as np

from tritflow.sim.measure import settling_time


def crossings(time, voltage, before, after, start, end, fraction=.5):
    """All interpolated crossings in the requested direction, relative to start."""
    if before == after: return []
    mask = (time >= start) & (time <= end)
    t = np.r_[start, time[mask], end]
    y = np.interp(t, time, voltage)
    threshold = 5*(before+fraction*(after-before))
    z = np.sign(after-before)*(y-threshold)
    indices = np.flatnonzero((z[:-1] < 0) & (z[1:] >= 0))
    return [float(t[i]+(t[i+1]-t[i])*(-z[i])/(z[i+1]-z[i])-start) for i in indices]


def edge_metrics(time, voltage, before, after, start, end):
    """Return final midpoint time, 10–90% slew and final-band entry from start."""
    settling = settling_time(time, voltage, 5*after, start, end)
    values = {f: crossings(time, voltage, before, after, start, end, f) for f in (.1,.5,.9)}
    midpoint = values[.5][-1] if values[.5] else None
    slew = values[.9][-1]-values[.1][-1] if values[.1] and values[.9] else None
    if slew is not None and slew <= 0: slew = None
    return {'midpoint_s': midpoint, 'slew_10_90_s': slew, 'settling_s': settling,
            'tail_s': settling-midpoint if midpoint is not None and settling is not None else None,
            'midpoint_crossing_count': len(values[.5])}
