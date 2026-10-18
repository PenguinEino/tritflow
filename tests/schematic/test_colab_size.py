"""Native SVG size and readable notebook type, independently of PNG resizing."""
from io import BytesIO
import xml.etree.ElementTree as ET

from PIL import Image
import pytest

from tritflow.schematic.audit import inspect
from test_schematic import ROOT,circuit


@pytest.fixture(scope='module')
def physical(tmp_path_factory):
    """Use real routed wire capacitance for both notebook circuits."""
    from tritflow.pnr import Library,place_and_route
    folder=tmp_path_factory.mktemp('schematic-colab')
    library=Library.load(ROOT/'cells')
    return {name:place_and_route(net,library,output_dir=folder/name,run_pdk_drc=False,anneal_steps=0)
            for name,net in [('half',circuit('half_add')),('adder',circuit('adder',2))]}


def native_size(sch):
    svg=ET.fromstring(sch.svg)
    return float(svg.get('width')),float(svg.get('height'))


@pytest.mark.parametrize('overlay',['plain','values','wire_c','both'])
def test_flat_half_adder_fits_native_1000_by_700_without_scroll(overlay,physical):
    net=circuit('half_add')
    sch=net.schematic(expand='*',
        inputs={'a':1,'b':1} if overlay in {'values','both'} else None,
        parasitics=physical['half'] if overlay in {'wire_c','both'} else None,
        title='Half adder: flat mapped cells, a = b = +1')
    width,height=native_size(sch)
    assert width<=1000 and height<=700
    # The same bound applies to the actual unresized PNG export, not just the
    # review helper's explicit output_width=1000 rasterization.
    image=Image.open(BytesIO(sch.png()))
    assert image.width<=1000 and image.height<=700
    assert abs(image.width-width)<1 and abs(image.height-height)<1
    assert inspect(sch.scene)==[]
    assert sch.metrics['bends_per_net_max']<=2


@pytest.mark.parametrize('name',['half','adder','annotated','minmax'])
def test_notebook_type_is_eleven_points_and_each_preview_fits(name,physical):
    if name=='half':
        sch=circuit('half_add').schematic(expand='*',inputs={'a':1,'b':1},
            title='Half adder: flat mapped cells, a = b = +1')
    elif name=='minmax':
        sch=circuit('minmax').schematic(net_names=True,title='minmax: schematic of the edited HDL')
    else:
        sch=circuit('adder',2).schematic(inputs={'a[0]':1,'a[1]':0,'b[0]':1,'b[1]':0,'cin':0},
            title='Two-trit adder: mapped hierarchy and settled trits')
        if name=='annotated':
            base=sch
            sch=sch.annotate(parasitics=physical['adder'],title='Same schematic: settled trits and routed wire C (fF)')
            assert sch.scene is base.scene
    v=sch._vector();width,height=native_size(sch)
    assert width<=1000 and height<=700
    assert height*1000/width<=700  # 1000 px review PNG also fits one viewport.
    for item in v.items:
        if item['kind']!='text':continue
        assert item['size']*.75*width/v.width>=11-1e-9
        assert item['size']*.75*1000/v.width>=11-1e-9
    if name=='minmax':
        sizes={i['text']:i['size'] for i in v.items if i['kind']=='text'}
        assert all(sizes[g]==sizes['a'] for g in ('g0','g1','g2','g3','Branch','Crossing: no connection'))
    if name in {'adder','annotated'}:
        assert v.height==sch.scene.height
        assert any(i['kind']=='text' and i['x']>sch.scene.width and 'Port values' in i['text'] for i in v.items)
        boxes=[n.box for n in sch.scene.symbols]
        boxes += [(s.a[0],s.a[1],s.b[0],s.b[1]) for s in sch.scene.segments]
        assert max(b[2] for b in boxes)==sch.scene.width-24
        assert sch.scene.width<=640
