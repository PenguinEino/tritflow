"""Hierarchy boundaries, exact terminal accounting and compact circuit scenes."""
from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable

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


def layout(net, expand=None, hierarchy=None):
    """Build a compact circuit drawing from public logical connectivity."""
    from .arithmetic import recognize
    from .placement import place
    from .routing import route
    nodes,driver,loads,connections,notes = _topology(net,expand)
    arithmetic=recognize(net)
    for node in nodes.values():
        if node.kind!='block':continue
        scope=node.key.split(':',1)[1]
        known=arithmetic.get(scope)
        supplied=(hierarchy or {}).get(scope,{})
        aliases=supplied.get('ports',known.ports if known else {})
        node.module=supplied.get('module',known.module if known else '')
        reverse={signal:name for name,signal in aliases.items()}
        node.pin_labels={p:reverse.get(signal,signal) for p,signal in {**node.inputs,**node.outputs}.items()}
    frames,width,height=place(nodes,driver,loads,arithmetic)
    try:routed,trunks=route(nodes,driver,loads,width,height,frames)
    except ValueError:
        # Dense block fanout can need its branches before the local nets.
        # Retry from an empty routing state, preserving the same clearances.
        routed,trunks=route(nodes,driver,loads,width,height,frames,fanout_first=True)
    segments=_merge(routed)
    # Crop the drawing, rather than leaving placement's routing workspace as
    # a large empty margin. Translation keeps pins and every wire unchanged.
    bounds=[n.box for n in nodes.values()]+[f.box for f in frames]
    bounds += [(s.a[0],s.a[1],s.b[0],s.b[1]) for s in segments]
    min_x=min((b[0] for b in bounds),default=0);min_y=min((b[1] for b in bounds),default=0)
    dx,dy=24-min_x,48-min_y
    for node in nodes.values():
        node.x+=dx;node.y+=dy
        node.pins={p:(x+dx,y+dy) for p,(x,y) in node.pins.items()}
    segments=tuple(Segment(s.net,(s.a[0]+dx,s.a[1]+dy),(s.b[0]+dx,s.b[1]+dy)) for s in segments)
    trunks=tuple(Segment(s.net,(s.a[0]+dx,s.a[1]+dy),(s.b[0]+dx,s.b[1]+dy)) for s in trunks)
    from .model import Frame
    frames=tuple(Frame(f.label,(f.box[0]+dx,f.box[1]+dy,f.box[2]+dx,f.box[3]+dy),f.members) for f in frames)
    width=max(400,max((b[2] for b in bounds),default=0)+dx+24)
    height=max((b[3] for b in bounds),default=0)+dy+40
    visible={s.net for s in segments}
    return Scene(net.top,tuple(nodes.values()),segments,_junctions(segments),tuple(connections),{},width,height,
                 tuple(sorted(net.nets()-visible,key=natural)),tuple(notes),frames,trunks)
