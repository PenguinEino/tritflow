"""Compact PCell standard-cell views, adapted from the taped-out geometry."""
import json
import os
from pathlib import Path
import sys

import klayout.db as db
from tritflow import CELLS_DIR, PDK_ROOT
from .circuits import circuits, spice, truth_table

LAYERS = {'WN': (140,0), 'GC': (8,1), 'M1': (13,0), 'M2': (20,0), 'TXM1': (48,0),
          'pin': (48,1), 'prBoundary': (235,0)}
_LIBRARY = None


class Drawing:
    """Micrometre geometry and immutable PDK device/contact instances."""
    def __init__(self, layout, top):
        self.layout, self.top = layout, top
        self.devices = []

    def box(self, layer, rect):
        self.top.shapes(self.layout.layer(*LAYERS[layer])).insert(db.DBox(*rect))

    def wire(self, layer, points, width=2.6):
        h = width/2
        for (x,y), (xx,yy) in zip(points, points[1:]):
            assert x == xx or y == yy
            self.box(layer, (min(x,xx)-h,min(y,yy)-h,max(x,xx)+h,max(y,yy)+h))

    def pcell(self, name, x, y, params=None):
        c = self.layout.create_cell(name, 'TR-1um', params or {})
        if c is None or not c.is_pcell_variant():
            raise RuntimeError(f'Missing TR-1um PCell {name}')
        self.top.insert(db.DCellInstArray(c.cell_index(), db.DTrans(db.DVector(float(x),float(y)))))
        self.devices.append({'pcell': name, 'origin': [x,y], 'parameters': c.pcell_parameters_by_name()})

    def label(self, net, x, y):
        self.top.shapes(self.layout.layer(*LAYERS['TXM1'])).insert(db.DText(net, db.DTrans(db.DVector(float(x),float(y)))))


def register_pdk():
    global _LIBRARY
    if _LIBRARY is None:
        sys.path.insert(0, str(PDK_ROOT/'libs.tech/klayout/tech/python'))
        from cells import tr_1um
        _LIBRARY = tr_1um('TR-1um')


def build_cell(circuit, out, template):
    """Generate a compact macro from the taped-out device placement."""
    from .compact import draw
    register_pdk()
    ly=db.Layout();ly.dbu=.001;ly.technology_name='TR-1um'
    top=ly.create_cell(circuit.name);d=Drawing(ly,top)
    width,signal_pins=draw(d,circuit,template)
    height=template['height'];pins={}
    for net in circuit.ports:
        direction='power' if net in ('VDD','VMID','VSS') else ('input' if net in circuit.inputs else 'output')
        if direction=='power':
            y0,y1=template['rails'][net];rect=[0,y0,width,y1];access=[3.,(y0+y1)/2]
        else:
            access=signal_pins[net];x,y=access;rect=[x-1.7,y-1.7,x+1.7,y+1.7]
            d.box('M1',rect)
        d.label(net,*access);d.box('pin',rect)
        pins[net]={'dir':direction,'layer':'M1','rects':[rect],'access':[access]}
    d.box('prBoundary',(0,0,width,height))
    folder=out/circuit.name;folder.mkdir(parents=True,exist_ok=True)
    for child in ly.each_cell():
        if child!=top:child.name+='__'+circuit.name
    ly.write(str(folder/f'{circuit.name}.gds'))
    obstructions={}
    for key,layer in [('M1',(13,0)),('M2',(20,0)),('V1',(19,0))]:
        region=db.Region(top.begin_shapes_rec(ly.layer(*layer))).merged()
        obstructions[key]=[[v*ly.dbu for v in (p.bbox().left,p.bbox().bottom,p.bbox().right,p.bbox().top)]
                           for p in region.decompose_trapezoids()]
    # A continuous 3.4 um M2 wire must remain 2 um from every internal M2 shape.
    free=[3.+6*k for k in range(round(width/6)) if all(x1+3.7<=3.+6*k or 3.+6*k<=x0-3.7
          for x0,y0,x1,y1 in obstructions['M2'])]
    abstract={'name':circuit.name,'width':width,'height':height,'pins':pins,
              'obstructions':obstructions,'orientations':['R0','MY'],
              'free_M2_tracks':{'x':free,'count':len(free),'wire_width':3.4,'clearance':2.0}}
    (folder/f'{circuit.name}.abstract.json').write_text(json.dumps(abstract,indent=2)+'\n')
    (folder/f'{circuit.name}.spice').write_text(spice(circuit))
    (folder/f'{circuit.name}.lvs.spice').write_text(spice(circuit,False))
    (folder/f'{circuit.name}.truth.json').write_text(json.dumps(truth_table(circuit),indent=2)+'\n')
    (folder/f'{circuit.name}.pcells.json').write_text(json.dumps(d.devices,indent=2)+'\n')
    render(folder/f'{circuit.name}.gds',folder/f'{circuit.name}.png')
    return abstract


def render(gds, png):
    """Render the actual hierarchical GDS with the PDK layer palette."""
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    import klayout.lay as lay
    view = lay.LayoutView()
    idx = view.load_layout(str(gds),False)
    view.load_layer_props(str(PDK_ROOT/'libs.tech/klayout/tech/TR-1um.lyp'),idx,True)
    view.max_hier(); view.set_config('grid-visible','false')
    view.save_image(str(png),1200,900)


def build(out=CELLS_DIR/'out', names=None):
    out = Path(out).resolve()
    if out==(CELLS_DIR/'out').resolve():
        from .publish import qualified_build
        qualified_build(out,names)
        return json.loads((out/'library.json').read_text())
    out.mkdir(parents=True,exist_ok=True)
    from .compact import TEMPLATE
    template = TEMPLATE
    (out/'template.json').write_text(json.dumps(template,indent=2)+'\n')
    library = []
    for name,c in circuits().items():
        if names and name not in names: continue
        a = build_cell(c,out,template)
        library.append({'name':name,'width':a['width'],'height':a['height'],
                        **{key:f'{name}/{name}.{suffix}' for key,suffix in
                           [('gds','gds'),('spice','spice'),('extracted','ext.spice'),
                            ('abstract','abstract.json'),('characterization','char.json'),('truth','truth.json'),('png','png')]}})
    (out/'library.json').write_text(json.dumps(library,indent=2)+'\n')
    (out/'all.spice').write_text(''.join(spice(circuits()[e['name']]) for e in library))
    return library
