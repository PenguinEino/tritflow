import pytest
from tritflow.extract import wire_capacitance, append_wire_capacitance
from tritflow.sim.spice import simulation_netlist


def test_pdk_continuations_receive_real_wire_capacitors():
    from tritflow.sim.spice import subcircuits
    source='.SUBCKT chip a\n+ y VDD VMID VSS\nM1 n a VSS VSS NMOS W=5u L=1u\n+ AS=14p AD=14p\nR1 n y 1k\n.ENDS chip\n'
    definition=subcircuits(source)['chip']
    assert definition['text'] in source
    assert definition['pins']==['a','y','VDD','VMID','VSS']
    result=append_wire_capacitance(source,'chip',{'y':1e-13})
    assert 'Ctfwire0 y 0 1e-13' in result
    assert result.count('Ctfwire')==1
    assert 'AS=14p AD=14p' in result


def test_union_geometry_no_overlap_double_count():
    wire = {'net':'n','layer':'M1','width':2,'points':[[0,0],[10,0]]}
    pnr={'wires':[wire,wire], 'pins':[]}
    coefficients={'M1':{'area_f_per_um2':1e-15,'fringe_f_per_um':1e-15}}
    r=wire_capacitance(pnr,coefficients=coefficients)['nets']['n']
    assert r['layers']['M1']['area_um2'] == pytest.approx(20)
    assert r['layers']['M1']['perimeter_um'] == pytest.approx(24)
    assert r['capacitance_f'] == pytest.approx(44e-15)


def test_append_inside_subckt_and_reject_unknown():
    spice='.subckt test a y VDD VSS\nX1 a \\$1 y VDD VSS gate\n.ends test\n'
    out=append_wire_capacitance(spice,'test',{'n':1e-13},net_map={'n':'$1'})
    assert 'Ctfwire0 \\$1 0 1e-13' in out
    assert out.index('Ctfwire') < out.index('.ends test')
    assert 'n_ex_1' in simulation_netlist(out)
    with pytest.raises(ValueError): append_wire_capacitance(spice,'test',{'absent':1e-13})
    with pytest.raises(ValueError): append_wire_capacitance(out,'test',{'n':1e-13},net_map={'n':'$1'})
    with pytest.raises(ValueError): append_wire_capacitance(spice,'test',{'a':-1})
