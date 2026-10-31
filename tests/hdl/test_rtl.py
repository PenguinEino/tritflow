"""Exhaustive integer/table oracles independent of source IR and mapped gates."""

import operator
import re

import numpy as np
import pytest

from tritflow.hdl import HDLError, load, loads
from tritflow.synth import evaluate_netlist, synthesize


def bus(table, name, width):
    return sum(table[f'{name}[{i}]'].astype(np.int64)*3**i for i in range(width))


def wrap(values, width):
    modulus = 3**width
    return (values + modulus//2) % modulus - modulus//2


def checked(design):
    table = design.truth_table()
    inputs = {k:table[k] for k in design.inputs}
    net = synthesize(design)
    actual = evaluate_netlist(net, inputs)
    for k in design.outputs:
        np.testing.assert_array_equal(actual[k], table[k])
    assert net.report()['equivalence']['mode'] == 'exhaustive'
    return table, net


@pytest.mark.parametrize('op, reference', [('+', operator.add), ('-', operator.sub), ('*', operator.mul)])
@pytest.mark.parametrize('width', [1, 2, 3])
@pytest.mark.parametrize('extra', [-1, 0, 1, 3])
def test_integer_arithmetic_truncation_and_extension(op, reference, width, extra):
    out_width = max(1, width+extra)
    d = loads(f'''module m(input trit [{width-1}:0] a,b,
        output trit [{out_width-1}:0] y); assign y=a {op} b; endmodule''')
    t, _ = checked(d)
    np.testing.assert_array_equal(bus(t, 'y', out_width),
                                  wrap(reference(bus(t,'a',width),bus(t,'b',width)),out_width))


@pytest.mark.parametrize('op, reference', [('==',operator.eq),('!=',operator.ne),('<',operator.lt),
                                           ('<=',operator.le),('>',operator.gt),('>=',operator.ge)])
def test_comparisons_never_truncate_operands_to_result_width(op, reference):
    d = loads(f'''module m(input trit [2:0] a,input trit [1:0] b,output trit y);
                  assign y=a {op} b; endmodule''')
    t, _ = checked(d)
    np.testing.assert_array_equal(t['y'], np.where(reference(bus(t,'a',3),bus(t,'b',2)),1,-1))


def test_carry_context_and_self_determined_concatenation():
    d = loads('''module m(input trit a,b,cin,output trit cout,sum,wrapped,
                          output trit [2:0] self_sized);
        assign {cout,sum}=a+b+cin;
        assign wrapped=a+b+cin;
        assign self_sized={a+b,a+b+cin}; endmodule''')
    t, net = checked(d)
    total = t['a'].astype(np.int64)+t['b']+t['cin']
    np.testing.assert_array_equal(t['sum']+3*t['cout'],total)
    np.testing.assert_array_equal(t['wrapped'],wrap(total,1))
    np.testing.assert_array_equal(t['self_sized[0]'],wrap(total,1))
    np.testing.assert_array_equal(t['self_sized[1]'],wrap(t['a']+t['b'],1))
    assert (t['self_sized[2]'] == 0).all()
    assert net.report()['equivalence']['passed']


def test_zero_extension_unary_negation_parameters_and_constants():
    d = loads('''module m #(parameter K=2)(input trit [1:0] a,output trit [3:0] y,z,n);
       assign y=-(a+K); assign z=a+0; assign n=~a; endmodule''')
    t, _ = checked(d)
    for name, expected in [('y',-bus(t,'a',2)-2),('z',bus(t,'a',2)),('n',-bus(t,'a',2))]:
        np.testing.assert_array_equal(bus(t,name,4),expected)
    assert (t['n[3]'] == 0).all() and (t['n[2]'] == 0).all()


def test_assignment_and_bitwise_context_resize():
    d = loads('''module m(input trit [1:0] a,input trit b,
       output trit [2:0] y,output trit z);
       assign y=a&b; assign z={a,b}; endmodule''')
    t, _ = checked(d)
    np.testing.assert_array_equal(t['y[0]'],np.minimum(t['a[0]'],t['b']))
    np.testing.assert_array_equal(t['y[1]'],np.minimum(t['a[1]'],0))
    assert (t['y[2]']==0).all()
    np.testing.assert_array_equal(t['z'],t['b'])


def test_vector_kleene_conditional_all_inputs():
    d = loads('''module m(input trit c,input trit [1:0] a,b,output trit [2:0] y);
        assign y=c?a:b; endmodule''')
    t, _ = checked(d)
    for i in range(2):
        a,b,c=t[f'a[{i}]'],t[f'b[{i}]'],t['c']
        expected = np.array([int(x) if s==1 else int(y) if s==-1 else int(x) if x==y else 0
                             for s,x,y in zip(c,a,b)],dtype=np.int8)
        np.testing.assert_array_equal(t[f'y[{i}]'],expected)
    assert (t['y[2]']==0).all()


def test_kleene_logical_operators_and_precedence():
    d = loads('''module m(input trit a,b,c,output trit y,z,n);
        assign y=a||b&&c; assign z=a&&b||c; assign n=!a; endmodule''')
    t, _ = checked(d)
    np.testing.assert_array_equal(t['y'],np.maximum(t['a'],np.minimum(t['b'],t['c'])))
    np.testing.assert_array_equal(t['z'],np.maximum(np.minimum(t['a'],t['b']),t['c']))
    np.testing.assert_array_equal(t['n'],-t['a'])


def test_blocking_assignments_if_else_and_unknown_condition():
    d=loads('''module m(input trit a,b,output reg trit y,z);
       reg trit t;
       always @(*) begin
          t=a; y=t; t=b; z=t;
          if (a) y=~y; else if(b) y=z; else y=0;
       end
       endmodule''')
    t,_=checked(d)
    np.testing.assert_array_equal(t['z'],t['b'])
    np.testing.assert_array_equal(t['y'],np.where(t['a']==1,-t['a'],np.where(t['b']==1,t['b'],0)))


def test_partial_assignments_and_defaults_prevent_latches():
    d=loads('''module m(input trit a,output trit [1:0] y);
        always @* begin
          y=2't00;
          if(a) y[1]=1't1; else y[0]=1'tT;
        end endmodule''')
    t,_=checked(d)
    np.testing.assert_array_equal(t['y[1]'],np.where(t['a']==1,1,0))
    np.testing.assert_array_equal(t['y[0]'],np.where(t['a']==1,0,-1))


def test_case_all_labels_no_default_and_nested_blocks():
    d=loads('''module m(input trit a,output reg trit y);
       always @* case(a)
          1'tT: begin y=1't1; end
          1't0,1't1: if(a) y=1'tT; else y=1't0;
       endcase endmodule''')
    t,_=checked(d)
    np.testing.assert_array_equal(t['y'],-t['a'])


@pytest.mark.parametrize('body,message', [
    ('assign y=a/1;', 'division'),
    ('assign y=a%1;', 'remainder'),
    ('always @* if(a) y=a;', 'latch'),
    ("always @* case(a) 1'tT: y=0; endcase", 'latch'),
    ('always @* begin y=y; end', 'read before'),
    ('reg trit t; always @* begin y=t; t=a; end', 'read before'),
    ('always @* begin if(a) y=a; y=y; end', 'read before'),
    ("always @* case(a) 1'tT:y=0; 1'tT:y=1; default:y=a; endcase", 'duplicate case'),
    ('always @* case(a) default:y=0; default:y=1; endcase','duplicate default'),
    ('always @* case(a) a:y=0; default:y=1; endcase','constant'),
    ('always @(posedge a) y=a;', 'syntax'),
    ('always @* y<=a;', 'syntax'),
    ("assign y=2't0x;", 'x/z'),
    ('assign y={a,a}?a:a;', 'single-trit'),
    ('always @* if({a,a}) y=a; else y=0;', 'single-trit'),
    ('assign y=!{a,a};', 'single-trit'),
    ('assign y={a,a}&&a;', 'single-trit'),
])
def test_new_located_diagnostics(body,message):
    with pytest.raises(HDLError,match=message) as error:
        loads('module m(input trit a,output trit y);\n'+body+'\nendmodule',filename='rtl.tv')
    assert re.match(r'rtl.tv:\d+:\d+: ',str(error.value))


def test_new_examples_against_integer_and_table_oracles():
    for name in ['full_add_rtl','adder4_rtl','case_table','comparator_rtl','mux_rtl','alu']:
        t,net=checked(load('examples/'+name+'.tv'))
        if name=='full_add_rtl':
            np.testing.assert_array_equal(t['sum']+3*t['cout'],t['a']+t['b']+t['cin'])
            assert net.report()['cells']=={'INV':5,'NANY':11}
        elif name=='adder4_rtl':
            np.testing.assert_array_equal(bus(t,'sum',4)+81*t['cout'],bus(t,'a',4)+bus(t,'b',4))
        elif name=='case_table':
            np.testing.assert_array_equal(t['y'],t['a']*t['b'])
        elif name=='comparator_rtl':
            a,b=bus(t,'a',2),bus(t,'b',2)
            for key,test in [('lt',a<b),('eq',a==b),('gt',a>b)]:
                np.testing.assert_array_equal(t[key],np.where(test,1,-1))
        elif name=='mux_rtl':
            ref=[a if c==1 else b if c==-1 else a if a==b else 0 for c,a,b in zip(t['c'],t['a'],t['b'])]
            np.testing.assert_array_equal(t['y'],ref)
        else:
            from examples.alu_reference import result
            expected=[result(int(a),int(b),int(code)) for a,b,code in
                      zip(bus(t,'a',2),bus(t,'b',2),t['op'])]
            assert len(expected) == 243
            np.testing.assert_array_equal(bus(t,'r',3),expected)


def test_constant_case_expressions_and_provably_active_if():
    d=loads('''module m #(parameter K=1)(input trit a,output trit y,z);
        always @* if (1) y=a;
        always @* case(a)
          -K: z=1;
          K-1: z=-1;
          default: z=0;
        endcase endmodule''')
    t,_=checked(d)
    np.testing.assert_array_equal(t['y'],t['a'])
    np.testing.assert_array_equal(t['z'],[1,-1,0])


def test_verilog_precedence_for_relations_equality_and_bitwise_logic():
    d=loads('''module m(input trit a,b,c,output trit y,z,q,r);
        assign y=a&b==c;
        assign z=a==b<c;
        assign q=a<b<c;
        assign r=a?b:c?~b:a;
        endmodule''')
    t,_=checked(d)
    a,b,c=t['a'],t['b'],t['c']
    np.testing.assert_array_equal(t['y'],np.minimum(a,np.where(b==c,1,-1)))
    np.testing.assert_array_equal(t['z'],np.where(a==np.where(b<c,1,-1),1,-1))
    np.testing.assert_array_equal(t['q'],np.where(np.where(a<b,1,-1)<c,1,-1))
    def choose(s,x,y):
        return x if s==1 else y if s==-1 else x if x==y else 0
    np.testing.assert_array_equal(t['r'],[choose(x,y,choose(z,-y,x)) for x,y,z in zip(a,b,c)])
