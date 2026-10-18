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
