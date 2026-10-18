"""Compact device placement/wiring adapted from the taped-out TR-1um builders.

Geometry originates in balanced-ternary-logic/layout/build_inverter.py,
build_nany.py and build_mul_primitives.py (Apache-2.0). Device placements and
short local poly gate connections are retained. NAND/NOR's upper row is moved
8 um down and its upper resistor 6 um down to share NANY's vertical envelope.
A coordinate adapter adds rail/pin margins without altering PCells.
"""

def inverter(d):
    """RR30 inverter with the original two-transistor placement."""
    # Fixed schematic devices, without modifying the PCell implementations.
    d.pcell("XM1", "fet_p", 13.2, 44, {"w": 13.5, "l": 1., "n": 1,
                                       "cont_between_gates": True, "y0": "c"})
    d.pcell("XM2", "fet_n", 13.2, 14, {"w": 5., "l": 1., "n": 1,
                                       "cont_between_gates": True, "y0": "c"})
    d.pcell("R1", "res_diff", 64, 45, {"w": 2.8, "l": 30.})
    d.pcell("R2", "res_diff", 64, 32, {"w": 2.8, "l": 30.})

    # Distinct PMOS and RR wells: the PDK prohibits PMOS active in an RR well.
    d.box("WN", 2.9, 30.25, 23.5, 61.3)
    # The mask deck requires 10 um around an RR-well tap, while the drawing
    # deck's generic N+ tap rule is only 5 um. Honor the stronger mask rule.
    d.box("WN", 36.5, 20.6, 91.5, 65.3)
    d.pcell("PMOS well tap", "cont_n", 13.2, 55)
    d.pcell("RR well tap", "cont_n", 64, 54)
    d.pcell("NMOS bulk tap", "cont_p", 5.8, 14)

    # Parent-accessible power rails and their physically connected taps.
    d.box("M1", 0, 62.6, 96, 66)
    d.box("M1", 0, 0, 96, 3.4)
    d.wire("M1", [(11.2, 44), (11.2, 64.3)], 2.6)
    d.wire("M1", [(11.2, 55), (13.2, 55)], 2.6)
    d.wire("M1", [(11.2, 14), (11.2, 1.7)], 2.6)
    d.wire("M1", [(5.8, 14), (5.8, 1.7)], 2.6)
    d.wire("M1", [(64, 54), (64, 64.3)], 2.6)

    # Both resistor GC guard rings are tied to their common VDD well.
    for y in (32, 45):
        # dev GC.R3 forbids contacts in the RR recognition region.
        d.wire("GC", [(84.5, y), (86.5, y)], 2.6)
        d.pcell(f"RR GC tie at y={y}", "cont_g", 86.5, y)
    d.wire("M1", [(86.5, 32), (86.5, 54), (64, 54)], 2.6)

    # Shared gate input. Only the two intended active crossings form MOS gates.
    d.wire("GC", [(13.2, 14), (13.2, 44)], 1.)
    d.pcell("vin gate contact", "cont_g", 13.2, 25)
    d.box("M1", 0, 23.7, 13.2, 26.3)

    # XM1.D -> R1.A and XM2.D -> R2.A; right RR terminals form vout.
    d.wire("M1", [(15.2, 44), (30, 44), (30, 45), (48.5, 45)], 2.6)
    d.wire("M1", [(15.2, 14), (30, 14), (30, 32), (48.5, 32)], 2.6)
    d.wire("M1", [(79.5, 32), (79.5, 45)], 2.6)
    # M2 crosses the RR guard supply without a short. Via is between GC rings.
    d.pcell("vout M1-M2 access", "via_1", 79.5, 38.5)
    d.box("M2", 79.5, 36.8, 96, 40.2)



