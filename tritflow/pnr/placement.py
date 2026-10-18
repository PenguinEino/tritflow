"""Signal-flow placement followed by deterministic HPWL annealing."""
from __future__ import annotations

import math
import random
from collections import defaultdict

from tritflow import RAILS
from .library import Library


def validate_netlist(netlist, library: Library) -> list:
    """Check single drivers and combinational acyclicity; return topological order."""
    names, drivers, dependencies = set(), {}, {}
    ports = set()
    for port in netlist.ports:
        if port.name in ports or port.name in RAILS or port.dir not in ("input", "output"):
            raise ValueError(f"Invalid or duplicate port {port.name}")
        ports.add(port.name)
        if port.dir == "input":
            drivers[port.name] = None
    by_name = {}
    for inst in netlist.instances:
        if inst.name in names:
            raise ValueError(f"Duplicate instance {inst.name}")
        names.add(inst.name)
        by_name[inst.name] = inst
        cell = library.cells[inst.cell]
        required = {p for p in cell.pins if p not in RAILS}
        if set(inst.pins) != required:
            raise ValueError(f"{inst.name}: expected signal pins {sorted(required)}")
        for pin, net in inst.pins.items():
            if net in RAILS:
                raise ValueError("Power names are reserved; use TIE cells for constants")
            if cell.pins[pin]["dir"] == "output":
                if net in drivers:
                    raise ValueError(f"Multiple drivers on {net}")
                drivers[net] = inst.name
    for inst in netlist.instances:
        deps = set()
        for pin, net in inst.pins.items():
            if net not in drivers:
                raise ValueError(f"Undriven net {net}")
            if library.cells[inst.cell].pins[pin]["dir"] == "input" and drivers[net] is not None:
                deps.add(drivers[net])
        dependencies[inst.name] = deps
    for port in netlist.ports:
        if port.name not in drivers:
            raise ValueError(f"Undriven output {port.name}")
    order = []
    ready = sorted(name for name, deps in dependencies.items() if not deps)
    while ready:
        current = ready.pop(0)
        order.append(by_name[current])
        for name in sorted(dependencies):
            if current in dependencies[name]:
                dependencies[name].remove(current)
                if not dependencies[name]:
                    ready.append(name)
        del dependencies[current]
    if dependencies:
        raise ValueError("Combinational cycle in netlist")
    return order


def pin_location(cell, pin: str, placement: dict) -> tuple[float, float]:
    x, y = cell.selected_access.get(pin, cell.pins[pin]["access"][0])
    if placement["orient"] == "MY":
        x = cell.width - x
    return placement["x"] + x, placement["y"] + y


def place(netlist, library, rows=None, seed=0, steps=600, history_every=25):
    """Pack row lists, preserving rail polarity under R0 or left/right mirror."""
    if rows is not None and rows < 1:
        raise ValueError("rows must be positive")
    if steps < 0 or history_every < 1:
        raise ValueError("Invalid annealing schedule")
    order = validate_netlist(netlist, library)
    h, p = library.template["height"], library.template["grid"]
    total = sum(library.cells[i.cell].width for i in order)
    count = rows or max(1, round(math.sqrt(total / (h + 12 * p))))
    count = min(count, max(1, len(order)))
    row_lists = [[] for _ in range(count)]
    widths = [0.] * count
    # Topological breadth first order naturally fills successive columns.
    for inst in order:
        r = min(range(count), key=lambda r: (widths[r], r))
        row_lists[r].append(inst.name)
        widths[r] += library.cells[inst.cell].width
    by_name = {i.name: i for i in order}
    orientations = {i.name: "R0" for i in order}

    def unpack():
        result = []
        for row, entries in enumerate(row_lists):
            x = 0.
            for name in entries:
                inst = by_name[name]
                result.append({"inst": name, "cell": inst.cell, "x": x,
                               "y": row * (h + 12*p), "row": row, "orient": orientations[name],
                               "width": library.cells[inst.cell].width, "height": h, "hier": inst.hier})
                x += library.cells[inst.cell].width
        return result

    def cost(placements):
        nets = defaultdict(list)
        for pl in placements:
            inst, cell = by_name[pl["inst"]], library.cells[pl["cell"]]
            for pin, net in inst.pins.items():
                nets[net].append(pin_location(cell, pin, pl))
        hpwl = sum(max(x for x, y in pts)-min(x for x, y in pts) +
                   max(y for x, y in pts)-min(y for x, y in pts) for pts in nets.values())
        # A weak width term prevents annealing from collapsing every cell into one row.
        spans = [sum(library.cells[by_name[n].cell].width for n in rr) for rr in row_lists]
        return hpwl + .5 * max(spans, default=0), hpwl

    rng = random.Random(seed)
    current = unpack()
    energy, hpwl = cost(current)
    best_energy, best = energy, (list(map(list, row_lists)), dict(orientations))
    history = [{"step": 0, "hpwl": hpwl, "placements": current}]
    for step in range(1, steps + 1):
        old_rows, old_orient = list(map(list, row_lists)), dict(orientations)
        nonempty = [r for r in range(count) if row_lists[r]]
        if not nonempty:
            break
        r = rng.choice(nonempty)
        a = rng.randrange(len(row_lists[r]))
        s = rng.randrange(count)
        choice = rng.random()
        if choice < .6 and row_lists[s]:
            b = rng.randrange(len(row_lists[s]))
            row_lists[r][a], row_lists[s][b] = row_lists[s][b], row_lists[r][a]
        elif choice < .9 and (r == s or len(row_lists[r]) > 1):
            name = row_lists[r].pop(a)
            row_lists[s].insert(rng.randrange(len(row_lists[s])+1), name)
        else:
            name = row_lists[r][a]
            orientations[name] = "MY" if orientations[name] == "R0" else "R0"
        candidate = unpack()
        new_energy, new_hpwl = cost(candidate)
        temperature = max(p*.02, p*8 * (1-step/max(1, steps))**2)
        if new_energy <= energy or rng.random() < math.exp(min(0, (energy-new_energy)/temperature)):
            current, energy, hpwl = candidate, new_energy, new_hpwl
            if energy < best_energy:
                best_energy, best = energy, (list(map(list, row_lists)), dict(orientations))
        else:
            row_lists, orientations = old_rows, old_orient
        if step % history_every == 0:
            history.append({"step": step, "hpwl": hpwl, "placements": current})
    row_lists, orientations = best
    placements = unpack()
    history.append({"step": steps+1, "hpwl": cost(placements)[1], "placements": placements})
    return placements, history, count
