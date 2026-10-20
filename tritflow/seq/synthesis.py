"""Register-boundary mapping and independent RTL/cell next-state equivalence."""
from collections import Counter

import numpy as np

from tritflow.hdl.ir import Design, normalize_inputs
from tritflow.netlist import GateNetlist, Instance, Port
from tritflow.synth.mapping import SynthesizedNetlist, synthesize as map_comb
from tritflow.synth.simulate import check_equivalence, evaluate_netlist
from .ir import d_name


def source_cut(design):
    """Cut every DFF at Q; retain all D functions even for unobserved registers."""
    names = set(design.state_names)
    outputs = {name: node for name, node in design.outputs.items() if name not in names}
    outputs.update({d_name(r.name): r.d for r in design.registers})
    inputs = {**design.inputs, **{r.name: r.q for r in design.registers}}
    ports = [Port(name, 'input') for name in inputs]
    ports += [Port(name, 'output') for name in outputs]
    return Design(design.top, ports, outputs, inputs, design.params)


class SequentialNetlist(SynthesizedNetlist):
    """Unchanged GateNetlist JSON schema: TDFF instances mark state boundaries."""
    @property
    def registers(self):
        return [i for i in self.instances if i.cell == 'TDFF']

    @property
    def state_names(self):
        return [i.pins['Q'] for i in self.registers]

    @property
    def clock(self):
        clocks = {i.pins['CLK'] for i in self.registers}
        if len(clocks) != 1:
            raise ValueError('sequential netlist requires exactly one clock')
        return next(iter(clocks))

    @property
    def data_inputs(self):
        return [p.name for p in self.ports if p.dir == 'input' and p.name != self.clock]

    def cut(self):
        states = set(self.state_names)
        ports = [p for p in self.ports if p.dir == 'input']
        ports += [Port(name, 'input') for name in self.state_names]
        ports += [p for p in self.ports if p.dir == 'output' and p.name not in states]
        outputs = {p.name for p in ports if p.dir == 'output'}
        for inst in self.registers:
            if inst.pins['D'] not in outputs:
                ports.append(Port(inst.pins['D'], 'output'))
                outputs.add(inst.pins['D'])
        return GateNetlist(self.top, ports, [i for i in self.instances if i.cell != 'TDFF'])

    def values(self, inputs, state):
        """Evaluate the mapped combinational network for one present state."""
        if set(inputs) != set(self.data_inputs):
            raise ValueError(f'expected data inputs {self.data_inputs}')
        state = normalize_inputs(self.state_names, state)
        return evaluate_netlist(self.cut(), {**inputs, self.clock: 1, **state}, return_all=True)

    def transition(self, inputs, state):
        values = self.values(inputs, state)
        return {i.pins['Q']: values[i.pins['D']] for i in self.registers}

    def evaluate(self, inputs, state):
        values = self.values(inputs, state)
        return {p.name: values[p.name] for p in self.ports if p.dir == 'output'}

    def cycles(self, vectors, initial):
        state = normalize_inputs(self.state_names, initial)
        rows = []
        for vector in vectors:
            state = self.transition(vector, state)
            rows.append({'state': state.copy(), 'outputs': self.evaluate(vector, state)})
        return rows

    def report(self):
        counts = Counter(i.cell for i in self.instances)
        loads = Counter(net for i in self.instances for p, net in i.pins.items()
                        if p != ('Q' if i.cell == 'TDFF' else 'Y'))
        from tritflow.synth.mapping import SynthesizedNetlist
        cut = self.cut()
        comb = SynthesizedNetlist(cut.top, cut.ports, cut.instances)
        info = comb.report()
        for inst in self.registers:
            group = info['hierarchy'].setdefault(inst.hier or '<top>', {})
            group['TDFF'] = group.get('TDFF', 0) + 1
        return {**info, 'cells': dict(sorted(counts.items())), 'total_cells': len(self.instances),
                'registers': self.state_names, 'clock': self.clock,
                'clock_fanout': loads[self.clock], 'max_fanout': max(loads.values(), default=0),
                'data_max_fanout': max((n for name,n in loads.items() if name != self.clock),default=0),
                'fanout_limit_scope': 'data input pins; clock is reported separately without CTS',
                'fanout_limit': self.fanout_limit, 'equivalence': self.equivalence,
                'clock_tree_synthesis': False}


