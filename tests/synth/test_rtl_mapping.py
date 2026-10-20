"""Library completeness, legacy netlist identity and independent RTL oracles."""

import json
from itertools import product
from pathlib import Path
import random

import numpy as np
import pytest

from tritflow.hdl import Design, Node, load, loads
from tritflow.netlist import Port
from tritflow.synth import check_equivalence, evaluate_netlist, optimize, synthesize, tritverilog
from tritflow.synth.lower import Lowerer, unary_networks


def test_all_original_examples_retain_exact_netlists_and_cell_counts():
    snapshot = json.loads(Path(__file__).with_name('fixtures').joinpath('legacy_netlists.json').read_text())
    assert len(snapshot) == 11
    for name, before in snapshot.items():
        path = Path('examples')/name
        net = synthesize(load(path,top=path.stem))
        assert json.loads(net.to_json()) == before['netlist'],name
        assert net.report()['cells'] == before['cells'],name


def test_retained_first_round_rtl_examples_retain_exact_physical_netlists():
    snapshot = json.loads(Path(__file__).with_name('fixtures').joinpath('round1_netlists.json').read_text())
    assert len(snapshot) == 5
    for name, before in snapshot.items():
        net = synthesize(load(Path('examples')/name))
        assert json.loads(net.to_json()) == before['netlist'], name
        assert net.report()['cells'] == before['cells'], name


def test_unary_cell_basis_closure_maps_all_twenty_seven_functions():
    networks = unary_networks()
    assert set(networks) == set(product((-1,0,1),repeat=3))
    for table in networks:
        x=Node('input',name='x')
        worker=Lowerer()
        worker.source=x
        result=worker.unary(table,x)
        design=Design('unary',[Port('x','input'),Port('y','output')],{'y':result},{'x':x})
        net=synthesize(design)
        np.testing.assert_array_equal(evaluate_netlist(net,{'x':np.array([-1,0,1])})['y'],table)


def literal(values):
    return str(len(values))+"'t"+''.join({-1:'T',0:'0',1:'1'}[v] for v in values)


def table_source(table, inputs):
    labels=list(product((-1,0,1),repeat=inputs))
    items='\n'.join(f'{literal(label)}: y={literal([value])};' for label,value in zip(labels,table))
    return f'''module m(input trit [{inputs-1}:0] a,output reg trit y);
               always @* case(a) {items} endcase endmodule'''


@pytest.mark.parametrize('table',list(product((-1,0,1),repeat=3)))
def test_every_unary_truth_table_written_as_a_case_statement(table):
    source=loads(table_source(table,1))
    mapped=synthesize(source)
    np.testing.assert_array_equal(source.truth_table()['y'],table)
    np.testing.assert_array_equal(evaluate_netlist(mapped,{'a[0]':[-1,0,1]})['y'],table)


@pytest.mark.parametrize('inputs,count',[(2,32),(3,8)])
def test_arbitrary_multi_input_truth_tables_against_independent_table(inputs,count):
    rng=random.Random(2027+inputs)
    for _ in range(count):
        table=[rng.choice([-1,0,1]) for _ in range(3**inputs)]
        source=loads(table_source(table,inputs))
        net=synthesize(source)
        t=source.truth_table()
        np.testing.assert_array_equal(t['y'],table)
        actual=evaluate_netlist(net,{k:t[k] for k in source.inputs})
        np.testing.assert_array_equal(actual['y'],table)
        assert {i.cell for i in net.instances} <= {'INV','NAND','NOR','NANY','BUF','TIEP','TIEZ','TIEN'}


@pytest.mark.parametrize('name',['full_add_rtl','adder4_rtl','alu','case_table','comparator_rtl','mux_rtl'])
def test_new_constructs_no_optimize_and_gate_writer_round_trip(name):
    source=load('examples/'+name+'.tv')
    net=synthesize(source)
    check_equivalence(source,synthesize(source,optimize_logic=False))
    check_equivalence(source,synthesize(loads(tritverilog(net))))
    table=source.truth_table()
    optimized=optimize(source).evaluate({k:table[k] for k in source.inputs})
    for k in source.outputs:
        np.testing.assert_array_equal(optimized[k],table[k])


