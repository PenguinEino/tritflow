"""Cell visuals must preserve physical geometry and real schematic identities."""
import json
from pathlib import Path
import re
import shutil

import klayout.db as db
import plotly.graph_objects as go
import pytest

from tritflow import CELLS_DIR
from tritflow.viz.cell import (LAYERS, cell_figure, device_locations, device_mapping,
                               device_table, row_abutment)

LIBRARY=CELLS_DIR/'out'
COUNTS={'INV':4,'NAND':6,'NOR':6,'NANY':10,'BUF':8,'TIEP':1,'TIEZ':1,'TIEN':1,'FILL':0}


def trace_region(trace, dbu=.001):
    """Reconstruct rendered polygons, independently checking area and holes."""
    result=db.Region();points=[]
    for x,y in zip(trace.x,trace.y):
        if x is None:
            if points:
                result.insert(db.DPolygon(points).to_itype(dbu));points=[]
        else:points.append(db.DPoint(x,y))
    return result.merged()


@pytest.mark.parametrize('cell',list(COUNTS))
@pytest.mark.parametrize('theme',['light','dark'])
def test_real_gds_layers_holes_and_all_cells(cell,theme):
    original=(LIBRARY/cell/f'{cell}.gds').read_bytes()
    fig=cell_figure(cell,theme=theme)
    layout=db.Layout();layout.read(str(LIBRARY/cell/f'{cell}.gds'))
    top=layout.cell(cell)
    traces={t.meta['layer']:t for t in fig.data if (t.meta or {}).get('kind')=='layer'}
    for name,pair in LAYERS.items():
        index=layout.find_layer(*pair)
        actual=db.Region() if index is None else db.Region(top.begin_shapes_rec(index)).merged()
        if actual.is_empty():
            assert name not in traces
        else:
            assert (trace_region(traces[name],layout.dbu)^actual).is_empty(),name
            assert traces[name].meta['area_um2']==pytest.approx(actual.area()*layout.dbu**2)
            assert traces[name].legendgroup==name and traces[name].showlegend
    for trace in fig.data:
        if (trace.meta or {}).get('kind')=='obstruction':
            layer=layout.layer(*LAYERS[trace.meta['layer']])
            actual=db.Region(top.begin_shapes_rec(layer)).merged()
            assert (trace_region(trace,layout.dbu)^actual).is_empty()
    assert fig.layout.yaxis.scaleanchor=='x' and fig.layout.yaxis.scaleratio==1
    assert fig.layout.legend.groupclick=='togglegroup'
    assert fig.layout.paper_bgcolor==('#ffffff' if theme=='light' else '#151b26')
    assert {t.meta['net'] for t in fig.data if (t.meta or {}).get('kind')=='rail'}=={'VDD','VMID','VSS'}
    assert original==(LIBRARY/cell/f'{cell}.gds').read_bytes()
    assert json.loads(fig.to_json())['layout']['meta']['cell']==cell


@pytest.mark.parametrize('cell,count',list(COUNTS.items()))
def test_every_source_device_has_lvs_position_wl_outline_and_table(cell,count):
    mapping=device_mapping(cell)
    assert len(mapping.rows)==count
    # Source identifiers are taken from the published subcircuit, not PCell order.
    source=(LIBRARY/cell/f'{cell}.spice').read_text()
    names=set(re.findall(r'(?m)^(X\S+)\s',source))
    assert {r['name'] for r in mapping.rows}==names
    outlined={t.meta['device']:t for t in mapping.figure.data if (t.meta or {}).get('kind')=='device'}
    labels={t.meta['device'] for t in mapping.figure.data if (t.meta or {}).get('kind')=='device_label'}
    assert set(outlined)==labels==names
    for row in mapping.rows:
        x0,y0,x1,y1=row['bbox_um']
        assert x0<=row['x_um']<=x1 and y0<=row['y_um']<=y1
        assert f'W/L = {row["w_um"]:g}/{row["l_um"]:g} µm' in outlined[row['name']].hovertemplate
        assert row['schematic_name'] in outlined[row['name']].hovertemplate
        if row['model']=='F_RR':
            assert row['w_um']==pytest.approx(2.8) and row['l_um']==pytest.approx(30.)
            assert x1-x0==pytest.approx(35.)  # AR includes ends; L stays 30 µm.
    assert mapping.static_figures()==(mapping.figure,mapping.table)
    assert isinstance(mapping.figure,go.Figure) and isinstance(mapping.table,go.Figure)
    assert isinstance(device_table(cell),go.Figure)
    if count:
        assert set(mapping.table.data[0].cells.values[1])==names
    else:
        assert 'No schematic devices' in mapping.to_html(include_plotlyjs=False)


