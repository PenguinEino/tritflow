"""Independent geometry checks for publication schematic clearances."""
from collections import Counter,defaultdict

from .model import Segment
from .rules import PITCH,CLEARANCE,TRUNK_PITCH,PIN_RUN,box,distance,parallel_gap

NORMAL={'left':(-1,0),'right':(1,0),'top':(0,-1),'bottom':(0,1)}


def inspect(scene):
    """Return concrete violations; an empty list means all spacing rules pass.

    Clearances use centre lines and closed symbol/label keep-outs. Intentional
    perpendicular crossings away from pins/dots are permitted. Own pin entry
    is the only exception to the symbol keep-out, never a foreign pin entry.
    """
    problems=[]
    wires=scene.segments
    for i,a in enumerate(wires):
        for b in wires[i+1:]:
            if a.net==b.net:continue
            gap=parallel_gap(a,b)
            if gap is not None and gap<PITCH:problems.append(('parallel',a,b,gap))
    for i,a in enumerate(scene.trunks):
        for b in scene.trunks[i+1:]:
            gap=parallel_gap(a,b)
            if a.net!=b.net and gap is not None and gap<TRUNK_PITCH:problems.append(('trunk_spacing',a,b,gap))
    for node in scene.symbols:
        for pin,point in node.pins.items():
            net=(node.inputs|node.outputs)[pin];dx,dy=NORMAL[node.sides[pin]]
            end=point[0]+dx*PIN_RUN,point[1]+dy*PIN_RUN
            stub=Segment(net,min(point,end),max(point,end))
            for w in wires:
                if w.net!=net and distance(box(w),box(stub))<CLEARANCE:problems.append(('pin_clearance',node.key,pin,w))
            # Every point of the straight escape must exist. No perpendicular
            # leg may meet its interior, even when the electrical net is same.
            for k in range(0,PIN_RUN,8):
                p=point[0]+dx*k,point[1]+dy*k
                for w in wires:
                    if w.net!=net:continue
                    horizontal=w.a[1]==w.b[1]
                    if horizontal==bool(dx):continue
                    if (w.a[0]<=p[0]<=w.b[0] and w.a[1]<=p[1]<=w.b[1]):problems.append(('pin_jog',node.key,pin,w))
            assert_line=any(w.net==net and (w.a[1]==w.b[1]==point[1] and w.a[0]<=stub.a[0]<=stub.b[0]<=w.b[0]
                             if dx else w.a[0]==w.b[0]==point[0] and w.a[1]<=stub.a[1]<=stub.b[1]<=w.b[1]) for w in wires)
            if not assert_line:problems.append(('pin_run',node.key,pin))
        for w in wires:
            if distance(box(w),node.box)>=CLEARANCE:continue
            allowed=False
            for pin,p in node.pins.items():
                if (node.inputs|node.outputs)[pin]!=w.net:continue
                side=node.sides[pin]
                allowed|=(side=='left' and w.a[1]==w.b[1]==p[1] and w.b[0]<=p[0])
                allowed|=(side=='right' and w.a[1]==w.b[1]==p[1] and w.a[0]>=p[0])
                allowed|=(side=='top' and w.a[0]==w.b[0]==p[0] and w.b[1]<=p[1])
                allowed|=(side=='bottom' and w.a[0]==w.b[0]==p[0] and w.a[1]>=p[1])
            if not allowed:problems.append(('symbol_clearance',node.key,w))
    for net,points in scene.junctions.items():
        for p in points:
            for w in wires:
                if w.net!=net and distance((p[0],p[1],p[0],p[1]),box(w))<CLEARANCE:problems.append(('dot_clearance',net,p,w))
    # One trunk in each routing domain. Reusing a module preserves its own
    # local operand buses; the parent has one separate bus between boundaries.
    domains=defaultdict(Counter)
    framed={m:f.label for f in scene.frames if f.pins for m in f.members}
    for n in scene.symbols:
        domain=next((framed[m] for m in n.members if m in framed),'')
        for signal in n.inputs.values():domains[domain][signal]+=1
    for f in scene.frames:
        for name,signal in f.nets.items():
            if f.sides[name]=='left':domains[''][signal]+=1
            else:domains[f.label][signal]+=1
    expected=Counter()
    for fanouts in domains.values():expected.update(s for s,count in fanouts.items() if count>1)
    counts=Counter(s.net for s in scene.trunks)
    if counts!=expected:problems.append(('fanout_trunks',expected,counts))
    for frame in scene.frames:
        for w in scene.interconnect:
            a,b,c,d=frame.box
            inside=(a<w.a[0]<c and max(b,w.a[1])<min(d,w.b[1]) if w.a[0]==w.b[0]
                    else b<w.a[1]<d and max(a,w.a[0])<min(c,w.b[0]))
            if inside:problems.append(('frame_channel',frame.label,w))
    return problems


def counts(scene):
    """Stable review counters without serializing internal geometry objects."""
    result=Counter(p[0] for p in inspect(scene))
    names=('parallel','trunk_spacing','pin_clearance','pin_jog','pin_run','symbol_clearance','dot_clearance','fanout_trunks','frame_channel')
    return {name:result[name] for name in names}