def nany(d):
    """Original eight-MOS main/clamp stacks and two RR30 branches."""
    width = 148.
    for role, kind, x, y, w in [
        ('XM5', 'fet_p', 20, 88, 34), ('XM3', 'fet_p', 35, 88, 34),
        ('XM6', 'fet_p', 50, 88, 14), ('XM8', 'fet_p', 65, 88, 14),
        ('XM2', 'fet_n', 20, 15, 11), ('XM1', 'fet_n', 35, 15, 11),
        ('XM7', 'fet_n', 50, 15, 8), ('XM9', 'fet_n', 65, 15, 8),
    ]:
        d.pcell(role, kind, x, y, dict(w=w, l=1., n=1,
                                     cont_between_gates=True, y0='c'))
    for role, y in [('R2', 72), ('R1', 42)]:
        d.pcell(role, 'res_diff', 112.5, y, dict(w=2.8, l=30.))

    d.box('WN', 6.3, 64, 75.3, 112)
    d.box('WN', 85, 30.6, 140, 83.4)
    d.pcell('PMOS well tap', 'cont_n', 12.6, 88)
    d.pcell('RR well tap', 'cont_n', 112.5, 57)
    for x in (8, 76):
        d.pcell('VSS bulk tap', 'cont_p', x, 15)
        d.wire('M1', [(x, 15), (x, 1.7)], 2.6)
    d.box('M1', 0, 111.6, width, 115)
    d.box('M1', 0, 0, width, 3.4)
    d.wire('M1', [(12.6, 88), (15, 88), (15, 113.3)], 2.6)
    d.wire('M1', [(112.5, 57), (112.5, 98), (135, 98), (135, 113.3)], 2.6)
    for y in (42, 72):
        # dev GC.R3: extend GC out of the RR recognition region before contacting it.
        d.wire('GC', [(133, y), (135, y)], 2.6)
        d.pcell('RR GC tie', 'cont_g', 135, y)
    d.wire('M1', [(135, 42), (135, 98)], 2.6)

    def via(x, y, role):
        d.pcell(role, 'via_1', x, y)

    def fanout(x0, y0, x):
        # Fill the same-net notch between the diffusion contact strip and trunk.
        w = (34 if x0 < 40 else 14) if y0 == 88 else (11 if x0 < 40 else 8)
        d.box('M1', min(x0,x)-1.3, y0-w/2, max(x0,x)+1.3, y0+w/2)

    def trunk(x0, y0, x, y, role):
        if y0 in (15,88) and x0 != x:
            fanout(x0, y0, x)
        d.wire('M1', [(x0, y0), (x, y0), (x, y)], 2.6)
        via(x, y, role)

    # Main series stacks. Left/right diffusion assignment is electrically
    # interchangeable; bulk is fixed to VDD or VSS by the well/tap structure.
    fanout(18, 88, 15)
    d.wire('M1', [(18, 88), (15, 88)], 2.6)
    d.wire('M1', [(22, 88), (33, 88)], 2.6)  # net1
    trunk(37, 88, 40, 64, 'net2')
    trunk(18, 15, 15, 32, 'net3')
    d.wire('M1', [(22, 15), (33, 15)], 2.6)  # net4
    fanout(37, 15, 40)
    d.wire('M1', [(37, 15), (40, 15), (40, 1.7)], 2.6)

    for x in (50, 65):
        trunk(x-2, 88, x-5, 58, 'vout clamp')
        trunk(x-2, 15, x-5, 38, 'VMID clamp')
        fanout(x+2, 88, x+5)
        fanout(x+2, 15, x+5)
        d.wire('M1', [(x+2, 88), (x+5, 88), (x+5, 15), (x+2, 15)], 2.6)

    # Main gates share vertical GC, since their p/n gate nets are identical.
    for x, y in [(20, 52), (35, 46)]:
        d.wire('GC', [(x, 15), (x, 88)], 1.)
        d.pcell('main input gate', 'cont_g', x, y)
        d.wire('M1', [(x,y), (x+3.3,y)], 2.6)
        via(x+3.3, y, 'main input access')
    # The two clamp stacks use opposite p/n gate nets.
    for x, track in [(50, 52), (65, 46)]:
        d.wire('GC', [(x, 88), (x, 76)], 1.)
        d.pcell('clamp p gate', 'cont_g', x, 76)
        trunk(x, 76, x, track, 'clamp p input')
    for x in (50, 65):
        d.wire('GC', [(x, 15), (x, 23)], 1.)
        d.pcell('clamp n gate', 'cont_g', x, 23)
    trunk(50, 23, 50, 46, 'clamp n b')
    d.wire('M1', [(65,23), (65,26.3)], 2.6)
    via(65, 26.3, 'clamp n a crossover')
    d.wire('M2', [(65, 26.3), (75, 26.3)], 3.4)
    via(75, 26.3, 'clamp n a return')
    trunk(75, 26.3, 75, 52, 'clamp n a')

    # RR terminals; SUB and both GC rings are already physically tied to VDD.
    trunk(97, 72, 97, 64, 'R2 input')
    trunk(97, 42, 97, 32, 'R1 input')
    d.wire('M1', [(128, 42), (128, 72)], 2.6)
    via(128, 58, 'RR output')
    for xa, xb, y in [(15, 97, 32), (40, 97, 64),
                       (45, width-1.7, 58), (1.7, 80, 38),
                       (1.7, 75, 52), (1.7, 65, 46)]:
        d.wire('M2', [(xa, y), (xb, y)], 3.4)