def test_original_schematic_labels_and_canonical_ids_are_both_preserved():
    inv={r['schematic_name']:r for r in device_locations('INV')}
    assert inv['XM1']['name']=='XMP'
    assert (inv['XM1']['x_um'],inv['XM1']['y_um'])==pytest.approx((19.2,56.))
    assert inv['R1']['name']=='XRP'
    nany={r['schematic_name']:r for r in device_locations('NANY')}
    assert set(nany)=={'XM1','XM2','XM3','XM5','XM6','XM7','XM8','XM9','R1','R2'}
    assert nany['XM9']['name']=='XCN2'
    assert nany['XM9']['w_um']==8.
    buf=device_locations('BUF')
    assert len({r['schematic_name'] for r in buf})==8
    assert {r['schematic_name'] for r in buf if r['model']=='PMOS'}=={'STAGE0_MXM1','STAGE1_MXM1'}


def test_selection_controls_table_links_and_portable_html(tmp_path):
    mapping=device_mapping('NANY',theme='dark',selected='XM1')
    chosen=next(t for t in mapping.figure.data if (t.meta or {}).get('device')=='XN2' and t.meta['kind']=='device')
    assert chosen.line.width==4 and chosen.line.color=='#f39b24'
    assert mapping.selected=='XN2'
    index=next(i for i,r in enumerate(mapping.rows) if r['name']=='XN2')
    assert mapping.table.data[0].cells.fill.color[0][index]=='#754b08'
    assert mapping.table.data[0].cells.font.color[0][index]=='#ffffff'
    assert mapping.figure.layout.updatemenus[0].active==index+1
    menu=mapping.figure.layout.updatemenus[0]
    assert {b.label for b in menu.buttons}=={'All devices'}|{r['name'] for r in mapping.rows}
    assert all(mapping.figure.data[i].meta['kind']=='device' for i in menu.buttons[0].args[1])
    path=mapping.write_html(tmp_path/'mapping.html')
    html=path.read_text()
    assert 'Plotly.restyle' in html and 'Plotly.relayout' in html
    assert "row.addEventListener('click'" in html
    assert 'aria-pressed="true"' in html and 'aria-selected="true"' in html
    assert 'data-device="XN2"' in html and 'XM1</button>' in html
    assert not re.search(r'<script[^>]+src=["\']https?://',html)
    representation=mapping._repr_html_()
    assert 'srcdoc=' in representation and representation.isascii()
    mapping.select()
    assert mapping.selected is None
    assert all(t.line.width==1.8 for t in mapping.figure.data if (t.meta or {}).get('kind')=='device')
    with pytest.raises(ValueError,match='Unknown or ambiguous'):
        mapping.select('missing')


