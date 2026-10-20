"""Clock semantics, independent integer references and illegal storage syntax."""
from itertools import product

import pytest

from tritflow import hdl, synth
from tritflow.seq.synthesis import as_sequential
from tritflow.netlist import GateNetlist


def digits(number, width):
    out = []
    for _ in range(width):
        digit = (number + 1) % 3 - 1
        out.append(digit)
        number = (number - digit) // 3
    return list(reversed(out))


def test_counter_exhaustive_and_cycles():
    design = hdl.load('examples/counter2.tv')
    net = synth.synthesize(design)
    assert net.report()['cells']['TDFF'] == 2
    assert net.equivalence['vectors'] == 9
    assert net.equivalence['random_cycles'] == 256
    for x in range(-4, 5):
        state = dict(zip(design.state_names, digits(x, 2)))
        actual = net.transition({}, state)
        assert list(map(int, actual.values())) == digits(x + 1, 2)
    initial = dict(zip(design.state_names, digits(-4, 2)))
    rows = net.cycles([{}] * 27, initial)
    for index, row in enumerate(rows):
        assert list(map(int, row['state'].values())) == digits(-4 + index + 1, 2)
    reopened = as_sequential(GateNetlist.from_dict(__import__('json').loads(net.to_json())))
    assert reopened.transition({}, initial).keys() == initial.keys()


def test_shift_simultaneous_and_roundtrip():
    design = hdl.load('examples/shift3.tv')
    net = synth.synthesize(design)
    for q in product((-1, 0, 1), repeat=3):
        for d in (-1, 0, 1):
            actual = net.transition({'d': d}, dict(zip(design.state_names, q)))
            assert actual == {'q[0]': d, 'q[1]': q[0], 'q[2]': q[1]}
    assert net.equivalence['vectors'] == 81
    roundtrip = synth.synthesize(hdl.loads(synth.tritverilog(net)))
    assert roundtrip.equivalence['passed']
    assert '.subckt shift3' in synth.spice(net)
    assert net.report()['clock_fanout'] == 3


def test_nonblocking_conditions_case_and_last_assignment():
    design = hdl.loads('''module m(input trit clk, en, d, output reg trit q, r);
      always @(posedge clk) begin
        q <= d;
        if (en) q <= q;
        case (q)
          1'tT: r <= d;
          1't0: r <= q;
          1't1: begin r <= d; r <= -d; end
        endcase
      end
    endmodule''')
    net = synth.synthesize(design)
    for q, r, en, d in product((-1, 0, 1), repeat=4):
        expected = {'q': q if en == 1 else d, 'r': d if q == -1 else 0 if q == 0 else -d}
        assert net.transition({'en': en, 'd': d}, {'q': q, 'r': r}) == expected


def test_hold_and_synchronous_reset():
    design = hdl.loads('''module m(input trit clk, en, rst, d, output reg trit q);
      always @(posedge clk) if (rst == 1't1) q <= 1't0; else if (en) q <= d;
    endmodule''')
    net = synth.synthesize(design)
    for q, en, rst, d in product((-1, 0, 1), repeat=4):
        assert net.transition({'en': en, 'rst': rst, 'd': d}, {'q': q})['q'] == (
            0 if rst == 1 else d if en == 1 else q)
    with pytest.raises(ValueError, match='explicit'):
        design.evaluate({'clk': 1, 'en': 1, 'rst': 1, 'd': 0})
    with pytest.raises(ValueError, match='clock'):
        design.evaluate({'clk': 0, 'en': 1, 'rst': 1, 'd': 0}, {'q': 0})


def test_hierarchy_generate_registers():
    design = hdl.loads('''module ff(input trit clk,d,output reg trit q);
      always @(posedge clk) q <= d; endmodule
      module m(input trit clk, input trit [1:0] d, output trit [1:0] q);
      generate for(genvar i=0;i<2;i=i+1) begin:g
      ff u(.clk(clk),.d(d[i]),.q(q[i])); end endgenerate endmodule''', top='m')
    net = synth.synthesize(design)
    assert net.state_names == ['g[0].u.q', 'g[1].u.q']
    assert net.evaluate({'d[1]': -1, 'd[0]': 1}, dict(zip(net.state_names, [1, -1]))) == {'q[1]': -1, 'q[0]': 1}


@pytest.mark.parametrize('body,message', [
    ('always @(negedge clk) q <= d;', 'negedge'),
    ('always @(posedge clk or posedge d) q <= d;', 'asynchronous'),
    ('always @(posedge clk) q = d;', 'nonblocking'),
    ('always @* q <= d;', 'nonblocking'),
    ('always @* if (d) q = d;', 'latch'),
    ('always @(posedge clk) q <= d; always @(posedge d) r <= q;', 'multiple clocks'),
    ('always @(posedge clk) q <= d; always @(posedge clk) q <= d;', 'multiple drivers'),
    ('always @(posedge (clk & d)) q <= d;', 'directly'),
    ('always @(posedge clk) q <= clk;', 'clock cannot'),
])
def test_located_errors(body, message):
    with pytest.raises(hdl.HDLError, match=r'bad.tv:\d+:\d+:.*' + message):
        hdl.loads('module m(input trit clk,d,output reg trit q,r); ' + body + (' endmodule' if 'r <=' in body else ' assign r = d; endmodule'), filename='bad.tv')


def test_nonreg_rejected():
    with pytest.raises(hdl.HDLError, match='reg trit'):
        hdl.loads('module m(input trit clk,d,output trit q); always @(posedge clk) q <= d; endmodule')


def test_accumulator_integer_reference():
    design = hdl.load('examples/accumulator2.tv')
    net = synth.synthesize(design)
    for q, a, rst in product(range(-4, 5), range(-4, 5), (-1, 0, 1)):
        actual = net.transition(dict(zip(['rst','a[1]','a[0]'], [rst,*digits(a,2)])),
                                dict(zip(net.state_names,digits(q,2))))
        assert list(map(int,actual.values())) == digits(0 if rst == 1 else q+a,2)
