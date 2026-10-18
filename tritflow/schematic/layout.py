"""Layered logic placement and dedicated-track Manhattan channel routing.

Long nets receive a pass-through lane at every crossed column. Each channel
uses one vertical track per net. Drivers escape on their pin row when it
is free, or on y = 8 mod 16 when a sink from another net occupies that row.
Sink lanes stay on y = 0 mod 16, preventing shared wires at crossings.
"""
from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable
from statistics import mean

from tritflow.netlist import GateNetlist
from tritflow.synth.simulate import CELL_INPUTS, ordered_instances
from .model import Connection, Scene, Segment, Symbol, natural


def _scopes(instances, expand):
    """Collapse module scopes while skipping unary generate-only containers."""
    if isinstance(expand, str):
        selected = (expand,)
    elif expand is True:
        selected = ('*',)
    elif expand is None or expand is False:
        selected = ()
    elif isinstance(expand, Iterable):
        selected = tuple(expand)
    else:
        raise TypeError('expand must be a hierarchy path, a sequence, or "*"')
    if any(not isinstance(s, str) for s in selected):
        raise TypeError('expand entries must be hierarchy paths')
    paths = {i.hier for i in instances if i.hier}
    available = {'.'.join(p.split('.')[:n]) for p in paths for n in range(1, len(p.split('.'))+1)}
    unknown = set(selected) - available - {'*', 'all'}
    if unknown:
        raise ValueError(f'unknown hierarchy scope: {sorted(unknown)}')
    flat = any(s in {'*', 'all'} for s in selected)
    groups = defaultdict(list)

    def walk(prefix, members):
        direct, children = [], defaultdict(list)
        depth = len(prefix.split('.')) if prefix else 0
        for inst in members:
            parts = inst.hier.split('.') if inst.hier else []
            if len(parts) <= depth:
                direct.append(inst)
            else:
                children['.'.join(parts[:depth+1])].append(inst)
        for inst in direct:
            groups[('cell', inst.name)].append(inst)
        for scope, child in sorted(children.items(), key=lambda kv: natural(kv[0])):
            # A generate container with exactly one child and no gates has no
            # electrical boundary of its own; show the module path below it.
            while not any(i.hier == scope for i in child):
                descendants = {'.'.join(i.hier.split('.')[:len(scope.split('.'))+1]) for i in child}
                if len(descendants) != 1:
                    break
                scope = descendants.pop()
            open_scope = flat or any(scope == s or scope.startswith(s+'.') or s.startswith(scope+'.')
                                     for s in selected)
            if open_scope:
                walk(scope, child)
            else:
                groups[('block', scope)].extend(child)
    walk('', instances)
    return groups


