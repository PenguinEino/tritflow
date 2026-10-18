"""Repeated modules retain their standalone circuit layout and readable type."""
from collections import defaultdict

import pytest

from tritflow.netlist import GateNetlist,Instance
from tritflow.schematic import draw,legend
from tritflow.schematic.audit import inspect
from tritflow.schematic.arithmetic import recognize
from test_schematic import CASES,circuit,assert_connections,assert_geometry


@pytest.mark.parametrize('name,n', [('full_add',None),('adder',2),('adder',4),('mac1',None),('mul2',None)])
def test_framed_cells_and_internal_routes_are_standalone_templates(name,n):
    net=circuit(name,n);sch=draw(net,expand='*')
    symbols={s.key:s for s in sch.scene.symbols}
    for f in sch.scene.frames:
        reference=draw(circuit(f.module)).scene
        actual={s.label.rsplit('.',1)[-1]:s for s in sch.scene.symbols if set(s.members)&set(f.members)}
        expected={s.label:s for s in reference.symbols if s.members}
        assert actual.keys()==expected.keys()
        role=next(iter(expected));a,b=actual[role],expected[role]
        dx,dy=a.x-b.x,a.y-b.y
        mapping={}
        for role,b in expected.items():
            a=actual[role]
            assert (a.x,a.y,a.width,a.height)==(b.x+dx,b.y+dy,b.width,b.height)
            assert a.pins=={pin:(p[0]+dx,p[1]+dy) for pin,p in b.pins.items()}
            mapping.update({s:(a.inputs|a.outputs)[pin] for pin,s in (b.inputs|b.outputs).items()})
        # Boundary adapters only change port-net leads. All internal lanes,
        # bends and fan-out junctions remain the exact standalone drawing.
        ports={p.net for p in reference.connections if p.endpoint.startswith('port:')}
        wanted={(mapping[w.net],(w.a[0]+dx,w.a[1]+dy),(w.b[0]+dx,w.b[1]+dy))
                for w in reference.segments if w.net not in ports}
        got={(w.net,w.a,w.b) for w in sch.scene.segments if w.net in {row[0] for row in wanted}}
        # MAC's two explicit Boolean taps add boundary leads to those nets.
        taps={f.nets[p] for p in ('t1','t3') if p in f.nets}
        assert {w for w in wanted if w[0] not in taps}=={w for w in got if w[0] not in taps}
        assert all(p in f.nets and p in f.sides for p in f.pins)
        assert all(s.key in symbols for s in actual.values())
    assert sch.scene.interconnect
    assert inspect(sch.scene)==[]


def test_full_adder_flags_are_local_and_its_inputs_do_not_wrap():
    sch=draw(circuit('full_add'),expand='*');s={n.key:n for n in sch.scene.symbols}
    first,second=sorted(sch.scene.frames,key=lambda f:f.box[0])
    for name in ('a','b'):
        source=s['input:'+name].pins['port'];target=first.pins[name]
        assert source[1]==target[1] and target[0]-source[0]==96
        routes=[w for w in sch.scene.interconnect if w.net==name]
        assert len(routes)==1 and routes[0].a==source and routes[0].b==target
    assert first.box[2]<s['input:cin'].x<second.box[0]
    assert s['input:cin'].pins['port'][1]==second.pins['b'][1]
    assert s['output:sum'].x>second.box[2]
    assert s['output:cout'].x>s['cell:g_cout'].box[2]


@pytest.mark.parametrize('name,n',CASES)
@pytest.mark.parametrize('overlay',[False,True])
def test_every_label_is_at_least_nine_points_at_1000_pixels(name,n,overlay):
    net=circuit(name,n)
    sch=draw(net,expand='*',inputs={p.name:1 for p in net.ports if p.dir=='input'} if overlay else None)
    v=sch._vector()
    assert all(i['size']*.75*1000/v.width>=9-1e-9 for i in v.items if i['kind']=='text')
    assert sch.metrics['min_font_pt_at_1000px']>=9-1e-9


def test_symbol_legend_has_the_same_readable_minimum_type_size():
    v=legend()._vector()
    assert min(i['size'] for i in v.items if i['kind']=='text')*.75*1000/v.width>=9


def test_flat_adder_uses_one_digit_row_without_reducing_label_size():
    scene=draw(circuit('adder',4),expand='*').scene
    rows=defaultdict(list)
    for f in scene.frames:rows[f.box[1]].append(f)
    assert len(rows)==4 and all(len(v)==2 for v in rows.values())
    assert len({(f.box[2]-f.box[0],f.box[3]-f.box[1]) for f in scene.frames})==1


def test_compare2_is_feedforward_without_a_return_to_the_left_edge():
    net=circuit('compare2');scene=draw(net,expand='*').scene
    symbols={s.key:s for s in scene.symbols}
    producer={s:n for n in scene.symbols for s in n.outputs.values()}
    for node in scene.symbols:
        if node.kind in {'input','output'}:continue
        for signal in node.inputs.values():
            assert producer[signal].pins[next(p for p,s in producer[signal].outputs.items() if s==signal)][0]<node.x
    assert inspect(scene)==[]


def test_macro_recovery_without_serialized_child_hierarchy():
    original=circuit('full_add')
    net=GateNetlist(original.top,original.ports,[Instance(i.name,i.cell,i.pins) for i in original.instances])
    sch=draw(net,expand='*')
    assert {f.label for f in sch.scene.frames}=={'ha1','ha2'}
    assert_geometry(sch.scene);assert_connections(net,sch.scene)


def test_selective_half_expansion_keeps_parent_wires_outside_the_frame():
    net=circuit('full_add');sch=draw(net,expand='ha1')
    assert len(sch.scene.frames)==1
    assert_geometry(sch.scene);assert_connections(net,sch.scene)
    assert inspect(sch.scene)==[]


@pytest.mark.parametrize('module,taps',[('half_add',()),('mul1',()),('mul1',('t1','t3'))])
def test_local_template_wires_stay_within_its_frame(module,taps):
    from tritflow.schematic.macros import template
    gates,wires,trunks,pins,sides,width,height=template(module,taps)
    assert all(0<=p[0]<=width and 0<=p[1]<=height for w in wires for p in (w.a,w.b))


def test_unused_input_is_preserved_when_composing_frames():
    from tritflow.netlist import Port
    original=circuit('full_add')
    net=GateNetlist(original.top,original.ports+[Port('unused','input')],original.instances)
    sch=draw(net,expand='*')
    assert_geometry(sch.scene);assert_connections(net,sch.scene)
    assert inspect(sch.scene)==[]
