"""Compose expanded modules from the same routed drawing used on their own.

A module is routed once in local coordinates. The outer router sees only its
boundary pins and a solid keep-out, so an unrelated signal cannot cut through
its cells or borrow an internal fan-out channel.
"""
from copy import deepcopy
from functools import lru_cache
from collections import defaultdict

from tritflow.netlist import GateNetlist,Instance,Port
from tritflow.synth.simulate import CELL_INPUTS
from .arithmetic import HALF,MUL,match,Arithmetic
from .model import Frame,Segment,Symbol,natural
from .placement import anchors


@lru_cache(maxsize=8)
def template(module,taps=()):
    """Return the standalone cell geometry, with named boundary terminals.

    Carry exits above its producer rather than crossing the sum datapath to
    reach the right edge. Input and sum leads retain their standalone lanes.
    """
    from .layout import layout,_merge
    pattern=HALF if module=='half_add' else MUL
    exports=(('sum','carry') if module=='half_add' else ('p',))+taps
    net=GateNetlist(module,[Port(n,'input') for n in ('a','b')]+[Port(n,'output') for n in exports],
        [Instance(name,kind,dict(zip(CELL_INPUTS[kind],ins))|{'Y':out}) for name,kind,ins,out in pattern])
    scene=layout(net,_macros=False)
    gates=[n for n in scene.symbols if n.kind not in {'input','output'}]
    terminals={n.label:n.pins['port'] for n in scene.symbols if n.kind in {'input','output'}}
    left=min(terminals[n][0] for n in ('a','b'))
    top=min(n.y for n in gates)-64
    right=max(n.box[2] for n in gates)+96
    bottom=max(n.box[3] for n in gates)+32
    rails={s.net:s for s in scene.trunks if s.net in {'a','b'}}
    pins={n:(left,terminals[n][1]+(-32 if n=='a' else 32)) for n in ('a','b')}
    sides={'a':'left','b':'left'}
    wires=list(scene.segments)
    if module=='mul1':
        # Enter the two operands at opposite ends of their existing trunks.
        # Both leads stay straight and the two wide flag labels are separated.
        for name in ('a','b'):
            point=terminals[name];rail=rails[name]
            pins[name]=(left,rail.a[1] if name=='a' else rail.b[1])
            for i,s in enumerate(wires):
                if s.net==name and s.a==point and s.b[1]==point[1]:
                    wires[i]=Segment(name,(rail.a[0],point[1]),s.b);break
            wires.append(Segment(name,pins[name],(rail.a[0],pins[name][1])))
    else:
        for name in ('a','b'):
            point=terminals[name];corner=(left+128,point[1]);entry=(corner[0],pins[name][1])
            for i,s in enumerate(wires):
                if s.net==name and s.a==point and s.b[1]==point[1]:
                    junction_x=[p[0] for p in scene.junctions.get(name,()) if p[1]==point[1]]
                    wires[i]=Segment(name,(min(junction_x or [corner[0]]),point[1]),(max(corner[0],s.b[0]),point[1]));break
            wires.extend((Segment(name,min(entry,corner),max(entry,corner)),Segment(name,pins[name],entry)))
    for name in exports:
        point=terminals[name]
        target=(point[0],top) if name=='carry' or name in taps else (right,point[1])
        wires.append(Segment(name,min(point,target),max(point,target)))
        pins[name]=target;sides[name]='top' if name=='carry' or name in taps else 'right'
    def move(p):return p[0]-left,p[1]-top
    for n in gates:
        n.x-=left;n.y-=top;n.pins={p:move(q) for p,q in n.pins.items()}
    shift=lambda s:Segment(s.net,move(s.a),move(s.b))
    return gates,_merge([shift(s) for s in wires]),tuple(shift(s) for s in scene.trunks),\
           {n:move(p) for n,p in pins.items()},sides,right-left,bottom-top