def _topology(net, expand):
    # The shared validator checks cell pin sets, drivers and combinational cycles.
    canonical = GateNetlist(net.top, sorted(net.ports,key=lambda p:natural(p.name)),
                            sorted(net.instances,key=lambda i:natural(i.name)))
    ordered = ordered_instances(canonical)
    groups = _scopes(ordered, expand)
    notes = []
    while True:
        owner = {i.name: f'{kind}:{name}' for (kind, name), group in groups.items() for i in group}
        nodes = {}
        driver, loads = {}, defaultdict(list)
        for p in sorted(net.ports, key=lambda p: natural(p.name)):
            key = f'{p.dir}:{p.name}'
            nodes[key] = Symbol(key, p.dir, p.name,
                                inputs={'port': p.name} if p.dir == 'output' else {},
                                outputs={'port': p.name} if p.dir == 'input' else {})
            if p.dir == 'input':
                driver[p.name] = (key, 'port')
            else:
                loads[p.name].append((key, 'port'))
        cell_driver = {i.pins['Y']: owner[i.name] for i in ordered}
        cell_driver.update({p.name: f'input:{p.name}' for p in net.ports if p.dir == 'input'})
        for (kind, name), members in groups.items():
            key = f'{kind}:{name}'
            if kind == 'cell':
                i = members[0]
                node = Symbol(key, i.cell, i.name, (i.name,),
                              {pin: i.pins[pin] for pin in CELL_INPUTS[i.cell]}, {'Y': i.pins['Y']})
            else:
                ins, outs = set(), set()
                for i in members:
                    for pin in CELL_INPUTS[i.cell]:
                        signal = i.pins[pin]
                        if cell_driver[signal] != key:
                            ins.add(signal)
                for i in ordered:
                    if owner[i.name] != key:
                        ins_external = [i.pins[p] for p in CELL_INPUTS[i.cell]]
                        outs.update(s for s in ins_external if cell_driver[s] == key)
                outs.update(p.name for p in net.ports if p.dir == 'output' and cell_driver[p.name] == key)
                node = Symbol(key, 'block', name, tuple(i.name for i in members),
                              {f'i{k}': s for k, s in enumerate(sorted(ins, key=natural))},
                              {f'o{k}': s for k, s in enumerate(sorted(outs, key=natural))})
            nodes[key] = node
            for pin, signal in node.inputs.items():
                loads[signal].append((key, pin))
            for pin, signal in node.outputs.items():
                driver[signal] = (key, pin)
        parents, children = defaultdict(set), defaultdict(set)
        for signal, sinks in loads.items():
            for key, _ in sinks:
                parent = driver[signal][0]
                parents[key].add(parent)
                children[parent].add(key)
        degree = {key: len(parents[key]) for key in nodes}
        ready = deque(sorted((key for key, d in degree.items() if not d), key=natural))
        seen = []
        while ready:
            key = ready.popleft()
            seen.append(key)
            node = nodes[key]
            node.level = max((nodes[p].level+1 for p in parents[key]), default=0)
            if node.kind not in {'input'} and not parents[key]:
                node.level = 1
            for child in sorted(children[key], key=natural):
                degree[child] -= 1
                if not degree[child]:
                    ready.append(child)
        if len(seen) == len(nodes):
            break
        # Logic sharing across module boundaries can make collapsed scopes
        # non-convex. Open the affected scopes rather than invent feedback.
        blocked = {key for key, d in degree.items() if d and nodes[key].kind == 'block'}
        if not blocked:
            raise ValueError('cannot form an acyclic hierarchy view')
        for key in sorted(blocked, key=natural):
            name = key.split(':', 1)[1]
            for i in groups.pop(('block', name)):
                groups[('cell', i.name)] = [i]
            notes.append(f'Opened {name}: shared logic crosses its boundary more than once.')
    final_level = max((n.level for n in nodes.values() if n.kind != 'output'), default=0)+1
    for node in nodes.values():
        if node.kind == 'output':
            node.level = final_level
    connections = []
    for p in sorted(net.ports, key=lambda p: natural(p.name)):
        connections.append(Connection(f'port:{p.name}', p.name, f'{p.dir}:{p.name}', 'port'))
    for i in sorted(ordered, key=lambda i: natural(i.name)):
        node = nodes[owner[i.name]]
        for pin, signal in sorted(i.pins.items()):
            display = ('Y' if pin == 'Y' else pin) if node.kind != 'block' else next(
                (p for p, s in (node.outputs if pin == 'Y' else node.inputs).items() if s == signal), None)
            connections.append(Connection(f'cell:{i.name}:{pin}', signal, node.key, display))
    return nodes, driver, loads, connections, notes