def as_sequential(net):
    """Reopen saved ordinary gate JSON using only explicit TDFF pins."""
    result = SequentialNetlist(net.top, net.ports, net.instances)
    result.fanout_limit = getattr(net, 'fanout_limit', None)
    result.equivalence = getattr(net, 'equivalence', None)
    # Validate the register interface independently of the combinational cut.
    if not result.registers:
        raise ValueError('no TDFF registers')
    if any(set(i.pins) != {'D', 'CLK', 'Q'} for i in result.registers):
        raise ValueError('TDFF requires D, CLK, Q pins')
    if len(set(result.state_names)) != len(result.state_names):
        raise ValueError('multiple register drivers')
    if result.clock not in [p.name for p in result.ports if p.dir == 'input']:
        raise ValueError('clock must be a top-level input')
    from tritflow.synth.simulate import ordered_instances
    ordered_instances(result.cut())
    return result


def check_sequential(design, net, *, seed=0, cycles=256):
    """Compare all D/output functions and then simultaneous multi-cycle state."""
    if design.state_names != net.state_names:
        raise ValueError('RTL/netlist register identities differ')
    # Clock is not data and takes +/-1 only. Exclude it from the ternary count;
    # equivalence evaluates the data/state cut with clock held at +1.
    source = source_cut(design)
    source.inputs = {n: v for n, v in source.inputs.items() if n != design.clock}
    source.ports = [p for p in source.ports if p.name != design.clock]
    cut = net.cut()
    cut.ports = [p for p in cut.ports if p.name != net.clock]
    # Clock output aliases are rejected at elaboration; there are no clock loads
    # in this cut, so its input can be removed without fabricating a driver.
    check = check_equivalence(source, cut, seed=seed)
    rng = np.random.default_rng(seed)
    state = {n: int(rng.integers(-1, 2)) for n in design.state_names}
    mapped = state.copy()
    for cycle in range(cycles):
        inputs = {n: int(rng.integers(-1, 2)) for n in design.data_inputs}
        state = design.transition(inputs, state)
        mapped = net.transition(inputs, mapped)
        if any(int(state[n]) != int(mapped[n]) for n in state):
            raise ValueError(f'sequential state mismatch at cycle {cycle}')
        expected = design.evaluate({**inputs, design.clock: 1}, state)
        actual = net.evaluate(inputs, mapped)
        if any(int(expected[n]) != int(actual[n]) for n in expected):
            raise ValueError(f'sequential output mismatch at cycle {cycle}')
    return {**check, 'state_trits': len(state), 'data_input_trits': len(design.data_inputs),
            'random_cycles': cycles, 'seed': seed, 'register_matching': 'RTL bit name = TDFF.Q'}


def synthesize(design, *, fanout_limit=4, optimize_logic=True, verify=True, seed=0):
    mapped = map_comb(source_cut(design), fanout_limit=fanout_limit,
                      optimize_logic=optimize_logic, verify=False, seed=seed)
    names = {i.name for i in mapped.instances}
    registers = []
    for index, reg in enumerate(design.registers):
        name = f'_tdff{index}'
        while name in names:
            name += '_'
        names.add(name)
        registers.append(Instance(name, 'TDFF', {'D': d_name(reg.name),
                                               'CLK': design.clock, 'Q': reg.name}, reg.q.hier))
    result = SequentialNetlist(design.top, list(design.ports), [*mapped.instances, *registers])
    result.fanout_limit = fanout_limit
    result.equivalence = check_sequential(design, result, seed=seed) if verify else None
    return result
