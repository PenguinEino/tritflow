"""Arithmetic-aware compaction and consumer/producer-local external ports."""
from collections import defaultdict
import math

from .model import Frame, natural


def anchors(node):
    """Gate terminal coordinates; down-facing gates fold feedforward rows."""
    x,y=node.x,node.y
    if node.kind in {'input','output'}:
        node.width,node.height=max(48,16*math.ceil((len(node.label)*6+16)/16)),32
        side=('bottom' if node.kind=='input' else 'top') if node.orient=='down' else ('right' if node.kind=='input' else 'left')
        point={'bottom':(x+node.width//2,y+32),'top':(x+node.width//2,y),'left':(x,y+16),'right':(x+node.width,y+16)}[side]
        node.pins={'port':point};node.sides={'port':side}
        return
    if node.kind=='block':
        node.width=160
        node.height=max(160,64+32*max(len(node.inputs),len(node.outputs)))
        by_alias={node.pin_labels.get(p,s):p for p,s in {**node.inputs,**node.outputs}.items()}
        if node.module=='full_add' and set(by_alias)>={'a','b','cin','sum','cout'}:
            placement={'a':('top',48),'b':('top',112),'cin':('left',104),'cout':('right',104),'sum':('bottom',80)}
        else:
            placement={}
        node.pins={};node.sides={}
        for direction,pins in [('left',node.inputs),('right',node.outputs)]:
            for k,(p,signal) in enumerate(pins.items()):
                side,offset=placement.get(node.pin_labels.get(p,signal),(direction,80+32*k))
                node.sides[p]=side
                node.pins[p]={'left':(x,y+offset),'right':(x+node.width,y+offset),
                              'top':(x+offset,y),'bottom':(x+offset,y+node.height)}[side]
        return
    node.width,node.height=80,96
    cy=y+56
    if node.orient=='down':
        offsets=[0] if len(node.inputs)==1 else [-16,16]
        node.pins={p:(x+40-off,y) for p,off in zip(node.inputs,offsets)}
        node.pins.update({p:(x+40,y+96) for p in node.outputs})
        node.sides={p:'top' for p in node.inputs}|{p:'bottom' for p in node.outputs}
    else:
        offsets=[0] if len(node.inputs)==1 else [-16,16]
        node.pins={p:(x,cy+off) for p,off in zip(node.inputs,offsets)}
        node.pins.update({p:(x+80,cy) for p in node.outputs})
        node.sides={p:'left' for p in node.inputs}|{p:'right' for p in node.outputs}


def _overlap(a,b,pad=0):
    return max(a[0]-pad,b[0])<min(a[2]+pad,b[2]) and max(a[1]-pad,b[1])<min(a[3]+pad,b[3])


def place(nodes,driver,loads,arithmetic):
    """Place verified arithmetic as small panels, then compact remaining logic.

    A full-adder flat panel contains two side-by-side framed half adders. Each
    half folds its latter stages into a lower feedforward row; a downward NANY
    marks the row transition. Standalone halves retain a straight t-net lane.
    """
    frames=[];placed=set();panels=[]
    for node in nodes.values():anchors(node)

    def put(node,x,y,orient='right'):
        node.x,node.y,node.orient=int(x),int(y),orient
        anchors(node);placed.add(node.key)

    def half(pattern,x,y,fold):
        positions=({'g_na':(0,0),'g_t':(0,112),'g_u':(112,112),'g_c':(224,0),
                    'g_d':(112,240),'g_nd':(224,288),'g_s':(336,304)} if fold else
                   {'g_t':(0,128),'g_u':(128,0),'g_na':(128,256),'g_c':(256,0),
                    'g_d':(384,144),'g_nd':(512,144),'g_s':(640,192)})
        for role,(dx,dy) in positions.items():
            node=nodes['cell:'+pattern.cells[role]]
            put(node,x+dx,y+dy,'down' if fold and role=='g_d' else 'right')
        return (416,400) if fold else (720,352)

    def full(pattern,x,y):
        cursor=x;children=[]
        for child in ('ha1','ha2'):
            scope=(pattern.scope+'.' if pattern.scope else '')+child
            block=nodes.get('block:'+scope)
            if block:
                put(block,cursor,y+64);w,h=160,224
            else:
                sub=arithmetic.get(scope)
                if sub is None:return None
                w0,h0=half(sub,cursor+24,y+40,True)
                w,h=w0+48,h0+64
                frames.append(Frame(scope,(cursor,y,cursor+w,y+h),tuple(sub.cells.values())))
            children.append((cursor,w,h));cursor+=w+64
        x2,w2,h2=children[1]
        # Carry combining gates sit alongside the upper half-adder row, so the
        # sum output can leave the lower row next to its actual producer.
        final_x=x2+w2+40
        put(nodes['cell:'+pattern.cells['g_nc']],final_x,y+64)
        put(nodes['cell:'+pattern.cells['g_cout']],final_x+112,y+64)
        return final_x+192-x,max(h for _,_,h in children)

    # Prefer deepest aliases when generate-only and module scopes contain the
    # same instances; never draw a generate wrapper as another arithmetic unit.
    candidates=[]
    for scope,m in sorted(arithmetic.items(),key=lambda kv:(-len(kv[0]),natural(kv[0]))):
        if m.module!='full_add':continue
        member_set=set(m.cells.values())
        if any(member_set==set(other.cells.values()) for other in candidates):continue
        if 'block:'+scope in nodes or all('cell:'+n in nodes for n in member_set):
            candidates.append(m)
        elif scope=='' and all('block:'+child in nodes or all('cell:'+name in nodes for name in arithmetic.get(child,m).cells.values()) for child in ('ha1','ha2')):
            candidates.append(m)
    candidates.sort(key=lambda m:natural(m.scope))
    full_keys={'cell:'+name for m in candidates for name in m.cells.values()}
    full_keys.update('block:'+m.scope for m in candidates)
    external_core=bool(candidates) and any(
        n.kind not in {'input','output'} and n.key not in full_keys for n in nodes.values())
    if any(m.scope=='' for m in candidates):external_core=False
    # Keep external multiplier/min/max producers to the left of their full
    # adder load, including when the latter is a single collapsed block.
    base_x=960 if external_core else 160
    if candidates:
        closed=all('block:'+m.scope in nodes for m in candidates)
        if closed:
            for k,m in enumerate(candidates):
                node=nodes['block:'+m.scope]
                put(node,base_x+224*k,200)
                panels.append((node.x,node.y,node.x+160,node.y+160))
        else:
            # Two full cells per row for N>=3; two-trit flat views stack panels
            # to avoid recreating the original very wide ripple diagram.
            columns=2 if len(candidates)>=3 else 1
            if len(candidates)==1:columns=1
            for k,m in enumerate(candidates):
                x=base_x+(k%columns)*1392
                y=(320 if external_core else 176)+(k//columns)*640
                if 'block:'+m.scope in nodes:
                    node=nodes['block:'+m.scope];put(node,x,y)
                    size=(160,160)
                else:size=full(m,x,y)
                if size:panels.append((x,y,x+size[0],y+size[1]))
    if not placed:
        root=arithmetic.get('')
        if root and root.module=='half_add' and all('cell:'+n in nodes for n in root.cells.values()):
            w,h=half(root,160,160,False);panels.append((160,160,160+w,160+h))

    # Other recognized module instances also remain visually grouped when
    # flattened (e.g. four one-trit multipliers and two half adders in mul2).
    units=[];unit_members=set()
    for scope,m in sorted(arithmetic.items(),key=lambda kv:(-len(kv[0]),natural(kv[0]))):
        keys={'cell:'+name for name in m.cells.values()}
        if not scope or m.module not in {'half_add','mul1'} or keys&placed or keys&unit_members:continue
        if keys<=nodes.keys():
            units.append(m);unit_members.update(keys)
    if units:
        units.sort(key=lambda m:(min(nodes['cell:'+n].level for n in m.cells.values()),natural(m.scope)))
        columns=3 if len(units)>=5 else 2
        base_y=max((n.y+n.height for n in nodes.values() if n.key in placed),default=64)+112
        for k,m in enumerate(units):
            x=160+(k%columns)*560;y=base_y+(k//columns)*560
            if m.module=='half_add':w,h=half(m,x+24,y+40,True)
            else:
                coords={'g_t1':(0,0),'g_t2':(0,128),'g_t3':(128,128),'g_p':(256,64)}
                for role,(dx,dy) in coords.items():put(nodes['cell:'+m.cells[role]],x+24+dx,y+40+dy)
                w,h=336,224
            frames.append(Frame(m.scope,(x,y,x+w+48,y+h+64),tuple(m.cells.values())))

    core=[n for n in nodes.values() if n.kind not in {'input','output'} and n.key not in placed]
    if core:
        levels=defaultdict(list)
        for n in core:levels[n.level].append(n)
        bottom=max((n.y+n.height for n in nodes.values() if n.key in placed),default=48)
        offset_y=160 if external_core or not placed else bottom+112
        fold_span=max(min(3,len(v)) for v in levels.values())*208+112
        unique=sorted(levels)
        column=0;fold=0
        for level in unique:
            group=sorted(levels[level],key=lambda n:natural(n.key))
            across=math.ceil(len(group)/3)
            if column+across>4:column=0;fold+=1
            for row,node in enumerate(group):
                put(node,160+(column+row//3)*208,offset_y+fold*fold_span+(row%3)*208)
            column+=across

    # External terminals follow their consumers/producers, not a bus-name sort
    # at opposite edges of the entire sheet. Preserve bit order within ties.
    occupied=[n.box for n in nodes.values() if n.key in placed]
    def free(box):return not any(_overlap(box,b,0) for b in occupied)
    def port(node,preferred,orient):
        px,py=preferred
        # Search nearby whole-grid offsets, keeping horizontal anchors aligned
        # whenever possible. Resolve unused inputs after all connected ports.
        options=[(0,0)]+[(0,d*48) for d in (-1,1,-2,2,-3,3)]
        options += [(dx,dy) for dy in (-96,96,-192,192) for dx in (-96,96,0)]
        for dx,dy in options:
            box=(px+dx,py+dy,px+dx+node.width,py+dy+32)
            if box[0]>=32 and box[1]>=88 and free(box):
                put(node,box[0],box[1],orient);occupied.append(node.box);return
        # Rare dense edge: place in a free lower margin, retaining the true net.
        py=max(b[3] for b in occupied)+64
        put(node,max(32,px),py,orient);occupied.append(node.box)
    ports=sorted((n for n in nodes.values() if n.kind=='input'),key=lambda n:(
        min((nodes[k].x for k,_ in loads[n.label]),default=1e9),natural(n.label)))
    top_slots=defaultdict(int)
    for node in ports:
        sinks=loads[node.label]
        if not sinks:
            bottom=max(b[3] for b in occupied)+48
            port(node,(48,bottom),'right');continue
        key,pin=min(sinks,key=lambda p:(nodes[p[0]].x,nodes[p[0]].pins[p[1]][1]))
        target=nodes[key];tx,ty=target.pins[pin]
        if target.sides[pin]=='top':
            port(node,(tx-node.width//2,ty-80),'down')
        else:
            containing=[f for f in frames if target.members and target.members[0] in f.members]
            if containing:
                frame=containing[0];slot=top_slots[frame.label];top_slots[frame.label]+=1
                port(node,(frame.box[0]+48+slot*88,frame.box[1]-80),'down')
            else:
                ys=[nodes[k].pins[p][1] for k,p in sinks if nodes[k].x==target.x]
                cy=8*round(sum(ys)/len(ys)/8)
                port(node,(tx-96,cy-16),'right')
    for node in sorted((n for n in nodes.values() if n.kind=='output'),key=lambda n:natural(n.label)):
        key,pin=driver[node.label];producer=nodes[key];x,y=producer.pins[pin]
        side=producer.sides[pin]
        if side=='bottom':port(node,(x-node.width//2,y+48),'down')
        else:port(node,(x+48,y-16),'right')
    width=max(640,max((n.x+n.width for n in nodes.values()),default=0)+48)
    height=max((n.y+n.height for n in nodes.values()),default=112)+96
    return tuple(frames),width,height
