"""Independent checks of flattened *drawn* metal, not the router's graph."""
from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import klayout.db as db

from tritflow import PDK_ROOT, RAILS
from .placement import pin_location


class PhysicalVerificationError(RuntimeError):
    """A geometry check or PDK report contains violations."""


def read_regions(path, top_name, template):
    layout = db.Layout()
    layout.read(str(path))
    top = layout.cell(top_name)
    regions = {name: db.Region(top.begin_shapes_rec(layout.layer(*template["layers"][name]))).merged()
               for name in ("M1", "V1", "M2")}
    return layout, regions


class Index:
    """Spatial bins keep via/terminal-to-island queries local on large layouts."""

    def __init__(self, polygons, unit):
        self.polygons, self.unit = polygons, unit
        self.bins = defaultdict(set)
        for index, polygon in enumerate(polygons):
            for key in self.keys(polygon.bbox()):
                self.bins[key].add(index)

    def keys(self, b):
        for x in range(b.left//self.unit, b.right//self.unit+1):
            for y in range(b.bottom//self.unit, b.top//self.unit+1):
                yield x, y

    def query(self, b):
        result = set()
        for key in self.keys(b):
            result.update(self.bins.get(key, ()))
        return [i for i in result if not (db.Region(self.polygons[i]) & db.Region(b)).is_empty()]


def connectivity(path, data, netlist, library):
    """Union physical metal islands through V1, then compare all expected nets.

    Every signal/power terminal and every drawn route must belong to exactly one
    expected net component. Transistors/resistors are intentionally not treated
    as shorts: this is the metal interconnect check before device-level LVS.
    """
    layout, regions = read_regions(path, data["top"], library.template)
    unit = round(48/layout.dbu)
    polys = {name: list(regions[name].each()) for name in regions}
    indices = {name: Index(polys[name], unit) for name in polys}
    offsets, count = {}, 0
    for layer in ("M1", "M2", "V1"):
        offsets[layer] = count
        count += len(polys[layer])
    parent = list(range(count))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a
    for i, polygon in enumerate(polys["V1"]):
        for metal in ("M1", "M2"):
            for j in indices[metal].query(polygon.bbox()):
                # Actual polygon overlap, not merely touching bounding boxes.
                if not (db.Region(polygon) & db.Region(polys[metal][j])).is_empty():
                    union(offsets["V1"]+i, offsets[metal]+j)
    aliases = {inst.pins["Y"]: {"TIEP": "VDD", "TIEZ": "VMID", "TIEN": "VSS"}[inst.cell]
               for inst in netlist.instances if inst.cell in ("TIEP", "TIEZ", "TIEN")}
    tags = defaultdict(set)
    terminals = defaultdict(set)
    errors = []
    def tag(net, layer, x, y, terminal=False):
        ix, iy = round(x/layout.dbu), round(y/layout.dbu)
        hits = indices[layer].query(db.Box(ix-1, iy-1, ix+1, iy+1))
        if not hits:
            errors.append(f"{net}: no drawn {layer} at ({x}, {y})")
        for hit in hits:
            component = find(offsets[layer]+hit)
            tags[component].add(net)
            if terminal:
                terminals[net].add(component)
    by_name = {inst.name: inst for inst in netlist.instances}
    for pl in data["placements"]:
        cell, inst = library.cells[pl["cell"]], by_name[pl["inst"]]
        for pin, net in inst.pins.items():
            tag(net, "M1", *pin_location(cell, pin, pl), terminal=True)
        for rail in RAILS:
            # Verify cell rail continuity, not just the extra drawn row extensions.
            band = library.template["rails"][rail]
            tag(rail, "M1", pl["x"]+cell.width/2, pl["y"]+sum(band)/2, terminal=True)
    for pin in data["pins"]+data["power"]["pins"]:
        x0, y0, x1, y1 = pin["rect"]
        tag(pin["name"], "M2", (x0+x1)/2, (y0+y1)/2, terminal=True)
    for wire in data["wires"]+data["power"]["rails"]+data["power"]["straps"]:
        (x0, y0), (x1, y1) = wire["points"]
        tag(wire["net"], wire["layer"], (x0+x1)/2, (y0+y1)/2, terminal=True)
    for via in data["vias"]+data["power"]["vias"]:
        tag(via["net"], "V1", via["x"], via["y"], terminal=True)
    for component, nets in tags.items():
        # A direct-metal TIE may intentionally join its logical output to a
        # supply. A resistor-based TIE keeps separate metal islands; do not
        # demand a metal short across its resistor when checking for opens.
        if len({aliases.get(net, net) for net in nets}) > 1:
            errors.append(f"Short: {', '.join(sorted(nets))}")
    for net, components in terminals.items():
        if len(components) > 1:
            errors.append(f"Open: {net} has {len(components)} metal components")
    return {"clean": not errors, "errors": errors, "checked_nets": len(terminals),
            "metal_islands": count, "power_aliases": aliases, "method": "flattened GDS metal islands + via union-find"}


def routing_drc(path, data, library):
    """Check drawn metal widths, spaces, wide-metal space, V1 and enclosures."""
    layout, regions = read_regions(path, data["top"], library.template)
    rules, dbu = library.template["rules"], layout.dbu
    errors = {}
    for metal in ("M1", "M2"):
        region = regions[metal]
        width = region.width_check(round(rules[f"{metal}_w"]/dbu))
        space = region.space_check(round(rules[f"{metal}_s"]/dbu))
        if not width.is_empty():
            errors[f"{metal}_width"] = width.size()
        if not space.is_empty():
            errors[f"{metal}_spacing"] = space.size()
        # Same morphology as the PDK drawing-layer maximum-width check.
        wide = region.sized(-round(22.5/dbu)).sized(round(22.5/dbu))
        if not wide.is_empty():
            errors[f"{metal}_max_width"] = wide.size()
    # The PDK's M1(W) spacing is 2.0 µm (normal M1 is 1.4 µm).
    wide_m1 = regions["M1"].sized(-round(5/dbu)+1).sized(round(5/dbu)-1)
    wide_pairs = regions["M1"].space_check(round(2/dbu))
    if not wide_pairs.is_empty() and not wide_m1.is_empty():
        hits = wide_pairs.polygons().interacting(wide_m1)
        if not hits.is_empty():
            errors["M1_wide_spacing"] = hits.size()
    vias = regions["V1"]
    size = round(rules["V1"]/dbu)
    bad = sum(1 for polygon in vias.each() if not polygon.is_box() or
              polygon.bbox().width() != size or polygon.bbox().height() != size)
    if bad:
        errors["V1_cut"] = bad
    space = vias.space_check(round(1.5/dbu))
    if not space.is_empty():
        errors["V1_spacing"] = space.size()
    for metal in ("M1", "M2"):
        missing = vias.sized(round(rules[f"V1_enc_{metal}"]/dbu))-regions[metal]
        if not missing.is_empty():
            errors[f"V1_enclosure_{metal}"] = missing.size()
    return {"clean": not errors, "errors": errors,
            "scope": "flattened M1/V1/M2; device rules are checked by the PDK deck"}


def pdk_drc(gds_path, top, report_path=None, *, pdk_root=PDK_ROOT, binary=None, timeout=180):
    """Run the unmodified drawing-layer deck and parse its actual item count.

    KLayout exit status alone is insufficient: a successful run can report DRC
    errors. Missing executables/decks raise errors rather than reporting a pass.
    """
    binary = Path(binary or Path.home()/"bin/klayout/klayout")
    deck = Path(pdk_root)/"libs.tech/klayout/tech/drc/run.drc"
    gds_path = Path(gds_path).resolve()
    report = Path(report_path or gds_path.with_suffix(".drc.lyrdb")).resolve()
    if not binary.is_file() or not deck.is_file():
        raise FileNotFoundError(f"PDK DRC executable/deck missing: {binary}, {deck}")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.unlink(missing_ok=True)
    command = [str(binary), "-b", "-r", str(deck), "-rd", f"input={gds_path}",
               "-rd", f"top_cell={top}", "-rd", f"report={report}"]
    run = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    log = report.with_suffix(".log")
    log.write_text(run.stdout+run.stderr)
    if run.returncode or not report.exists():
        raise PhysicalVerificationError(f"PDK DRC failed to execute; see {log}")
    root = ET.parse(report).getroot()
    categories = defaultdict(int)
    for item in root.findall("./items/item"):
        categories[item.findtext("category", "unknown")] += 1
    count = sum(categories.values())
    return {"clean": count == 0, "violations": count, "categories": dict(categories),
            "report_path": str(report), "log_path": str(log), "deck": str(deck),
            "command": command}
