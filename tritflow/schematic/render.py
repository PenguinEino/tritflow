"""Textbook logic symbols and overlays in the shared TritFlow paper palette."""
from __future__ import annotations

from dataclasses import asdict
import math

from .vector import INK, SECONDARY, TRIT_COLOR, Vector
from .model import natural


def _rect(v,x,y,w,h,**style):
    v.path([('M',x,y),('L',x+w,y),('L',x+w,y+h),('L',x,y+h),('Z',)],**style)


def _anonymous(name):
    return name.startswith('_n') and name[2:].isdigit()


def _wire_name(node,pin,signal,ports):
    if signal in ports:return signal
    label=node.pin_labels.get(pin,pin)
    return f'{node.label}.{pin if _anonymous(label) else label}'


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
    elif kind == 'NOR':
        v.path([('M',left-3,cy-24),('C',cx-2,cy-24,cx+14,cy-20,right,cy),
                ('C',cx+14,cy+20,cx-2,cy+24,left-3,cy+24),
                ('Q',left+15,cy,left-3,cy-24),('Z',)],fill='white')
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
        v.text(cx,y+(74 if full else 46)+max(0,v.font_min-16),node.module or f'{len(node.members)} cells',size=10,color=SECONDARY,anchor='middle')
        for pin,signal in {**node.inputs,**node.outputs}.items():
            px,py=node.pins[pin];side=node.sides[pin]
            label=node.pin_labels.get(pin,signal)
            if _anonymous(label):label=('in ' if pin in node.inputs else 'out ')+str(list(node.inputs if pin in node.inputs else node.outputs).index(pin)+1)
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
            v.text(cx,y+node.height/2+(8 if node.height>32 else 0),node.label,size=11,anchor='middle')
        else:
            cy=y+node.height/2;half=node.height/2-4
            v.path([('M',x,cy-half),('L',x1-8,cy-half),('L',x1,cy),('L',x1-8,cy+half),('L',x,cy+half),('Z',)],fill='white',width=.8)
            v.text(cx-3,cy+(8 if node.height>32 else 4),node.label,size=11,anchor='middle')
        return
    local=node.label.rsplit('.',1)[-1]
    v.text(cx,y+32,local,size=10.6667,anchor='middle',owner=node.key)
    cy=y+80
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
    ports={c.net for c in scene.connections if c.endpoint.startswith('port:')}
    visible=sorted(ports&{s.net for s in scene.segments},key=natural)
    visible=[n for n in visible if values is not None or n in caps]
    annotated=bool(visible)
    # Native 11 pt text prevents small notebook figures from inheriting the
    # tiny legend font used by the old, wide publication canvases.
    small=sum(n.kind not in {'input','output'} for n in scene.symbols)<=10
    font=max(44/3,(44/3 if small else 12)*scene.width/1000)
    row_pitch=max(18,math.ceil(font*1.5))
    beside=annotated and scene.width+208<=1000
    columns=1 if beside else max(1,min(len(visible),int(scene.width/max(192,font*15))))
    rows=math.ceil(len(visible)/columns) if annotated else 0
    extra=row_pitch*(2+rows+(1 if caps else 0)) if annotated and not beside else 0
    v = Vector(scene.width+(208 if beside else 0),scene.height+extra,font_min=font,stroke_min=.8*scene.width/1000)
    v.net_labels={signal:_wire_name(n,p,signal,ports)
                  for n in scene.symbols for p,signal in n.outputs.items()}
    v.text(24,max(20,v.font_min+4),title,size=12,weight='bold')
    gates=sum(len(n.members) for n in scene.symbols)
    v.text(v.width-24,max(20,v.font_min+4),f'{gates} cells',size=9,color=SECONDARY,anchor='end')
    for frame in scene.frames:
        x0,y0,x1,y1=frame.box
        _rect(v,x0,y0,x1-x0,y1-y0,stroke='#c3c2b7',fill='#fafaf8',width=.8)
        v.text(x0+16,y0+max(24,v.font_min),frame.label,size=11,color=SECONDARY)
        for name,(px,py) in frame.pins.items():
            if frame.sides[name]=='top':v.text(px+12,py+max(24,v.font_min),name,size=11,color=SECONDARY)
            elif frame.sides[name]=='left':v.text(px+12,py-max(12,v.font_min*.35),name,size=11,color=SECONDARY)
            else:v.text(px-12,py-max(12,v.font_min*.35),name,size=11,color=SECONDARY,anchor='end')
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
    footer=scene.height-16
    if scene.junctions:
        v.line((24,footer-3),(48,footer-3),width=1.2)
        v.line((36,footer-11),(36,footer-3),width=1.2)
        v.circle(36,footer-3,2.4,fill=INK,stroke=INK,width=0)
        v.text(56,footer,'Branch',size=9,color=SECONDARY)
    if any(h.net!=s.net and h.a[1]==h.b[1] and s.a[0]==s.b[0]
           and h.a[0]<s.a[0]<h.b[0] and s.a[1]<h.a[1]<s.b[1]
           for h in horizontal for s in vertical):
        offset=max(132,56+4*v.font_min)
        v.line((offset+12,footer-11),(offset+12,footer+5),width=1.2)
        v.line((offset,footer-3),(offset+24,footer-3),stroke='white',width=5)
        v.line((offset,footer-3),(offset+24,footer-3),width=1.2)
        v.text(offset+32,footer,'Crossing: no connection',size=9,color=SECONDARY)
    if annotated:
        baseline=64 if beside else scene.height+row_pitch
        legend_x=scene.width+8 if beside else 24
        heading='Port values' if values is not None else 'Port wire C'
        if values is not None and caps:heading+=' / wire C'
        v.text(legend_x,baseline,heading,size=10,weight='bold')
        cell_width=(scene.width-48)/columns
        for k,signal in enumerate(visible):
            col=k//max(1,rows);row=k%max(1,rows)
            x=legend_x+col*cell_width;y=baseline+row_pitch+row*row_pitch
            parts=[signal]
            if values is not None:parts.append({-1:'−1',0:'0',1:'+1'}[values[signal]])
            if signal in caps:parts.append(f'{caps[signal]*1e15:.1f} fF')
            color,width=styles[signal]
            v.line((x,y-4),(x+16,y-4),stroke=color,width=width)
            v.text(x+24,y,'   '.join(parts),size=10,color=color)
        if caps:
            if beside:
                y=baseline+(rows+2)*row_pitch
                v.text(legend_x,y,'Estimated wire C (fF).',size=9,color=SECONDARY)
                v.text(legend_x,y+row_pitch,'Darker / thicker = more C.',size=9,color=SECONDARY)
            else:v.text(24,v.height-max(8,font*.3),'Estimated wire C (fF); darker / thicker = more C.',size=9,color=SECONDARY)
    return v


def metadata(scene,values,caps):
    """Machine-readable connection ledger also documents closed-block contents."""
    return {'top':scene.top,'connections':[asdict(c) for c in scene.connections],
            'symbols':[{'key':n.key,'kind':n.kind,'members':list(n.members),
                        'module':n.module,'pin_labels':n.pin_labels} for n in scene.symbols],
            'frames':[asdict(f) for f in scene.frames],
            'trunks':[asdict(t) for t in scene.trunks],
            'interconnect':[asdict(t) for t in scene.interconnect],
            'hidden_nets':list(scene.hidden_nets),'notes':list(scene.notes),
            'values':values,'capacitance_f':caps}
