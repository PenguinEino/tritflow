"""Textbook logic symbols and overlays in the shared TritFlow paper palette."""
from __future__ import annotations

from dataclasses import asdict
import math

from .vector import INK, SECONDARY, TRIT_COLOR, Vector
from .model import natural


def _rect(v,x,y,w,h,**style):
    v.path([('M',x,y),('L',x+w,y),('L',x+w,y+h),('L',x,y+h),('Z',)],**style)


def gate(v,kind,cx,cy):
    """Draw a 64x48 body; bubbles mean arithmetic sign reversal in ternary."""
    left,right = cx-32,cx+24
    if kind in {'INV','BUF'}:
        v.path([('M',left,cy-24),('L',right,cy),('L',left,cy+24),('Z',)],fill='white')
        end = right
        if kind == 'INV':
            v.circle(right+5,cy,5)
            end += 10
        return left,end
    if kind == 'NAND':
        v.path([('M',left,cy-24),('L',cx,cy-24),
                ('C',cx+32,cy-24,cx+32,cy+24,cx,cy+24),('L',left,cy+24),('Z',)],fill='white')
        v.text(cx-3,cy+4,'min',size=10,anchor='middle')
    elif kind == 'NOR':
        v.path([('M',left-3,cy-24),('C',cx-2,cy-24,cx+14,cy-20,right,cy),
                ('C',cx+14,cy+20,cx-2,cy+24,left-3,cy+24),
                ('Q',left+15,cy,left-3,cy-24),('Z',)],fill='white')
        v.text(cx-1,cy+4,'max',size=10,anchor='middle')
    else:  # NANY: summing body with clipped corners, then sign reversal.
        v.path([('M',left+8,cy-24),('L',cx+12,cy-24),('L',right,cy-12),
                ('L',right,cy+12),('L',cx+12,cy+24),('L',left+8,cy+24),
                ('L',left,cy+16),('L',left,cy-16),('Z',)],fill='white')
        v.text(cx-3,cy+5,'Σ',size=21,anchor='middle')
    v.circle(right+5,cy,5)
    return left,right+10


def _symbol(v,node):
    x,y,x1,y1=node.box
    cx=(x+x1)/2
    if node.kind=='block':
        _rect(v,x,y,node.width,node.height,fill='white',width=.8)
        full=node.module=='full_add'
        v.text(cx,y+(56 if full else 28),node.label,size=11,weight='bold',anchor='middle')
        v.text(cx,y+(74 if full else 46),node.module or f'{len(node.members)} cells',size=10,color=SECONDARY,anchor='middle')
        for pin,signal in {**node.inputs,**node.outputs}.items():
            px,py=node.pins[pin];side=node.sides[pin]
            label=node.pin_labels.get(pin,signal)
            if side=='left':
                v.line((px,py),(px+8,py));v.text(px+12,py+3,label,size=10)
            elif side=='right':
                v.line((px-8,py),(px,py));v.text(px-12,py+3,label,size=10,anchor='end')
            elif side=='top':
                v.line((px,py),(px,py+8));v.text(px,py+22,label,size=10,anchor='middle')
            else:
                v.line((px,py-8),(px,py));v.text(px,py-14,label,size=10,anchor='middle')
        return
    if node.kind in {'input','output'}:
        if node.orient=='down':
            v.path([('M',x,y),('L',x1,y),('L',x1,y1-8),('L',cx,y1),('L',x,y1-8),('Z',)],fill='white',width=.8)
            v.text(cx,y+16,node.label,size=11,anchor='middle')
        else:
            cy=y+16
            v.path([('M',x,cy-12),('L',x1-8,cy-12),('L',x1,cy),('L',x1-8,cy+12),('L',x,cy+12),('Z',)],fill='white',width=.8)
            v.text(cx-3,cy+4,node.label,size=11,anchor='middle')
        return
    local=node.label.rsplit('.',1)[-1]
    v.text(cx,y+16,local,size=10.6667,anchor='middle')
    cy=y+56
    if node.kind.startswith('TIE'):
        value={'TIEP':'+1','TIEZ':'0','TIEN':'−1'}[node.kind]
        v.line((cx-20,cy-12),(cx+20,cy-12),width=1.2)
        v.line((cx,cy-12),(cx,cy));v.line((cx,cy),(x1,cy))
        v.text(cx,cy-18,value,size=11,anchor='middle');return
    left,right=gate(v,node.kind,cx,cy)
    for pin,(px,py) in node.pins.items():
        if pin in node.outputs:
            end=(right,cy)
        else:
            offset=left
            if node.kind=='NOR':offset=cx-35+9*(1-(16/24)**2)
            end=(offset,py)
        v.line((px,py),end)


