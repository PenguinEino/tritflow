"""Map ternary expressions onto TR-1um cells and bound every input-pin fanout."""

from __future__ import annotations

from collections import Counter, defaultdict

from tritflow.hdl.ir import Design
from tritflow.netlist import GateNetlist, Instance
from .optimize import optimize, primitive_inputs
from .simulate import CELL_INPUTS, check_equivalence, ordered_instances


def fanouts(net: GateNetlist):
    """Count physical cell input pins (an external output load is unspecified)."""
    return Counter(inst.pins[pin] for inst in net.instances for pin in CELL_INPUTS[inst.cell])


class SynthesizedNetlist(GateNetlist):
    """Shared GateNetlist format plus notebook-oriented synthesis reporting."""

    def schematic(self, **options):
        """Draw mapped hierarchy; optional trit values/wire C use the public renderer.

        ``expand='*'`` exposes every cell. ``inputs`` gives settled scalar
        trits; ``parasitics`` accepts PNR's public net-parasitics report. This
        display stage does not alter synthesis or invoke physical tools.
        """
        from tritflow.schematic import draw
        return draw(self, **options)

    def report(self) -> dict:
        """Count mapped cells and longest gate chain, retaining source scopes.

        Hierarchy counts are exclusive to each module/generate scope. Depth
        counts cell stages, including inserted BUFs and TIE drivers; it is not
        an electrical delay estimate. The report includes the equivalence mode
        and vector count recorded by ``synthesize``.
        """
        ordered = ordered_instances(self)
        depths = {p.name: 0 for p in self.ports if p.dir == "input"}
        hierarchy = defaultdict(Counter)
        for inst in ordered:
            depths[inst.pins["Y"]] = 1 + max((depths[inst.pins[p]] for p in CELL_INPUTS[inst.cell]), default=0)
            hierarchy[inst.hier or "<top>"][inst.cell] += 1
        counts = Counter(inst.cell for inst in ordered)
        return {
            "top": self.top, "cells": dict(sorted(counts.items())), "total_cells": len(ordered),
            "logic_depth": max((depths[p.name] for p in self.ports if p.dir == "output"), default=0),
            "hierarchy": {key: dict(sorted(count.items())) for key, count in sorted(hierarchy.items())},
            "max_fanout": max(fanouts(self).values(), default=0),
            "fanout_limit": getattr(self, "fanout_limit", None),
            "equivalence": getattr(self, "equivalence", None),
        }


class Mapper:
    def __init__(self, design):
        self.design = design
        self.net = SynthesizedNetlist(design.top, list(design.ports))
        self.used_nets = {p.name for p in design.ports}
        self.used_names = set()
        self.nets, self.inverse = {}, {}
        self.preferred = {}
        for name, node in design.outputs.items():
            if node.op != "input":
                self.preferred.setdefault(node, name)

    def unique(self, base, used):
        result, index = base, 0
        while result in used:
            index += 1
            result = f"{base}_{index}"
        used.add(result)
        return result

    def emit(self, cell, args, source, output=None, name=None):
        if output is None:
            output = self.unique(f"_n{len(self.net.instances)}", self.used_nets)
        inst_name = self.unique(name or f"g{len(self.net.instances)}", self.used_names)
        pins = dict(zip(CELL_INPUTS[cell], args))
        pins["Y"] = output
        self.net.instances.append(Instance(inst_name, cell, pins, source.hier))
        return output

    def negative_lattice(self, node, output=None, source=None):
        if node not in self.inverse:
            self.inverse[node] = self.emit("NAND" if node.op == "min" else "NOR",
                                           [self.map(arg) for arg in node.args], source or node, output)
        return self.inverse[node]

    def map(self, node):
        if node in self.nets:
            return self.nets[node]
        output = self.preferred.get(node)
        if node.op == "input":
            result = node.name
        elif node.primitive:
            result = self.emit(node.primitive, [self.map(arg) for arg in primitive_inputs(node)],
                               node, output, node.name)
        elif node.op == "const":
            result = self.emit({-1: "TIEN", 0: "TIEZ", 1: "TIEP"}[node.value], [], node, output)
        elif node.op == "neg" and node.args[0].op in {"min", "max"} and not node.args[0].primitive:
            result = self.negative_lattice(node.args[0], output, node)
        elif node.op in {"min", "max"}:
            result = self.emit("INV", [self.negative_lattice(node)], node, output)
        else:
            result = self.emit("INV" if node.op == "neg" else "NANY",
                               [self.map(arg) for arg in node.args], node, output)
        self.nets[node] = result
        return result

    def finish(self):
        for name, node in self.design.outputs.items():
            actual = self.map(node)
            if actual != name:
                self.emit("BUF", [actual], node, name)
        return self.net


