"""Opt-in sequential counterpart of the existing notebook flow wrappers."""
from dataclasses import dataclass
from pathlib import Path

from tritflow.flow import Layout as CombinationalLayout
from tritflow.seq.synthesis import SequentialNetlist
from .library import EXTENSION, load_library, subckts


class Netlist(SequentialNetlist):
    """Use the extension only for a design with explicit TDFF state boundaries."""
    def place_and_route(self, *, output_dir=None, extension=EXTENSION, **kwargs):
        from tritflow.pnr import place_and_route
        library = load_library(self.settings.cells, extension)
        options = {'pdk_root':self.settings.pdk, 'klayout_binary':self.settings.klayout,
                   'sequential_rails':True, **kwargs}
        result = place_and_route(self, library, output_dir=output_dir, **options)
        return Layout(result, self, self.settings, extension=Path(extension))

    def simulate(self, vectors, *, initial, load=10e-15, **kwargs):
        from .spice import simulate
        from .writers import spice
        return simulate(self, spice(self) + '\n' + subckts(self.settings.cells),
                        vectors, initial=initial, load=load, pdk=self.settings.pdk, **kwargs)


@dataclass
class Layout(CombinationalLayout):
    extension: Path = EXTENSION

    def lvs(self, *, output_dir=None, **kwargs):
        from .physical import lvs
        self._lvs_report = lvs(self.gds_path, self.netlist,
            subckts(self.settings.cells, self.extension), output_dir or self.gds_path.parent/'lvs',
            **{'pdk':self.settings.pdk, 'executable':self.settings.klayout, **kwargs})
        return self._lvs_report

    def extract(self, *, wire_c=True, **kwargs):
        from tritflow.extract import gds_wire_capacitance, append_wire_capacitance
        # Always rerun strict LVS: no stale-result cache for the extension.
        report = self.lvs(**kwargs)
        if not report['matched']:
            raise ValueError(f"Cannot simulate unmatched sequential layout: {report['errors']}")
        text = Path(report['extracted']).read_text()
        caps = None
        if wire_c:
            caps = gds_wire_capacitance(self.gds_path, report['report'], top=self.netlist.top)
            text = append_wire_capacitance(text, self.netlist.top, caps)
        return Extracted(text, self.netlist, self.settings, report, caps)


@dataclass
class Extracted:
    spice: str
    netlist: Netlist
    settings: object
    report: dict
    capacitance: dict | None

    def simulate(self, vectors, *, initial, load=10e-15, **kwargs):
        from .spice import simulate
        return simulate(self.netlist, self.spice, vectors, initial=initial,
                        load=load, pdk=self.settings.pdk, lvs_report=self.report['report'], **kwargs)
