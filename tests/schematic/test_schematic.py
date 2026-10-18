"""Electrical completeness and geometric invariants of the schematic stage."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from tritflow.flow import load, loads
from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.schematic import draw, legend
from tritflow.schematic.vector import TRIT_COLOR

ROOT = Path(__file__).resolve().parents[2]


def circuit(name, n=None):
    return load(ROOT/f'examples/{name}.tv', name, {'N':n} if n else {}).synthesize()


CASES = [('half_add',None),('full_add',None),('adder',2),('adder',4),('mul1',None),
         ('mac1',None),('sign',None),('compare2',None),('mul2',None),('minmax',None)]


def inside_wire(segment, box):
    """A wire may touch its terminal on the keep-out boundary, never enter it."""
    x0,y0,x1,y1=box
    a,b=segment.a,segment.b
    if a[1]==b[1]:
        return y0 < a[1] < y1 and max(a[0],x0) < min(b[0],x1)
    return x0 < a[0] < x1 and max(a[1],y0) < min(b[1],y1)


def assert_geometry(scene):
    for index,node in enumerate(scene.symbols):
        for other in scene.symbols[index+1:]:
            a,b=node.box,other.box
            assert max(a[0],b[0]) >= min(a[2],b[2]) or max(a[1],b[1]) >= min(a[3],b[3])
        for wire in scene.segments:
            assert not inside_wire(wire,node.box),(wire,node)
    for index,a in enumerate(scene.segments):
        assert a.a[0]==a.b[0] or a.a[1]==a.b[1]
        assert all(coord%8==0 for point in (a.a,a.b) for coord in point)
        for b in scene.segments[index+1:]:
            if a.net==b.net:
                continue
            if a.a[0]==a.b[0]==b.a[0]==b.b[0]:
                assert max(a.a[1],b.a[1])>=min(a.b[1],b.b[1]),(a,b)
            if a.a[1]==a.b[1]==b.a[1]==b.b[1]:
                assert max(a.a[0],b.a[0])>=min(a.b[0],b.b[0]),(a,b)


def assert_connections(net,scene):
    expected={f'port:{p.name}':p.name for p in net.ports}
    expected.update({f'cell:{i.name}:{p}':s for i in net.instances for p,s in i.pins.items()})
    assert Counter(c.endpoint for c in scene.connections)==Counter({key:1 for key in expected})
    assert {c.endpoint:c.net for c in scene.connections}==expected
    # Every displayed terminal must lie on the connected drawing of its net.
    # Build a same-net connectivity graph, splitting at intersections / T joins.
    by_net=defaultdict(list)
    symbols={s.key:s for s in scene.symbols}
    for c in scene.connections:
        if c.pin is not None:
            by_net[c.net].append(symbols[c.symbol].pins[c.pin])
    for signal,pins in by_net.items():
        segments=[s for s in scene.segments if s.net==signal]
        points=set(pins)|{p for s in segments for p in (s.a,s.b)}
        adjacency=defaultdict(set)
        for s in segments:
            on=[p for p in points if ((s.a[0]==s.b[0]==p[0] and s.a[1]<=p[1]<=s.b[1]) or
                                    (s.a[1]==s.b[1]==p[1] and s.a[0]<=p[0]<=s.b[0]))]
            for a,b in zip(sorted(on),sorted(on)[1:]):
                adjacency[a].add(b); adjacency[b].add(a)
        visited=set()
        stack=[pins[0]]
        while stack:
            p=stack.pop()
            if p not in visited:
                visited.add(p); stack.extend(adjacency[p]-visited)
        assert set(pins)<=visited,(signal,pins,visited)
        assert all(p in visited for p in points),(signal,'disconnected wire island')


@pytest.mark.parametrize('name,n',CASES)
@pytest.mark.parametrize('expand',[None,'*'])
def test_real_circuits(name,n,expand):
    net=circuit(name,n)
    sch=draw(net,expand=expand)
    assert_geometry(sch.scene)
    assert_connections(net,sch.scene)
    assert sch.svg==draw(net,expand=expand).svg
    # Netlist JSON ordering is incidental, never part of placement determinism.
    shuffled=GateNetlist(net.top,list(reversed(net.ports)),list(reversed(net.instances)))
    assert sch.svg==draw(shuffled,expand=expand).svg


def test_hierarchy_expansion_and_block_contents():
    net=circuit('adder',4)
    closed=draw(net)
    assert {s.label for s in closed.scene.symbols if s.kind=='block'}=={f'digit[{i}].fa' for i in range(4)}
    opened=draw(net,expand=['digit[1].fa'])
    assert len([s for s in opened.scene.symbols if s.kind=='block'])==3
    assert len([s for s in opened.scene.symbols if s.members and s.kind!='block'])==16
    assert_geometry(opened.scene)
    assert_connections(net,opened.scene)
    assert sum(len(s.members) for s in closed.scene.symbols)==len(net.instances)
    assert closed.scene.hidden_nets
    with pytest.raises(ValueError,match='unknown hierarchy'):
        draw(net,expand='digit[99].fa')


def test_overlay_reuses_routes_and_public_pnr_method():
    net=circuit('half_add')
    sch=draw(net)
    class Pnr:
        def net_parasitics(self):
            return {'nets':{'a':{'wire_capacitance_f':10e-15,'total_load_f':900e-15},'b':{'wire_capacitance_f':100e-15},
                            'VDD':{'capacitance_f':1000e-15}},'assumptions':'estimated'}
    annotated=sch.annotate(inputs={'a':-1,'b':1},parasitics=Pnr(),net_names=True)
    assert annotated.scene is sch.scene
    assert annotated.values['sum']==0
    assert annotated.values['carry']==0
    assert annotated.capacitance_f=={'a':10e-15,'b':100e-15}
    assert '10.0 fF' in annotated.svg and '100.0 fF' in annotated.svg
    assert TRIT_COLOR[0] in annotated.svg
    assert annotated.annotate(inputs=None,parasitics=None,net_names=False).svg==sch.svg
    assert sch.svg==draw(net).svg


@pytest.mark.parametrize('cap',[-1,float('nan'),float('inf'),'bad',{}])
def test_invalid_capacitance(cap):
    with pytest.raises(ValueError):
        draw(circuit('half_add'),parasitics={'a':cap})


def test_constants_unused_input_fanout_repeated_pins_and_bus_order():
    net=loads("""module edge(input trit [11:0] a, output trit p, z, n, v);
       assign p = 1't1; assign z = 1't0; assign n = 1'tT;
       nany repeated(v,a[10],a[10]); endmodule""",'edge').synthesize()
    sch=draw(net,net_names=True)
    assert_geometry(sch.scene)
    assert_connections(net,sch.scene)
    inputs=sorted((s for s in sch.scene.symbols if s.kind=='input'),key=lambda s:s.y)
    assert [n.label for n in inputs]==[f'a[{i}]' for i in range(12)]
    assert {'TIEP','TIEZ','TIEN'} <= {s.kind for s in sch.scene.symbols}
    assert sch.scene.junctions['a[10]']


def test_pdf_png_svg_and_connection_metadata(tmp_path):
    sch=draw(circuit('half_add'))
    assert sch.pdf.startswith(b'%PDF-')
    assert sch.pdf==sch.pdf
    assert sch.png().startswith(b'\x89PNG')
    assert sch._repr_svg_()==sch.svg
    root=ET.fromstring(sch.svg)
    info=json.loads(root.find('{http://www.w3.org/2000/svg}metadata').text)
    assert len(info['connections'])==len(sch.scene.connections)
    for suffix in ('.svg','.pdf','.png'):
        path=sch.save(tmp_path/('circuit'+suffix))
        assert path.is_file()
    with pytest.raises(ValueError): sch.save(tmp_path/'bad.jpg')
    with pytest.raises(ValueError): sch.png(scale=0)
    with pytest.raises(ValueError): draw(circuit('half_add'),inputs={'a':[0,1],'b':[0,1]})
    figure=legend()
    assert '−sat(a + b)' in figure.svg
    assert figure.pdf.startswith(b'%PDF-')
    assert figure.png().startswith(b'\x89PNG')


def test_public_pnr_result_integration(tmp_path):
    from tritflow.pnr import mock_library, place_and_route
    net=circuit('half_add')
    result=place_and_route(net,mock_library(),output_dir=tmp_path,run_pdk_drc=False,anneal_steps=0)
    report=result.net_parasitics()
    sch=draw(net,parasitics=result)
    assert sch.capacitance_f=={s:r['wire_capacitance_f'] for s,r in report['nets'].items()}
    assert all(c>=0 for c in sch.capacitance_f.values())
    assert 'fF' in sch.svg


@pytest.mark.parametrize('name,n',CASES)
@pytest.mark.parametrize('expand',[None,'*'])
def test_labels_never_overlap_with_all_overlays(name,n,expand):
    from matplotlib.backends.backend_agg import RendererAgg
    from matplotlib.font_manager import FontProperties
    net=circuit(name,n)
    sch=draw(net,expand=expand,net_names=True,
             inputs={p.name:1 for p in net.ports if p.dir=='input'},
             parasitics={s:100e-15 for s in net.nets()})
    renderer=RendererAgg(100,100,96)
    boxes=[]
    for item in sch._vector().items:
        if item['kind']!='text':
            # Check symbol pin stubs as well as the routed wires: gate curves
            # themselves use longer paths; every simple line is Manhattan.
            if item['kind']=='path' and len(item['commands'])==2:
                (_,x0,y0),(_,x1,y1)=item['commands']
                assert x0==x1 or y0==y1
            continue
        font=FontProperties(family='DejaVu Sans',size=item['size']*.75,weight=item['weight'])
        w,h,d=renderer.get_text_width_height_descent(item['text'],font,False)
        x=item['x']-{'start':0,'middle':.5,'end':1}[item['anchor']]*w
        y=item['y']-h+d
        box=(x,y,x+w,y+h,item['text'])
        assert x>=0 and y>=0 and x+w<=sch.scene.width and y+h<=sch.scene.height
        for other in boxes:
            assert (max(x,other[0])>=min(x+w,other[2]) or
                    max(y,other[1])>=min(y+h,other[3])),(box,other)
        boxes.append(box)


def test_nonconvex_hierarchy_opens_without_drawing_false_feedback():
    net=GateNetlist('shared',[Port('a','input'),Port('y','output')],[
        Instance('left.first','INV',{'A':'a','Y':'n1'},'left'),
        Instance('middle.g','INV',{'A':'n1','Y':'n2'},'middle'),
        Instance('left.last','INV',{'A':'n2','Y':'y'},'left')])
    sch=draw(net)
    assert sch.scene.notes
    assert not [s for s in sch.scene.symbols if s.kind=='block']
    assert_geometry(sch.scene)
    assert_connections(net,sch.scene)


def test_xml_escapes_and_invalid_public_netlists():
    net=GateNetlist('special & <title>',[Port('a&b','input'),Port('y','output')],
                    [Instance('g"<','INV',{'A':'a&b','Y':'y'})])
    sch=draw(net,net_names=True)
    ET.fromstring(sch.svg)
    assert '&amp;' in sch.svg and '&lt;' in sch.svg
    net.instances.append(Instance('other','INV',{'A':'a&b','Y':'y'}))
    with pytest.raises(ValueError,match='multiple drivers'):
        draw(net)


def test_paper_palette_matches_source():
    # Source is not an importable installed-package dependency; check the
    # copied three constants so paper and notebook signal hues cannot drift.
    import runpy
    palette=runpy.run_path(str(ROOT/'figures/style.py'))
    assert TRIT_COLOR==palette['TRIT_COLOR']
