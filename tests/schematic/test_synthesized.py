"""Every shipped combinational netlist, including flat RTL synthesis cones.

Render the same review cases with:
    PYTHONPATH=. python3 tests/schematic/test_synthesized.py build/schem-route
The review uses already-installed CairoSVG; no schematic runtime dependency
is added. Native-size SVGs and overview/detail PNGs share the tested scene.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET

import pytest

from tritflow import flow
from tritflow.netlist import GateNetlist
from tritflow.schematic import draw
from tritflow.schematic.audit import inspect
from tritflow.schematic.metrics import measure
from tritflow.schematic.vector import TRIT_COLOR
from test_schematic import ROOT, assert_connections, assert_geometry, assert_labels


SOURCES={
    'add2': 'module add2(input trit [1:0] a, b, output trit [2:0] s); assign s = a + b; endmodule',
    'mul_table': """module mul_table(input trit a, b, output reg trit y);
      always @(*) begin case ({a, b})
        2'tTT, 2't11: y = 1't1;
        2'tT1, 2't1T: y = 1'tT;
        default: y = 1't0;
      endcase end
    endmodule""",
}
CASES=sorted(p.stem for p in (ROOT/'examples').glob('*.tv'))+list(SOURCES)
OPTIONS=dict(net_names=True,expand='*',title='',legend=False)
# Captured before SCHEM_ROUTE changed placement or routing (full expanded SVG).
REVIEWED={
    'half_add':'7c9ca18dfcb2ada0aeb106d2400787391e0e2628beebefc6ac86d38ecc214416',
    'full_add':'204ddd9723852e3843d760097293ca0997f156205e2d139c61cdbc0c4d65ade3',
    'adder2':'a4ebc188e720eeacc98c5cb400b5135b2b5491a2a2627895df8d01cb17d9678e',
}


def mapped(name):
    """Use the notebook's public synthesis facade with the real example top."""
    design=flow.loads(SOURCES[name]) if name in SOURCES else flow.load(ROOT/f'examples/{name}.tv',name)
    return design.synthesize()


@pytest.fixture(scope='module',params=CASES)
def example(request):
    net=mapped(request.param)
    original=net.to_json()
    sch=net.schematic(**OPTIONS)
    assert net.to_json()==original
    return request.param,net,sch


def test_every_synthesized_example_is_connected_and_clear(example):
    name,net,sch=example
    assert_geometry(sch.scene)
    assert_connections(net,sch.scene)
    assert inspect(sch.scene)==[]
    metrics=measure(sch.scene)
    assert metrics['short_jogs']==metrics['symbol_edge_runs']==metrics['rotated_gates']==0
    assert_labels(sch)
    if sch.scene.detailed:
        drivers={s:n for n in sch.scene.symbols for s in n.outputs.values()}
        for node in sch.scene.symbols:
            for s in node.inputs.values():assert drivers[s].box[2]<node.x
        vector=sch._vector()
        assert min(i['size'] for i in vector.items if i['kind']=='text')*.75*vector.display_size[0]/vector.width>=11
    if name in REVIEWED:assert sha256(sch._repr_svg_().encode()).hexdigest()==REVIEWED[name]


def test_value_colouring_and_javascript_net_identifiers_survive_routing(example):
    _,net,sch=example
    coloured=sch.annotate(inputs={p.name:1 for p in net.ports if p.dir=='input'})
    assert coloured.scene is sch.scene
    root=ET.fromstring(coloured._repr_svg_())
    wires=[element for element in root.iter() if 'data-net' in element.attrib]
    assert {element.get('data-net') for element in wires}=={s.net for s in sch.scene.segments}
    assert all(e.get('stroke')==TRIT_COLOR[coloured.values[e.get('data-net')]] for e in wires)
    text=[e.text for e in root.iter() if e.tag.endswith('text')]
    assert 'Branch' not in text and 'Crossing: no connection' not in text
    assert_labels(coloured)


