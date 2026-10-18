"""Unused physical rails remain explicit while only connected wire C is added."""
from pathlib import Path
import pytest
from tritflow import CELLS_DIR
from tritflow.extract import extract_layout,gds_wire_capacitance


def test_unused_power_formal_and_purged_metal(tmp_path):
    cell=CELLS_DIR/'out/INV'
    if not (cell/'INV.gds').exists():pytest.skip('Optional generated INV not published')
    result=extract_layout(cell/'INV.gds','INV',tmp_path,reference=cell/'INV.spice')
    assert result['matched']
    assert result['unused_power_formals_restored']==['VMID']
    assert (tmp_path/'INV.raw.ext.spice').exists()
    caps=gds_wire_capacitance(cell/'INV.gds',result['report'])
    assert caps['excluded_unconnected_metal_um2']['M1']>0
    assert caps['nets']['Y']['capacitance_f']>0


@pytest.mark.parametrize('fault', ['metal', 'label', 'cut'])
def test_deleted_vmid_is_rejected(tmp_path, fault):
    """Deleting an unloaded rail must fail even though its schematic has no load."""
    import klayout.db as db
    source = CELLS_DIR/'out/INV'
    layout = db.Layout(); layout.read(str(source/'INV.gds'))
    cell = layout.cell('INV'); m1 = layout.layer(13, 0)
    labels = cell.shapes(layout.layer(48, 0))
    label = next(s.text for s in labels.each() if s.is_text() and s.text.string == 'VMID')
    rail = next(p for p in db.Region(cell.begin_shapes_rec(m1)).merged().each()
                if p.inside(label.trans.disp))
    if fault == 'label':
        for shape in list(labels.each()):
            if shape.is_text() and shape.text.string == 'VMID': shape.delete()
    else:
        remove = db.Region(rail) if fault == 'metal' else db.Region(db.Box(
            rail.bbox().center().x-100, rail.bbox().bottom, rail.bbox().center().x+100, rail.bbox().top))
        # The pass-through VMID rail is top-level, independent of device PCells.
        remaining = db.Region(cell.shapes(m1)) - remove
        cell.shapes(m1).clear(); cell.shapes(m1).insert(remaining)
    gds = tmp_path/f'{fault}.gds'; layout.write(str(gds))
    result = extract_layout(gds, 'INV', tmp_path/'lvs', reference=source/'INV.spice')
    assert not result['matched']
    assert 'VMID' not in result['unused_power_formals_restored']
    assert any('VMID' in error or 'vmid' in error for error in result['errors'])
