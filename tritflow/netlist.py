"""Gate-level netlist shared by synthesis, P&R and simulation.

Serialized as JSON (see docs/interfaces.md). Power rails VDD/VMID/VSS are
global and never appear in `pins`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Port:
    name: str          # scalar names; vector bits are "a[0]"
    dir: str           # "input" | "output"


@dataclass
class Instance:
    name: str
    cell: str          # INV NAND NOR NANY BUF TIEP TIEZ TIEN
    pins: dict[str, str]   # cell pin -> net
    hier: str = ""     # source hierarchy path, e.g. "fa[1].u.ha2"


@dataclass
class GateNetlist:
    top: str
    ports: list[Port] = field(default_factory=list)
    instances: list[Instance] = field(default_factory=list)

    def nets(self) -> set[str]:
        out = {p.name for p in self.ports}
        for inst in self.instances:
            out.update(inst.pins.values())
        return out

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=1)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json())

    @classmethod
    def from_dict(cls, d: dict) -> "GateNetlist":
        return cls(
            top=d["top"],
            ports=[Port(**p) for p in d["ports"]],
            instances=[Instance(**i) for i in d["instances"]],
        )

    @classmethod
    def load(cls, path: str | Path) -> "GateNetlist":
        return cls.from_dict(json.loads(Path(path).read_text()))
