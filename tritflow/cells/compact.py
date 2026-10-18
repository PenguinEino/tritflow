"""Adapt the taped-out macros to common rails and accessible M1 terminals."""
from . import primitives

HEIGHT = 132.
TEMPLATE = {
    'height': HEIGHT, 'grid': 6.,
    'rails': {'VDD':[124.,132.], 'VMID':[6.,10.], 'VSS':[0.,4.]},
    'pin_rows':[37.,50.5,58.,64.,70.,71.],
    'well_band':[116.,132.],
    'layers':{'M1':[13,0],'V1':[19,0],'M2':[20,0],'TXM1':[48,0],
              'TXM2':[49,0],'pin':[48,1],'prBoundary':[235,0]},
    'rules':{'M1_w':1.8,'M1_s':1.4,'M2_w':3.,'M2_s':2.,'V1':1.4,
             'V1_enc_M1':1.,'V1_enc_M2':1.}
}
WIDTHS = {'INV':108.,'NAND':144.,'NOR':144.,'NANY':168.,'BUF':216.,
          'TIEP':72.,'TIEZ':72.,'TIEN':72.,'FILL':24.}


class OriginalCoordinates:
    """Six-um side margin, 12-um bottom extension, cropped M2 port stubs."""
    def __init__(self,drawing,kind,dx=0.):
        self.drawing,self.kind,self.dx=drawing,kind,dx
        self.width={'INV':96.,'NANY':148.,'NAND':132.,'NOR':132.}[kind]

    def box(self,layer,x0,y0,x1,y1):
        if layer=='M2':
            cy=(y0+y1)/2
            if self.kind=='NANY' and abs(cy-38)<.01 and x0<1:
                x0=43.3  # VMID's old external stub is no longer a signal pin.
            elif self.kind in ('NANY','NAND','NOR') and cy in (46,52) and x0<1:
                x0=1.3  # leave a DRC-legal gap to a router via at x=3.
            if abs(x1-self.width)<.01: x1=self.width-1.3
        self.drawing.box(layer,(x0+6+self.dx,y0+12,x1+6+self.dx,y1+12))

    def wire(self,layer,points,width=2.6):
        half=width/2
        for (x,y),(xx,yy) in zip(points,points[1:]):
            assert x==xx or y==yy
            self.box(layer,min(x,xx)-half,min(y,yy)-half,max(x,xx)+half,max(y,yy)+half)

    def pcell(self,role,name,x,y,parameters=None):
        self.drawing.pcell(name,x+6+self.dx,y+12,parameters)
        self.drawing.devices[-1]['role']=role


def _inverter(d,dx=0.):
    primitives.inverter(OriginalCoordinates(d,'INV',dx))
    # Join the original PMOS well and VDD stripe to the common upper band/rail.
    d.box('WN',(dx+8.9,42.25,dx+29.5,132))
    d.wire('M1',[(dx+17.2,76.3),(dx+17.2,128)])
    # Keep output crossover in M2, return to M1 beyond the RR guard connection.
    d.pcell('via_1',dx+99,50.5)
    d.wire('M1',[(dx+99,50.5),(dx+105,50.5)],3.4)
    d.wire('M1',[(dx+3,37),(dx+19.2,37)],3.4)
    return {'A':[dx+3,37.], 'Y':[dx+105,50.5]}


