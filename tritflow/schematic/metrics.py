"""Geometry-only review metrics; pixel lengths are not physical chip lengths."""
from collections import defaultdict


def measure(scene):
    """Count unique wire length, non-junction bends, crossings and canvas aspect.

    A bend is a same-net degree-two corner. T joins are reported separately,
    rather than counting each branch as several bends. Crossings are distinct
    different-net perpendicular intersections, with no electrical connection.
    """
    groups=defaultdict(list)
    for s in scene.segments:
        groups[s.net].append(s)
    by_net={}
    for signal,segments in sorted(groups.items()):
        ends={p for s in segments for p in (s.a,s.b)}
        bends=0
        for x,y in ends:
            axes=set(); degree=0
            for s in segments:
                if s.a[1]==s.b[1]==y and s.a[0]<=x<=s.b[0]:
                    axes.add('h');degree+=int(s.a[0]<x)+int(x<s.b[0])
                if s.a[0]==s.b[0]==x and s.a[1]<=y<=s.b[1]:
                    axes.add('v');degree+=int(s.a[1]<y)+int(y<s.b[1])
            bends+=degree==2 and len(axes)==2
        by_net[signal]={'wire_length_px':sum(abs(s.a[0]-s.b[0])+abs(s.a[1]-s.b[1]) for s in segments),
                        'bends':bends}
    crossings=set()
    for h in scene.segments:
        if h.a[1]!=h.b[1]:continue
        for v in scene.segments:
            if v.net==h.net or v.a[0]!=v.b[0]:continue
            if h.a[0]<v.a[0]<h.b[0] and v.a[1]<h.a[1]<v.b[1]:
                crossings.add((min(h.net,v.net),max(h.net,v.net),v.a[0],h.a[1]))
    bends=[n['bends'] for n in by_net.values()]
    return {'wire_length_px':sum(n['wire_length_px'] for n in by_net.values()),
            'bends_total':sum(bends),'bends_per_net_mean':sum(bends)/max(1,len(bends)),
            'bends_per_net_max':max(bends,default=0),'nets_over_two_bends':sum(n>2 for n in bends),
            'crossings':len(crossings),'aspect_ratio':scene.width/scene.height,
            'width_px':scene.width,'height_px':scene.height,'nets':by_net}