def _dimensions(node):
    if node.kind in {'input', 'output'}:
        node.width = max(80, 16*((len(node.label)*7+31)//16))
        node.height = 64
    elif node.kind == 'block':
        # Independent input/output pin columns, with ample space for names.
        left = max((len(s) for s in node.inputs.values()), default=1)
        right = max((len(s) for s in node.outputs.values()), default=1)
        node.width = 16*((max(len(node.label)*7+24, (left+right)*6+64)+15)//16)
        node.height = 64+32*max(len(node.inputs), len(node.outputs), 1)
    else:
        scope, _, local = node.label.rpartition('.')
        node.width = max(96, 16*((max(len(local)*7, len(scope)*5)+31)//16))
        node.height = 128 if scope else 96


def _place(nodes, driver, loads):
    """Barycenter sweeps include dummy lanes, reducing long-edge crossings."""
    columns = defaultdict(list)
    parents, children = defaultdict(list), defaultdict(list)
    dummy = {}
    for node in nodes.values():
        _dimensions(node)
        columns[node.level].append(node.key)
    for signal in sorted(driver, key=natural):
        source = driver[signal][0]
        last = max((nodes[key].level for key, _ in loads[signal]), default=nodes[source].level)
        previous = source
        for level in range(nodes[source].level+1, last):
            key = f'lane:{level}:{signal}'
            dummy[(signal, level)] = key
            node = Symbol(key, 'lane', signal, level=level, width=0, height=32)
            nodes[key] = node
            columns[level].append(key)
            parents[key].append(previous)
            children[previous].append(key)
            previous = key
        for sink, _ in loads[signal]:
            previous = source if nodes[sink].level == nodes[source].level+1 else dummy[(signal, nodes[sink].level-1)]
            parents[sink].append(previous)
            children[previous].append(sink)
    for level, keys in columns.items():
        keys.sort(key=natural)
    def coordinates():
        result = {}
        for keys in columns.values():
            y = 0
            for key in keys:
                result[key] = y + nodes[key].height/2
                y += nodes[key].height+32
        return result
    def crossing_count():
        total = 0
        pos = coordinates()
        for level, keys in columns.items():
            edges = [(pos[key], pos[c]) for key in keys for c in children[key] if nodes[c].level == level+1]
            total += sum((a-c)*(b-d) < 0 for k, (a,b) in enumerate(edges) for c,d in edges[k+1:])
        return total
    best = {k: list(v) for k, v in columns.items()}
    best_cost = crossing_count()
    for sweep in range(10):
        forward = sweep % 2 == 0
        adjacent = parents if forward else children
        pos = coordinates()
        for level in sorted(columns, reverse=not forward):
            keys = columns[level]
            if all(nodes[k].kind in {'input','output'} for k in keys):
                continue  # external bus order is a fixed circuit interface
            previous_order = {key: index for index, key in enumerate(keys)}
            keys.sort(key=lambda key: (mean(pos[p] for p in adjacent[key]) if adjacent[key] else pos[key],
                                       previous_order[key]))
            pos = coordinates()
        cost = crossing_count()
        if cost < best_cost:
            best, best_cost = {k: list(v) for k,v in columns.items()}, cost
    columns = best
    heights = {level: sum(nodes[k].height+32 for k in keys)-32 for level,keys in columns.items()}
    total_height = max(heights.values(), default=0)
    # Reserve space for any annotation without changing geometry on re-use.
    label_width = max((len(s)*6+88 for s in driver), default=88)
    label_width = 16*((label_width+15)//16)
    x = 48
    widths = {level: max((nodes[k].width for k in keys), default=96) for level,keys in columns.items()}
    for level in sorted(columns):
        width = widths[level]
        y = 96+32*((total_height-heights[level])//64)
        for key in columns[level]:
            node = nodes[key]
            node.x, node.y = x, y
            node.width = width
            if node.kind == 'lane':
                cy = y+16
                node.pins = {'in':(x,cy), 'out':(x+width,cy)}
            elif node.kind == 'block':
                node.pins = {pin:(x,y+64+32*k) for k,pin in enumerate(node.inputs)}
                node.pins.update({pin:(x+width,y+64+32*k) for k,pin in enumerate(node.outputs)})
            else:
                # Gate centers and every driver are 0 mod 32; gate inputs at
                # +/-16 permit labels between the incoming horizontal lanes.
                cy = y+32 if node.kind in {'input', 'output'} else y+64
                if len(node.inputs) == 2:
                    node.pins = {pin:(x,cy+offset) for pin,offset in zip(node.inputs, (-16,16))}
                else:
                    node.pins = {pin:(x,cy) for pin in node.inputs}
                node.pins.update({pin:(x+width,cy) for pin in node.outputs})
            y += node.height+32
        tracks = sum(nodes[src[0]].level <= level < max((nodes[k].level for k,_ in loads[s]), default=-1)
                     for s,src in driver.items())
        x += width + 48+label_width+16*tracks
    return columns, dummy, widths, label_width, total_height+192


def _merge(segments):
    """Merge collinear same-net pieces so a shared trunk is drawn once."""
    groups = defaultdict(list)
    for s in segments:
        if s.a == s.b:
            continue
        horizontal = s.a[1] == s.b[1]
        fixed = s.a[1] if horizontal else s.a[0]
        interval = sorted((s.a[0],s.b[0]) if horizontal else (s.a[1],s.b[1]))
        groups[s.net,horizontal,fixed].append(interval)
    merged = []
    for (signal,horizontal,fixed), intervals in sorted(groups.items()):
        runs = []
        for lo,hi in sorted(intervals):
            if runs and lo <= runs[-1][1]:
                runs[-1][1] = max(runs[-1][1],hi)
            else:
                runs.append([lo,hi])
        for lo,hi in runs:
            merged.append(Segment(signal, (lo,fixed) if horizontal else (fixed,lo),
                                   (hi,fixed) if horizontal else (fixed,hi)))
    return tuple(merged)


def _junctions(segments):
    """Only same-net intersections with >=3 incident directions get dots."""
    result = defaultdict(list)
    by_net = defaultdict(list)
    for s in segments:
        by_net[s.net].append(s)
    for signal, group in by_net.items():
        candidates = {p for s in group for p in (s.a,s.b)}
        for h in group:
            if h.a[1] != h.b[1]:
                continue
            for v in group:
                if v.a[0] == v.b[0] and h.a[0] <= v.a[0] <= h.b[0] and v.a[1] <= h.a[1] <= v.b[1]:
                    candidates.add((v.a[0],h.a[1]))
        for x,y in sorted(candidates):
            directions = set()
            for s in group:
                if s.a[1] == s.b[1] == y and s.a[0] <= x <= s.b[0]:
                    if s.a[0] < x: directions.add('W')
                    if s.b[0] > x: directions.add('E')
                if s.a[0] == s.b[0] == x and s.a[1] <= y <= s.b[1]:
                    if s.a[1] < y: directions.add('N')
                    if s.b[1] > y: directions.add('S')
            if len(directions) >= 3:
                result[signal].append((x,y))
    return {s:tuple(points) for s,points in result.items()}


def layout(net, expand=None):
    """Produce a deterministic, fully connected schematic without external tools."""
    nodes,driver,loads,connections,notes = _topology(net,expand)
    columns,dummy,_,label_width,height = _place(nodes,driver,loads)
    segments, labels = [], {}
    def line(signal,a,b):
        if a != b:
            segments.append(Segment(signal,a,b))
    for level in sorted(columns):
        active = [s for s,(key,pin) in driver.items()
                  if nodes[key].level <= level < max((nodes[k].level for k,_ in loads[s]), default=-1)]
        # Ordering by source height is a stable channel-crossing heuristic.
        def source(signal):
            key,pin = driver[signal]
            if nodes[key].level < level:
                key,pin = dummy[signal,level],'out'
            return nodes[key].pins[pin]
        active.sort(key=lambda s:(source(s)[1],natural(s)))
        destinations = {}
        for signal in active:
            points = [nodes[key].pins[pin] for key,pin in loads[signal] if nodes[key].level == level+1]
            if (signal,level+1) in dummy:
                points.append(nodes[dummy[signal,level+1]].pins['in'])
            destinations[signal] = points
        for index,signal in enumerate(active):
            sx,sy = source(signal)
            tx = sx+32+label_width+16*index
            conflict = any(y == sy for other,points in destinations.items() if other != signal for x,y in points)
            lane_y = sy+8 if conflict else sy
            line(signal,(sx,sy),(sx+8,sy))
            line(signal,(sx+8,sy),(sx+8,lane_y))
            line(signal,(sx+8,lane_y),(tx,lane_y))
            dest = destinations[signal]
            line(signal,(tx,min([lane_y]+[y for x,y in dest])),(tx,max([lane_y]+[y for x,y in dest])))
            for dx,dy in dest:
                line(signal,(tx,dy),(dx,dy))
            if nodes[driver[signal][0]].level == level:
                labels[signal] = (sx+24,sy-3)
    for (signal,level),key in dummy.items():
        node = nodes[key]
        line(signal,node.pins['in'],node.pins['out'])
    # A live output with no consumer still has a short visible terminal stub.
    for signal,(key,pin) in driver.items():
        if not loads[signal]:
            x,y = nodes[key].pins[pin]
            line(signal,(x,y),(x+24,y))
            labels[signal] = (x+24,y-3)
    segments = _merge(segments)
    visible = {s.net for s in segments}
    width = max(640, max((n.x+n.width for n in nodes.values()),default=96)+64)
    return Scene(net.top,tuple(n for n in nodes.values() if n.kind != 'lane'),segments,
                 _junctions(segments),tuple(connections),labels,width,height,
                 tuple(sorted(net.nets()-visible,key=natural)),tuple(notes))