def test_foreign_crossings_have_straight_runs_on_both_sides(example):
    _,_,sch=example
    horizontal=[s for s in sch.scene.segments if s.a[1]==s.b[1]]
    vertical=[s for s in sch.scene.segments if s.a[0]==s.b[0]]
    for h in horizontal:
        for v in vertical:
            if h.net==v.net:continue
            x,y=v.a[0],h.a[1]
            if h.a[0]<=x<=h.b[0] and v.a[1]<=y<=v.b[1]:
                # The SVG opens a white gap only at straight perpendicular
                # crossings. A foreign bend/endpoint here would be ambiguous.
                assert h.a[0]<x<h.b[0] and v.a[1]<y<v.b[1],(h,v)


def test_dense_placement_is_independent_of_serialized_instance_order():
    net=mapped('add2')
    reversed_net=GateNetlist(net.top,list(reversed(net.ports)),list(reversed(net.instances)))
    assert draw(net,**OPTIONS).svg==draw(reversed_net,**OPTIONS).svg


def test_track_fallback_preserves_constants_unused_inputs_and_repeated_pins(monkeypatch):
    import tritflow.schematic.routing
    net=flow.loads("""module edge(input trit [2:0] a, output trit p, z, n, v);
      assign p = 1't1; assign z = 1't0; assign n = 1'tT;
      nany repeated(v,a[1],a[1]); endmodule""").synthesize()
    def congested(*args,**kwargs):raise ValueError('No available compact channel')
    monkeypatch.setattr(tritflow.schematic.routing,'route',congested)
    sch=net.schematic(**OPTIONS)
    assert any('interval-coloured' in note for note in sch.scene.notes)
    assert {'TIEP','TIEZ','TIEN'}<={node.kind for node in sch.scene.symbols}
    assert_geometry(sch.scene)
    assert_connections(net,sch.scene)
    assert inspect(sch.scene)==[]
    assert_labels(sch)


def rasterize(svg,folder,name,detailed):
    """Render overview and native-scale SVG windows on a white background."""
    import cairosvg
    cairosvg.svg2png(bytestring=svg.encode(),write_to=str(folder/f'{name}.png'),output_width=2400)
    if not detailed:return
    full=ET.fromstring(svg);width=float(full.get('viewBox').split()[2])
    for side,x in [('left',0),('middle',max(0,width/2-600)),('right',max(0,width-1200))]:
        root=ET.fromstring(svg)
        ys=[float(e.get('y')) for e in root.iter() if e.tag.endswith('text') and e.text
            and x<=float(e.get('x'))<=x+1200 and float(e.get('y'))>=48]
        y=max(0,min(ys,default=64)-64)
        root.set('width','1200');root.set('height','900')
        root.set('viewBox',f'{x} {y} 1200 900')
        cairosvg.svg2png(bytestring=ET.tostring(root),write_to=str(folder/f'{name}-{side}.png'),background_color='white')


def review(folder):
    """Save PNGs from SVG, not from a separate rendering implementation."""
    folder.mkdir(parents=True,exist_ok=True)
    records={}
    for name in CASES:
        start=time.monotonic();net=mapped(name);sch=net.schematic(**OPTIONS)
        svg=sch._repr_svg_();(folder/f'{name}.svg').write_text(svg)
        rasterize(svg,folder,name,sch.scene.detailed)
        metrics=sch.metrics
        records[name]=dict(cells=len(net.instances),sha256=sha256(svg.encode()).hexdigest(),
                           seconds=round(time.monotonic()-start,2),metrics=metrics,notes=sch.scene.notes)
        (folder/'results.json').write_text(json.dumps(records,indent=2)+'\n')
        print(name,records[name]['cells'],metrics['clearance_violations'],records[name]['seconds'],flush=True)
    return records


if __name__=='__main__':review(Path(sys.argv[1] if len(sys.argv)>1 else 'build/schem-route'))
