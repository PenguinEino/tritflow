"""Geometric circuit drawing records, in SVG pixels on an eight-pixel grid."""
from __future__ import annotations

from dataclasses import dataclass, field
import re

Point = tuple[int, int]
# Gate input spacing is also the minimum useful leg between routing corners.
# Pin escape uses the finer eight-pixel raster.
from .rules import PITCH as JOG_PITCH


def natural(name):
    """Keep bit vectors in ascending numerical order, including indices >= 10."""
    return tuple((1, int(part)) if part.isdigit() else (0, part)
                 for part in re.split(r'(\d+)', name))


@dataclass
class Symbol:
    """A gate, hierarchy boundary, or external port and its exact pin anchors."""
    key: str
    kind: str
    label: str
    members: tuple[str, ...] = ()
    inputs: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    level: int = 0
    x: int = 0
    y: int = 0
    width: int = 96
    height: int = 96
    pins: dict[str, Point] = field(default_factory=dict)
    pin_labels: dict[str, str] = field(default_factory=dict)
    sides: dict[str, str] = field(default_factory=dict)
    orient: str = 'right'
    module: str = ''

    @property
    def box(self):
        """Keep-out includes the gate name and all pin labels, not just outline."""
        return self.x, self.y, self.x + self.width, self.y + self.height


@dataclass(frozen=True)
class Segment:
    net: str
    a: Point
    b: Point


@dataclass(frozen=True)
class Connection:
    """One original cell/port terminal, including terminals inside closed blocks."""
    endpoint: str
    net: str
    symbol: str
    pin: str | None


@dataclass(frozen=True)
class Frame:
    label: str
    box: tuple[int, int, int, int]
    members: tuple[str, ...]
    module: str = ''
    pins: dict[str, Point] = field(default_factory=dict)
    sides: dict[str, str] = field(default_factory=dict)
    nets: dict[str, str] = field(default_factory=dict)


@dataclass
class Scene:
    """Annotation-independent topology and routing, reusable after P&R."""
    top: str
    symbols: tuple[Symbol, ...]
    segments: tuple[Segment, ...]
    junctions: dict[str, tuple[Point, ...]]
    connections: tuple[Connection, ...]
    labels: dict[str, Point]
    width: int
    height: int
    hidden_nets: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    frames: tuple[Frame, ...] = ()
    trunks: tuple[Segment, ...] = ()
    # Outer routes are kept separately so frame-boundary access is auditable.
    interconnect: tuple[Segment, ...] = ()
    # Detailed flat RTL drawings need zoom/scroll instead of growing labels
    # beyond the fixed gate outlines merely to fit a 1000 px overview.
    detailed: bool = False
