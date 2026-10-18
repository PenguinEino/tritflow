"""Geometry-only review metrics; pixel lengths are not physical chip lengths."""
from collections import defaultdict

from .model import JOG_PITCH


def _edge_run(segment,box):
    """Positive wire overlap along a symbol keep-out edge; pin contact is fine."""
    x0,y0,x1,y1=box
    a,b=segment.a,segment.b
    if a[1]==b[1]:
        return a[1] in (y0,y1) and max(a[0],x0)<min(b[0],x1)
    return a[0] in (x0,x1) and max(a[1],y0)<min(b[1],y1)


def _interior(point,segment):
    x,y=point
    a,b=segment.a,segment.b
    return ((a[1]==y==b[1] and a[0]<x<b[0]) or
            (a[0]==x==b[0] and a[1]<y<b[1]))


def measure(scene):
    """Count unique wire length, non-junction bends, crossings and canvas aspect.

    A bend is a same-net degree-two corner. T joins are reported separately,
    rather than counting each branch as several bends. Crossings are distinct
    different-net perpendicular intersections, with no electrical connection.
    A short jog is a straight leg shorter than the 32-pixel gate input pitch
    between two degree-two corners. Short terminal stubs and T joins are not
    jogs. Symbol-edge runs include the label keep-out as well as the body.
    """
    groups=defaultdict(list)
    for s in scene.segments:
        groups[s.net].append(s)
    by_net={}
    for signal,segments in sorted(groups.items()):
        ends={p for s in segments for p in (s.a,s.b)}
        corners=set();junctions=set()
        for x,y in ends:
            axes=set(); degree=0
            for s in segments:
                if s.a[1]==s.b[1]==y and s.a[0]<=x<=s.b[0]:
                    axes.add('h');degree+=int(s.a[0]<x)+int(x<s.b[0])
                if s.a[0]==s.b[0]==x and s.a[1]<=y<=s.b[1]:
                    axes.add('v');degree+=int(s.a[1]<y)+int(y<s.b[1])
            if degree==2 and len(axes)==2:corners.add((x,y))
            if degree>=3:junctions.add((x,y))
        jogs=sum(s.a in corners and s.b in corners
                 and abs(s.a[0]-s.b[0])+abs(s.a[1]-s.b[1])<JOG_PITCH
                 and not any(_interior(p,s) for p in junctions) for s in segments)
        by_net[signal]={'wire_length_px':sum(abs(s.a[0]-s.b[0])+abs(s.a[1]-s.b[1]) for s in segments),
                        'bends':len(corners),'short_jogs':jogs}
    crossings=set()
    for h in scene.segments:
        if h.a[1]!=h.b[1]:continue
        for v in scene.segments:
            if v.net==h.net or v.a[0]!=v.b[0]:continue
            if h.a[0]<v.a[0]<h.b[0] and v.a[1]<h.a[1]<v.b[1]:
                crossings.add((min(h.net,v.net),max(h.net,v.net),v.a[0],h.a[1]))
    bends=[n['bends'] for n in by_net.values()]
    from .audit import counts
    return {'wire_length_px':sum(n['wire_length_px'] for n in by_net.values()),
            'bends_total':sum(bends),'bends_per_net_mean':sum(bends)/max(1,len(bends)),
            'bends_per_net_max':max(bends,default=0),'nets_over_two_bends':sum(n>2 for n in bends),
            'crossings':len(crossings),'aspect_ratio':scene.width/scene.height,
            'short_jogs':sum(n['short_jogs'] for n in by_net.values()),'jog_pitch_px':JOG_PITCH,
            'symbol_edge_runs':sum(_edge_run(s,n.box) for s in scene.segments for n in scene.symbols),
            'rotated_gates':sum(n.orient!='right' for n in scene.symbols
                                if n.kind not in {'input','output','block'}),
            'clearance_violations':counts(scene),
            'width_px':scene.width,'height_px':scene.height,'nets':by_net}