def buffer_fanout(net: GateNetlist, limit: int) -> None:
    """Insert balanced BUF trees, counting repeated gate pins separately.

    Outputs remain on the original driven net so their public names are stable.
    External load capacitance is a simulation concern; no external pin load is
    invented here.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 2:
        raise ValueError("fanout_limit must be an integer >= 2")
    consumers = defaultdict(list)
    for inst in net.instances:
        for pin in CELL_INPUTS[inst.cell]:
            consumers[inst.pins[pin]].append((inst, pin))
    used_nets = net.nets()
    used_names = {inst.name for inst in net.instances}
    index = 0

    def branch(signal, loads):
        nonlocal index
        if len(loads) <= limit:
            for inst, pin in loads:
                inst.pins[pin] = signal
            return
        # At most 'limit' children per node, distributing loads evenly.
        size = (len(loads) + limit - 1) // limit
        for start in range(0, len(loads), size):
            while f"_buf{index}" in used_names or f"_bufnet{index}" in used_nets:
                index += 1
            name, output = f"_buf{index}", f"_bufnet{index}"
            index += 1
            used_names.add(name)
            used_nets.add(output)
            group = loads[start:start + size]
            net.instances.append(Instance(name, "BUF", {"A": signal, "Y": output}, group[0][0].hier))
            branch(output, group)

    for signal, loads in consumers.items():
        if len(loads) > limit:
            branch(signal, loads)


def synthesize(design: Design, *, fanout_limit: int = 4, optimize_logic: bool = True,
               verify: bool = True, seed: int = 0) -> SynthesizedNetlist:
    """Simplify, assign cells, buffer fanout and verify the circuit's truth values.

    ``design`` is the elaborated result of ``tritflow.hdl.load``. Negated min/max
    operations fuse into NAND/NOR; positive min/max add an output INV. NANY maps
    directly and constants become supply TIE cells. Explicit live gate instances
    preserve cell identity and source hierarchy, even with constant inputs.

    Integer arithmetic and procedural selections lower to the cell basis before
    local rewriting. Source simulation retains independent integer/table rules.

    ``fanout_limit`` counts cell input pins, including repeated pins on one
    gate; it must be >=2. ``optimize_logic=False`` skips expression rewriting
    while retaining required operator lowering. ``verify=True`` checks the mapped
    result against the unoptimized source, exhaustively for <=12 inputs and with 100,000 vectors
    otherwise; ``seed`` controls that random sample. ``verify=False`` explicitly
    skips this check and leaves report equivalence evidence unset.
    """
    if not isinstance(fanout_limit, int) or isinstance(fanout_limit, bool) or fanout_limit < 2:
        raise ValueError("fanout_limit must be an integer >= 2")
    from .lower import lower
    mapped = Mapper(optimize(design) if optimize_logic else lower(design)).finish()
    buffer_fanout(mapped, fanout_limit)
    mapped.fanout_limit = fanout_limit
    mapped.equivalence = check_equivalence(design, mapped, seed=seed) if verify else None
    return mapped
