"""Deterministic channel tracks for circuits that exhaust compact maze routing.

Each logic level has its own column. Adjacent levels connect in their channel;
separate vertical lanes carry long nets to interval-coloured horizontal tracks
above the gates. A net can cross intermediate levels without crossing a symbol.
This trades canvas area for bounded routing work on large, reconvergent cones.
"""
from collections import defaultdict

from .model import Segment, natural
from .placement import anchors
from .rules import PIN_RUN, PITCH, TRUNK_PITCH


def channel_layout(nodes, driver, loads):
    """Place and connect an acyclic left-to-right view with reserved net lanes.

    Long-net drivers have distinct escape lanes; all consumers of one net in
    a column share one receiving lane. Only nonoverlapping horizontal intervals
    reuse an upper track. Parallel foreign wires cannot overlap, and crossings
    stay on straight runs away from a pin, bend or junction.
    """
    levels=defaultdict(list)
    for node in nodes.values():
        anchors(node,font=20,input_pitch=2*PITCH,stagger_unary=True)
        if any(side not in {'left','right'} for side in node.sides.values()):
            raise ValueError('channel tracks require left/right boundary pins')
        levels[node.level].append(node)
    ranks=sorted(levels)
    groups={level:sorted(levels[level],key=lambda n:(n.y,natural(n.key))) for level in ranks}
    following=dict(zip(ranks,ranks[1:]))
    # Gate inputs lie one pitch above/below gate outputs, including unary
    # inputs. This prevents collinear foreign pin approaches in a channel.
    # Arbitrary module blocks retain their boundary grammar and use the
    # separated global lanes instead.
    staggered=all(n.kind!='block' for n in nodes.values())
    local={s for s,(key,pin) in driver.items() if staggered and loads[s]
           and all(nodes[k].level==following.get(nodes[key].level) for k,p in loads[s])}
    sources={level:sorted((s for s,(k,p) in driver.items()
                           if nodes[k].level==level and loads[s] and s not in local),key=natural)
             for level in ranks}
    receivers={level:sorted({s for n in groups[level] for s in n.inputs.values()},key=natural)
               for level in ranks}
    outgoing={};incoming={};cursor=64
    # All pin approaches stay in their adjacent channel. Drivers use its
    # left half and receivers its right half, even when their y values match.
    for index,level in enumerate(ranks):
        for node in groups[level]:node.x=cursor
        cursor+=max(n.width for n in groups[level])+2*PIN_RUN
        for signal in sources[level]:
            outgoing[signal]=cursor;cursor+=TRUNK_PITCH
        if index+1<len(ranks):
            for signal in receivers[ranks[index+1]]:
                incoming[signal,ranks[index+1]]=cursor;cursor+=TRUNK_PITCH
        cursor+=2*PIN_RUN

    spans={s:(outgoing[s],max((incoming[s,nodes[k].level] for k,p in loads[s]),default=outgoing[s]))
           for s in outgoing}
    track_ends=[];tracks={}
    for signal,(lo,hi) in sorted(spans.items(),key=lambda item:(item[1][0],natural(item[0]))):
        if not loads[signal]:continue
        track=next((i for i,end in enumerate(track_ends) if end+TRUNK_PITCH<=lo),len(track_ends))
        if track==len(track_ends):track_ends.append(hi)
        else:track_ends[track]=hi
        tracks[signal]=64+track*TRUNK_PITCH

    top=128+len(track_ends)*TRUNK_PITCH
    row_pitch=max(192,32*((max(n.height for n in nodes.values())+64+31)//32))
    for level,group in groups.items():
        for row,node in enumerate(group):
            node.y=top+16+row*row_pitch
            anchors(node,font=20,input_pitch=2*PITCH,stagger_unary=True)

    wires=[];trunks=[]
    def line(signal,a,b):
        if a!=b:wires.append(Segment(signal,min(a,b),max(a,b)))
    for signal,(key,pin) in driver.items():
        source=nodes[key].pins[pin]
        if not loads[signal]:
            line(signal,source,(source[0]+PIN_RUN,source[1]));continue
        if signal in local:
            # An adjacent-level connection fits entirely in that channel.
            # Its receiving lane doubles as the fanout trunk; short inverter
            # chains need no round trip through the upper long-net tracks.
            points=[nodes[k].pins[p] for k,p in loads[signal]]
            x=incoming[signal,nodes[loads[signal][0][0]].level]
            ys=[source[1],*(p[1] for p in points)]
            line(signal,source,(x,source[1]))
            line(signal,(x,min(ys)),(x,max(ys)))
            for point in points:line(signal,(x,point[1]),point)
            if len(loads[signal])>1:trunks.append(Segment(signal,(x,min(ys)),(x,max(ys))))
            continue
        x=outgoing[signal];y=tracks[signal]
        line(signal,source,(x,source[1]))
        line(signal,(x,y),(x,source[1]))
        bus=Segment(signal,(x,y),(spans[signal][1],y))
        wires.append(bus)
        if len(loads[signal])>1:trunks.append(bus)
        sinks=defaultdict(list)
        for k,p in loads[signal]:sinks[nodes[k].level].append(nodes[k].pins[p])
        for level,points in sinks.items():
            x=incoming[signal,level]
            line(signal,(x,y),(x,max(p[1] for p in points)))
            for point in points:line(signal,(x,point[1]),point)
    width=max(n.box[2] for n in nodes.values())+64
    height=max(n.box[3] for n in nodes.values())+64
    return wires,tuple(trunks),width,height
