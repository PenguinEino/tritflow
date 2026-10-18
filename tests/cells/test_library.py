"""Circuit and physical-contract regressions using real PDK extraction.

No mock geometry is accepted: rebuild all views in a temporary directory,
run official decks, and independently compare the four source Xschem netlists.
"""
import json
from pathlib import Path
import shutil

import klayout.db as db
import pytest
from tritflow import CELLS_DIR
from tritflow.cells.circuits import circuits
from tritflow.cells.layout import build, Drawing
from tritflow.cells.verify import verify, lvs, drc



def test_official_qualification(library):
    _,manifest,report=library
    assert {e['name'] for e in manifest}==set(circuits())
    assert report['passed'],json.dumps(report,indent=2)
    assert report['abutment']['items']==0
    assert report['abutment']['ordered_pair_orientation_cases']==9*9*4
    assert report['cells']['FILL']['lvs']['probe']['passed']
    for name,cell in report['cells'].items():
        if name!='FILL':
            expected=3**len(circuits()[name].inputs)
            assert len(cell['dc']['cases'])==expected


@pytest.mark.parametrize('name',['INV','NAND','NOR','NANY'])
def test_independent_current_schematic(library,tmp_path,name):
    """Fresh source snapshots prevent a generator/reference common-mode bug."""
    out,_,_=library
    shutil.copyfile(CELLS_DIR/'source'/f'{name}.lvs.spice',tmp_path/f'{name}.lvs.spice')
    result=lvs(out/name/f'{name}.gds',circuits()[name],tmp_path)
    assert result['passed'],result


def test_physical_contract(library):
    out,manifest,_=library
    template=json.loads((out/'template.json').read_text())
    for entry in manifest:
        name=entry['name'];folder=out/name
        a=json.loads((folder/f'{name}.abstract.json').read_text())
        ly=db.Layout();ly.read(str(folder/f'{name}.gds'));top=ly.cell(name)
        assert top.dbbox()==db.DBox(0,0,a['width'],a['height'])
        assert a['width']%template['grid']==0
        for layer in [(63,0),(63,1),(63,2)]:
            assert db.Region(top.begin_shapes_rec(ly.layer(*layer))).is_empty()
        assert set(a['pins'])==set(circuits()[name].ports)
        boundary=db.Region(top.begin_shapes_rec(ly.layer(235,0)))
        assert (boundary^db.Region(top.bbox())).is_empty()
        m1=db.Region(top.begin_shapes_rec(ly.layer(13,0)))
        for key,layer in [('M1',(13,0)),('M2',(20,0)),('V1',(19,0))]:
            actual=db.Region(top.begin_shapes_rec(ly.layer(*layer)))
            obs=db.Region()
            for rect in a['obstructions'][key]:
                obs.insert(db.DBox(*rect).to_itype(ly.dbu))
            assert (obs^actual).is_empty()
        for p in a['pins'].values():
            for x,y in p['access']:
                assert (x-template['grid']/2)%template['grid']==0
                pad=db.Region(db.DBox(x-1.7,y-1.7,x+1.7,y+1.7).to_itype(ly.dbu))
                assert (pad-m1).is_empty()
        ext=(folder/f'{name}.ext.spice').read_text()
        formal=next(line.split()[2:] for line in ext.splitlines() if line.lower().startswith('.subckt'))
        assert formal==list(circuits()[name].ports)
        assert (folder/f'{name}.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')


@pytest.mark.parametrize('damage',['deleted','severed','unlabelled'])
def test_unloaded_vmid_requires_a_physical_continuous_rail(library,tmp_path,damage):
    """A schematic-unused formal cannot rescue damaged INV pass-through metal."""
    out,_,_=library
    ly=db.Layout();ly.read(str(out/'INV/INV.gds'));top=ly.cell('INV');top.flatten(-1,True)
    layer=ly.layer(13,0);metal=db.Region(top.begin_shapes_rec(layer))
    cut=db.DBox(0,6,108,10) if damage=='deleted' else db.DBox(50,6,54,10)
    if damage!='unlabelled':
        metal-=db.Region(cut.to_itype(ly.dbu));top.shapes(layer).clear();top.shapes(layer).insert(metal)
    else:
        labels=top.shapes(ly.layer(48,0))
        for shape in list(labels.each()):
            if shape.is_text() and shape.text.string=='VMID':shape.delete()
    gds=tmp_path/'INV.gds';ly.write(str(gds))
    shutil.copyfile(out/'INV/INV.lvs.spice',tmp_path/'INV.lvs.spice')
    result=lvs(gds,circuits()['INV'],tmp_path)
    assert not result['passed'],result
    assert any('VMID' in e or 'vmid' in e for e in result['errors']),result


def test_m2_pin_landings(library,tmp_path):
    """Drop the real PDK via at every abstract access, in both legal orientations."""
    out,manifest,_=library
    ly=db.Layout();ly.dbu=.001;ly.technology_name='TR-1um'
    for e in manifest:ly.read(str(out/e['name']/f'{e["name"]}.gds'))
    top=ly.create_cell('PIN_ACCESS');d=Drawing(ly,top)
    y=0.
    for e in manifest:
        a=json.loads((out/e['name']/f'{e["name"]}.abstract.json').read_text())
        for mirror in (False,True):
            t=db.DTrans(2,True,a['width'],y) if mirror else db.DTrans(db.DVector(0.,y))
            top.insert(db.DCellInstArray(ly.cell(e['name']).cell_index(),t))
            for name,pin in a['pins'].items():
                for px,py in pin['access']:
                    point=t*db.DPoint(px,py)
                    d.pcell('via_1',point.x,point.y)
                    d.label(f'{e["name"]}_{mirror}_{name}',point.x,point.y)
            y+=a['height']+24
    gds=tmp_path/'pins.gds';ly.write(str(gds))
    result=drc(gds,'PIN_ACCESS',tmp_path)
    assert result['passed'],result
