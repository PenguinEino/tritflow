"""The round-4 drawing rules, checked independently of routing choices."""
import xml.etree.ElementTree as ET
import re
from collections import Counter

import pytest

from tritflow.schematic import draw
from tritflow.schematic.audit import inspect
from tritflow.schematic.model import Scene,Segment,Symbol
from tritflow.schematic.rules import PITCH,TRUNK_PITCH
from test_schematic import CASES,circuit


@pytest.mark.parametrize('name,n',CASES)
@pytest.mark.parametrize('expand',[None,'*'])
def test_every_gallery_scene_satisfies_clearances(name,n,expand):
    s=draw(circuit(name,n),expand=expand)
    assert inspect(s.scene)==[]
    assert all(v==0 for v in s.metrics['clearance_violations'].values())
    # The crop uses a fixed 48 px header and 24 px side margins, independent
    # of where the placement workspace happened to start.
    bounds=[n.box for n in s.scene.symbols]+[f.box for f in s.scene.frames]
    bounds += [(w.a[0],w.a[1],w.b[0],w.b[1]) for w in s.scene.segments]
    assert min(b[0] for b in bounds)==24
    assert min(b[1] for b in bounds)==48
    assert s.scene.height-max(b[3] for b in bounds)==40
    for node in s.scene.symbols:
        if node.kind not in {'input','output'}:continue
        related={m for n in s.scene.symbols for m in n.members
                 if node.label in (n.inputs if node.kind=='input' else n.outputs).values()}
        for frame in s.scene.frames:
            a,b=node.box,frame.box
            overlap=max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3])
            assert not overlap or related.intersection(frame.members),(node.label,frame.label)
    pins={(sig,p) for n in s.scene.symbols for pin,p in n.pins.items() for sig in [(n.inputs|n.outputs)[pin]]}
    degree=Counter()
    for w in s.scene.segments:
        dx,dy=(8,0) if w.a[1]==w.b[1] else (0,8)
        p=w.a
        while p!=w.b:
            q=p[0]+dx,p[1]+dy
            degree[w.net,p]+=1;degree[w.net,q]+=1;p=q
    assert all(d!=1 or key in pins for key,d in degree.items())


@pytest.mark.parametrize('name',['half_add','minmax'])
def test_operand_buses_have_one_ordered_trunk_and_clear_dots(name):
    s=draw(circuit(name))
    a,b=[next(t for t in s.scene.trunks if t.net==net) for net in ('a','b')]
    assert a.a[0]==a.b[0] and b.a[0]==b.b[0]
    assert b.a[0]-a.a[0]>=TRUNK_PITCH
    for net,t in [('a',a),('b',b)]:
        assert all(p[0]==t.a[0] for p in s.scene.junctions[net])
    assert PITCH==32


@pytest.mark.parametrize('name,n',CASES)
def test_only_actual_overlays_have_port_legends(name,n):
    net=circuit(name,n)
    plain=net.schematic(net_names=True)
    def texts(s):return [e.text or '' for e in ET.fromstring(s.svg).iter() if e.tag.endswith('text')]
    assert not any(t.startswith('Port ') for t in texts(plain))
    assert plain.scene.height==plain.metrics['height_px']
    values=plain.annotate(inputs={p.name:1 for p in net.ports if p.dir=='input'})
    visible=texts(values)
    assert any(t=='Port values' for t in visible)
    assert not any(re.search(r'\b_n\d+\b',t) for t in visible)
    assert values.scene is plain.scene
    assert values.annotate(inputs=None).svg==plain.svg
    # Anonymous logical names remain exact in metadata/data-net only. Hover
    # captions derive from the producing cell or module terminal.
    titles=[e.text or '' for e in ET.fromstring(values.svg).iter() if e.tag.endswith('title')]
    assert not any(t.startswith('_n') for t in titles)


def test_auditor_detects_close_tracks_pin_turns_and_foreign_stubs():
    a=Segment('a',(0,0),(64,0));b=Segment('b',(0,24),(64,24))
    s=Scene('close',(),(a,b),{},(),{},200,200)
    assert any(p[0]=='parallel' for p in inspect(s))
    node=Symbol('g','INV','g',inputs={'A':'a'},outputs={'Y':'y'},x=80,y=0,width=80,height=96,
                pins={'A':(80,56),'Y':(160,56)},sides={'A':'left','Y':'right'})
    s.symbols=(node,)
    s.segments=(Segment('a',(64,56),(80,56)),Segment('a',(64,24),(64,56)),
                Segment('b',(56,48),(72,48)))
    kinds={p[0] for p in inspect(s)}
    assert {'pin_jog','pin_run','pin_clearance'}<=kinds


def test_mul2_partial_products_follow_a_two_by_two_operand_matrix():
    s=draw(circuit('mul2'),expand='*')
    products=[f for f in s.scene.frames if f.label in {'u00','u01','u10','u11'}]
    assert len(products)==4
    assert len({f.box[0] for f in products})==2
    assert len({f.box[1] for f in products})==2
    halves=[f for f in s.scene.frames if f.label in {'middle','upper'}]
    assert min(f.box[0] for f in halves)>max(f.box[2] for f in products)
