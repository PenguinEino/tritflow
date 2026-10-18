"""Strict device LVS plus physical evidence for unloaded boundary input pads."""
from __future__ import annotations

import copy
from pathlib import Path
import re

import klayout.db as db

from .gds import box
from .verify import connectivity, read_regions


def _isolated_inputs(gds, data, netlist, library):
    """Prove unloaded input pads from actual metal/vias and top-level labels."""
    used = {net for inst in netlist.instances for net in inst.pins.values()}
    unloaded = {p.name for p in netlist.ports if p.dir == "input" and p.name not in used}
    if not unloaded:
        return []
    layout, regions = read_regions(gds, netlist.top, library.template)
    top = layout.cell(netlist.top)
    labels = [shape.text for shape in top.shapes(layout.layer(*library.template["layers"]["TXM2"])).each()
              if shape.is_text()]
    islands = list(regions["M2"].each())
    proven = []
    for name in sorted(unloaded):
        pads = [p for p in data["pins"] if p["name"] == name and p["layer"] == "M2"]
        if len(pads) != 1:
            continue
        rectangle = box(pads[0]["rect"])
        island = [p for p in islands if not (db.Region(p) & db.Region(rectangle)).is_empty()]
        if (len(island) == 1 and (db.Region(island[0]) ^ db.Region(rectangle)).is_empty()
                and (regions["V1"] & db.Region(rectangle)).is_empty()
                and any(t.string == name and rectangle.contains(t.trans.disp) for t in labels)):
            proven.append(name)
    # A disconnected pad must also be isolated from every other expected net.
    if proven and not connectivity(gds, data, netlist, library)["clean"]:
        return []
    return proven


def strict_lvs(gds, data, netlist, library, directory, cell_subckts, **extraction_options):
    """Compare devices and all active ports; physically verify unloaded inputs.

    The PDK removes standalone metal nets during device extraction. Exclude an
    unused input formal from the device reference only after proving that its
    actual labeled M2 island is exactly its pad and has no V1. Restore those
    formals in extracted SPICE after native LVS passes. Missing/mislabeled
    loaded ports and every native device/circuit mismatch still fail.
    """
    from tritflow.extract import extract_layout
    from tritflow.sim.spice import gate_spice, subcircuits, logical_spice_names
    from tritflow.synth.writers import spice_names
    proven = _isolated_inputs(gds, data, netlist, library)
    reference = copy.deepcopy(netlist)
    reference.ports = [p for p in reference.ports if p.name not in proven]
    report = extract_layout(gds, netlist.top, directory,
                            gate_netlist=reference, cell_subckts=cell_subckts, **extraction_options)
    if not report["matched"] or not proven:
        return report
    path = Path(report["extracted"])
    raw = path.read_text()
    safe_top = spice_names([netlist.top])[netlist.top]
    definition = subcircuits(raw).get(safe_top.lower())
    if definition is None:
        return report
    decoded = logical_spice_names(raw)
    actual = {decoded.get(p,p).lower() for p in definition["pins"]}
    expected = {p.name.lower() for p in netlist.ports} | {"vdd", "vmid", "vss"}
    if actual | {p.lower() for p in proven} != expected:
        report.update(matched=False, errors=["Full physical top-level port set differs after isolated-input proof"])
        return report
    path.with_name(f"{netlist.top}.before_unused_inputs.ext.spice").write_text(raw)
    full_reference = gate_spice(netlist, cell_subckts)
    (Path(directory)/"full_port_reference.spice").write_text(full_reference)
    encoding = {logical:encoded for encoded,logical in logical_spice_names(full_reference).items()}
    signature = re.compile(r"(?im)^(\s*\.subckt\s+"+re.escape(safe_top)+r"\b[^\n]*)")
    restored = signature.sub(lambda m: m[1]+" "+" ".join(encoding.get(p,p) for p in proven), raw, count=1)
    annotations = "\n".join(f"* net {encoding[p]} = {p}" for p in proven if p in encoding)
    path.write_text(annotations+"\n"+restored)
    report.update(unused_input_formals_restored=proven,
        unloaded_input_proof="exact isolated M2 pad, no V1, actual TXM2 label, drawn connectivity; native LVS on all devices and loaded ports")
    return report
