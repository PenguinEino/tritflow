"""End-to-end PDK extraction, strict LVS and post-layout 27-vector regression.

The integration source is copied into pytest's temporary folder, never modified.
Skip only when the optional taped-out reference checkout/tools are unavailable.
"""
from pathlib import Path
import shutil
import pytest

from tritflow import PDK_ROOT
from tritflow.extract import (extract_layout, gds_wire_capacitance,
                              append_wire_capacitance, reference_net_map)
from tritflow.sim import input_vectors, simulate, compare_layout

SOURCE=Path.home()/'balanced-ternary-logic'
KLAYOUT=Path.home()/'bin/klayout/klayout'
pytestmark=pytest.mark.skipif(not (SOURCE/'full_adder.gds').is_file() or not KLAYOUT.is_file()
                             or not shutil.which('ngspice')
                             or not (PDK_ROOT/'libs.tech/klayout/tech/lvs/run.lvs').is_file(),
                             reason='full_adder reference, KLayout, ngspice and TR-1um required')


def arithmetic(vector):
    """Independent balanced-radix addition oracle, not a gate simulation."""
    total=sum(vector); carry=(total+1)//3
    return {'sum':total-3*carry,'cout':carry}


@pytest.fixture(scope='module')
def extracted(tmp_path_factory):
    out=tmp_path_factory.mktemp('full-adder')
    gds=out/'full_adder.gds'
    shutil.copyfile(SOURCE/'full_adder.gds',gds)
    reference=out/'reference.extracted'
    shutil.copyfile(SOURCE/'full_adder.extracted',reference)
    report=extract_layout(gds,'full_adder',out/'lvs',reference=reference)
    assert report['matched'], report
    assert len(report['circuits']) == 4
    assert all(c['status']=='Match' for c in report['circuits'])
    assert not report['errors']
    return out,gds,report


def test_27_vector_post_layout_and_pre_post_comparison(extracted):
    out,gds,report=extracted
    post=Path(report['extracted']).read_text()
    pre=(Path(__file__).parents[1]/'sim/fixtures/full_adder.spice').read_text()
    result=compare_layout(pre,post,'full_adder',['a','b','cin'],['sum','cout'],input_vectors(3),arithmetic)
    assert result['passed']
    assert len(result['post']['rows'])==27
    assert result['post']['max_error_v'] < .5
    assert result['post']['unsettled']==0
    assert len(result['transitions'])==26
    # Exercise wire C taken from actual GDS and LVS connected-net polygons.
    caps=gds_wire_capacitance(gds,report['report'])
    assert caps['nets']['sum']['capacitance_f'] > 0
    assert caps['nets']['VDD']['layers']['M1']['area_um2'] > 0
    with_cap=append_wire_capacitance(post,'full_adder',caps)
    simulated=simulate(with_cap,'full_adder',['a','b','cin'],['sum','cout'],input_vectors(3),arithmetic,
                       hold_s=500e-9,timeout=600)
    assert simulated['measurements']['passed']
    assert reference_net_map(report['report'],'full_adder')['SUM']=='sum'


def test_strict_port_mismatch_is_reported(extracted):
    out,gds,report=extracted
    reference=out/'bad-reference.spice'
    raw=(SOURCE/'full_adder.extracted').read_text()
    reference.write_text(raw.replace('.SUBCKT full_adder VDD VMID VSS a b cin cout sum',
                                     '.SUBCKT full_adder VDD VMID VSS a b cin cout'))
    mismatch=extract_layout(gds,'full_adder',out/'mismatch',reference=reference)
    assert not mismatch['matched']
    assert mismatch['strict_ports']
    assert any(c['status']!='Match' for c in mismatch['circuits']) or mismatch['errors']


def test_extract_without_reference(extracted):
    out,gds,_=extracted
    result=extract_layout(gds,'full_adder',out/'netlist-only')
    assert result['matched'] is None
    assert '.SUBCKT full_adder' in Path(result['extracted']).read_text()
