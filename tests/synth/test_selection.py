"""Crispness proofs, one-hot selection and pin-counted compact BUF trees."""

from itertools import product
from math import ceil

import numpy as np
import pytest

from tritflow.hdl import Design, Node, loads
from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.synth import evaluate_netlist, fanouts, synthesize
from tritflow.synth.mapping import buffer_fanout
from tritflow.synth.predicates import Predicates, case_partition


def check(source):
    design = loads(source)
    table = design.truth_table()
    for do_optimize in (True, False):
        net = synthesize(design, optimize_logic=do_optimize)
        actual = evaluate_netlist(net, {k: table[k] for k in design.inputs})
        for k in design.outputs:
            np.testing.assert_array_equal(actual[k], table[k])
    return design, synthesize(design), table


def test_value_proof_never_loses_a_reachable_value():
    x, y = Node('input', name='x'), Node('input', name='y')
    constants = [Node('const', value=v) for v in (-1, 0, 1)]
    comparisons = [Node(op, (x, y)) for op in ('eq', 'ne', 'lt', 'le', 'gt', 'ge')]
    base = [x, y, *constants, *comparisons, Node('is_true', (x,))]
    nodes = base + [Node('neg', (a,)) for a in base]
    nodes += [Node(op, (a,b)) for op in ('min','max','nany') for a,b in product(base, repeat=2)]
    nodes += [Node(op, (c,a,b)) for op in ('mux','select')
              for c in (x, comparisons[0]) for a,b in product(base, repeat=2)]
    design = Design('proof', [Port('x','input'),Port('y','input')],
                    {str(i):n for i,n in enumerate(nodes)}, {'x':x,'y':y})
    table = design.truth_table()
    proof = Predicates()
    for index, node in enumerate(nodes):
        reachable = set(table[str(index)].tolist())
        assert reachable <= proof.values(node)
        if proof.crisp(node):
            assert 0 not in reachable
    assert proof.crisp(Node('min', tuple(comparisons[:2])))
    assert not proof.crisp(Node('max', (x,Node('neg',(x,)))))
    assert not proof.crisp(Node('mux', (x,constants[0],constants[2])))


def test_crisp_conditional_and_procedural_if_share_the_same_cheap_selection():
    header = 'module m(input trit [1:0] a,b,output trit [2:0] r);'
    conditional = loads(header + 'assign r=(a>b) ? a+b : a-b; endmodule')
    procedural = loads(header + 'always @* if(a>b) r=a+b; else r=a-b; endmodule')
    assert synthesize(conditional).to_json() == synthesize(procedural).to_json()
    _, net, table = check(header + 'assign r=(a>b) ? a+b : a-b; endmodule')
    a = 3*table['a[1]']+table['a[0]']
    b = 3*table['b[1]']+table['b[0]']
    np.testing.assert_array_equal(9*table['r[2]']+3*table['r[1]']+table['r[0]'],
                                  np.where(a>b, a+b, a-b))
    assert len(net.instances) < 116


def test_unknown_selectors_keep_consensus_and_procedural_zero_takes_else():
    _, _, t = check('''module m(input trit c,a,b,output trit x,y,z);
        assign x=c ? a:b;
        assign y=(c | ~c) ? a:b;
        always @* if(c) z=a; else z=b;
        endmodule''')
    np.testing.assert_array_equal(t['x'], [a if c==1 else b if c==-1 else a if a==b else 0
                                          for c,a,b in zip(t['c'],t['a'],t['b'])])
    np.testing.assert_array_equal(t['z'],np.where(t['c']==1,t['a'],t['b']))
    np.testing.assert_array_equal(t['y'],[a if c else a if a==b else 0
                                         for c,a,b in zip(t['c'],t['a'],t['b'])])


def test_case_partition_requires_common_selectors_and_disjoint_labels():
    a,b = Node('input',name='a'),Node('input',name='b')
    def equal(x,k):
        return Node('eq',(x,Node('const',value=k)))
    tests = [equal(a,k) for k in (-1,0,1)]
    assert case_partition(tests) is True
    assert case_partition(tests[:2]) is False
    assert case_partition([tests[0],tests[0]]) is None
    assert case_partition([tests[0],equal(b,0)]) is None
    assert case_partition([a]) is None
    assert case_partition([Node('max',tuple(tests[:2])),tests[2]]) is True


def test_unproved_case_ir_retains_priority_and_unknown_condition_rules():
    x = Node('input', name='x')
    yes,zero,no = (Node('const',value=v) for v in (1,0,-1))
    # Deliberately overlapping predicates are not a one-hot partition.
    eq = Node('eq',(x,yes))
    for conditions, expected in [((eq,eq),[-1,-1,0]), ((x,eq),[-1,-1,0])]:
        root = Node('case',(conditions[0],zero,conditions[1],yes,no))
        design = Design('m',[Port('x','input'),Port('y','output')],{'y':root},{'x':x})
        net = synthesize(design)
        np.testing.assert_array_equal(evaluate_netlist(net,{'x':[-1,0,1]})['y'],expected)


def test_case_defaults_multiple_labels_shared_data_and_constant_outputs():
    _, net, t = check('''module m(input trit [1:0] op,input trit a,b,
        output trit [2:0] r,output trit z);
        always @* begin
          case(op)
            2'tTT,2't11:r={a,b,a};
            2't00:r={b,a,b};
            default:r=3't000;
          endcase
          case(op) 2't00:z=0; default:z=0; endcase
        end endmodule''')
    op = 3*t['op[1]']+t['op[0]']
    for i, yes, mid in [(2,t['a'],t['b']),(1,t['b'],t['a']),(0,t['a'],t['b'])]:
        np.testing.assert_array_equal(t[f'r[{i}]'],np.where(abs(op)==4,yes,np.where(op==0,mid,0)))
    assert (t['z']==0).all()
    constant = synthesize(loads('''module m(input trit [1:0] op,output trit [2:0] r);
        always @* case(op) 2'tTT:r=0; default:r=0; endcase endmodule'''))
    assert set(constant.report()['cells']) <= {'TIEZ','BUF'}
    assert net.report()['max_fanout'] <= 4


@pytest.mark.parametrize('limit,loads',[(2,3),(2,27),(3,5),(4,5),(4,8),(4,21),(4,100)])
def test_compact_buffer_tree_uses_direct_loads_and_meets_every_pin_limit(limit,loads):
    net = GateNetlist('m',[Port('a','input')],
                      [Instance(f'g{i}','INV',{'A':'a','Y':f'n{i}'}) for i in range(loads)])
    buffer_fanout(net,limit,compact=True)
    assert sum(i.cell=='BUF' for i in net.instances) == ceil((loads-limit)/(limit-1))
    assert max(fanouts(net).values()) <= limit
    # Follow each leaf to the original source; the grouping must not drop loads.
    drivers = {i.pins['Y']:i for i in net.instances}
    for i in net.instances[:loads]:
        source = i.pins['A']
        visited = set()
        while source != 'a':
            assert source not in visited
            visited.add(source)
            source = drivers[source].pins['A']
