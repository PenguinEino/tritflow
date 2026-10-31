"""Clearance-aware channel routing, straight pin access and ordered fanout."""
from collections import defaultdict
import heapq
from itertools import count
from functools import lru_cache

from .model import Segment,natural
from .rules import RASTER as STEP,PITCH,CLEARANCE,TRUNK_PITCH,PIN_RUN

DIRECTIONS=((STEP,0),(-STEP,0),(0,STEP),(0,-STEP))
NORMAL={'right':(STEP,0),'left':(-STEP,0),'top':(0,-STEP),'bottom':(0,STEP)}


def route(nodes,driver,loads,width,height,frames=(),*,fanout_first=False,search_limit=None,
          reserve_feeds=False):
    """Reserve straight pin escapes, then route shared, separated net trees.

    Wider retry sheets also reserve the driver-to-bus feed before connecting
    loads. A bounded, weighted search favours progress across a large cone;
    the original compact drawings retain their unweighted search and order.
    """
    blocked=defaultdict(set);access=defaultdict(set);pin_halo=defaultdict(set)
    frame_text=set();stubs={};pin_axis={}
    def area(x0,y0,x1,y1):
        return ((x,y) for x in range(x0,x1+1,STEP) for y in range(y0,y1+1,STEP))
    for key,node in nodes.items():
        x0,y0,x1,y1=node.box
        for p in area(x0-CLEARANCE+STEP,y0-CLEARANCE+STEP,x1+CLEARANCE-STEP,y1+CLEARANCE-STEP):blocked[p].add(key)
        for pin,p in node.pins.items():
            signal=(node.inputs|node.outputs)[pin]
            dx,dy=NORMAL[node.sides[pin]]
            path=[(p[0]+dx*k,p[1]+dy*k) for k in range(PIN_RUN//STEP+1)]
            stubs[key,pin]=path
            for point in path[:-1]:pin_axis[signal,point]=0 if dx else 1
            for point in path:
                access[signal,point].add(key)
                for q in area(point[0]-CLEARANCE+STEP,point[1]-CLEARANCE+STEP,point[0]+CLEARANCE-STEP,point[1]+CLEARANCE-STEP):pin_halo[q].add(signal)
    for frame in frames:
        x0,y0,_,_=frame.box
        frame_text.update(area(x0+8,y0,min(frame.box[2]-8,x0+24+8*len(frame.label)),y0+32))
    edges={};at=defaultdict(dict);parallel=defaultdict(set)
    trunk_halo=defaultdict(set);dot_halo=defaultdict(set)
    trunks={};spines={};rails={};local_loads={}

    def axis(a,b):return 0 if a[1]==b[1] else 1
    def edge(a,b):return tuple(sorted((a,b)))
    def track(a,b):
        p=min(a,b)
        return axis(a,b),p[0],p[1]
    def clear(signal,p):
        return (not blocked[p]-access[signal,p] and p not in frame_text
                and not pin_halo[p]-{signal} and not dot_halo[p]-{signal})
    def dot_clear(signal,p):
        return not any(at[q].keys()-{signal} for q in area(p[0]-16,p[1]-16,p[0]+16,p[1]+16))

    def add(signal,path,trunk=False):
        for a,b in zip(path,path[1:]):
            if edges.get(edge(a,b))==signal:continue
            edges[edge(a,b)]=signal
            d=axis(a,b)
            at[a].setdefault(signal,set()).add(d);at[b].setdefault(signal,set()).add(d)
            _,x,y=track(a,b)
            for offset in range(-PITCH+STEP,PITCH,STEP):
                parallel[d,x+(offset if d else 0),y+(offset if d==0 else 0)].add(signal)
            if trunk:
                for offset in range(-TRUNK_PITCH+STEP,TRUNK_PITCH,STEP):
                    trunk_halo[d,x+(offset if d else 0),y+(offset if d==0 else 0)].add(signal)
        for p in path:
            degree=sum(edges.get(edge(p,(p[0]+dx,p[1]+dy)))==signal for dx,dy in DIRECTIONS)
            if degree>=3:
                for q in area(p[0]-16,p[1]-16,p[0]+16,p[1]+16):dot_halo[q].add(signal)

    # Protect the last full pitch before every pin before any other wire routes.
    for (key,pin),path in stubs.items():
        signal=(nodes[key].inputs|nodes[key].outputs)[pin]
        if any(not clear(signal,p) for p in path):raise ValueError(f'Pin clearance is congested at {key}.{pin}')
        add(signal,path)

    def rail(signal):
        key,pin=driver[signal];source=nodes[key];point=source.pins[pin]
        sinks=loads[signal]
        scope=source.label.rsplit('.',1)[0] if '.' in source.label else ''
        local=[(k,p) for k,p in sinks if nodes[k].kind not in {'input','output'}
               and (nodes[k].label.rsplit('.',1)[0] if '.' in nodes[k].label else '')==scope]
        if source.kind=='input' or len(local)<2:local=sinks
        local_loads[signal]=set(local)
        ends=[stubs[k,p][-1] for k,p in local]
        vertical=source.kind=='input' or all(nodes[k].pins[p][0]>point[0] for k,p in local)
        if vertical:
            base=(min(nodes[k].pins[p][0] for k,p in local)-PIN_RUN-CLEARANCE
                  if source.sides[pin]=='bottom' else point[0]+PIN_RUN+CLEARANCE)
            lo=min(p[1] for p in ends+[stubs[key,pin][-1]])
            hi=max(p[1] for p in ends+[stubs[key,pin][-1]])
        else:
            base=max(nodes[k].box[3] for k,p in local)+PITCH
            lo=min(p[0] for p in ends+[stubs[key,pin][-1]])
            hi=max(p[0] for p in ends+[stubs[key,pin][-1]])
        if lo==hi:hi+=PITCH
        for offset in [0,-16,16]+[sign*d for d in range(TRUNK_PITCH,max(width,height),TRUNK_PITCH) for sign in (1,-1)]:
            fixed=base+offset
            if not vertical and any(0<abs(fixed-nodes[k].pins[p][1])<PITCH for k,p in local):continue
            path=[(fixed,v) if vertical else (v,fixed) for v in range(lo,hi+1,STEP)]
            if not all(16<=p[0]<=width-16 and 64<=p[1]<=height-16 and clear(signal,p) for p in path):continue
            d=int(vertical)
            if any(pin_axis.get((signal,p),d)!=d for p in path):continue
            if any(parallel[track(a,b)]-{signal} or trunk_halo[track(a,b)]-{signal} for a,b in zip(path,path[1:])):continue
            feed=[]
            if reserve_feeds:
                tip=stubs[key,pin][-1]
                target=(fixed,tip[1]) if vertical else (tip[0],fixed)
                dx=STEP if target[0]>tip[0] else -STEP if target[0]<tip[0] else 0
                dy=STEP if target[1]>tip[1] else -STEP if target[1]<tip[1] else 0
                normal=NORMAL[source.sides[pin]]
                if dx*normal[0]+dy*normal[1]<0:continue
                feed=[(tip[0]+dx*k,tip[1]+dy*k) for k in range((abs(target[0]-tip[0])+abs(target[1]-tip[1]))//STEP+1)]
                if (not all(clear(signal,p) for p in feed)
                        or any(parallel[track(a,b)]-{signal} for a,b in zip(feed,feed[1:]))):continue
            add(signal,path,trunk=True)
            trunks[signal]=Segment(signal,path[0],path[-1]);spines[signal]=set(path);rails[signal]=set(path)
            if feed:add(signal,feed);spines[signal].update(feed)
            return
        raise ValueError(f'No separated fanout trunk for {signal!r}')

    for signal in sorted((s for s in driver if len(loads[s])>1),key=lambda s:(nodes[driver[s][0]].kind!='input',nodes[driver[s][0]].level,natural(s))):rail(signal)

    def find(signal,start,tree,normal):
        # A reserved driver feed already belongs to the connected tree.
        if start in tree:return [start]
        # Distance to the actual tree, rather than its bounding rectangle:
        # a long, bent net otherwise gives A* a zero estimate over most of
        # the canvas. Compress its fine-grid points into straight runs.
        rows=defaultdict(list);columns=defaultdict(list)
        for x,y in tree:rows[y].append(x);columns[x].append(y)
        runs=[];covered=set()
        for vertical,groups in ((False,rows),(True,columns)):
            for fixed,values in groups.items():
                values=sorted(values);first=last=values[0]
                for value in [*values[1:],values[-1]+2*STEP]:
                    if value-last>STEP:
                        if first<last:
                            runs.append((fixed,first,fixed,last) if vertical else (first,fixed,last,fixed))
                            covered.update((fixed,v) if vertical else (v,fixed) for v in range(first,last+1,STEP))
                        first=value
                    last=value
        runs.extend((x,y,x,y) for x,y in tree-covered)
        @lru_cache(None)
        def heuristic(p):
            x,y=p
            return min(max(a-x,0,x-c)+max(b-y,0,y-d) for a,b,c,d in runs)
        if not reserve_feeds:
            xs=[p[0] for p in tree];ys=[p[1] for p in tree]
            bounds=min(xs),min(ys),max(xs),max(ys)
            def heuristic(p):return max(bounds[0]-p[0],0,p[0]-bounds[2])+max(bounds[1]-p[1],0,p[1]-bounds[3])
        q=[];serial=count();best={};previous={}
        minimum=PITCH//STEP
        # A turn at the escape tip is already a real bend. Retain the pin
        # direction so the next leg cannot be a sub-pitch stair.
        state=(start,DIRECTIONS.index(normal),minimum)
        heapq.heappush(q,(heuristic(start),0,next(serial),state));best[state]=0
        finish=None
        searched=0
        while q:
            _,cost,_,state=heapq.heappop(q)
            if cost!=best[state]:continue
            searched+=1
            # A crowded placement should trigger more room instead of
            # exploring millions of fine-grid states on an unusable sheet.
            if search_limit is not None and searched>search_limit:break
            p,old_direction,run=state;old_axis=old_direction//2
            degree=sum(edges.get(edge(p,(p[0]+dx,p[1]+dy)))==signal for dx,dy in DIRECTIONS) if p in tree else 0
            end_corner=degree==1 and at[p].get(signal)!={old_axis}
            if (p in tree and dot_clear(signal,p) and (not end_corner or run>=minimum)
                    and pin_axis.get((signal,p),old_axis)==old_axis):finish=state;break
            for direction,(dx,dy) in enumerate(DIRECTIONS):
                if direction==(old_direction^1):continue
                nxt=(p[0]+dx,p[1]+dy)
                if not (16<=nxt[0]<=width-16 and 64<=nxt[1]<=height-16):continue
                if not clear(signal,nxt):continue
                d=0 if dy==0 else 1
                if pin_axis.get((signal,p),d)!=d or pin_axis.get((signal,nxt),d)!=d:continue
                turning=old_axis!=d
                if turning and run<minimum:continue
                t=track(p,nxt)
                if parallel[t]-{signal}:continue
                foreign=at[p].keys()-{signal}
                if foreign and (d!=old_axis or any(at[p][n]!={1-d} for n in foreign)):continue
                other=at[nxt].keys()-{signal}
                if other and any(at[nxt][n]!={1-d} for n in other):continue
                if other and nxt in tree:continue
                new_cost=cost+STEP+(32 if turning else 0)+24*len(other)
                new_state=(nxt,direction,1 if turning else min(minimum,run+1))
                if new_cost<best.get(new_state,float('inf')):
                    best[new_state]=new_cost;previous[new_state]=state
                    # Optimal pixel length is less useful than completing a
                    # large detailed view within a predictable search budget.
                    weight=2 if reserve_feeds else 1
                    heapq.heappush(q,(new_cost+weight*heuristic(nxt),new_cost,next(serial),new_state))
        if finish is None:
            reason='search limit' if q else 'blocked channel'
            raise ValueError(f'No clear schematic channel for {signal!r} at {start} ({reason}, {searched} states)')
        path=[];state=finish
        while True:
            path.append(state[0])
            if state not in previous:break
            state=previous[state]
        return list(reversed(path))

    def order(signal):
        source=nodes[driver[signal][0]].pins[driver[signal][1]]
        dest=[nodes[k].pins[p] for k,p in loads[signal]]
        fanout=len(dest)>1
        straight=len(dest)==1 and (source[0]==dest[0][0] or source[1]==dest[0][1])
        # Rails already reserve every fanout channel. Connect local logic
        # first so a long bus tap cannot fence off a short inter-gate net.
        return (not fanout if fanout_first else not straight,
                not straight if fanout_first else fanout,
                sum(abs(source[0]-p[0])+abs(source[1]-p[1]) for p in dest),natural(signal))
    for signal in sorted(driver,key=order):
        key,pin=driver[signal];source=nodes[key].pins[pin]
        tree=set(spines.get(signal,stubs[key,pin]))
        destinations=sorted(loads[signal],key=lambda kp:(
            -abs(nodes[kp[0]].pins[kp[1]][0]-source[0])-abs(nodes[kp[0]].pins[kp[1]][1]-source[1]),natural(kp[0]),kp[1]))
        if signal in spines:
            for k,p in destinations:
                if (k,p) not in local_loads[signal]:continue
                path=find(signal,stubs[k,p][-1],spines[signal],NORMAL[nodes[k].sides[p]])
                add(signal,path);tree.update(path);tree.update(stubs[k,p])
            path=find(signal,stubs[key,pin][-1],spines[signal],NORMAL[nodes[key].sides[pin]])
            add(signal,path);tree.update(path);tree.update(stubs[key,pin])
            destinations=[kp for kp in destinations if kp not in local_loads[signal]]
        for k,p in destinations:
            path=find(signal,stubs[k,p][-1],tree,NORMAL[nodes[k].sides[p]])
            add(signal,path);tree.update(path);tree.update(stubs[k,p])
    # Rails are routing workspaces. Trim any unused rail tail or exploratory
    # lead that does not end at a real terminal; a schematic has no dead spurs.
    protected={((n.inputs|n.outputs)[pin],p) for n in nodes.values() for pin,p in n.pins.items()}
    protected.update((s,stubs[k,p][-1]) for s,(k,p) in driver.items() if not loads[s])
    adjacency=defaultdict(set)
    for (a,b),s in edges.items():adjacency[s,a].add(b);adjacency[s,b].add(a)
    leaves=[key for key,other in adjacency.items() if len(other)==1 and key not in protected]
    while leaves:
        key=leaves.pop();s,p=key
        if len(adjacency[key])!=1 or key in protected:continue
        q=adjacency[key].pop();adjacency[s,q].remove(p);edges.pop(edge(p,q))
        if len(adjacency[s,q])==1 and (s,q) not in protected:leaves.append((s,q))
    trimmed=[]
    for signal in trunks:
        points=sorted(p for p in rails[signal] if adjacency[signal,p])
        if points:trimmed.append(Segment(signal,points[0],points[-1]))
    return [Segment(s,a,b) for (a,b),s in edges.items()],tuple(trimmed)
