"""Electrical completeness and geometric invariants of the schematic stage."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from tritflow.flow import load, loads
from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.schematic import draw, legend
from tritflow.schematic.vector import TRIT_COLOR, FONT

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
    assert inputs[0].label=='a[10]'  # the used bit stays next to its consumer
    assert [n.label for n in inputs[1:]]==[f'a[{i}]' for i in range(12) if i!=10]
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
    from tritflow.pnr import Library, place_and_route
    net=circuit('half_add')
    result=place_and_route(net,Library.load(ROOT/'cells'),output_dir=tmp_path,run_pdk_drc=False,anneal_steps=0)
    assert result.data['library']['mock'] is False
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
    vector=sch._vector()
    for item in vector.items:
        if item['kind']!='text':
            # Check symbol pin stubs as well as the routed wires: gate curves
            # themselves use longer paths; every simple line is Manhattan.
            if item['kind']=='path' and len(item['commands'])==2:
                (_,x0,y0),(_,x1,y1)=item['commands']
                assert x0==x1 or y0==y1
            continue
        font=FontProperties(family=FONT,size=item['size']*.75,weight=item['weight'])
        w,h,d=renderer.get_text_width_height_descent(item['text'],font,False)
        x=item['x']-{'start':0,'middle':.5,'end':1}[item['anchor']]*w
        y=item['y']-h+d
        box=(x,y,x+w,y+h,item['text'])
        assert x>=0 and y>=0 and x+w<=vector.width and y+h<=vector.height
        for wire in sch.scene.segments:
            assert not (max(x,wire.a[0])<min(x+w,wire.b[0]) and
                        max(y,wire.a[1])<min(y+h,wire.b[1])),(box,wire)
            if wire.a[1]==wire.b[1]:
                assert not (y<wire.a[1]<y+h and max(x,wire.a[0])<min(x+w,wire.b[0])),(box,wire)
            else:
                assert not (x<wire.a[0]<x+w and max(y,wire.a[1])<min(y+h,wire.b[1])),(box,wire)
        for node in sch.scene.symbols:
            if item.get('owner')==node.key:
                # Gate names occupy the reserved strip above the outline.
                # A large readable label may extend into the empty side halo.
                assert y+h<=node.y+56
                continue
            a,b,c,d=node.box
            contained=a<=x<=x+w<=c and b<=y<=y+h<=d
            assert contained or max(x,a)>=min(x+w,c) or max(y,b)>=min(y+h,d),(box,node)
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
    palette=runpy.run_path(str(ROOT/'figures/paperstyle.py'))
    assert TRIT_COLOR==palette['TRIT_COLOR']


@pytest.mark.parametrize('name,n',CASES)
@pytest.mark.parametrize('expand',[None,'*'])
def test_gallery_metric_budgets_against_reviewed_baseline(name,n,expand):
    baseline=json.loads((ROOT/'tritflow/schematic/assets/baseline_metrics.json').read_text())['items']
    stem=f'adder{n}' if name=='adder' else name
    mode='flat' if expand else 'hierarchical'
    before=baseline[f'{stem}-{mode}']
    after=draw(circuit(name,n),expand=expand).metrics
    # Round 4 reserves actual wire/pin clearances. Do not reward the close
    # tracks of the old gallery; retain a bound against the original dump.
    assert after['wire_length_px'] <= 1.25*before['wire_length_px']
    assert after['bends_total'] <= before['bends_total']
    assert after['bends_per_net_mean'] <= before['bends_per_net_mean']
    assert 0.65 < after['aspect_ratio'] < 4.5
    assert after['wire_length_px']==sum(row['wire_length_px'] for row in after['nets'].values())
    previous={i['name']:i['metrics'] for i in json.loads(
        (ROOT/'tritflow/schematic/assets/phase4_metrics.json').read_text())}[f'{stem}-{mode}']
    # Standalone macro reuse and blocked frame interiors replace phase 4's
    # global compaction. Bound that deliberate channel cost against the last
    # reviewed gallery; exact geometry/type invariants are tested separately.
    assert after['wire_length_px']<=1.5*previous['wire_length_px']
    assert after['bends_total']<=max(previous['bends_total']*1.4,previous['bends_total']+4)
    assert after['crossings']<=max(previous['crossings']*1.75,previous['crossings']+5)


@pytest.mark.parametrize('name,n',CASES)
@pytest.mark.parametrize('expand',[None,'*'])
def test_gallery_gates_face_right_without_short_jogs_or_symbol_edge_runs(name,n,expand):
    sch=draw(circuit(name,n),expand=expand)
    assert sch.metrics['short_jogs']==0
    assert sch.metrics['symbol_edge_runs']==0
    assert sch.metrics['rotated_gates']==0
    for node in sch.scene.symbols:
        if node.kind in {'input','output','block'}:continue
        assert all(node.sides[p]=='left' and node.pins[p][0]==node.x for p in node.inputs)
        assert all(node.sides[p]=='right' and node.pins[p][0]==node.x+node.width for p in node.outputs)


def test_ripple_is_straight_with_formal_ports_and_local_external_pins():
    sch=draw(circuit('adder',4))
    symbols={s.key:s for s in sch.scene.symbols}
    blocks=sorted((s for s in sch.scene.symbols if s.kind=='block'),key=lambda s:s.x)
    assert len({s.y for s in blocks})==1
    for i,block in enumerate(blocks):
        assert block.module=='full_add'
        aliases={alias:block.pins[pin] for pin,alias in block.pin_labels.items()}
        assert set(aliases)=={'a','b','cin','sum','cout'}
        assert aliases['cin'][1]==aliases['cout'][1]
        for name in ('a','b'):
            flag=symbols[f'input:{name}[{i}]']
            assert flag.pins['port'][0]==aliases[name][0]
            assert 0<block.y-flag.pins['port'][1]<=96
        flag=symbols[f'output:sum[{i}]']
        assert flag.pins['port'][0]==aliases['sum'][0]
        assert 0<flag.pins['port'][1]-aliases['sum'][1]<=96
    assert sch.metrics['crossings']==sch.metrics['bends_total']==0


def test_half_adder_straight_t_trunk_and_two_bend_target():
    net=circuit('half_add')
    sch=draw(net)
    gt=next(s for s in sch.scene.symbols if s.label=='g_t')
    gd=next(s for s in sch.scene.symbols if s.label=='g_d')
    source,target=gt.pins['Y'],gd.pins['A']
    assert source[1]==target[1]
    signal=gt.outputs['Y']
    assert any(s.net==signal and s.a[1]==s.b[1]==source[1]
               and s.a[0]<=source[0]<target[0]<=s.b[0] for s in sch.scene.segments)
    assert sch.metrics['bends_per_net_max']<=2
    gu=next(s for s in sch.scene.symbols if s.label=='g_u')
    gc=next(s for s in sch.scene.symbols if s.label=='g_c')
    source,target=gu.pins['Y'],gc.pins['B']
    assert source[1]==target[1]
    assert any(s.net==gu.outputs['Y'] and s.a[1]==s.b[1]==source[1]
               and s.a[0]<=source[0]<target[0]<=s.b[0] for s in sch.scene.segments)


def test_full_adder_compact_frames_contain_the_correct_cells():
    sch=draw(circuit('full_add'),expand='*')
    # Identical standalone half-adder templates take precedence over the
    # old folded 2:1 panel. Two uncompressed templates remain side by side.
    assert 3.0<=sch.metrics['aspect_ratio']<=4.2
    frames=sorted(sch.scene.frames,key=lambda f:f.box[0])
    assert [f.label for f in frames]==['ha1','ha2']
    assert frames[0].box[2]<frames[1].box[0]
    for frame in frames:
        assert len(frame.members)==7
        for node in sch.scene.symbols:
            if not set(node.members)&set(frame.members):continue
            x0,y0,x1,y1=frame.box;a,b,c,d=node.box
            assert x0<=a<c<=x1 and y0<=b<d<=y1


def test_arithmetic_aliases_are_verified_without_instance_name_heuristics():
    from tritflow.schematic.arithmetic import recognize
    net=circuit('full_add')
    original=recognize(net)[''].ports
    for k,inst in enumerate(net.instances):inst.name=f'renamed_{k}'
    assert recognize(net)[''].ports==original
    # A different gate function must not retain a claimed full-adder grammar.
    next(i for i in net.instances if i.cell=='NANY').cell='NAND'
    assert '' not in recognize(net)


def test_explicit_port_metadata_for_an_unknown_module():
    net=GateNetlist('custom',[Port('a','input'),Port('y','output')],[
        Instance('inner.first','INV',{'A':'a','Y':'mid'},'inner'),
        Instance('inner.second','INV',{'A':'mid','Y':'y'},'inner')])
    sch=draw(net,hierarchy={'inner':{'module':'custom_buffer','ports':{'P':'a','Q':'y'}}})
    block=next(s for s in sch.scene.symbols if s.kind=='block')
    assert block.module=='custom_buffer'
    assert set(block.pin_labels.values())=={'P','Q'}
    assert_connections(net,sch.scene)


def test_metric_definition_counts_bends_and_unconnected_crossings():
    from tritflow.schematic.metrics import measure
    from tritflow.schematic.model import Scene,Segment
    scene=Scene('known',(),(Segment('n',(0,0),(16,0)),Segment('n',(16,0),(16,16)),
                            Segment('other',(8,-8),(8,8))),{},(),{},40,20)
    metrics=measure(scene)
    assert metrics['wire_length_px']==48
    assert metrics['bends_total']==1 and metrics['crossings']==1
    assert metrics['aspect_ratio']==2


def test_review_audit_distinguishes_jogs_stubs_junctions_and_pin_contact():
    from tritflow.schematic.metrics import measure
    from tritflow.schematic.model import Scene,Segment,Symbol
    jog=(Segment('jog',(0,0),(16,0)),Segment('jog',(16,0),(16,16)),
         Segment('jog',(16,16),(48,16)))
    pitch=(Segment('pitch',(0,32),(16,32)),Segment('pitch',(16,32),(16,64)),
           Segment('pitch',(16,64),(48,64)))
    stub=(Segment('stub',(0,80),(8,80)),Segment('stub',(8,80),(8,112)))
    edge=(Segment('edge',(64,64),(144,64)),Segment('pin',(144,96),(160,96)))
    node=Symbol('gate','INV','gate',x=64,y=64,width=80,height=96,orient='down')
    scene=Scene('audit',(node,),jog+pitch+stub+edge,{},(),{},192,192)
    m=measure(scene)
    assert m['short_jogs']==1 and m['nets']['jog']['short_jogs']==1
    assert m['nets']['pitch']['short_jogs']==m['nets']['stub']['short_jogs']==0
    assert m['rotated_gates']==m['symbol_edge_runs']==1
    # A T splits the short leg into two branches, neither between two corners.
    scene.segments+=(Segment('jog',(16,8),(32,8)),)
    assert measure(scene)['short_jogs']==0


def test_legend_uses_the_same_orthogonal_pin_stubs():
    for item in legend()._vector().items:
        if item['kind']=='path' and len(item['commands'])==2:
            (_,x0,y0),(_,x1,y1)=item['commands']
            assert x0==x1 or y0==y1
