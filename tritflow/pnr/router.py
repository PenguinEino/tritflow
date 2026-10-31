"""A* maze routing on horizontal channel M1 and vertical over-cell M2 tracks."""
from __future__ import annotations

import bisect
import heapq
import math
import random
from collections import defaultdict

import numpy as np

from tritflow import progress
from .placement import pin_location
from .constraints import m2_obstacles
from .gds import wire_box


class RoutingFailure(RuntimeError):
    """A legal path was not found in the current channel allocation."""

    def __init__(self, net, reason="no legal maze path", *, region=None,
                 blocking_nets=(), failed_nets=None):
        self.net = net
        self.reason, self.region_um = reason, region
        self.blocking_nets = sorted(set(blocking_nets))
        self.failed_nets = sorted(set(failed_nets or [net]))
        message = f"Routing failed for nets {', '.join(self.failed_nets)}: {reason}."
        if region:
            x0, y0, x1, y1 = region
            message += f" Congested connection region: x={x0:g}..{x1:g} µm, y={y0:g}..{y1:g} µm."
        if self.blocking_nets:
            message += f" Nearby occupied nets: {', '.join(self.blocking_nets[:8])}."
        message += " Try more rows (rows=...) or channel tracks (channel_tracks=...); check cell pin-access obstructions."
        super().__init__(message)


def floorplan(netlist, library, relative, row_count, margin, tracks, *, core_width=None):
    """Place channels below, between, and above rows; put I/O outside power banks."""
    p, h = library.template["grid"], library.template["height"]
    channels, row_y, cursor = [], [], 0.
    for row in range(row_count+1):
        channels.append([round(cursor+(k+.5)*p, 6) for k in range(tracks)])
        cursor += (tracks+1)*p
        if row < row_count:
            row_y.append(cursor)
            cursor += h+p
    if core_width is None:
        core_width = max((pl["x"]+library.cells[pl["cell"]].width for pl in relative), default=6*p)
    width = math.ceil((core_width + 2*margin)/p)*p
    placements = [{**pl, "x": pl["x"]+margin, "y": row_y[pl["row"]]} for pl in relative]
    pins, terminals = [], defaultdict(list)
    for pl in placements:
        inst = next(i for i in netlist.instances if i.name == pl["inst"])
        for pin, net in inst.pins.items():
            x, y = pin_location(library.cells[inst.cell], pin, pl)
            terminals[net].append({"x": x, "y": y, "inst": inst.name, "pin": pin})
    for direction in ("input", "output"):
        ports = [port for port in netlist.ports if port.dir == direction]
        for index, port in enumerate(ports):
            channel, slot = index % len(channels), index // len(channels)
            k = 1+2*slot
            if k >= tracks:
                raise RoutingFailure(port.name, "not enough boundary pin tracks")
            y = channels[channel][k]
            x = p/2 if direction == "input" else width-p/2
            pad = library.template["rules"]["V1"] + 2*max(
                library.template["rules"]["V1_enc_M1"], library.template["rules"]["V1_enc_M2"])
            rect = ([0., y-pad/2, x+pad/2, y+pad/2] if direction == "input" else
                    [x-pad/2, y-pad/2, width, y+pad/2])
            pins.append({"name": port.name, "layer": "M2", "rect": rect})
            terminals[port.name].append({"x": x, "y": y, "port": port.name})
    return {"die": [width, cursor], "rows": [{"y": y, "orient": "R0"} for y in row_y],
            "placements": placements, "pins": pins, "wires": [], "vias": [],
            "channels": [{"tracks": yy, "height": tracks*p} for yy in channels]}, terminals