def pair(d,kind):
    """NAND parallel-P/series-N or NOR series-P/parallel-N topology."""
    p,n=(19,13) if kind=="nand" else (37,6.5)
    rl=30
    width,height=132,115
    assert rl==30
    left,right,tie=74.5,105.5,112.5
    for x,tag in [(20,'a'),(35,'b')]:
     for cell,y,w in [('fet_p',88,p),('fet_n',16,n)]:d.pcell(cell+'_'+tag,cell,x,y,dict(w=w,l=1.,n=1,cont_between_gates=True,y0='c'))
    for role,y in [('Rtop',72),('Rbottom',42)]:d.pcell(role,'res_diff',90,y,dict(w=2.8,l=rl))
    d.box('WN',6.3,62.5,45.3,113.5);d.box('WN',62.5,30.6,117.5,83.4)
    d.pcell('PMOS well tap','cont_n',12.6,88);d.pcell('RR well tap','cont_n',90,60);d.pcell('bulk tap','cont_p',8,16)
    d.box('M1',0,111.6,width,115);d.box('M1',0,0,width,3.4)
    d.wire('M1',[(8,16),(8,1.7)],2.6);d.wire('M1',[(12.6,88),(15,88),(15,113.3)],2.6)
    d.wire('M1',[(90,60),(90,100),(tie,100),(tie,113.3)],2.6)
    for y in (42,72):d.wire('GC',[(tie-2,y),(tie,y)],2.6);d.pcell('RR GC tie','cont_g',tie,y)
    d.wire('M1',[(tie,42),(tie,100)],2.6)
    def via(x,y,role):d.pcell(role,'via_1',x,y)
    def fan(x0,y,x,w):d.box('M1',min(x0,x)-1.3,y-w/2,max(x0,x)+1.3,y+w/2)
    def trunk(x0,y,x,yy,w,role):fan(x0,y,x,w);d.wire('M1',[(x0,y),(x,y),(x,yy)],2.6);via(x,yy,role)
    if kind=='nand':
     for x in (20,35):
      fan(x-2,88,x-5,p);d.wire('M1',[(x-2,88),(x-5,88),(x-5,113.3)],2.6)
      trunk(x+2,88,x+5,64,p,'parallel P drain')
     d.wire('M2',[(25,64),(left,64)],3.4)
     trunk(18,16,15,30,n,'series N drain');d.wire('M1',[(22,16),(33,16)],2.6)
     fan(37,16,40,n);d.wire('M1',[(37,16),(40,16),(40,1.7)],2.6)
     d.wire('M2',[(15,30),(left,30)],3.4)
    else:
     fan(18,88,15,p);d.wire('M1',[(18,88),(15,88)],2.6);d.wire('M1',[(22,88),(33,88)],2.6)
     trunk(37,88,40,64,p,'series P drain');d.wire('M2',[(40,64),(left,64)],3.4)
     for x in (20,35):
      fan(x-2,16,x-5,n);d.wire('M1',[(x-2,16),(x-5,16),(x-5,1.7)],2.6)
      trunk(x+2,16,x+5,30,n,'parallel N drain')
     d.wire('M2',[(25,30),(left,30)],3.4)
    for x,y in [(20,46),(35,52)]:
     d.wire('GC',[(x,16),(x,88)],1.);d.pcell('input gate','cont_g',x,y)
     d.wire('M1',[(x,y),(x+3.3,y)],2.6);via(x+3.3,y,'input access');d.wire('M2',[(1.7,y),(x+3.3,y)],3.4)
    for y,track in [(72,64),(42,30)]:d.wire('M1',[(left,y),(left,track)],2.6);via(left,track,'RR input')
    d.wire('M1',[(right,42),(right,72)],2.6);via(right,59,'output access');d.wire('M2',[(right,59),(width-1.7,59)],3.4)