def _wire_styles(scene,values,caps):
    maximum = max(caps.values(),default=0)
    styles = {}
    for signal in {s.net for s in scene.segments}:
        fraction = math.sqrt(caps.get(signal,0)/maximum) if maximum else 0
        width = 1.6+1.6*fraction
        if values is not None and signal in values:
            color = TRIT_COLOR[values[signal]]
            # Increased C also darkens the settled-value hue.
            factor = 1-.22*fraction
            color = '#'+''.join(f'{round(int(color[i:i+2],16)*factor):02x}' for i in (1,3,5))
        else:
            grey = round(135-105*fraction) if caps else 80
            color = '#'+f'{grey:02x}'*3
        styles[signal] = color,width
    return styles


def render(scene,values=None,caps=None,net_names=False,title=None):
    """Paint an existing scene; geometry does not depend on any overlay."""
    caps = caps or {}
    title = scene.top if title is None else title
    visible=sorted({s.net for s in scene.segments},key=natural)
    annotated=values is not None or caps or net_names
    columns=max(1,scene.width//240)
    rows=math.ceil(len(visible)/columns) if annotated else 0
    extra=48+rows*18 if annotated else 0
    v = Vector(scene.width,scene.height+extra)
    v.text(48,32,title,size=16,weight='bold')
    gates=sum(len(n.members) for n in scene.symbols)
    v.text(48,52,f'{gates} synthesized cells',size=10.6667,color=SECONDARY)
    for frame in scene.frames:
        x0,y0,x1,y1=frame.box
        _rect(v,x0,y0,x1-x0,y1-y0,stroke='#c3c2b7',fill='#fafaf8',width=.8)
        v.text(x0+16,y0+20,frame.label,size=11,color=SECONDARY)
    styles = _wire_styles(scene,values,caps)
    # Vertical trunks first. White under-strokes on all horizontals open the
    # perpendicular crossing; same-net T junctions are restored by dots.
    vertical = [s for s in scene.segments if s.a[0] == s.b[0]]
    horizontal = [s for s in scene.segments if s.a[1] == s.b[1]]
    for segment in vertical:
        color,width = styles[segment.net]
        v.line(segment.a,segment.b,stroke=color,width=width,net=segment.net)
    for segment in horizontal:
        color,width = styles[segment.net]
        # Only real crossings get gaps: leaving a tiny white halo around every
        # horizontal would break its own bends and make short wires look open.
        for other in vertical:
            if (other.net != segment.net and segment.a[0] < other.a[0] < segment.b[0]
                    and other.a[1] < segment.a[1] < other.b[1]):
                _,other_width = styles[other.net]
                px,py = other.a[0],segment.a[1]
                v.line((px-other_width/2-1.5,py),(px+other_width/2+1.5,py),stroke='white',width=width+3)
        v.line(segment.a,segment.b,stroke=color,width=width,net=segment.net)
    for signal,points in scene.junctions.items():
        color,width = styles[signal]
        for x,y in points:
            v.circle(x,y,2.4+width*.2,fill=color,stroke=color,width=0,net=signal)
    for node in scene.symbols:
        _symbol(v,node)
    footer=scene.height-24
    v.text(48,footer,'• Connected branch    Crossing gaps: no connection',size=10,color=SECONDARY)
    if annotated:
        baseline=scene.height+4
        v.text(48,baseline,'Net / settled trit / routed wire C',size=11,weight='bold')
        cell_width=(scene.width-96)/columns
        for k,signal in enumerate(visible):
            col=k//max(1,rows);row=k%max(1,rows)
            x=48+col*cell_width;y=baseline+22+row*18
            parts=[signal] if net_names or caps else []
            if values is not None:parts.append({-1:'−1',0:'0',1:'+1'}[values[signal]])
            if signal in caps:parts.append(f'{caps[signal]*1e15:.1f} fF')
            color,width=styles[signal]
            v.line((x,y-4),(x+16,y-4),stroke=color,width=width)
            v.text(x+24,y,'   '.join(parts),size=10,color=color)
        if caps:v.text(48,v.height-10,'Wire C is an estimated lumped parasitic; darker / thicker = more C.',size=10,color=SECONDARY)
    return v


def metadata(scene,values,caps):
    """Machine-readable connection ledger also documents closed-block contents."""
    return {'top':scene.top,'connections':[asdict(c) for c in scene.connections],
            'symbols':[{'key':n.key,'kind':n.kind,'members':list(n.members),
                        'module':n.module,'pin_labels':n.pin_labels} for n in scene.symbols],
            'frames':[asdict(f) for f in scene.frames],
            'hidden_nets':list(scene.hidden_nets),'notes':list(scene.notes),
            'values':values,'capacitance_f':caps}
