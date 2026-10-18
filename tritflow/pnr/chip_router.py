"""Manhattan interconnect in the free space around a fixed MPW macro.

M1 carries horizontal links, M2 vertical links. Real probe-pad metal is an
obstacle for other nets; ordinary small vias are forbidden near pad openings.
The macro interior is reserved, so this router cannot alter its device wiring.
"""
from __future__ import annotations

import bisect
import heapq
import itertools

import numpy as np

from .router import RoutingFailure


class ChipRouter:
    """A physical-width-aware two-layer maze with immutable terminal escapes."""

    def __init__(self, shapes, terminals, core, pads, widths, bound=1152., pitch=6.):
        self.shapes = shapes
        self.terminals, self.widths = terminals, widths
        self.core, self.pads = core, pads
        self.xs = sorted({round(x, 3) for x in np.arange(-bound, bound+.01, pitch)} |
                         {round(t[1], 3) for pair in terminals.values() for t in pair})
        self.ys = sorted({round(y, 3) for y in np.arange(-bound, bound+.01, pitch)} |
                         {round(t[2], 3) for pair in terminals.values() for t in pair})
        self.nx, self.ny = len(self.xs), len(self.ys)
        self.xi = {v: i for i, v in enumerate(self.xs)}
        self.yi = {v: i for i, v in enumerate(self.ys)}
        self.paths = {}

    def _fill(self, grid, rect, clearance, value=True):
        x0, y0, x1, y1 = rect
        a = bisect.bisect_right(self.xs, x0-clearance)
        b = bisect.bisect_left(self.xs, x1+clearance)
        c = bisect.bisect_right(self.ys, y0-clearance)
        d = bisect.bisect_left(self.ys, y1+clearance)
        grid[c:d, a:b] = value

    def route(self, net):
        """Route one pad to its escaped macro terminal, or name the failed region."""
        width = self.widths[net]
        blocked = np.zeros((2, self.ny, self.nx), dtype=bool)
        for layer, owner, rect in self.shapes:
            if owner != net:
                self._fill(blocked[layer], rect, width/2+2.05)
        for layer in range(2):
            self._fill(blocked[layer], self.core, width/2+2.05)
        # No new via may infringe the 15 um metal enclosure of a pad via.
        no_via = np.zeros((self.ny, self.nx), dtype=bool)
        for _, x, y in self.pads:
            self._fill(no_via, [x-50, y-50, x+50, y+50], width/2+16.)
        no_via |= blocked[0] | blocked[1]
        start, goal = [(layer, self.xi[round(x, 3)], self.yi[round(y, 3)])
                       for layer, x, y in self.terminals[net]]
        region = [min(self.xs[start[1]], self.xs[goal[1]]),
                  min(self.ys[start[2]], self.ys[goal[2]]),
                  max(self.xs[start[1]], self.xs[goal[1]]),
                  max(self.ys[start[2]], self.ys[goal[2]])]
        for layer, x, y in (start, goal):
            if blocked[layer, y, x]:
                raise RoutingFailure(net, 'blocked chip terminal escape', region=region)
        def heuristic(n):
            return abs(self.xs[n[1]]-self.xs[goal[1]]) + abs(self.ys[n[2]]-self.ys[goal[2]])
        counter = itertools.count()
        queue = [(heuristic(start), 0., next(counter), start)]
        costs, previous = {start: 0.}, {}
        while queue:
            _, cost, _, node = heapq.heappop(queue)
            if cost != costs[node]:
                continue
            if node == goal:
                path = [node]
                while path[-1] != start:
                    path.append(previous[path[-1]])
                path.reverse()
                self.paths[net] = path
                return self._draw(net, path)
            layer, x, y = node
            candidates = []
            for delta in (-1, 1):
                xx, yy = (x+delta, y) if layer == 0 else (x, y+delta)
                if 0 <= xx < self.nx and 0 <= yy < self.ny and not blocked[layer, yy, xx]:
                    length = abs(self.xs[xx]-self.xs[x])+abs(self.ys[yy]-self.ys[y])
                    candidates.append(((layer, xx, yy), length))
            if not no_via[y, x]:
                candidates.append(((1-layer, x, y), 24.))
            for other, length in candidates:
                value = cost+length
                if value < costs.get(other, float('inf')):
                    costs[other], previous[other] = value, node
                    heapq.heappush(queue, (value+heuristic(other), value, next(counter), other))
        raise RoutingFailure(net, 'MPW pad escape/channel congestion', region=region)

    def _draw(self, net, path):
        width = self.widths[net]
        wires, vias = [], []
        first = path[0]
        def wire(a, b):
            if a == b:
                return
            layer = a[0]
            x0, y0, x1, y1 = self.xs[a[1]], self.ys[a[2]], self.xs[b[1]], self.ys[b[2]]
            wires.append({'net': net, 'layer': 'M1' if layer == 0 else 'M2',
                          'width': width, 'points': [[x0, y0], [x1, y1]]})
            self.shapes.append((layer, net, [min(x0,x1)-width/2, min(y0,y1)-width/2,
                                           max(x0,x1)+width/2, max(y0,y1)+width/2]))
        for a, b in zip(path, path[1:]):
            if a[0] != b[0]:
                wire(first, a)
                x, y = self.xs[a[1]], self.ys[a[2]]
                vias.append({'net': net, 'x': x, 'y': y, 'landing_width': width})
                # Reserve both metal landings, including very short segments.
                for layer in range(2):
                    self.shapes.append((layer, net, [x-width/2,y-width/2,x+width/2,y+width/2]))
                first = b
        wire(first, path[-1])
        return wires, vias
