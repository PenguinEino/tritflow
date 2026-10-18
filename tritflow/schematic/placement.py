"""Arithmetic-aware compaction and consumer/producer-local external ports."""
from collections import defaultdict
import math

from .model import Frame, natural


def anchors(node):
    """Keep every logic gate facing right, including gates in folded rows."""
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
    node.orient='right'
    node.width,node.height=80,96
    cy=y+56
    offsets=[0] if len(node.inputs)==1 else [-16,16]
    node.pins={p:(x,cy+off) for p,off in zip(node.inputs,offsets)}
    node.pins.update({p:(x+80,cy) for p in node.outputs})
    node.sides={p:'left' for p in node.inputs}|{p:'right' for p in node.outputs}


def _overlap(a,b,pad=0):
    return max(a[0]-pad,b[0])<min(a[2]+pad,b[2]) and max(a[1]-pad,b[1])<min(a[3]+pad,b[3])


def place(nodes,driver,loads,arithmetic):
    """Place verified arithmetic as small panels, then compact remaining logic.

    A full-adder flat panel contains two side-by-side framed half adders. Each
    half folds its latter stages into a lower left-to-right feedforward row.
    Standalone halves retain a straight t-net lane and align u with c's input.
    """
    frames=[];placed=set()
    for node in nodes.values():anchors(node)

    def put(node,x,y,orient='right'):
        node.x,node.y,node.orient=int(x),int(y),orient
        anchors(node);placed.add(node.key)

    def half(pattern,x,y,fold):
        positions=({'g_na':(0,0),'g_t':(0,112),'g_u':(112,96),'g_c':(224,16),
                    'g_d':(112,288),'g_nd':(224,288),'g_s':(336,304)} if fold else
                   {'g_t':(0,128),'g_u':(128,16),'g_na':(128,256),'g_c':(256,0),
                    'g_d':(384,144),'g_nd':(512,144),'g_s':(640,192)})
        for role,(dx,dy) in positions.items():
            node=nodes['cell:'+pattern.cells[role]]
            put(node,x+dx,y+dy)
        return (416,400) if fold else (720,352)

    def full(pattern,x,y):
        cursor=x;children=[]
        for child in ('ha1','ha2'):
            scope=(pattern.scope+'.' if pattern.scope else '')+child
            block=nodes.get('block:'+scope)
            if block:
                put(block,cursor,y+64);w=160
            else:
                sub=arithmetic.get(scope)
                if sub is None:return None
                w0,h0=half(sub,cursor+24,y+40,True)
                w,h=w0+48,h0+64
                frames.append(Frame(scope,(cursor,y,cursor+w,y+h),tuple(sub.cells.values())))
            children.append((cursor,w,block));cursor+=w+64
        x2,w2,second_block=children[1]
        # Carry combining gates sit alongside the upper half-adder row, so the
        # sum output can leave the lower row next to its actual producer.
        final_x=x2+w2+(128 if second_block else 40)
        # Align the second carry with B; the first carry needs one full-pitch
        # vertical leg. Leave the collapsed half's sum flag its own channel.
        carry=nodes['cell:'+pattern.cells['g_nc']].inputs['B']
        key,pin=driver[carry]
        final_y=nodes[key].pins[pin][1]-72
        put(nodes['cell:'+pattern.cells['g_nc']],final_x,final_y)
        put(nodes['cell:'+pattern.cells['g_cout']],final_x+112,final_y)

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
        else:
            # Two full cells per row for N>=3; two-trit flat views stack panels
            # to avoid recreating the original very wide ripple diagram.
            columns=2 if len(candidates)>=3 else 1
            for k,m in enumerate(candidates):
                x=base_x+(k%columns)*1392
                y=(320 if external_core else 176)+(k//columns)*640
                if 'block:'+m.scope in nodes:
                    node=nodes['block:'+m.scope];put(node,x,y)
                else:full(m,x,y)
    if not placed:
        root=arithmetic.get('')
        if root and root.module=='half_add' and all('cell:'+n in nodes for n in root.cells.values()):
            half(root,160,160,False)

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
        row_pitch=208 if any(n.kind=='block' for n in core) else 128
        fold_span=max(min(3,len(v)) for v in levels.values())*row_pitch+112
        unique=sorted(levels)
        column=0;fold=0
        for level in unique:
            def aligned_y(node):
                parents=[(nodes[driver[s][0]],driver[s][1],p)
                         for p,s in node.inputs.items() if driver[s][0] in placed]
                # A fanout from an earlier row should not pull the next gate
                # away from its adjacent producer in this feedforward row.
                row_top=offset_y+fold*fold_span
                local=[p for p in parents if p[0].y>=row_top-32]
                aligned=[parent.pins[out][1]-(node.pins[pin][1]-node.y)
                         for parent,out,pin in (local or parents)]
                return sum(aligned)/len(aligned) if aligned else row_top
            group=sorted(levels[level],key=lambda n:(aligned_y(n),natural(n.key)))
            percol=2 if len(group)>=4 and all(n.kind=='block' for n in group) else 3
            across=math.ceil(len(group)/percol)
            if column+across>4:column=0;fold+=1
            bottom_by_column={}
            for row,node in enumerate(group):
                col=column+row//percol
                base=offset_y+fold*fold_span
                minimum=bottom_by_column.get(col,base if col==0 else base-32)
                desired=8*round(aligned_y(node)/8)
                y=max(minimum,desired)
                put(node,160+col*208,y)
                bottom_by_column[col]=y+max(row_pitch,node.height+32)
            column+=across

    # External terminals follow their consumers/producers, not a bus-name sort
    # at opposite edges of the entire sheet. Preserve bit order within ties.
    occupied=[n.box for n in nodes.values() if n.key in placed]
    core_boxes=tuple(occupied)
    def free(box):
        # Labels may sit close to other port labels, while gate terminals need
        # their outward access segment clear even beyond the symbol keep-out.
        return (not any(_overlap(box,b,16) for b in core_boxes)
                and not any(_overlap(box,b) for b in occupied))
    def port(node,preferred,orient):
        px,py=preferred
        # Search nearby whole-grid offsets, keeping horizontal anchors aligned
        # whenever possible. Resolve unused inputs after all connected ports.
        options=[(0,0)]+[(0,sign*d) for d in range(16,257,16) for sign in (-1,1)]
        options += [(dx,dy) for dy in (-96,96,-192,192) for dx in (-96,96,0)]
        for dx,dy in options:
            box=(px+dx,py+dy,px+dx+node.width,py+dy+32)
            if box[0]>=32 and box[1]>=88 and free(box):
                put(node,box[0],box[1],orient);occupied.append(node.box);return
        # Rare dense edge: place in a free lower margin, retaining the true net.
        py=max((b[3] for b in occupied),default=128)+64
        put(node,max(32,px),py,orient);occupied.append(node.box)
    ports=sorted((n for n in nodes.values() if n.kind=='input'),key=lambda n:(
        min((nodes[k].x for k,_ in loads[n.label]),default=1e9),natural(n.label)))
    top_slots=defaultdict(int)
    for node in ports:
        sinks=loads[node.label]
        if not sinks:
            bottom=max((b[3] for b in occupied),default=128)+48
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
    width=max(400,max((n.x+n.width for n in nodes.values()),default=0)+48)
    height=max((n.y+n.height for n in nodes.values()),default=112)+96
    return tuple(frames),width,height