class Maze:
    """Layer occupancy belongs to actual nets, including all unrouted pin landings.

    Track pitch separates neighboring x columns and M1 channel tracks. M2 uses
    extra y coordinates at off-grid cell pins. Occupancy is expanded along y to
    preserve metal spacing even where those additional coordinates are close.
    """

    def __init__(self, data, terminals, library):
        self.data, self.terminals, self.library = data, terminals, library
        self.pitch = p = library.template["grid"]
        self.rules = library.template["rules"]
        self.pad = self.rules["V1"]+2*max(self.rules["V1_enc_M1"], self.rules["V1_enc_M2"])
        self.xs = [round(p/2+i*p, 6) for i in range(round(data["die"][0]/p))]
        self.channel_ys = {y for c in data["channels"] for y in c["tracks"]}
        obstacles = [rect for pl in data["placements"]
                     for rect in m2_obstacles(library.cells[pl["cell"]], pl, library.template)]
        obstacles += [wire_box(w) for w in data["power"]["straps"]]
        clearance = self.pad/2+self.rules["M2_s"]
        # Boundary and interior samples prevent a compressed vertical edge from
        # jumping through metal between two channel/pin coordinates.
        obstacle_ys = {round(y, 6) for _, y0, _, y1 in obstacles
                      for y in (y0-clearance, y0-clearance+.05, (y0+y1)/2,
                                y1+clearance-.05, y1+clearance)
                      if 0 <= y <= data["die"][1]}
        self.ys = sorted(self.channel_ys | obstacle_ys |
                         {t["y"] for terms in terminals.values() for t in terms})
        self.xi, self.yi = {x: i for i, x in enumerate(self.xs)}, {y: i for i, y in enumerate(self.ys)}
        self.nx, self.ny = len(self.xs), len(self.ys)
        self.horizontal = [y in self.channel_ys for y in self.ys]
        self.ids = {net: i+1 for i, net in enumerate(sorted(terminals))}
        self.base1 = np.zeros((self.ny, self.nx), dtype=np.int32)
        self.base2 = self.base1.copy()
        for rect in obstacles:
            self.block_rect(rect, -1)
        self.nodes = {}
        for net, terms in terminals.items():
            self.nodes[net] = []
            for terminal in terms:
                x, y = round(terminal["x"], 6), round(terminal["y"], 6)
                if x not in self.xi:
                    raise RoutingFailure(net, f"off-track pin x={x}")
                node = (1, self.xi[x], self.yi[y])
                self.nodes[net].append(node)
                if "port" in terminal:
                    self.base1[node[2], node[1]] = self.ids[net]
                # Boundary pins have the same y span as an ordinary via pad.
                width = self.pad
                self.block_rect([x-width/2, y-width/2, x+width/2, y+width/2], self.ids[net])
        for net, nodes in self.nodes.items():
            if any(self.base2[y, x] != self.ids[net] for _, x, y in nodes):
                raise self.failure(net, "pin access conflicts with another terminal or M2 obstruction")
        self.escape_paths = {net: {} for net in terminals}
        # Pins sharing a column (e.g. compact NANY A/B) must escape on opposite
        # sides. Reserve those mandatory stubs before another net uses their
        # channel exits. Unconstrained pins retain both routing choices.
        mandatory = []
        for net, nodes in self.nodes.items():
            owner = self.ids[net]
            for node in nodes:
                _, x, y = node
                choices = []
                for direction in (-1, 1):
                    path, index = [node], y
                    while 0 <= index+direction < self.ny:
                        index += direction
                        if self.base2[index, x] not in (0, owner):
                            break
                        path.append((1, x, index))
                        if self.horizontal[index]:
                            choices.append(path)
                            break
                if len(choices) == 1 and len(choices[0]) > 1:
                    self.escape_paths[net][node] = choices[0]
                    mandatory.append((choices[0], owner))
                    end = choices[0][-1]
                    value = self.base1[end[2], end[1]]
                    if value not in (0, owner):
                        raise self.failure(net, "mandatory pin escapes share a channel landing")
                    self.base1[end[2], end[1]] = owner
        self.reset()
        for path, owner in mandatory:
            self.occupy(path, owner)
        self.base2 = self.occ[1].copy()
        self.reset()

    def failure(self, net, reason, nodes=None):
        """Describe the failed connection window and occupied nets within it."""
        points = ([(self.xs[x], self.ys[y]) for _, x, y in nodes] if nodes is not None
                  else [(t["x"], t["y"]) for t in self.terminals[net]])
        p = self.pitch
        region = [max(0., min(x for x, y in points)-p),
                  max(0., min(y for x, y in points)-p),
                  min(self.data["die"][0], max(x for x, y in points)+p),
                  min(self.data["die"][1], max(y for x, y in points)+p)]
        x0, x1 = bisect.bisect_left(self.xs, region[0]), bisect.bisect_right(self.xs, region[2])
        y0, y1 = bisect.bisect_left(self.ys, region[1]), bisect.bisect_right(self.ys, region[3])
        occupancy = getattr(self, "occ", (self.base1, self.base2))
        owners = {int(v) for layer in occupancy for v in np.unique(layer[y0:y1, x0:x1]) if v > 0}
        blockers = [name for name, owner in self.ids.items() if owner in owners and name != net]
        return RoutingFailure(net, reason, region=region, blocking_nets=blockers)

    def block_rect(self, rect, owner):
        x0, y0, x1, y1 = rect
        clearance = self.pad/2 + self.rules["M2_s"]
        a, b = bisect.bisect_right(self.xs, x0-clearance), bisect.bisect_left(self.xs, x1+clearance)
        c, d = bisect.bisect_right(self.ys, y0-clearance), bisect.bisect_left(self.ys, y1+clearance)
        view = self.base2[c:d, a:b]
        conflict = (view != 0) & (view != owner)
        view[view == 0] = owner
        view[conflict] = -2

    def reset(self):
        self.occ = [self.base1.copy(), self.base2.copy()]
        self.paths = {}

    def available(self, node, owner):
        layer, x, y = node
        value = self.occ[layer][y, x]
        return (value == 0 or value == owner) and (layer == 1 or self.horizontal[y])

    def search(self, start, tree, owner):
        if start in tree:
            return [start]
        minx = min(n[1] for n in tree)
        maxx = max(n[1] for n in tree)
        miny = min(self.ys[n[2]] for n in tree)
        maxy = max(self.ys[n[2]] for n in tree)
        def heuristic(node):
            _, x, y = node
            return max(minx-x, 0, x-maxx) + max(miny-self.ys[y], 0, self.ys[y]-maxy)/self.pitch
        heap = [(heuristic(start), 0., start)]
        distance, parent = {start: 0.}, {}
        while heap:
            _, cost, current = heapq.heappop(heap)
            if cost != distance[current]:
                continue
            if current in tree:
                result = [current]
                while current in parent:
                    current = parent[current]
                    result.append(current)
                return list(reversed(result))
            layer, x, y = current
            neighbors = []
            if layer == 0:
                if x > 0:
                    neighbors.append(((0, x-1, y), 1.))
                if x+1 < self.nx:
                    neighbors.append(((0, x+1, y), 1.))
            else:
                if y > 0:
                    neighbors.append(((1, x, y-1), (self.ys[y]-self.ys[y-1])/self.pitch))
                if y+1 < self.ny:
                    neighbors.append(((1, x, y+1), (self.ys[y+1]-self.ys[y])/self.pitch))
            if self.horizontal[y]:
                neighbors.append(((1-layer, x, y), 2.5))
            for other, weight in neighbors:
                if not self.available(other, owner):
                    continue
                new_cost = cost+weight
                if new_cost < distance.get(other, math.inf):
                    distance[other], parent[other] = new_cost, current
                    heapq.heappush(heap, (new_cost+heuristic(other), new_cost, other))
        return None

    def occupy(self, path, owner):
        gap = self.pad + self.rules["M2_s"]
        for layer, x, y in path:
            if layer == 0:
                self.occ[0][y, x] = owner
            else:
                low = bisect.bisect_right(self.ys, self.ys[y]-gap+1e-7)
                high = bisect.bisect_left(self.ys, self.ys[y]+gap-1e-7)
                view = self.occ[1][low:high, x]
                conflict = (view != 0) & (view != owner)
                view[view == 0] = owner
                view[conflict] = -2

    def route_net(self, net):
        nodes, owner = self.nodes[net], self.ids[net]
        stubs = self.escape_paths[net]
        first = stubs.get(nodes[0], [nodes[0]])
        tree, paths = set(first), [first]
        remaining = {node: stubs.get(node, [node]) for node in nodes[1:]}
        while remaining:
            start_node = min(remaining, key=lambda a: min(abs(remaining[a][-1][1]-b[1])+
                abs(self.ys[remaining[a][-1][2]]-self.ys[b[2]])/self.pitch for b in tree))
            stub = remaining[start_node]
            path = self.search(stub[-1], tree, owner)
            if path is None:
                target = min(tree, key=lambda b: abs(stub[-1][1]-b[1])+
                             abs(self.ys[stub[-1][2]]-self.ys[b[2]])/self.pitch)
                raise self.failure(net, "no legal maze path", [stub[-1], target])
            self.occupy(path, owner)
            tree.update(stub)
            tree.update(path)
            paths.extend((stub, path))
            del remaining[start_node]
        self.paths[net] = paths

    def segments(self, net):
        """One routed net for live views: wires as (layer, x0, y0, x1, y1) and V1 cuts as (x, y), in µm."""
        wires, vias = [], {(t["x"], t["y"]) for t in self.terminals[net] if "inst" in t}
        for path in self.paths[net]:
            for a, b in zip(path, path[1:]):
                if a[0] == b[0]:
                    wires.append(("M1" if a[0] == 0 else "M2", self.xs[a[1]], self.ys[a[2]],
                                  self.xs[b[1]], self.ys[b[2]]))
                else:
                    vias.add((self.xs[a[1]], self.ys[a[2]]))
        return {"wires": wires, "vias": sorted(vias)}

    def export(self):
        wires, vias = [], set()
        for net, paths in self.paths.items():
            # Every M1 cell terminal gets a real cut and landings, even singleton nets.
            for terminal in self.terminals[net]:
                if "inst" in terminal:
                    vias.add((net, terminal["x"], terminal["y"]))
            edges = set()
            for path in paths:
                for a, b in zip(path, path[1:]):
                    if a[0] != b[0]:
                        vias.add((net, self.xs[a[1]], self.ys[a[2]]))
                    else:
                        edges.add(tuple(sorted((a, b))))
            # Coalesce consecutive collinear edges for compact JSON and GDS.
            runs = defaultdict(list)
            for a, b in edges:
                if a[0] == 0:
                    runs[("M1", a[2])].append((min(a[1], b[1]), max(a[1], b[1])))
                else:
                    runs[("M2", a[1])].append((min(a[2], b[2]), max(a[2], b[2])))
            for (layer, fixed), intervals in sorted(runs.items()):
                intervals.sort()
                merged = []
                for lo, hi in intervals:
                    if merged and lo <= merged[-1][1]:
                        merged[-1][1] = max(merged[-1][1], hi)
                    else:
                        merged.append([lo, hi])
                for lo, hi in merged:
                    points = ([[self.xs[lo], self.ys[fixed]], [self.xs[hi], self.ys[fixed]]]
                              if layer == "M1" else
                              [[self.xs[fixed], self.ys[lo]], [self.xs[fixed], self.ys[hi]]])
                    wires.append({"net": net, "layer": layer, "width": self.rules[f"{layer}_w"], "points": points})
        return wires, [{"net": n, "x": x, "y": y} for n, x, y in sorted(vias)]


