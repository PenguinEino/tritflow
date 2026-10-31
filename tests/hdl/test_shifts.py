"""Shifts checked against integer multiplication and nearest-integer division."""

import re

import numpy as np
import pytest

from tritflow.hdl import HDLError, loads
from tritflow.synth import evaluate_netlist, synthesize


def integer_bus(table, name, width):
    return sum(table[f'{name}[{i}]'].astype(object)*3**i for i in range(width))


def reference(value, amount, width, left=True):
    """Integer oracle: nearest division by an odd power has no half ties."""
    amount = int(amount) * (1 if left else -1)
    if abs(amount) >= width:
        return 0
    if amount >= 0:
        shifted = int(value) * 3**amount
    else:
        denominator = 3**(-amount)
        # Use sign and magnitude to make rounding independent of digit dropping.
        shifted = (abs(int(value)) + denominator//2)//denominator
        if value < 0:
            shifted = -shifted
    modulus = 3**width
    return (shifted + modulus//2) % modulus - modulus//2


def check(design):
    table = design.truth_table()
    net = synthesize(design)
    cells = evaluate_netlist(net, {key: table[key] for key in design.inputs})
    for key in design.outputs:
        np.testing.assert_array_equal(cells[key], table[key])
    assert net.equivalence['passed'] and net.equivalence['mode'] == 'exhaustive'
    return table, net


@pytest.mark.parametrize('operator', ['<<', '>>', '<<<', '>>>'])
@pytest.mark.parametrize('out_width', [1, 2, 4])
def test_constant_shifts_all_data_and_integer_amounts(operator, out_width):
    # Multiple outputs cover overshift, zero, both signs and negative rounding.
    amounts = [-100000, -5, -2, -1, 0, 1, 2, 5, 100000]
    ports = ','.join(f'output trit [{out_width-1}:0] y{j}' for j in range(len(amounts)))
    body = ''.join(f'assign y{j}=a {operator} ({k});' for j, k in enumerate(amounts))
    design = loads(f'module m(input trit [1:0] a,{ports});{body}endmodule')
    table, net = check(design)
    # Boundary aliases/zeros may require BUF/TIE drivers, never shifter logic.
    assert set(net.report()['cells']) <= {'BUF', 'TIEZ'}
    for j, k in enumerate(amounts):
        expected = [reference(a, k, max(2, out_width), operator.startswith('<<'))
                    for a in integer_bus(table, 'a', 2)]
        modulus = 3**out_width
        expected = [(a+modulus//2)%modulus-modulus//2 for a in expected]
        np.testing.assert_array_equal(integer_bus(table, f'y{j}', out_width), expected)


@pytest.mark.parametrize('operator', ['<<', '>>', '<<<', '>>>'])
@pytest.mark.parametrize('data_width,amount_width,out_width', [(1,2,1),(2,1,4),(2,2,3),(2,3,1),(3,2,4)])
def test_signal_shift_amounts_exhaustive(operator, data_width, amount_width, out_width):
    design = loads(f'''module m(input trit [{data_width-1}:0] a,
        input trit [{amount_width-1}:0] k,output trit [{out_width-1}:0] y);
        assign y=a {operator} k; endmodule''')
    table, _ = check(design)
    expected = [reference(a,k,max(data_width,out_width),operator.startswith('<<')) for a,k in
                zip(integer_bus(table,'a',data_width),integer_bus(table,'k',amount_width))]
    modulus=3**out_width
    np.testing.assert_array_equal(integer_bus(table,'y',out_width),
                                  [(a+modulus//2)%modulus-modulus//2 for a in expected])


def test_shift_precedence_context_and_self_determined_amount():
    design = loads('''module m(input trit [1:0] a,b,k,
        output trit [3:0] y,z,q,output trit c);
        assign y=a+b << 1+1;
        assign z=a << k >> 1;
        assign q={a << 1,a >> 1};
        assign c=(a << k) < b;
        endmodule''')
    table,_=check(design)
    a,b,k=(integer_bus(table,name,2) for name in ('a','b','k'))
    np.testing.assert_array_equal(integer_bus(table,'y',4),[reference(x+y,2,4) for x,y in zip(a,b)])
    np.testing.assert_array_equal(integer_bus(table,'z',4),
                                  [reference(reference(x,s,4),1,4,False) for x,s in zip(a,k)])
    np.testing.assert_array_equal(integer_bus(table,'q',4),
                                  [9*reference(x,1,2)+reference(x,1,2,False) for x in a])
    np.testing.assert_array_equal(table['c'],
                                  [1 if reference(x,s,2)<y else -1 for x,y,s in zip(a,b,k)])


def test_shift_amount_constant_expressions_parameters_and_generate_indices():
    design = loads('''module m #(parameter K=1<<1)(input trit [1:0] a,output trit [3:0] y);
        for(genvar i=0;i<4;i=i+1) begin:s
          assign y[i] = a >> (K-i);
        end endmodule''')
    table,_=check(design)
    assert design.params['K']==3
    for i in range(4):
        expected=[reference(x,3-i,2,False) for x in integer_bus(table,'a',2)]
        np.testing.assert_array_equal(table[f'y[{i}]'],[(v+1)%3-1 for v in expected])


def test_wide_shift_source_semantics_use_python_integers():
    for operator in ('<<','>>'):
        width=42
        design=loads(f'''module m(output trit [{width-1}:0] y);
            assign y={width}'t{'1'*width} {operator} 2; endmodule''')
        table=design.evaluate({})
        expected=reference((3**width-1)//2,2,width,operator=='<<')
        assert integer_bus(table,'y',width)==expected


@pytest.mark.parametrize('expression,message', [('a << missing','undeclared'),('a >> (a/1)','division'),
                                                ('a <<','syntax')])
def test_bad_shift_has_file_line(expression,message):
    with pytest.raises(HDLError,match=message) as error:
        loads(f'module m(input trit a,output trit y);\nassign y={expression};\nendmodule',filename='shift.tv')
    assert re.match(r'shift.tv:2:\d+: ',str(error.value))
