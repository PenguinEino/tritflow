"""Geometric circuit drawing records, in SVG pixels on an eight-pixel grid."""
from __future__ import annotations

from dataclasses import dataclass, field
import re

Point = tuple[int, int]


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
