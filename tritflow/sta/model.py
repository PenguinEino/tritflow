"""Load/ramp surfaces for final entry into a ternary voltage band.

Timing is in seconds from the start of a full linear input ramp. Axes are
interpolated linearly in their physical units, not on logarithmic coordinates.
No missing or failed measurement is replaced with a guessed delay.
"""
from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

from tritflow import CELLS_DIR


class ModelDomainError(ValueError):
    """A requested operating point has no supported timing model."""


def _bracket(axis, value, *, extend=False):
    if not math.isfinite(value) or value < 0:
        raise ModelDomainError(f"Invalid timing coordinate: {value}")
    if value < axis[0] or value > axis[-1]:
        if not extend or value > 2 * axis[-1]:
            raise ModelDomainError(f"{value:g} outside measured axis {axis}; extension limit is 2x maximum")
        i = 0 if value < axis[0] else len(axis) - 2
    else:
        i = min(max(bisect_left(axis, value) - 1, 0), len(axis) - 2)
    return i, (value - axis[i]) / (axis[i + 1] - axis[i])


@dataclass
class CellTiming:
    """One published cell, preserving side-input and simultaneous-change classes."""

    data: dict

    @property
    def arcs(self):
        return self.data.get("arcs", []) + self.data.get("simultaneous", [])

    def capacitance(self, pin):
        """Maximum biased AC input C; cell metal is excluded by the producer."""
        value = float(self.data["input_capacitance"]["per_pin"][pin]["max_f"])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid input capacitance: {self.data['cell']}.{pin}")
        return value

    def sample(self, arc, load_f, ramp_s=1e-9, *, load_policy="error", field="settling_s"):
        """Bilinear interpolation; optional, explicit endpoint load extension.

        ``linear`` extends the nearest two load columns down to zero or up to
        twice the largest tested load. It is an estimate, never a certified
        bound. Negative extrapolated delays are floored at zero. Input ramps
        are always confined to the measured range. ``error`` is strict.
        """
        if load_policy not in {"error", "linear"}:
            raise ValueError("load_policy must be 'error' or 'linear'")
        axes = self.data["axes"]
        i, x = _bracket(axes["load_f"], load_f, extend=load_policy == "linear")
        j, y = _bracket(axes["input_transition_s"], ramp_s)
        value = 0.0
        for row, wy in ((j, 1-y), (j+1, y)):
            for col, wx in ((i, 1-x), (i+1, x)):
                weight = wx * wy
                if abs(weight) < 1e-14:
                    continue
                point = arc[field][row][col]
                if (not arc["passed"][row][col] or point is None
                        or not math.isfinite(point) or point < 0):
                    raise ModelDomainError(f"Invalid {field} point in {arc['id']} [{row}][{col}]")
                value += weight * point
        return max(0.0, value)


class TimingLibrary:
    """Immutable JSON snapshot; verify source hashes and atomic publication ID.

    A legacy .char.json is insufficient to reconstruct all directed arcs. When
    timing tables are absent we fail explicitly instead of promoting a partial
    characterization sequence to a complete timing surface.
    """

    def __init__(self, cells, root=None):
        self.root = Path(root) if root is not None else CELLS_DIR / "out"
        marker = self.root / "generation.json"
        before = marker.read_bytes() if marker.exists() else None
        self.cells = {}
        self.hashes = {}
        for cell in sorted(set(cells)):
            path = self.root / cell / f"{cell}.timing.json"
            raw = path.read_bytes()
            data = json.loads(raw)
            if (data.get("schema_version") != 1 or data.get("cell") != cell
                    or not data.get("complete") or not data.get("passed")):
                raise ValueError(f"Incomplete or failed timing table: {path}")
            source = self.root / cell / f"{cell}.ext.spice"
            if hashlib.sha256(source.read_bytes()).hexdigest() != data["source_sha256"]:
                raise ValueError(f"Stale timing source: {path}")
            for axis in data["axes"].values():
                if len(axis) < 2 or any(not math.isfinite(v) or v <= 0 for v in axis) or any(a >= b for a, b in zip(axis, axis[1:])):
                    raise ValueError(f"Invalid timing axis: {path}")
            self.cells[cell] = CellTiming(data)
            self.hashes[str(path)] = hashlib.sha256(raw).hexdigest()
        if before != (marker.read_bytes() if marker.exists() else None):
            raise RuntimeError("Cell publication changed during timing snapshot; retry")
        generations = {json.dumps(m.data.get("generation"), sort_keys=True) for m in self.cells.values()}
        if len(generations) > 1:
            raise ValueError("Timing tables mix cell generations")
        self.generation = json.loads(next(iter(generations))) if generations else None
        if before is not None and self.cells:
            marker_generation = json.loads(before)
            if self.generation != marker_generation:
                raise ValueError("Timing tables do not match the published generation marker")

    def __getitem__(self, cell):
        return self.cells[cell]
