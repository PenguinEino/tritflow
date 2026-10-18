"""Schematic spacing in drawing pixels; chip design rules are independent."""
RASTER=8
PITCH=32
CLEARANCE=PITCH//2
TRUNK_PITCH=3*PITCH//2
PIN_RUN=PITCH


def distance(a,b):
    """Chebyshev distance between closed axis-aligned rectangles."""
    return max(0,a[0]-b[2],b[0]-a[2],a[1]-b[3],b[1]-a[3])


def box(segment):
    return min(segment.a[0],segment.b[0]),min(segment.a[1],segment.b[1]),max(segment.a[0],segment.b[0]),max(segment.a[1],segment.b[1])


def parallel_gap(a,b):
    """Separation of parallel runs with positive overlap, otherwise None."""
    if a.a[1]==a.b[1] and b.a[1]==b.b[1]:
        if max(a.a[0],b.a[0])<min(a.b[0],b.b[0]):return abs(a.a[1]-b.a[1])
    if a.a[0]==a.b[0] and b.a[0]==b.b[0]:
        if max(a.a[1],b.a[1])<min(a.b[1],b.b[1]):return abs(a.a[0]-b.a[0])
    return None
