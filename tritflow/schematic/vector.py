"""A tiny common vector vocabulary for native SVG and Matplotlib PDF/PNG.

No SVG converter, browser, Cairo, TeX or system font installation is required.
The PDF uses the same paths and coordinates as the notebook's SVG.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from io import BytesIO
import json

INK = '#0b0b0b'
SECONDARY = '#52514e'
TRIT_COLOR = {-1: '#2a78d6', 0: '#6f6e69', 1: '#e34948'}


@dataclass
class Vector:
    width: int
    height: int
    items: list[dict] = field(default_factory=list)

    def path(self, commands, *, stroke=INK, fill='none', width=1.6, net=None):
        self.items.append(dict(kind='path',commands=commands,stroke=stroke,fill=fill,width=width,net=net))

    def line(self,a,b,**style):
        self.path([('M',*a),('L',*b)],**style)

    def circle(self,x,y,r,*,stroke=INK,fill='white',width=1.6,net=None):
        self.items.append(dict(kind='circle',x=x,y=y,r=r,stroke=stroke,fill=fill,width=width,net=net))

    def text(self,x,y,text,*,size=11,color=INK,anchor='start',weight='normal'):
        self.items.append(dict(kind='text',x=x,y=y,text=str(text),size=size,color=color,anchor=anchor,weight=weight))

    def svg(self, title, metadata=None):
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
                 f'viewBox="0 0 {self.width} {self.height}" role="img" aria-label="{escape(title,quote=True)}">',
                 f'<title>{escape(title)}</title>',
                 '<desc>Left-to-right balanced-ternary logic. Dots mark connected branches; '
                 'gaps at crossings mean no connection. All values are settled ideal trits.</desc>',
                 '<rect width="100%" height="100%" fill="white"/>']
        if metadata is not None:
            parts.append('<metadata>'+escape(json.dumps(metadata,sort_keys=True,separators=(',',':')))+'</metadata>')
        for item in self.items:
            kind = item['kind']
            if kind == 'text':
                parts.append(f'<text x="{item["x"]}" y="{item["y"]}" font-family="DejaVu Sans, sans-serif" '
                             f'font-size="{item["size"]}" text-anchor="{item["anchor"]}" '
                             f'font-weight="{item["weight"]}" fill="{item["color"]}">{escape(item["text"])}</text>')
                continue
            style = (f'stroke="{item["stroke"]}" fill="{item["fill"]}" stroke-width="{item["width"]:.3f}" '
                     'stroke-linecap="round" stroke-linejoin="round"')
            signal = item.get('net')
            attr = f' data-net="{escape(signal,quote=True)}"' if signal is not None else ''
            tooltip = f'<title>{escape(signal)}</title>' if signal is not None else ''
            if kind == 'path':
                data = ' '.join(c[0]+' '.join(str(v) for v in c[1:]) for c in item['commands'])
                parts.append(f'<path d="{data}" {style}{attr}>{tooltip}</path>')
            else:
                parts.append(f'<circle cx="{item["x"]}" cy="{item["y"]}" r="{item["r"]}" {style}{attr}>{tooltip}</circle>')
        parts.append('</svg>')
        return '\n'.join(parts)+'\n'

    def export(self, format, *, scale=1):
        """Export existing vector primitives with the project's Matplotlib dependency."""
        import matplotlib as mpl
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.path import Path
        from matplotlib.patches import Circle, PathPatch
        with mpl.rc_context({'font.family':'DejaVu Sans','pdf.fonttype':42,'path.simplify':False}):
            fig = Figure(figsize=(self.width/96,self.height/96),dpi=96,facecolor='white')
            FigureCanvasAgg(fig)
            ax = fig.add_axes([0,0,1,1])
            ax.set(xlim=(0,self.width),ylim=(self.height,0))
            ax.set_axis_off()
            for item in self.items:
                kind = item['kind']
                if kind == 'text':
                    ax.text(item['x'],item['y'],item['text'],fontsize=item['size']*.75,
                            color=item['color'],ha={'start':'left','middle':'center','end':'right'}[item['anchor']],
                            va='baseline',weight=item['weight'])
                    continue
                style = dict(edgecolor=item['stroke'],facecolor=item['fill'],linewidth=item['width']*.75,
                             capstyle='round',joinstyle='round')
                if kind == 'circle':
                    ax.add_patch(Circle((item['x'],item['y']),item['r'],**style))
                    continue
                vertices,codes = [],[]
                for command in item['commands']:
                    op,*coords = command
                    if op == 'Z':
                        vertices.append((0,0)); codes.append(Path.CLOSEPOLY)
                    else:
                        for index in range(0,len(coords),2):
                            vertices.append(tuple(coords[index:index+2]))
                            codes.append({'M':Path.MOVETO,'L':Path.LINETO,'Q':Path.CURVE3,'C':Path.CURVE4}[op])
                ax.add_patch(PathPatch(Path(vertices,codes),**style))
            result = BytesIO()
            metadata = {'Creator':'TritFlow schematic','CreationDate':None,'ModDate':None} if format == 'pdf' else {'Software':'TritFlow schematic'}
            fig.savefig(result,format=format,dpi=96*scale,metadata=metadata)
            fig.clear()
            return result.getvalue()
