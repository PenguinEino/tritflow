"""Real TDFF extension qualification; no mock cell can establish these claims."""
import copy
import json
from pathlib import Path

import pytest

from tritflow import CELLS_DIR, flow
from tritflow.pnr import Library
from tritflow.seq.library import EXTENSION, load_library, subckts, digest
from tritflow.seq.physical import qualify_cell
from tritflow.seq.spice import build_testbench
from tritflow.seq.synthesis import check_sequential
from tritflow.seq.power import bands


def test_extension_and_final_provenance():
    assert 'TDFF' not in Library.load().cells
    manifest=json.loads((CELLS_DIR/'out/library.json').read_text())
    assert 'TDFF' not in (manifest.get('cells',manifest) if isinstance(manifest,dict) else manifest)
    lib = load_library()
    tdff = lib.cells['TDFF']
    assert (tdff.width,tdff.height) == (1260.,132.)
    assert set(tdff.pins) == {'D','CLK','Q','VDD','VMID','VSS'}
    summary = json.loads((EXTENSION/'TDFF/tdff_summary.json').read_text())
    assert summary['artifact_sha256']['gds'] == digest(EXTENSION/'TDFF/TDFF.gds')
    assert summary['artifact_sha256']['extracted'] == digest(EXTENSION/'TDFF/TDFF.ext.spice')
    assert tdff.characterization['max_static_current_a'] > .0032
    assert Library.load().template == lib.template
    assert bands(lib.template,True)['VSS'] == [-8.,4.]
    assert bands(lib.template,18)['VDD'] == [124.,142.]


def test_independent_cell_drc_lvs(tmp_path):
    report = qualify_cell(output_dir=tmp_path)
    assert report['drc']['violations'] == 0
    assert report['lvs']['matched'] and report['lvs']['strict_ports']


def test_routed_registers_and_clock_deck(tmp_path):
    circuit = flow.load('examples/shift3.tv')
    net = circuit.synthesize()
    lay = net.place_and_route(output_dir=tmp_path/'shift',channel_tracks=12)
    assert lay.data['checks']['connectivity']['clean']
    assert lay.data['checks']['pdk_drc']['violations'] == 0
    assert lay.data['power']['dc_current_check']['reserved_margin_met']
    assert lay.data['power']['dc_current_check']['max_utilization'] <= .8
    assert isinstance(flow.load_layout(net,tmp_path/'shift'),type(lay))
    report = lay.lvs()
    assert report['matched'] and report['strict_ports']
    text = Path(report['extracted']).read_text()
    deck,plan = build_testbench(net,text,[{'d':-1},{'d':0},{'d':1}],
        initial={q:0 for q in net.state_names},lvs_report=report['report'])
    assert '.nodeset' in deck and '.ic ' not in deck and 'uic' not in deck.lower()
    assert '.nodeset v(tf_715b305d)=0' in deck
    assert '.nodeset v(xdut.tf_715b305d)' not in deck
    assert len(plan['logic_rows']) == 3
    assert set(net.state_names) <= set(plan['observed'])
    assert all(edge < sample < edge+1e-6 for edge,sample in zip(plan['edges'],plan['samples']))
    # Pre-layout uses the delivered schematic hierarchy under the same interface.
    from tritflow.seq.writers import spice
    before,_ = build_testbench(net,spice(net)+'\n'+subckts(),[{'d':-1}],
                              initial={q:0 for q in net.state_names})
    assert '.xs.u)' in before


def test_equivalence_detects_wrong_register_connection():
    circuit = flow.load('examples/counter2.tv')
    net = circuit.synthesize()
    broken = copy.deepcopy(net)
    broken.registers[0].pins['D'] = broken.registers[1].pins['D']
    with pytest.raises(ValueError):
        check_sequential(circuit.design,broken)


def test_actual_clocked_postlayout_transient(tmp_path):
    """Exercise the runner and sampler against an independent three-value write."""
    net=flow.loads('''module one_ff(input trit clk,d,output reg trit q);
                      always @(posedge clk) q <= d; endmodule''').synthesize()
    layout=net.place_and_route(output_dir=tmp_path/'one',channel_tracks=10)
    post=layout.extract()
    result=post.simulate([{'d':-1},{'d':0},{'d':1}],initial={'q':0},period_s=200e-9,
                         step_s=2e-9,workdir=tmp_path/'spice')
    report=result['measurements']
    assert report['passed'] and report['cycles']==3
    captured=[c for c in report['checks'] if c['phase']=='before next edge']
    assert [c['expected_trit'] for c in captured]==[-1,0,1]
    assert all(abs(c['actual_v']-5*want)<=.5 for c,want in zip(captured,[-1,0,1]))
    assert report['runtime_s']>0 and report['simulator']['version']=='42'


def test_sequential_floorplan_retains_narrow_vmid_limit():
    """Synthetic currents test packing policy; they are not cell qualification."""
    from tritflow.netlist import GateNetlist,Instance,Port
    from tritflow.pnr.flow import _floorplan_choice
    from tritflow.pnr.power import power_plan
    lib=copy.deepcopy(Library.load())
    lib.cells['NANY'].characterization={'dc':[{'rail_current_a':{'VDD':0.,'VMID':.001,'VSS':0.}}]}
    net=GateNetlist('packing',[Port('a','input'),Port('b','input')]+[Port(f'y{i}','output') for i in range(4)],
                    [Instance(f'g{i}','NANY',{'A':'a','B':'b','Y':f'y{i}'}) for i in range(4)])
    options={'sequential_rails':True}
    plan=power_plan([],lib,**options)
    capacity=3*2*plan['assumptions']['allowed_current_a_per_um']*4
    rows,spans,_,_,_=_floorplan_choice(net,lib,None,12,{i.name:.001 for i in net.instances},capacity,options)
    # One 1-mA load fits each 1.6-mA-reserved VMID span; two do not.
    assert rows*spans>=4
