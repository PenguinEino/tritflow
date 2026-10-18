"""One paper-ready legend for every cell and the three settled trit colours."""
from .model import Symbol
from .render import _symbol
from .vector import SECONDARY, TRIT_COLOR, Vector


class SymbolLegend:
    """A dependency-free SVG legend with the same gate paths as draw()."""
    def _vector(self):
        v = Vector(1088,624,font_min=(44/3)*1088/1000)
        v.text(32,34,'Balanced-ternary symbol legend',size=20,weight='bold')
        v.text(32,57,'A bubble reverses the sign of a trit. Inputs and outputs are −1, 0, +1.',size=12,color=SECONDARY)
        entries = [('INV','−a','Triangle: inversion'),('BUF','a','Triangle: level-preserving buffer'),
                   ('NAND','−min(a, b)','AND outline: minimum, then invert'),('NOR','−max(a, b)','OR outline: maximum, then invert'),
                   ('NANY','−sat(a + b)','Clipped Σ: saturated sum, then invert'),('TIEP','+1  ↔  +5 V','Positive supply-style source'),
                   ('TIEZ','0  ↔  0 V','Explicit middle-level source'),('TIEN','−1  ↔  −5 V','Negative supply-style source'),
                   ('input','a[0]','Flag: external input'),('output','sum[0]','Flag: external output')]
        for index,(kind,function,meaning) in enumerate(entries):
            col,row = index%2,index//2
            x,y = 32+col*528,80+row*96
            label = kind if kind not in {'input','output'} else function
            from .placement import anchors
            node = Symbol(kind,kind,label,x=x,y=y,width=80,height=96)
            if kind=='input' or kind.startswith('TIE'):
                node.outputs={'Y':'net'}
            elif kind=='output':node.inputs={'port':'net'}
            else:
                node.inputs={'A':'a'} if kind in {'INV','BUF'} else {'A':'a','B':'b'}
                node.outputs={'Y':'y'}
            if kind in {'input','output'}:node.x+=16;node.y+=32
            anchors(node)
            _symbol(v,node)
            v.text(x+136,y+40,function,size=14,weight='bold')
            v.text(x+136,y+61,meaning,size=11,color=SECONDARY)
        for index,value in enumerate((-1,0,1)):
            x=32+index*240
            v.line((x,588),(x+32,588),stroke=TRIT_COLOR[value],width=3)
            label = {-1:'−1 trit  (−5 V)',0:'0 trit  (0 V)',1:'+1 trit  (+5 V)'}[value]
            v.text(x+44,592,label,size=12)
        return v

    @property
    def svg(self):
        return self._vector().svg('Balanced-ternary symbol legend')

    @property
    def pdf(self):
        return self._vector().export('pdf')

    def png(self, *, scale=1):
        return self._vector().export('png',scale=scale)

    def _repr_svg_(self):
        return self.svg

    def save(self,path):
        from pathlib import Path
        path=Path(path)
        if path.suffix.lower() not in {'.svg','.pdf','.png'}:
            raise ValueError('legend output must be .svg, .pdf or .png')
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.suffix.lower()=='.svg': path.write_text(self.svg,encoding='utf-8')
        else: path.write_bytes(self.pdf if path.suffix.lower()=='.pdf' else self.png())
        return path

    def show(self):
        from IPython.display import SVG, display
        display(SVG(self.svg))
        return self
