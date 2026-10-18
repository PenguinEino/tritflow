"""Portable timing reports; every listed path has a realizable endpoint pattern."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from html import escape
import json
from pathlib import Path


@dataclass(frozen=True)
class PathStage:
    instance: str
    cell: str
    input_pin: str
    input_net: str
    output_net: str
    input_transition: tuple[int, int]
    output_transition: tuple[int, int]
    from_inputs: dict[str, int]
    to_inputs: dict[str, int]
    arc_id: str
    delay_s: float
    arrival_s: float
    load_f: float
    input_transition_s: float

    @property
    def transition(self):
        return f"{self.output_transition[0]:+d}→{self.output_transition[1]:+d}"


@dataclass
class TimingReport:
    """Seconds throughout. Arrival is the maximum modeled settling per output.

    ``patterns[output]`` gives complete before/after primary-input assignments
    that satisfy every cell condition along ``paths[output]``. This proves
    settled logical sensitization, not freedom from analog/skew hazards.
    ``transition_arrival`` includes local unchanged-output hazard recovery.
    """

    top: str
    arrival: dict[str, float]
    transition_arrival: dict[str, dict[str, float]]
    paths: dict[str, list[PathStage]]
    patterns: dict[str, dict]
    loads: dict[str, dict]
    assumptions: list[str]
    warnings: list[str]
    provenance: dict = field(default_factory=dict)
    statistics: dict = field(default_factory=dict)

    @property
    def critical_output(self):
        return max(self.arrival, key=self.arrival.get, default=None)

    @property
    def critical_path(self):
        return self.paths.get(self.critical_output, [])

    @property
    def sensitizing_pattern(self):
        return self.patterns.get(self.critical_output)

    def to_dict(self):
        return asdict(self)

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, allow_nan=False) + "\n")

    def to_html(self, path=None, *, include_plotlyjs="cdn"):
        """Return a notebook-ready HTML fragment, optionally write it to disk."""
        from .plot import timing_figure
        rows = "".join(f"<tr><td>{escape(name)}</td><td>{value*1e9:.3f}</td></tr>"
                       for name, value in self.arrival.items())
        notes = "".join(f"<li>{escape(note)}</li>" for note in self.assumptions + self.warnings)
        result = (f"<h3>{escape(self.top)}: ternary settling estimate</h3>"
                  "<table><tr><th>Output</th><th>Settling (ns)</th></tr>" + rows + "</table>"
                  + timing_figure(self).to_html(full_html=False, include_plotlyjs=include_plotlyjs)
                  + "<p>Sensitizing primary-input endpoints:</p><pre>"
                  + escape(json.dumps(self.sensitizing_pattern, indent=2)) + "</pre><ul>" + notes + "</ul>")
        if path is not None: Path(path).write_text(result)
        return result
