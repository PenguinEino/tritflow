"""Nonblocking clocked statements lower to D functions over the old Q values."""
from copy import deepcopy

from lark import Tree

from tritflow.hdl.ir import Node
from tritflow.hdl.procedural import elaborate_block
from .ir import Register, SequentialDesign


def elaborate_clocked(elaborator, block, scope, env, module, hier):
    """Reuse the if/case SSA builder with old-state defaults and frozen RHSs.

    A missing assignment means hold. Each RHS, condition and case selector reads
    old Q, including after earlier <= statements. Last executed assignment wins.
    """
    events = block.children[:-1]
    if len(events) != 1:
        raise module.location(block).error('asynchronous reset/multiple clock events are unsupported')
    event = events[0]
    if str(event.children[0]) != 'posedge':
        raise module.location(event).error('negedge is unsupported; use one posedge clock')
    clock = elaborator.expression(event.children[1], scope, env, module, hier)
    if len(clock) != 1:
        raise module.location(event).error('clock must be a scalar input')
    statement = deepcopy(block.children[-1])
    written = {}

    def collect(stmt):
        if stmt.data == 'blocking':
            raise module.location(stmt).error('invalid clocked syntax: registers require nonblocking <= assignments')
        if stmt.data == 'nonblocking':
            targets = elaborator.targets(stmt.children[0], scope, env, module)
            for bit in targets:
                if not bit.is_reg:
                    raise module.location(stmt).error(f'{bit.name!r} must be declared reg trit')
                if bit.direction == 'input':
                    raise module.location(stmt).error('cannot assign to input register')
                written[bit.name] = bit
            stmt.data = 'blocking'
        else:
            for child in stmt.children:
                if isinstance(child, Tree):
                    collect(child)
    collect(statement)
    if not written:
        raise module.location(block).error('clocked block does not assign any registers')
    for name, bit in written.items():
        if bit.driver is not None:
            raise module.location(block).error(f'multiple drivers for register {name!r}')
        bit.driver = Node('input', name=name, loc=bit.loc, hier=hier)

    # Reuse procedural coverage/constant-case validation and exact trit rules.
    # Defaults are evaluated through Q refs; every later RHS ignores SSA values.
    defaults = []
    for name in written:
        ref = Tree('seq_ref', [name], meta=statement.meta)
        defaults.append(Tree('blocking', [ref, ref], meta=statement.meta))
    body = Tree('always_comb', [Tree('block', [*defaults, statement], meta=statement.meta)], meta=block.meta)

    class Adapter:
        def targets(self, expr, *args):
            return [written[expr.children[0]]] if expr.data == 'seq_ref' else elaborator.targets(expr, *args)

        def expression(self, expr, s, e, m, h, context=None, values=None, required=()):
            if expr.data == 'seq_ref':
                return [Node('ref', name=expr.children[0], loc=module.location(block))]
            return elaborator.expression(expr, s, e, m, h, context)

        def drive(self, bits, nodes, loc):
            for bit, d in zip(bits, nodes):
                elaborator.registers.append(Register(bit.name, bit.driver, d, clock[0]))

    elaborate_block(Adapter(), body, scope, env, module, hier)


def finish_sequential(design, registers, resolve):
    """Resolve hierarchy, reject derived/multiple clocks, and cut feedback at Q."""
    registers = tuple(Register(r.name, r.q, resolve(r.d), resolve(r.clock)) for r in registers)
    clocks = {r.clock.name for r in registers if r.clock.op == 'input'}
    if any(r.clock.op != 'input' or r.clock.name not in design.inputs for r in registers):
        raise registers[0].clock.loc.error('clock must connect directly to one top-level scalar input')
    if len(clocks) != 1:
        raise registers[-1].clock.loc.error('multiple clocks are unsupported')
    clock = next(iter(clocks))
    # Clock may be observed at ports, but cannot participate in next-state logic.
    from tritflow.hdl.ir import reachable
    if any(node is design.inputs[clock] for root in [*(r.d for r in registers), *design.outputs.values()]
           for node in reachable([root])):
        raise registers[0].clock.loc.error('clock cannot be used as register data')
    return SequentialDesign(design.top, design.ports, design.outputs, design.inputs,
                            design.params, registers, clock)