def _units(nodes,arithmetic):
    """Use retained scopes; exact multiplier cones also cover MAC's primitives."""
    units=[];used=set()
    for scope,m in sorted(arithmetic.items(),key=lambda item:(-len(item[0]),natural(item[0]))):
        keys={'cell:'+n for n in m.cells.values()}
        if scope and m.module in {'half_add','mul1'} and keys<=nodes.keys() and not used&keys:
            units.append(m);used.update(keys)
    # A structurally verified full adder may arrive without serialized child
    # hierarchy. Recover its two exact subcircuits from the matched grammar.
    for _,m in sorted(arithmetic.items(),key=lambda item:natural(item[0])):
        if m.module!='full_add':continue
        for child in ('ha1','ha2'):
            members=[m.cells[child+'.'+role] for role,_,_,_ in HALF]
            keys={'cell:'+name for name in members}
            if not keys<=nodes.keys() or keys&used:continue
            scope=(m.scope+'.' if m.scope else '')+child
            instances=[Instance(name,nodes['cell:'+name].kind,nodes['cell:'+name].inputs|nodes['cell:'+name].outputs) for name in members]
            sub=match(instances,scope)
            if sub:units.append(sub);used.update(keys)
    if not units:return []
    # A MAC writes its four multiplier primitives directly in the parent.
    # Recognize their connectivity, including ordered inputs, not their names.
    remaining={k:n for k,n in nodes.items() if n.kind not in {'input','output','block'} and k not in used}
    producer={s:n for n in remaining.values() for s in n.outputs.values()}
    for n in sorted(remaining.values(),key=lambda n:natural(n.key)):
        if n.kind!='NAND':continue
        todo=[n];cone={}
        while todo and len(cone)<=4:
            q=todo.pop()
            if q.key in cone:continue
            cone[q.key]=q
            todo.extend(producer[s] for s in q.inputs.values() if s in producer)
        if len(cone)!=4 or set(cone)&used:continue
        instances=[Instance(q.members[0],q.kind,q.inputs|q.outputs) for q in cone.values()]
        m=match(instances,'multiply')
        if m and m.module=='mul1':
            external={s for k,q in nodes.items() if k not in cone for s in q.inputs.values()}
            ports=dict(m.ports)
            for role,_,_,out in MUL:
                signal=nodes['cell:'+m.cells[role]].outputs['Y']
                if signal in external and signal not in ports.values():ports[out]=signal
            units.append(Arithmetic(m.module,m.scope,ports,m.cells));used.update(cone)
    return units


