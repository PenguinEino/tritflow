"""Bend-aware rectilinear Steiner trees on a shared eight-pixel drawing grid.

Different nets may cross at straight segments, but never share an edge, end on
another net, or turn at a crossing. Same-net branches connect to an existing
trunk instead of drawing a separate detour for every pin.
"""
from collections import defaultdict
import heapq
from itertools import count

from .model import Segment, natural

STEP=8
DIRECTIONS=((8,0),(-8,0),(0,8),(0,-8))
NORMAL={'right':(8,0),'left':(-8,0),'top':(0,-8),'bottom':(0,8)}


def route(nodes,driver,loads,width,height,frames=()):
    """Route each electrical net once, preferring short paths with few turns."""
    blocked=set()
    for node in nodes.values():
        x0,y0,x1,y1=node.box
        blocked.update((x,y) for x in range(x0,x1+1,8) for y in range(y0,y1+1,8))
    for frame in frames:
        x0,y0,x1,y1=frame.box
        blocked.update((x,y) for x in range(x0+16,min(x1,x0+16+len(frame.label)*8)+1,8)
                       for y in range(y0,y0+32,8))
    for node in nodes.values():
        blocked.difference_update(node.pins.values())
    terminals={};reserved={}
    for node in nodes.values():
        for pin,point in node.pins.items():
            signal=({**node.inputs,**node.outputs})[pin]
            terminals[point]=signal
            dx,dy=NORMAL[node.sides[pin]]
            for k in (1,2):reserved[(point[0]+k*dx,point[1]+k*dy)]=signal
    edges={};at=defaultdict(dict);segments=[]

    def axis(a,b):return 0 if a[1]==b[1] else 1
    def edge(a,b):return tuple(sorted((a,b)))
    def add(signal,path):
        for a,b in zip(path,path[1:]):
            edges[edge(a,b)]=signal
            d=axis(a,b)
            at[a].setdefault(signal,set()).add(d);at[b].setdefault(signal,set()).add(d)
            segments.append(Segment(signal,a,b))

    def find(signal,start,normal,tree):
        xs=[p[0] for p in tree];ys=[p[1] for p in tree]
        bounds=min(xs),min(ys),max(xs),max(ys)
        def heuristic(p):
            return max(bounds[0]-p[0],0,p[0]-bounds[2])+max(bounds[1]-p[1],0,p[1]-bounds[3])
        # A shortest tree attachment ends at the first existing same-net point.
        q=[];serial=count();best={};previous={}
        state=(start,2)
        heapq.heappush(q,(heuristic(start),0,next(serial),state));best[state]=0
        finish=None
        while q:
            _,cost,_,state=heapq.heappop(q)
            if cost!=best[state]:continue
            p,old_axis=state
            if p in tree:
                finish=state;break
            for dx,dy in DIRECTIONS:
                if p==start and (dx,dy)!=normal:continue
                nxt=(p[0]+dx,p[1]+dy)
                if not (8<=nxt[0]<=width-8 and 80<=nxt[1]<=height-48):continue
                if nxt in blocked and nxt not in tree:continue
                if nxt in terminals and terminals[nxt]!=signal:continue
                if nxt in reserved and reserved[nxt]!=signal:continue
                used=edges.get(edge(p,nxt))
                if used is not None and used!=signal:continue
                new_axis=0 if dy==0 else 1
                # Crossing a wire must continue straight. A corner or T join
                # of another net is never a legal crossing point.
                foreign=at[p].keys()-{signal}
                if foreign and (new_axis!=old_axis or any(at[p][n]!={1-new_axis} for n in foreign)):continue
                other=at[nxt].keys()-{signal}
                if other and any(at[nxt][n]!={1-new_axis} for n in other):continue
                if other and nxt in tree:continue
                penalty=(24 if old_axis!=2 and old_axis!=new_axis else 0)+12*len(other)
                new_cost=cost+8+penalty
                new_state=(nxt,new_axis)
                if new_cost<best.get(new_state,float('inf')):
                    best[new_state]=new_cost;previous[new_state]=state
                    heapq.heappush(q,(new_cost+heuristic(nxt),new_cost,next(serial),new_state))
        if finish is None:
            raise ValueError(f'No schematic route for {signal!r} at {start}; tree={sorted(tree)[:5]}, start wires={at[start]}, source wires={at[next(iter(tree))]}, visited={len(best)}')
        path=[];state=finish
        while True:
            path.append(state[0])
            if state not in previous:break
            state=previous[state]
        return list(reversed(path))

    # Straight adjacent-module connections, notably cout -> cin, reserve their
    # tracks first. Then route short/local nets before longer fanout trees.
    def order(signal):
        source=nodes[driver[signal][0]].pins[driver[signal][1]]
        destinations=[nodes[k].pins[p] for k,p in loads[signal]]
        straight=len(destinations)==1 and (source[0]==destinations[0][0] or source[1]==destinations[0][1])
        distance=sum(abs(source[0]-p[0])+abs(source[1]-p[1]) for p in destinations)
        return (not straight,distance,natural(signal))
    for signal in sorted(driver,key=order):
        key,pin=driver[signal];source=nodes[key].pins[pin]
        tree={source}
        destinations=sorted(loads[signal],key=lambda kp:(
            abs(nodes[kp[0]].pins[kp[1]][0]-source[0])+abs(nodes[kp[0]].pins[kp[1]][1]-source[1]),natural(kp[0]),kp[1]))
        if not destinations:
            dx,dy=NORMAL[nodes[key].sides[pin]]
            path=[(source[0]+dx*k,source[1]+dy*k) for k in range(4)]
            add(signal,path)
        for k,p in destinations:
            start=nodes[k].pins[p]
            path=find(signal,start,NORMAL[nodes[k].sides[p]],tree)
            add(signal,path);tree.update(path)
    return segments
