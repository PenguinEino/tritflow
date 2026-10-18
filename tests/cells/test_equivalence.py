"""Re-run the taped-out DC neighborhoods, directed transitions and cascades."""
from pathlib import Path
import json

import pytest
from tritflow.cells.equivalence import equivalence
from tritflow.cells import regression
from tritflow.cells.parasitic import (capacitance_view, net_comparison, poly_runs,
                                     two_inv_capacitance)
from tritflow.cells.reference import ORIGINALS


@pytest.fixture(scope='module')
def proof(library):
    out,_,_=library
    reference=Path.home()/'balanced-ternary-logic'
    if not reference.is_dir():pytest.skip('Independent taped-out reference checkout unavailable')
    result=equivalence(out,reference)
    assert result['passed'],json.dumps({
        'cells':{k:v['passed'] for k,v in result['cells'].items()},
        'chains':{k:v['passed'] for k,v in result['chains'].items()}},indent=2)
    return result


@pytest.mark.parametrize('cell',['INV','NAND','NOR','NANY','BUF'])
def test_independent_physical_and_analog_equivalence(proof,cell):
    result=proof['cells'][cell]
    assert proof['schematic_equivalence'][cell]['passed']
    assert result['intrinsic_parameters_identical']
    assert result['dc_grid']['original']['points']==(81 if cell in ('INV','BUF') else 81*81)
    for label in ('original','compact'):
        assert result['dc_grid'][label]['max_half_volt_band_error_v']<=.5
        count=6 if cell in ('INV','BUF') else 72
        assert result['transient'][label]['10f']['transitions']==count
        assert result['transient'][label]['100f']['transitions']==count
        if cell=='NANY':
            assert result['transient'][label]['skew_A']['transitions']==72
            assert result['transient'][label]['skew_B']['transitions']==72
    assert result['passed']


@pytest.mark.parametrize('kind',['inverter_two','nor_six','nany_six','mixed_six'])
def test_taped_out_cascade_protocols(proof,kind):
    result=proof['chains'][kind]
    assert result['original']['passed'] and result['compact']['passed']
    assert result['passed']


def test_device_identity_scope(proof):
    assert 'Device-level identity only' in proof['scope']
    assert 'without interconnect parasitics' in proof['scope']


def wire_views(out,cell):
    """Read the independently matched source references produced by Phase 2."""
    reference=out/'equivalence/reference'/cell
    top=ORIGINALS[cell]
    original,old_caps=capacitance_view(
        Path.home()/'balanced-ternary-logic'/f'{top}.gds',reference/'lvs.lvsdb',top,
        (reference/'original.ext.spice').read_text(),cell)
    compact,new_caps=capacitance_view(
        out/cell/f'{cell}.gds',reference/'compact_lvs/lvs.lvsdb',cell,
        (out/cell/f'{cell}.ext.spice').read_text(),cell)
    return original,compact,old_caps,new_caps


@pytest.mark.parametrize('cell',list(ORIGINALS))
def test_wire_c_on_corresponding_lvs_nets(proof,library,cell):
    out,_,_=library
    original,compact,old,new=wire_views(out,cell)
    comparison=net_comparison(old,new)
    assert comparison['Y']['compact_f']>comparison['Y']['original_f']>0
    for text,caps in ((original,old),(compact,new)):
        lines=[line.split() for line in text.splitlines() if line.startswith('Ctfwire')]
        assert len(lines)==sum(row['capacitance_f']>0 for row in caps['nets'].values())
        assert sum(float(line[3]) for line in lines)==pytest.approx(
            sum(row['capacitance_f'] for row in caps['nets'].values()),rel=1e-12)
        assert all(line[2]=='0' for line in lines)


def test_wire_c_changes_inverter_timing(proof,library,tmp_path):
    out,_,_=library
    original,compact,_,_=wire_views(out,'INV')
    old=regression.transitions(original,'INV',tmp_path/'original')
    new=regression.transitions(compact,'INV',tmp_path/'compact')
    assert old['passed'] and new['passed']
    assert new['max_settling_s']['Y']>old['max_settling_s']['Y']+1e-12


def test_original_buf_has_both_midpoint_capacitances(proof,library):
    out,_,_=library
    _,_,inv,_=wire_views(out,'INV')
    text=(out/'equivalence/reference/BUF/original.ext.spice').read_text()
    annotated,caps=two_inv_capacitance(inv,text)
    assert caps['reference_nets']['MID']['capacitance_f']==pytest.approx(
        inv['reference_nets']['A']['capacitance_f']+inv['reference_nets']['Y']['capacitance_f'])
    assert 'stage0_n_ex_' in annotated and 'stage1_n_ex_' in annotated


def test_compaction_shortens_long_nand_poly(proof,library):
    out,_,_=library
    ref=out/'equivalence/reference/NAND'
    old=poly_runs(Path.home()/'balanced-ternary-logic/mul_nand.gds',ref/'lvs.lvsdb','mul_nand')
    new=poly_runs(out/'NAND/NAND.gds',ref/'compact_lvs/lvs.lvsdb','NAND')
    longest=lambda rows:max(r['length_um'] for r in rows if r['role']=='signal_field_poly')
    assert longest(old)-longest(new)==pytest.approx(8.)
    assert all(r['resistance_ohm']==pytest.approx(20*r['length_um']/r['width_um']) for r in old+new)