@pytest.mark.parametrize('theme',['light','dark'])
def test_abutment_is_physical_and_mirrors_pins_and_free_tracks(theme):
    names=['INV','NANY','FILL'];orients=['R0','MY','R0']
    fig=row_abutment(names,orientations=orients,theme=theme)
    widths=[108.,168.,24.];assert fig.layout.meta['width_um']==sum(widths)
    assert [p['x_um'] for p in fig.layout.meta['placements']]==[0.,108.,276.]
    for trace,name,offset,width,orient in zip(
            [t for t in fig.data if (t.meta or {}).get('kind')=='free_tracks'],names,[0.,108.,276.],widths,orients):
        abstract=json.loads((LIBRARY/name/f'{name}.abstract.json').read_text())
        expected=[offset+(width-x if orient=='MY' else x) for x in abstract['free_M2_tracks']['x']]
        assert trace.meta['track_x_um']==expected
        assert trace.meta['count']==abstract['free_M2_tracks']['count']
        for x in expected:
            for x0,y0,x1,y1 in abstract['obstructions']['M2']:
                # Transform back to local GDS coordinates and check the promise.
                local=width-(x-offset) if orient=='MY' else x-offset
                assert local+3.7<=x0+1e-9 or local-3.7>=x1-1e-9
    tracks=[t for t in fig.data if (t.meta or {}).get('kind')=='free_tracks']
    assert sum(t.showlegend for t in tracks)==1
    assert tracks[0].legendrank==0
    for trace in fig.data:
        if (trace.meta or {}).get('kind')=='rail':
            actual=trace_region(trace)
            bounds={'VDD':[124,132],'VMID':[6,10],'VSS':[0,4]}[trace.meta['net']]
            wanted=db.Region(db.DBox(0,bounds[0],300,bounds[1]).to_itype(.001))
            assert (actual^wanted).is_empty()
        if (trace.meta or {}).get('kind')=='pin_label' and trace.meta['cell']=='NANY' and trace.meta['pin']=='A':
            assert trace.x[0]==273.  # 108+168-3, rather than an unmirrored pin.
    assert json.loads(fig.to_json())['layout']['meta']['placements'][1]['orient']=='MY'


def test_library_data_is_portable_and_original_evidence_is_optional(tmp_path,monkeypatch):
    root=tmp_path/'published';root.mkdir()
    for filename in ['library.json','generation.json']:
        shutil.copyfile(LIBRARY/filename,root/filename)
    for name in COUNTS:
        (root/name).mkdir()
        for suffix in ['gds','abstract.json','spice','pcells.json','lvs.lvsdb']:
            shutil.copyfile(LIBRARY/name/f'{name}.{suffix}' if suffix!='lvs.lvsdb' else LIBRARY/name/suffix,
                            root/name/f'{name}.{suffix}' if suffix!='lvs.lvsdb' else root/name/suffix)
    # No independent checkout, PDK registration, models, or equivalence tree.
    monkeypatch.setattr(Path,'home',classmethod(lambda cls:tmp_path/'empty-home'))
    monkeypatch.setenv('TR1UM_PDK',str(tmp_path/'absent-pdk'))
    assert len(device_mapping('NANY',library=root).rows)==10
    assert len(device_mapping('TIEZ',library=root).rows)==1
    assert len({r['schematic_name'] for r in device_mapping('BUF',library=root).rows})==8
    assert device_mapping('FILL',library=root).rows==[]
    assert row_abutment(['INV','BUF','FILL'],library=root).layout.meta['width_um']==348.


def test_bad_inputs_and_changed_publication_are_rejected(tmp_path,monkeypatch):
    from tritflow.viz import cell as module
    with pytest.raises(ValueError,match='Unknown library'):
        cell_figure('missing')
    with pytest.raises(ValueError,match='theme'):
        cell_figure('INV',theme='unknown')
    with pytest.raises(ValueError,match='nonempty'):
        row_abutment([])
    with pytest.raises(ValueError,match='orientation'):
        row_abutment(['INV'],orientations=['MX'])
    # Generation guard must not silently return a figure read across a publish.
    shutil.copytree(LIBRARY/'FILL',tmp_path/'FILL')
    for filename in ['library.json','generation.json']:
        shutil.copyfile(LIBRARY/filename,tmp_path/filename)
    original=module._cell_figure
    def concurrent_publish(data,theme):
        result=original(data,theme)
        (tmp_path/'generation.json').write_text('{"id":"next"}')
        return result
    monkeypatch.setattr(module,'_cell_figure',concurrent_publish)
    with pytest.raises(RuntimeError,match='published during'):
        module.cell_figure('FILL',library=tmp_path)