def route(data, terminals, library, seed=0, ripup_passes=3):
    """Rip up all signal routes on failure and prioritize the blocked net next."""
    maze = Maze(data, terminals, library)
    def priority(net):
        pts = terminals[net]
        span = max(t["x"] for t in pts)-min(t["x"] for t in pts)+max(t["y"] for t in pts)-min(t["y"] for t in pts)
        return -len(pts), -span, net
    order = sorted(terminals, key=priority)
    rng = random.Random(seed)
    log = []
    for attempt in range(ripup_passes):
        maze.reset()
        try:
            for done, net in enumerate(order, 1):
                maze.route_net(net)
                if progress.active():
                    progress.report(kind="route", done=done, total=len(order), net=net,
                                    attempt=attempt, segments=maze.segments(net))
            data["wires"], data["vias"] = maze.export()
            data["routing_order"] = list(maze.paths)
            data["routing_progress"] = [{"step": i, "net": net, "routed_nets": i,
                                         "total_nets": len(order), "pass": attempt}
                                        for i, net in enumerate(maze.paths, 1)]
            return log
        except RoutingFailure as error:
            log.append({"pass": attempt, "failed_net": error.net, "routed_nets": len(maze.paths)})
            if attempt+1 == ripup_passes:
                error.ripup_log = log
                raise
            rest = [net for net in order if net != error.net]
            rng.shuffle(rest)
            order = [error.net] + rest
    raise AssertionError("unreachable")