def compose(nodes,arithmetic):
    """Return cells, fixed local routes and a blocked outer routing problem."""
    units=_units(nodes,arithmetic)
    if not units:return None
    outer={k:n for k,n in nodes.items()};local=[];trunks=[];frames=[];proxies={};patterns={}
    for node in outer.values():anchors(node)
    # First create macro boundaries, retaining exact original net identities.
    for m in units:
        taps=tuple(sorted(set(m.ports)-{'a','b','p','sum','carry'}))
        gates,wires,rails,pins,sides,w,h=deepcopy(template(m.module,taps))
        signal_map=dict(m.ports)
        for role,actual in m.cells.items():
            original=nodes['cell:'+actual]
            canonical=next(n for n in gates if n.label==role)
            for pin,signal in (canonical.inputs|canonical.outputs).items():
                signal_map[signal]=(original.inputs|original.outputs)[pin]
        for actual in m.cells.values():outer.pop('cell:'+actual)
        key='macro:'+m.scope
        proxy=Symbol(key,'block',m.scope,tuple(m.cells.values()),
            {n:m.ports[n] for n in ('a','b')},
            {n:s for n,s in m.ports.items() if n not in {'a','b'}},
            level=min(nodes['cell:'+n].level for n in m.cells.values()),
            width=w,height=h,pins=pins,sides=sides,module=m.module)
        outer[key]=proxy;proxies[m.scope]=proxy
        patterns[key]=(m,gates,wires,rails,signal_map)
    # Rebuild connectivity at boundaries. Internal terminals stay in the
    # original connection ledger and are restored after external routing.
    out_driver={};out_loads=defaultdict(list)
    for key,n in outer.items():
        for p,s in n.outputs.items():out_driver[s]=(key,p)
        for p,s in n.inputs.items():out_loads[s].append((key,p))

    def put(n,x,y):
        dx,dy=x-n.x,y-n.y;n.x=x;n.y=y
        n.pins={p:(q[0]+dx,q[1]+dy) for p,q in n.pins.items()}

    # Full adders form one readable row per digit. The half-adder drawings are
    # identical; the carry combiner sits above the second half in a bus channel.
    fulls=[]
    for _,m in sorted(arithmetic.items(),key=lambda t:natural(t[0])):
        if m.module!='full_add':continue
        children=[(m.scope+'.' if m.scope else '')+n for n in ('ha1','ha2')]
        if all(c in proxies for c in children) and not any(set(m.cells.values())==set(p.cells.values()) for p in fulls):fulls.append(m)
    assigned=set();row_y=320
    if 'multiply' in proxies:row_y=960
    if any(n.kind=='block' and n.key not in patterns for n in outer.values()):row_y=max(row_y,704)
    for m in fulls:
        prefix=m.scope+'.' if m.scope else ''
        first,second=[proxies[prefix+n] for n in ('ha1','ha2')]
        put(first,320,row_y);put(second,320+first.width+256,row_y)
        assigned.update((first.key,second.key))
        nc,co=[outer['cell:'+m.cells[n]] for n in ('g_nc','g_cout')]
        x=second.pins['carry'][0]+160
        put(nc,x,row_y-192);put(co,x+192,row_y-192)
        assigned.update((nc.key,co.key));row_y+=max(first.height,second.height)+384
    # Four partial products retain their 2x2 operand matrix. Accumulating
    # half-adders sit at its right, so products never return to the left edge.
    products=sorted((p for p in proxies.values() if p.module=='mul1'),key=lambda n:natural(n.label))
    halves=sorted((p for p in proxies.values() if p.module=='half_add' and p.key not in assigned),key=lambda n:natural(n.label))
    if len(products)==4 and len(halves)==2:
        pitch=max(p.width for p in products)+192
        row_pitch=max(p.height for p in products)+224
        for i,p in enumerate(products):put(p,320+(i%2)*pitch,256+(i//2)*row_pitch);assigned.add(p.key)
        x=max(p.box[2] for p in products)+256
        for i,p in enumerate(halves):put(p,x,256+i*(p.height+320));assigned.add(p.key)
    elif products:
        for i,p in enumerate(products):put(p,320+i*(p.width+256),256);assigned.add(p.key)

    # Remaining logic includes MAC's three buffered Boolean outputs and
    # selectively collapsed digits. Keep those gates in the upper workspace.
    core=[n for n in outer.values() if n.kind not in {'input','output'} and n.key not in assigned]
    by_level=defaultdict(list)
    for n in core:by_level[n.level].append(n)
    bottom_by_x={}
    for column,level in enumerate(sorted(by_level)):
        for row,n in enumerate(sorted(by_level[level],key=lambda n:natural(n.key))):
            parents=[outer[out_driver[s][0]] for s in n.inputs.values() if s in out_driver and out_driver[s][0] in assigned]
            x=max((p.box[2]+192 for p in parents),default=320+column*320)
            y=max(128+row*192,bottom_by_x.get(x,128))
            put(n,x,y);assigned.add(n.key)
            bottom_by_x[x]=y+n.height+64

    # Boundary-local flags. A/b sit left of the frame they feed; cin naturally
    # lands in the gap between the two half adders. Signals never start above
    # a frame only to travel around its left edge.
    port_font=52 if len(products)==4 else 36
    core_boxes=[n.box for n in outer.values() if n.kind not in {'input','output'}]
    occupied=[];pin_access=[]
    normals={'left':(-1,0),'right':(1,0),'top':(0,-1),'bottom':(0,1)}
    def reserve(n):
        for pin,(x,y) in n.pins.items():
            dx,dy=normals[n.sides[pin]];ex,ey=x+32*dx,y+32*dy
            pin_access.append(((n.inputs|n.outputs)[pin],(min(x,ex)-16,min(y,ey)-16,max(x,ex)+16,max(y,ey)+16)))
    for n in outer.values():
        if n.kind not in {'input','output'}:reserve(n)
    def overlap(a,b,pad=16):return max(a[0]-pad,b[0])<min(a[2]+pad,b[2]) and max(a[1]-pad,b[1])<min(a[3]+pad,b[3])
    def free(box,node):
        if any(overlap(box,b) for b in core_boxes) or any(overlap(box,b,0) for b in occupied):return False
        foreign=[b for signal,b in pin_access if signal!=node.label]
        if any(overlap(box,b,0) for b in foreign):return False
        px=(box[0]+box[2])//2 if node.orient=='down' else box[2] if node.kind=='input' else box[0]
        py=box[3] if node.orient=='down' and node.kind=='input' else box[1] if node.orient=='down' else (box[1]+box[3])//2
        side=('bottom' if node.kind=='input' else 'top') if node.orient=='down' else ('right' if node.kind=='input' else 'left')
        dx,dy=normals[side];ex,ey=px+32*dx,py+32*dy
        lead=min(px,ex)-16,min(py,ey)-16,max(px,ex)+16,max(py,ey)+16
        return not any(overlap(lead,b,0) for b in core_boxes+occupied+foreign)
    for n in sorted((n for n in outer.values() if n.kind=='input'),key=lambda n:natural(n.label)):
        sinks=out_loads[n.label]
        if not sinks:
            anchors(n,font=port_font)
            put(n,32,max(b[3] for b in core_boxes+occupied)+96)
            occupied.append(n.box);reserve(n);continue
        target,pin=min(sinks,key=lambda kp:(outer[kp[0]].x,outer[kp[0]].pins[kp[1]][1]))
        tx,ty=outer[target].pins[pin]
        if len(products)==4 and tx>min(p.x for p in products) and all(outer[k].x==tx for k,_ in sinks):
            n.orient='down';anchors(n,font=port_font)
            put(n,tx-96-n.width//2,outer[target].y-n.height-96)
            occupied.append(n.box);reserve(n);continue
        anchors(n,font=port_font)
        x=tx-n.width-(160 if len(sinks)>1 else 96);y=ty-n.height//2
        for delta in [0]+[sign*d for d in range(48,1200,48) for sign in (-1,1)]:
            box=x,y+delta,x+n.width,y+delta+n.height
            if box[0]>=32 and box[1]>=80 and free(box,n):break
        put(n,x,y+delta);occupied.append(n.box);reserve(n)
    for n in sorted((n for n in outer.values() if n.kind=='output'),key=lambda n:natural(n.label)):
        key,pin=out_driver[n.label];producer=outer[key];x,y=producer.pins[pin]
        anchors(n,font=port_font)
        if producer.sides[pin]=='bottom':
            n.orient='down';anchors(n,font=port_font)
            px=x-n.width//2;py=y+96
            for delta in range(0,1200,64):
                box=(px+delta,py,px+delta+n.width,py+n.height)
                if free(box,n):break
            put(n,px+delta,py);occupied.append(n.box);reserve(n);continue
        # Carry exported from a macro uses a short lead above that boundary.
        if producer.sides[pin]=='top':x+=96;y-=96
        else:x+=48 if len(products)==4 and producer.module=='mul1' else 96
        for delta in [0]+[sign*d for d in range(48,1200,48) for sign in (-1,1)]:
            box=x,y-n.height//2+delta,x+n.width,y+n.height//2+delta
            if box[0]>=32 and box[1]>=80 and free(box,n):break
        put(n,x,y-n.height//2+delta);occupied.append(n.box);reserve(n)

    # Resolve local cell/net identities without changing a single local lane.
    for key,(m,gates,wires,rails,signal_map) in patterns.items():
        p=outer[key]
        shift=lambda q:(q[0]+p.x,q[1]+p.y)
        for canonical in gates:
            actual=m.cells[canonical.label];node=nodes['cell:'+actual]
            node.label=m.scope+'.'+canonical.label
            node.x=canonical.x+p.x;node.y=canonical.y+p.y
            node.width,node.height=canonical.width,canonical.height
            node.pins={pin:shift(q) for pin,q in canonical.pins.items()};node.sides=dict(canonical.sides)
        local.extend(Segment(signal_map[s.net],shift(s.a),shift(s.b)) for s in wires)
        trunks.extend(Segment(signal_map[s.net],shift(s.a),shift(s.b)) for s in rails)
        frames.append(Frame(m.scope,p.box,tuple(m.cells.values()),m.module,dict(p.pins),dict(p.sides),m.ports))
    width=max(n.box[2] for n in outer.values())+256
    height=max(n.box[3] for n in outer.values())+256
    return outer,out_driver,out_loads,frames,local,trunks,width,height
