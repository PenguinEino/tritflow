"""Physical cell views and an explicit metal-only library for router tests."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from tritflow import CELLS_DIR, RAILS
from .constraints import free_m2_columns, legal_pin_access


@dataclass
class Cell:
    """A cell's boundary, legal via access points, and immutable GDS source."""

    name: str
    width: float
    height: float
    pins: dict
    obstructions: dict = field(default_factory=dict)
    gds: Path | None = None
    characterization: dict = field(default_factory=dict)
    free_tracks: dict = field(default_factory=dict)
    routing: dict = field(default_factory=dict)
    selected_access: dict = field(default_factory=dict, init=False, repr=False)


@dataclass
class Library:
    """Routing rules and physical views; mock cells contain no transistors."""

    template: dict
    cells: dict[str, Cell]
    source: str = "explicit"
    mock: bool = False

    @classmethod
    def load(cls, root: str | Path = CELLS_DIR) -> "Library":
        root = Path(root)
        template = json.loads((root / "template.json").read_text())
        # The manifest is the publication barrier: never consume half-built cells.
        manifest = json.loads((root / "out/library.json").read_text())
        entries = manifest.get("cells", manifest) if isinstance(manifest, dict) else manifest
        if isinstance(entries, dict):
            names = list(entries)
        else:
            names = [e if isinstance(e, str) else e["name"] for e in entries]
        cells = {}
        for name in names:
            base = root / "out" / name
            abstract = json.loads((base / f"{name}.abstract.json").read_text())
            char = base / f"{name}.char.json"
            cells[name] = Cell(
                name, abstract["width"], abstract["height"], abstract["pins"],
                abstract.get("obstructions", {}), base / f"{name}.gds",
                json.loads(char.read_text()) if char.exists() else {},
                (abstract.get("free_tracks", {}) if "free_M2_tracks" not in abstract else
                 {**abstract.get("free_tracks", {}), "M2": abstract["free_M2_tracks"]}),
                abstract.get("routing", {}),
            )
        lib = cls(template, cells, str(root.resolve()))
        lib.validate()
        return lib

    @classmethod
    def automatic(cls, root: str | Path = CELLS_DIR) -> "Library":
        root = Path(root)
        if (root / "template.json").exists() and (root / "out/library.json").exists():
            return cls.load(root)
        return mock_library(root / "template.provisional.json")

    def validate(self) -> None:
        pitch = self.template["grid"]
        rules = self.template["rules"]
        pad = rules["V1"] + 2 * max(rules["V1_enc_M1"], rules["V1_enc_M2"])
        if pitch < max(pad + rules["M2_s"], pad + rules["M1_s"]):
            raise ValueError("Template grid cannot separate neighboring via landings")
        for cell in self.cells.values():
            if abs(cell.height - self.template["height"]) > 1e-6:
                raise ValueError(f"{cell.name}: inconsistent row height")
            if abs(cell.width / pitch - round(cell.width / pitch)) > 1e-6:
                raise ValueError(f"{cell.name}: width is not a grid multiple")
            columns = free_m2_columns(cell)
            if columns is not None and any(not 0 <= x <= cell.width for x in columns):
                raise ValueError(f"{cell.name}: free M2 column outside boundary")
            for name, pin in cell.pins.items():
                if pin.get("layer", "M1") != "M1" or not pin.get("access"):
                    raise ValueError(f"{cell.name}.{name}: M1 access required")
                for x, y in pin["access"]:
                    if abs((x - pitch / 2) / pitch - round((x - pitch / 2) / pitch)) > 1e-6:
                        raise ValueError(f"{cell.name}.{name}: off-track access")
                    if not (0 <= x <= cell.width and 0 <= y <= cell.height):
                        raise ValueError(f"{cell.name}.{name}: access outside boundary")
                legal = pin["access"] if name in RAILS else legal_pin_access(cell, name, self.template)
                if not legal:
                    raise ValueError(f"{cell.name}.{name}: no access clears M2/V1/free-track constraints")
                cell.selected_access[name] = legal[0]


def mock_library(template_path: str | Path | None = None) -> Library:
    """Make DRC-legal isolated M1 terminals and three abutting power rails.

    This fixture tests metal routing, not cell electronics, LVS, or well continuity.
    Pin columns are distinct so each terminal has an unobstructed vertical escape.
    """
    template_path = Path(template_path or CELLS_DIR / "template.provisional.json")
    t = json.loads(template_path.read_text())
    p, h = t["grid"], t["height"]
    pad = max(3.4, t["rules"]["V1"] + 2 * t["rules"]["V1_enc_M1"])
    rows = t.get("pin_rows", [h / 2])
    definitions = {"INV": ["A", "Y"], "NAND": ["A", "B", "Y"],
                   "NOR": ["A", "B", "Y"], "NANY": ["A", "B", "Y"],
                   "BUF": ["A", "Y"], "TIEP": ["Y"], "TIEZ": ["Y"],
                   "TIEN": ["Y"], "FILL": []}
    cells = {}
    for name, signals in definitions.items():
        width = max(6, len(signals) * 3) * p
        pins = {}
        for i, pin in enumerate(signals):
            x, y = (3 * i + 1.5) * p, rows[i % len(rows)]
            if name in ("TIEP", "TIEZ", "TIEN"):
                rail = {"TIEP": "VDD", "TIEZ": "VMID", "TIEN": "VSS"}[name]
                y = sum(t["rails"][rail])/2
            pins[pin] = {"dir": "output" if pin == "Y" else "input", "layer": "M1",
                         "rects": [[x-pad/2, y-pad/2, x+pad/2, y+pad/2]], "access": [[x, y]]}
        for rail, (y0, y1) in t["rails"].items():
            pins[rail] = {"dir": "power", "layer": "M1", "rects": [[0, y0, width, y1]],
                          "access": [[p/2, (y0+y1)/2]]}
        cells[name] = Cell(name, width, h, pins,
                           {"M1": [r for pin in pins.values() for r in pin["rects"]], "M2": []})
    lib = Library(t, cells, f"mock:{template_path}", True)
    lib.validate()
    return lib
