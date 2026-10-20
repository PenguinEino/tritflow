"""Resolve widths, generate loops and named hierarchy into a scalar ternary DAG."""

from __future__ import annotations

from dataclasses import dataclass

from lark import Tree

from tritflow import RAILS
from tritflow.netlist import Port
from .ir import Design, Node
from .parser import AST, HDLError, Location, Module, identifier


@dataclass
class Bit:
    name: str
    loc: Location
    driver: Node | None = None
    is_reg: bool = False
    direction: str = "wire"


@dataclass
class Signal:
    bits: list[Bit]  # declared left-to-right, i.e. concatenation/MSB order
    indices: list[int] | None
    direction: str = "wire"


def integer(expr: Tree, env: dict[str, int], module: Module) -> int:
    """Evaluate elaboration-only integer arithmetic (division truncates to zero)."""
    op = str(expr.data)
    children = expr.children
    fail = module.location(expr).error
    if op == "integer":
        return int(children[0])
    if op == "ref" and len(children) == 1:
        name = identifier(children[0])
        if name not in env:
            raise fail(f"unknown integer parameter/genvar {name!r}")
        return env[name]
    if op in {"minus", "plus"}:
        value = integer(children[0], env, module)
        return -value if op == "minus" else value
    if op in {"shift_left", "shift_right"}:
        a, amount = (integer(child, env, module) for child in (children[0], children[-1]))
        amount *= 1 if op == "shift_left" else -1
        return a * 3**amount if amount >= 0 else (a + 3**(-amount)//2) // 3**(-amount)
    if op in {"add", "sub", "mul", "div", "mod"}:
        a, b = (integer(child, env, module) for child in children)
        if op in {"div", "mod"} and b == 0:
            raise fail("division by zero in integer expression")
        if op == "add":
            return a + b
        if op == "sub":
            return a - b
        if op == "mul":
            return a * b
        quotient = (abs(a) // abs(b)) * (-1 if (a < 0) != (b < 0) else 1)
        return quotient if op == "div" else a - quotient * b
    if op == "comparison":
        previous = integer(children[0], env, module)
        result = True
        for cmp, child in zip(children[1::2], children[2::2]):
            current = integer(child, env, module)
            result &= {"<": previous < current, ">": previous > current,
                       "<=": previous <= current, ">=": previous >= current,
                       "==": previous == current, "!=": previous != current}[str(cmp)]
            previous = current
        return int(result)
    raise fail("expected an integer constant expression for parameter, range, or generate loop")


class Elaborator:
    def __init__(self, ast: AST):
        self.ast = ast
        self.bits: dict[str, Bit] = {}
        self.registers = []

    def declare(self, name, range_node, direction, prefix, env, module, scope, source, is_reg=False):
        if name in scope:
            raise module.location(source).error(f"duplicate signal {name!r}")
        indices = None
        if range_node is not None:
            left, right = (integer(e, env, module) for e in range_node.children)
            if abs(left - right) > 100_000:
                raise module.location(range_node).error("vector width exceeds 100001 trits")
            indices = list(range(left, right + (1 if right >= left else -1), 1 if right >= left else -1))
        names = [name] if indices is None else [f"{name}[{i}]" for i in indices]
        bits = [Bit(prefix + n, module.location(source), is_reg=is_reg, direction=direction) for n in names]
        for bit in bits:
            if bit.name in RAILS:
                raise bit.loc.error(f"{bit.name!r} is reserved for a global power rail; use a TIE constant")
            if bit.name in self.bits:
                raise bit.loc.error(f"duplicate elaborated net {bit.name!r}")
            self.bits[bit.name] = bit
        scope[name] = Signal(bits, indices, direction)

    def selected(self, expr, scope, env, module):
        name = identifier(expr.children[0])
        if name not in scope:
            raise module.location(expr).error(f"undeclared trit signal {name!r}")
        signal = scope[name]
        if len(expr.children) == 1:
            return signal.bits
        select = expr.children[1]
        if signal.indices is None:
            raise module.location(select).error(f"cannot select a bit of scalar {name!r}")
        indices = [integer(e, env, module) for e in select.children]
        if len(indices) == 2:
            left, right = indices
            if (left < right) != (signal.indices[0] < signal.indices[-1]) and left != right:
                raise module.location(select).error("part select must follow the declared vector direction")
            indices = list(range(left, right + (1 if right >= left else -1), 1 if right >= left else -1))
        try:
            return [signal.bits[signal.indices.index(i)] for i in indices]
        except ValueError:
            raise module.location(select).error(f"index outside declared range of {name!r}") from None

    def expression(self, expr, scope, env, module, hier, context=None, values=None, required=()):
        from .expressions import Expressions
        return Expressions(lambda e: self.selected(e, scope, env, module), env,
                           module, hier, values, required).build(expr, context)

    def targets(self, expr, scope, env, module):
        if expr.data == "concat":
            return [bit for child in expr.children for bit in self.targets(child, scope, env, module)]
        if expr.data != "ref":
            raise module.location(expr).error("assignment output must be a signal, select, or concatenation")
        return self.selected(expr, scope, env, module)

    def drive(self, bits, nodes, loc):
        if len(bits) != len(nodes):
            raise loc.error(f"connection width mismatch: {len(bits)} versus {len(nodes)} trits")
        for bit, node in zip(bits, nodes):
            if bit.driver is not None:
                raise loc.error(f"multiple drivers for {bit.name!r} (first at {bit.loc.filename}:{bit.loc.line})")
            bit.driver = node

    def bindings(self, items, env, module, overrides=None):
        allowed = set()
        for item in items:
            if item.data not in {"parameter_decl", "localparam_decl"}:
                continue
            for binding in item.children[0].children:
                name = identifier(binding.children[0])
                if name in env:
                    raise module.location(binding).error(f"duplicate parameter {name!r}")
                if item.data == "parameter_decl":
                    allowed.add(name)
                env[name] = ((overrides or {})[name] if name in (overrides or {}) and name in allowed
                             else integer(binding.children[1], env, module))
        return allowed

    def module(self, name, overrides, prefix, stack):
        if name not in self.ast.modules:
            raise HDLError(f"<elaboration>:1:1: unknown module {name!r}")
        module = self.ast.modules[name]
        if any(not isinstance(v, int) or isinstance(v, bool) for v in overrides.values()):
            raise module.location().error("parameter overrides must be integers")
        if name in stack:
            raise module.location().error(f"recursive module hierarchy: {' -> '.join((*stack, name))}")
        env: dict[str, int] = {}
        declared_params = set()
        children = module.tree.children[1:]
        if children and children[0].data == "parameter_header":
            for entry in children[0].children:
                param = identifier(entry.children[0])
                if param in env:
                    raise module.location(entry).error(f"duplicate parameter {param!r}")
                declared_params.add(param)
                env[param] = overrides[param] if param in overrides else integer(entry.children[1], env, module)
            children = children[1:]
        port_tree = children[0] if children and children[0].data == "ports" else None
        items = children[1:] if port_tree is not None else children
        declared_params |= self.bindings(items, env, module, overrides)
        if set(overrides) - declared_params:
            raise module.location().error(f"unknown parameter override(s): {sorted(set(overrides) - declared_params)}")
        scope: dict[str, Signal] = {}
        ports = {}
        direction, width = None, None
        if port_tree:
            for port in port_tree.children:
                if port.data in {"typed_port", "typed_reg_port"}:
                    direction = str(port.children[0])
                    width = port.children[1] if isinstance(port.children[1], Tree) else None
                elif direction is None:
                    raise module.location(port).error("first port must declare input/output trit")
                port_name = identifier(port.children[-1])
                self.declare(port_name, width, direction, prefix, env, module, scope, port,
                             is_reg=port.data == "typed_reg_port" or (port.data == "continued_port" and register_port))
                register_port = scope[port_name].bits[0].is_reg
                ports[port_name] = scope[port_name]
        self.items(items, scope, env, module, prefix, (*stack, name))
        return ports, env

    def items(self, items, scope, env, module, prefix, stack):
        # Declarations precede connectivity so forward references behave like HDL wires.
        for item in items:
            if item.data in {"wire_decl", "reg_decl"}:
                width = item.children[0] if isinstance(item.children[0], Tree) else None
                for token in item.children[1:] if width is not None else item.children:
                    self.declare(identifier(token), width, "wire", prefix, env, module, scope, item,
                                 is_reg=item.data == "reg_decl")
        names = set()
        for item in items:
            loc = module.location(item)
            if item.data == "assign":
                lhs, rhs = item.children
                targets = self.targets(lhs, scope, env, module)
                self.drive(targets, self.expression(rhs, scope, env, module,
                                                   prefix.rstrip("."), len(targets)), loc)
            elif item.data == "always_seq":
                from tritflow.seq.elaborate import elaborate_clocked
                elaborate_clocked(self, item, scope, env, module, prefix.rstrip("."))
            elif item.data == "always_comb":
                from .procedural import elaborate_block
                elaborate_block(self, item, scope, env, module, prefix.rstrip("."))
            elif item.data == "primitive":
                cell, token, *connections = item.children
                inst = identifier(token)
                if inst in names:
                    raise loc.error(f"duplicate instance {inst!r}")
                names.add(inst)
                cell = str(cell).upper()
                arity = 1 if cell in {"INV", "BUF"} else 2
                if len(connections) != arity + 1:
                    raise loc.error(f"{cell} requires output followed by {arity} input(s)")
                args = [self.expression(e, scope, env, module, prefix.rstrip(".")) for e in connections[1:]]
                if any(len(a) != 1 for a in args):
                    raise loc.error("gate primitives require scalar trit inputs")
                args = tuple(a[0] for a in args)
                hier = prefix.rstrip(".")
                if cell in {"NAND", "NOR"}:
                    node = Node("neg", (Node("min" if cell == "NAND" else "max", args, loc=loc, hier=hier),),
                                name=prefix + inst, primitive=cell, loc=loc, hier=hier)
                elif cell == "BUF":
                    node = Node("neg", (Node("neg", args, loc=loc, hier=hier),),
                                name=prefix + inst, primitive=cell, loc=loc, hier=hier)
                else:
                    node = Node("neg" if cell == "INV" else "nany", args, name=prefix + inst,
                                primitive=cell, loc=loc, hier=hier)
                self.drive(self.targets(connections[0], scope, env, module), [node], loc)
            elif item.data == "instance":
                cell, *rest = item.children
                overrides = {}
                if isinstance(rest[0], Tree) and rest[0].data == "overrides":
                    for value in rest.pop(0).children:
                        key = identifier(value.children[0])
                        if key in overrides:
                            raise loc.error(f"duplicate parameter connection {key!r}")
                        overrides[key] = integer(value.children[1], env, module)
                inst = identifier(rest[0])
                if inst in names:
                    raise loc.error(f"duplicate instance {inst!r}")
                names.add(inst)
                if identifier(cell) not in self.ast.modules:
                    raise loc.error(f"unknown module {identifier(cell)!r}")
                ports, _ = self.module(identifier(cell), overrides, prefix + inst + ".", stack)
                values = {}
                for value in rest[1].children if len(rest) > 1 else []:
                    key = identifier(value.children[0])
                    if key in values:
                        raise loc.error(f"duplicate port connection {key!r}")
                    values[key] = value.children[1]
                if set(values) != set(ports):
                    raise loc.error(f"named ports must match {list(ports)}; got {list(values)}")
                for key, signal in ports.items():
                    if signal.direction == "input":
                        self.drive(signal.bits, self.expression(values[key], scope, env, module, prefix.rstrip(".")), loc)
                    else:
                        self.drive(self.targets(values[key], scope, env, module),
                                   [Node("ref", name=b.name, loc=loc) for b in signal.bits], loc)
            elif item.data == "generate":
                generated_env = env.copy()
                self.bindings(item.children, generated_env, module)
                self.items(item.children, scope, generated_env, module, prefix, stack)
            elif item.data == "for_generate":
                var, initial, condition, step, label, *body = item.children
                var, label = identifier(var), identifier(label)
                if label in names:
                    raise loc.error(f"duplicate generate label/instance {label!r}")
                names.add(label)
                loop_env = env.copy()
                loop_env[var] = integer(initial, env, module)
                if identifier(step.children[0]) != var:
                    raise loc.error("generate step must update its loop variable")
                seen = set()
                while integer(condition, loop_env, module):
                    index = loop_env[var]
                    if index in seen or len(seen) >= 100_000:
                        raise loc.error("generate loop does not terminate (or exceeds 100000 iterations)")
                    seen.add(index)
                    iteration_env = loop_env.copy()
                    self.bindings(body, iteration_env, module)
                    # A generated scope may shadow parent signals, but local declarations
                    # still receive unique flattened names.
                    iteration_scope = scope.copy()
                    local_names = [identifier(c) for stmt in body if stmt.data in {"wire_decl", "reg_decl"}
                                   for c in stmt.children if not isinstance(c, Tree)]
                    for local_name in local_names:
                        iteration_scope.pop(local_name, None)
                    self.items(body, iteration_scope, iteration_env, module,
                               prefix + f"{label}[{index}].", stack)
                    if step.data == "step_assign":
                        loop_env[var] = integer(step.children[1], loop_env, module)
                    else:
                        loop_env[var] += 1 if step.data == "step_inc" else -1

    def finish(self, top, params):
        ports, env = self.module(top, params, "", ())
        inputs = {}
        output_bits = {}
        flat_ports = []
        for signal in ports.values():
            for bit in signal.bits:
                flat_ports.append(Port(bit.name, signal.direction))
                if signal.direction == "input":
                    node = Node("input", name=bit.name, loc=bit.loc)
                    self.drive([bit], [node], bit.loc)
                    inputs[bit.name] = node
                else:
                    output_bits[bit.name] = bit
        cache, active = {}, set()

        def resolve(node):
            if node in cache:
                return cache[node]
            if node in active:
                raise node.loc.error(f"combinational cycle involving {node.name or node.op!r}")
            active.add(node)
            if node.op == "ref":
                bit = self.bits[node.name]
                if bit.driver is None:
                    raise node.loc.error(f"undriven signal {node.name!r}")
                result = resolve(bit.driver)
            else:
                node.args = tuple(resolve(arg) for arg in node.args)
                result = node
            active.remove(node)
            cache[node] = result
            return result

        # Validate even unused driven logic: dead-code removal must not hide cycles
        # or illegal, undriven operands in the user's circuit.
        for bit in self.bits.values():
            if bit.driver is not None:
                resolve(bit.driver)
        outputs = {}
        for name, bit in output_bits.items():
            if bit.driver is None:
                raise bit.loc.error(f"undriven output {name!r}")
            outputs[name] = resolve(bit.driver)
        design = Design(top, flat_ports, outputs, inputs, env)
        if self.registers:
            from tritflow.seq.elaborate import finish_sequential
            return finish_sequential(design, self.registers, resolve)
        return design


def elaborate(ast: AST, *, top: str | None = None, params: dict[str, int] | None = None) -> Design:
    """Flatten a parsed module using explicit top selection and parameter values."""
    if top is None:
        if len(ast.modules) != 1:
            raise HDLError("<elaboration>:1:1: specify top when source defines multiple modules")
        top = next(iter(ast.modules))
    return Elaborator(ast).finish(top, params or {})
