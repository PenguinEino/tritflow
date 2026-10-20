"""Thin notebook chain over the HDL, synthesis, P&R, extraction and SIM APIs.

    from tritflow import flow
    d = flow.load("examples/adder.tv", "adder", {"N": 4})
    net = d.synthesize(name="adder4")
    lay = net.place_and_route(output_dir="build/adder4")
    assert lay.drc()["clean"] and lay.lvs()["matched"]
    post = lay.extract().simulate(vectors, load=100e-15)

The wrapper uses the published physical library, never an automatic mock
fallback. Failed checks remain failed; extraction refuses an LVS mismatch.
Values in input vectors are trits, loads are farads, and all times are seconds.
Full simulation dictionaries and the underlying stream artifacts remain public.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
import shutil
import os
import json

from tritflow import CELLS_DIR, PDK_ROOT
from tritflow import hdl, synth


@dataclass(frozen=True)
class Settings:
    """Locations shared by every stage; defaults match the stream contract."""

    cells: Path = CELLS_DIR
    pdk: Path = PDK_ROOT
    klayout: Path = field(default_factory=lambda: Path(os.environ.get("KLAYOUT_BINARY")
                                                     or shutil.which("klayout") or Path.home()/"bin/klayout/klayout"))


@dataclass
class Circuit:
    """Elaborated source and the physical-tool settings for later stages."""

    design: hdl.Design
    settings: Settings

    def truth_table(self, **kwargs):
        """Delegate the complete small-circuit truth table to the HDL simulator."""
        return self.design.truth_table(**kwargs)

    def synthesize(self, *, name: str | None = None, **kwargs) -> Netlist:
        """Map/verify source logic; optional name selects the physical top name."""
        mapped = synth.synthesize(self.design, **kwargs)
        if any(i.cell == "TDFF" for i in mapped.instances):
            from tritflow.seq.flow import Netlist as SequentialNetlist
            net = SequentialNetlist(name or mapped.top, mapped.ports, mapped.instances)
        else:
            net = Netlist(name or mapped.top, mapped.ports, mapped.instances)
        net.settings = self.settings
        net.fanout_limit, net.equivalence = mapped.fanout_limit, mapped.equivalence
        return net


def _settings(cells, pdk, klayout_binary):
    defaults = Settings()
    return Settings(Path(cells).expanduser().resolve(), Path(pdk).expanduser().resolve(),
                    Path(klayout_binary or defaults.klayout).expanduser().resolve())


def load(path, top=None, params=None, *, cells=CELLS_DIR, pdk=PDK_ROOT,
         klayout_binary=None) -> Circuit:
    """Load source using positional or keyword top/params, then carry settings."""
    return Circuit(hdl.load(path, top=top, params=params), _settings(cells, pdk, klayout_binary))


def loads(source, top=None, params=None, *, filename="<notebook>", cells=CELLS_DIR,
          pdk=PDK_ROOT, klayout_binary=None) -> Circuit:
    """Use editable notebook source with the same downstream chain as load()."""
    return Circuit(hdl.loads(source, top=top, params=params, filename=filename),
                   _settings(cells, pdk, klayout_binary))


def _simulate(net, subckts, settings, vectors, load, options):
    from tritflow.sim import simulate

    inputs = [p.name for p in net.ports if p.dir == "input"]
    outputs = [p.name for p in net.ports if p.dir == "output"]

    def expected(vector):
        result = synth.evaluate_netlist(net, dict(zip(inputs, vector, strict=True)))
        return {name: int(value) for name, value in result.items()}

    options = {"pdk": settings.pdk, **options}
    reference = options.pop("expected", expected)
    return simulate(subckts, net.top, inputs, outputs, vectors, reference, loads_f=load, **options)


class Netlist(synth.SynthesizedNetlist):
    """GateNetlist-compatible synthesized circuit with physical-flow methods."""

    settings: Settings

    def place_and_route(self, *, output_dir=None, **kwargs) -> Layout:
        """Use the real cell library and the public PNR flow, including its checks."""
        from tritflow.pnr import Library, place_and_route

        library = Library.load(self.settings.cells)
        options = {"pdk_root": self.settings.pdk, "klayout_binary": self.settings.klayout, **kwargs}
        result = place_and_route(self, library, output_dir=output_dir, **options)
        return Layout(result, self, self.settings)

    def simulate(self, vectors, *, load=10e-15, **kwargs):
        """Run pre-layout cell SPICE with the same stimuli API as extraction."""
        from tritflow.sim import gate_spice

        text = gate_spice(self, (self.settings.cells/"out/all.spice").read_text())
        return _simulate(self, text, self.settings, vectors, load, kwargs)


@dataclass
class Layout:
    """PNR artifacts and their gate reference; methods return native reports."""

    result: object
    netlist: Netlist
    settings: Settings
    _lvs_report: dict | None = field(default=None, repr=False)
    _lvs_fingerprint: str | None = field(default=None, repr=False)
    _lvs_outputs: str | None = field(default=None, repr=False)

    @property
    def gds_path(self):
        return self.result.gds_path

    @property
    def data(self):
        return self.result.data

    @property
    def stats(self):
        return self.result.stats

    def drc(self, **kwargs):
        """Run the official drawing-layer deck; inspect the returned clean flag."""
        from tritflow.pnr import pdk_drc

        return pdk_drc(self.gds_path, self.netlist.top,
                       **{"pdk_root": self.settings.pdk, "binary": self.settings.klayout, **kwargs})

    def signoff(self, *, output_dir=None, **kwargs):
        """Delegate unwaived mask/MPW checks; inspect clean/submission_ready.

        Drawing DRC/LVS alone do not establish manufacturing readiness. PNR
        owns the report cache and validates all consumed and generated files.
        """
        from tritflow.pnr import Library

        return self.result.signoff(netlist=self.netlist, library=Library.load(self.settings.cells),
            output_dir=output_dir,
            **{"pdk_root": self.settings.pdk, "klayout_binary": self.settings.klayout, **kwargs})

    def _fingerprint(self):
        digest = sha256(self.gds_path.read_bytes())
        digest.update(self.netlist.to_json().encode())
        # PNR's unloaded-pad proof consumes the actual PNR record and physical
        # abstracts as well as the GDS. Mutating those must invalidate the proof.
        digest.update(json.dumps(self.data, sort_keys=True).encode())
        views = [self.settings.cells/"template.json", self.settings.cells/"out/all.spice",
                 *self.settings.cells.glob("out/*.json"),
                 *self.settings.cells.glob("out/**/*.abstract.json")]
        decks = [p for p in (self.settings.pdk/"libs.tech/klayout/tech/lvs").rglob("*") if p.is_file()]
        for root, paths in ((self.settings.cells, views), (self.settings.pdk, decks)):
            for path in sorted(set(paths)):
                digest.update(str(path.relative_to(root)).encode()+b"\0")
                digest.update(path.read_bytes())
        return digest.hexdigest()

    def lvs(self, *, output_dir=None, **kwargs):
        """Strict device/port LVS, including PNR's isolated unused-input proof.

        An unused HDL input is valid only when its actual labeled M2 pad is
        physically present and isolated. A missing label never becomes PASS
        merely because that input has no device load.
        """
        from tritflow.pnr import Library, strict_lvs

        before = self._fingerprint()
        report = strict_lvs(self.gds_path, self.data, self.netlist,
                            Library.load(self.settings.cells),
                            output_dir or self.gds_path.parent/"lvs",
                            (self.settings.cells/"out/all.spice").read_text(),
                            **{"pdk": self.settings.pdk, "executable": self.settings.klayout, **kwargs})
        self._lvs_report = report
        self._lvs_fingerprint = before if not kwargs and before == self._fingerprint() else None
        self._lvs_outputs = self._output_fingerprint(report)
        return report

    @staticmethod
    def _output_fingerprint(report):
        digest = sha256()
        for key in ("extracted", "report"):
            path = Path(report[key]) if report.get(key) else None
            if path is None or not path.is_file():
                return None
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def extract(self, *, wire_c: bool = True, **kwargs) -> Extracted:
        """Require matched LVS, then optionally append actual-GDS lumped wire C.

        The recent in-memory LVS result is reused only while its inputs and
        artifact files remain unchanged. No wire resistance or calibrated PEX
        is invented; capacitance assumptions come from the extraction stream.
        """
        from tritflow.extract import append_wire_capacitance, gds_wire_capacitance

        report = self._lvs_report
        if (kwargs or report is None or self._lvs_fingerprint != self._fingerprint()
                or self._lvs_outputs != self._output_fingerprint(report)):
            report = self.lvs(**kwargs)
        if report["matched"] is not True:
            raise RuntimeError(f"Cannot simulate unmatched layout: {report['errors']}")
        text = Path(report["extracted"]).read_text()
        caps = None
        if wire_c:
            caps = gds_wire_capacitance(self.gds_path, report["report"], top=self.netlist.top)
            text = append_wire_capacitance(text, self.netlist.top, caps)
        return Extracted(text, self.netlist, self.settings, report, caps)


@dataclass
class Extracted:
    """Extracted subcircuits, LVS evidence and optional estimated wire capacitance."""

    spice: str
    netlist: Netlist
    settings: Settings
    report: dict
    capacitance: dict | None

    def simulate(self, vectors, *, load=10e-15, **kwargs):
        """Delegate post-layout transients; return waveforms and native measurements."""
        return _simulate(self.netlist, self.spice, self.settings, vectors, load, kwargs)


def load_layout(net: Netlist, directory) -> Layout:
    """Reopen saved PNR artifacts for notebook caches; LVS is rerun on demand.

    This restores the public PnrResult dataclass. It does not treat stored DRC
    or LVS flags as new verification evidence. The notebook validates its cache
    fingerprint before choosing to reuse these artifacts.
    """
    import json
    from tritflow.pnr import PnrResult

    directory = Path(directory)
    data = json.loads((directory/f"{net.top}.pnr.json").read_text())
    if data["top"] != net.top or data.get("library", {}).get("mock"):
        raise ValueError("cached layout must match this top and use a real library")
    result = PnrResult(directory/f"{net.top}.gds", directory/f"{net.top}.pnr.json", data["stats"], data)
    if any(i.cell == "TDFF" for i in net.instances):
        from tritflow.seq.flow import Layout as SequentialLayout
        return SequentialLayout(result, net, net.settings)
    return Layout(result, net, net.settings)


__all__ = ["load", "loads", "load_layout", "Circuit", "Netlist", "Layout", "Extracted", "Settings"]