def test_zero_constant_add_and_multiply_simplify_without_unused_adders():
    for expr,cells in [('a+0',{'BUF':2}),('a*0',{'TIEZ':1,'BUF':1}),
                       ('a*1',{'BUF':2}),('a*-1',{'INV':2})]:
        design=loads(f'module m(input trit [1:0] a,output trit [1:0] y); assign y={expr}; endmodule')
        assert synthesize(design).report()['cells']==cells


def test_fused_vector_three_operand_sum_against_integer_reference():
    design=loads('''module m(input trit [2:0] a,b,c,output trit [3:0] y);
                   assign y=a+b+c; endmodule''')
    net=synthesize(design)
    table=design.truth_table()
    expected=sum(sum(table[f'{bus}[{i}]'].astype(np.int64)*3**i for i in range(3)) for bus in 'abc')
    actual=evaluate_netlist(net,{k:table[k] for k in design.inputs})
    np.testing.assert_array_equal(sum(actual[f'y[{i}]'].astype(np.int64)*3**i for i in range(4)),expected)


def test_wide_source_integer_semantics_do_not_overflow_int64():
    for op in ['+','-','*']:
        width=42
        design=loads(f'''module m(output trit [{width-1}:0] y);
           assign y={width}'t{'1'*width} {op} 2; endmodule''')
        actual=design.evaluate({})
        value=(3**width-1)//2
        expected=value+2 if op=='+' else value-2 if op=='-' else value*2
        for i in range(width):
            digit=(expected+1)%3-1
            assert int(actual[f'y[{i}]'])==digit
            expected=(expected-digit)//3


def test_constant_trit_increment_uses_a_shorter_carry_clamp():
    for fixed in [-1,1]:
        source=loads(f'''module m(input trit a,output trit [1:0] y);
                        assign y=a+({fixed}); endmodule''')
        net=synthesize(source)
        logic=[i for i in net.instances if not i.cell.startswith('TIE')]
        assert len(logic)==6
        values=evaluate_netlist(net,{'a':np.array([-1,0,1])})
        np.testing.assert_array_equal(values['y[0]']+3*values['y[1]'],np.array([-1,0,1])+fixed)


def test_authored_primitives_keep_helpers_when_mixed_with_rtl():
    source=loads('''module m(input trit a,b,output trit [1:0] sum,
                            output trit x,y,z);
        buf fixed_buffer(x,1't1);
        nand fixed_nand(y,1't0,1'tT);
        nor mixed_nor(z,a+b,1't0);
        assign sum=a+b;
        endmodule''')
    for do_optimize in [False,True]:
        net=synthesize(source,optimize_logic=do_optimize)
        authored={i.name:i.cell for i in net.instances if i.name in
                  {'fixed_buffer','fixed_nand','mixed_nor'}}
        assert authored=={'fixed_buffer':'BUF','fixed_nand':'NAND','mixed_nor':'NOR'}
        t=source.truth_table()
        assert (t['x']==1).all() and (t['y']==1).all()
        np.testing.assert_array_equal(t['z'],-np.maximum(t['sum[0]'],0))


def test_adder_fusion_respects_narrow_intermediate_signal_widths():
    source=loads('''module m(input trit [2:0] a,b,input trit [1:0] c,
                            output trit [1:0] y,output trit [2:0] z);
        wire trit [1:0] narrow;
        assign narrow=a+b;
        assign y=narrow+c;
        assign z=narrow+c;
        endmodule''')
    net=synthesize(source)
    t=source.truth_table()
    decode=lambda name,width:sum(t[f'{name}[{i}]'].astype(np.int64)*3**i for i in range(width))
    narrow=(decode('a',3)+decode('b',3)+4)%9-4
    expected=narrow+decode('c',2)
    np.testing.assert_array_equal(decode('y',2),(expected+4)%9-4)
    np.testing.assert_array_equal(decode('z',3),expected)
    assert net.report()['equivalence']['passed']