def draw(d,circuit,template):
    """Draw transistor bodies first, then rail extensions and public M1 pins."""
    name=circuit.name; width=WIDTHS[name]
    if name=='INV': pins=_inverter(d)
    elif name=='BUF':
        first=_inverter(d); second=_inverter(d,108.)
        d.pcell('via_1',*first['Y']); d.pcell('via_1',*second['A'])
        d.wire('M2',[first['Y'],[first['Y'][0],37.],second['A']],3.4)
        pins={'A':first['A'],'Y':second['Y']}
    elif name in ('NAND','NOR','NANY'):
        adapter=OriginalCoordinates(d,name)
        if name=='NANY': primitives.nany(adapter)
        else: primitives.pair(adapter,name.lower())
        # The source PMOS well now joins the continuous top nwell band.
        # It already reaches y>=124 for all three macros.
        py={'NANY':{'A':64.,'B':58.,'Y':70.},
            'NAND':{'A':58.,'B':64.,'Y':71.},
            'NOR':{'A':58.,'B':64.,'Y':71.}}[name]
        pins={}
        for pin in ('A','B'):
            y=py[pin]; d.pcell('via_1',9.,y)
            d.wire('M1',[(3.,y),(9.,y)],3.4); pins[pin]=[3.,y]
        ox=adapter.width+3
        d.pcell('via_1',ox,py['Y'])
        d.wire('M1',[(ox,py['Y']),(width-3,py['Y'])],3.4)
        pins['Y']=[width-3,py['Y']]
        if name=='NANY':
            # M1 crosses the two signal M2 buses. The lower M2 bridge crosses
            # the original VSS stripe without connecting it to VMID.
            d.wire('M2',[(84.,50.),(87.,50.)],3.4)
            d.pcell('via_1',87.,50.)
            d.wire('M1',[(87.,50.),(87.,20.)],3.4)
            d.pcell('via_1',87.,20.); d.pcell('via_1',87.,8.)
            d.wire('M2',[(87.,20.),(87.,8.)],3.4)
    elif name.startswith('TIE'):
        # One RR30 provides a finite-drive constant, with its well at VDD.
        rail={'TIEP':'VDD','TIEZ':'VMID','TIEN':'VSS'}[name]
        d.pcell('res_diff',36.,55.,{'w':2.8,'l':30.})
        d.box('WN',(8.5,43.6,63.5,88.4))
        d.pcell('cont_n',36.,77.)
        d.wire('GC',[(56.5,55.),(58.5,55.)])
        d.pcell('cont_g',58.5,55.)
        d.wire('M1',[(58.5,55.),(58.5,98.),(36.,98.),(36.,128.)])
        d.wire('M1',[(36.,77.),(36.,98.)])
        # Output escapes on M2 over the guard tie and returns at the right edge.
        d.wire('M1',[(51.5,55.),(51.5,66.)])
        d.pcell('via_1',51.5,66.); d.pcell('via_1',63.,66.)
        d.wire('M2',[(51.5,66.),(63.,66.)],3.4)
        d.wire('M1',[(63.,66.),(69.,66.)],3.4)
        y=sum(template['rails'][rail])/2
        if rail=='VDD':
            d.wire('M1',[(20.5,55.),(3.,55.),(3.,y)])
        else:
            d.wire('M1',[(20.5,55.),(3.,55.),(3.,20.)])
            d.pcell('via_1',3.,20.);d.pcell('via_1',3.,y)
            d.wire('M2',[(3.,20.),(3.,y)],3.4)
        pins={'Y':[69.,66.]}
    else: pins={}
    d.box('WN',(0,template['well_band'][0],width,template['well_band'][1]))
    # A dedicated tap makes the continuous band electrically VDD in every macro.
    d.pcell('cont_n',width-12.,125.5)
    d.wire('M1',[(width-12.,125.5),(width-12.,128.)])
    if name in ('INV','BUF','NAND','NOR','NANY'):
        # Original VSS stripe is at y=12..15.4. Cross VMID using a local M2 bridge.
        d.box('M1',(0,12.,width,15.4))
        d.pcell('via_1',15.,13.7);d.pcell('via_1',15.,2.)
        d.wire('M2',[(15.,13.7),(15.,2.)],3.4)
    else:
        d.pcell('cont_p',width-12.,28.)
        d.wire('M1',[(width-12.,28.),(width-12.,18.)])
        d.pcell('via_1',width-12.,18.);d.pcell('via_1',width-12.,2.)
        d.wire('M2',[(width-12.,18.),(width-12.,2.)],3.4)
    for rail,(y0,y1) in template['rails'].items():d.box('M1',(0,y0,width,y1))
    return width,pins
