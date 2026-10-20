"""Local ternary identities; no Boolean complementation/excluded-middle laws."""

from collections import Counter

from tritflow.hdl.ir import Design, Node


def primitive_inputs(node: Node) -> tuple[Node, ...]:
    """Extract authored gate pins from its functional DAG representation."""
    if node.primitive in {"NAND", "NOR", "BUF"}:
        return node.args[0].args
    return node.args


def primitive_node(original: Node, args: tuple[Node, ...]) -> Node:
    helper = {"NAND": "min", "NOR": "max", "BUF": "neg"}.get(original.primitive)
    if helper:
        args = (Node(helper, args, hier=original.hier, loc=original.loc),)
    return Node(original.op, args, value=original.value, name=original.name,
                hier=original.hier, loc=original.loc, primitive=original.primitive)


def optimize(design: Design) -> Design:
    """Fold constants, share expressions and remove unused nodes.

    Explicit primitive cells are retained. A De Morgan rewrite removes two
    single-use inferred inverters and permits a single NAND/NOR mapping.
    In particular min(a,-a) and max(a,-a) are never Boolean-folded: at a=0
    they both equal zero.
    """
    from .lower import lower
    design = lower(design)
    uses = Counter(arg for node in design.nodes for arg in node.args)
    uses.update(design.outputs.values())
    cache, shared = {}, {}

    def make(op, args=(), value=None, source=None):
        # Keep the first source operand order, but hash commutatively. Object-id
        # sorting would make generated netlists differ between Python processes.
        key = (op, frozenset(args) if op in {"min", "max", "nany"} else args, value)
        if key not in shared:
            shared[key] = Node(op, args, value=value, hier=source.hier, loc=source.loc)
        return shared[key]

    def visit(node):
        if node in cache:
            return cache[node]
        if node.op == "input":
            result = node
        elif node.primitive:
            result = primitive_node(node, tuple(visit(arg) for arg in primitive_inputs(node)))
        else:
            args = tuple(visit(arg) for arg in node.args)
            op = node.op
            if op == "const":
                result = make(op, value=node.value, source=node)
            elif all(arg.op == "const" and not arg.primitive for arg in args):
                values = [arg.value for arg in args]
                if op == "neg":
                    value = -values[0]
                elif op == "min":
                    value = min(values)
                elif op == "max":
                    value = max(values)
                else:
                    value = -max(-1, min(1, sum(values)))
                result = make("const", value=value, source=node)
            elif op == "neg" and args[0].op == "neg" and not args[0].primitive:
                result = args[0].args[0]
            elif op in {"min", "max"} and args[0] is args[1]:
                result = args[0]
            elif op in {"min", "max"} and any(arg.op == "const" for arg in args):
                const = next(arg for arg in args if arg.op == "const")
                other = args[1] if args[0] is const else args[0]
                absorbing = -1 if op == "min" else 1
                identity = -absorbing
                result = const if const.value == absorbing else other if const.value == identity else make(op, args, source=node)
            elif op == "nany" and any(arg.op == "const" and arg.value == 0 for arg in args):
                other = args[1] if args[0].op == "const" and args[0].value == 0 else args[0]
                result = other.args[0] if other.op == "neg" and not other.primitive else make("neg", (other,), source=node)
            elif op in {"min", "max"} and all(
                old.op == "neg" and not old.primitive and uses[old] == 1
                for old in node.args
            ) and all(
                arg.op == "neg" and not arg.primitive
                # A negative lattice expression already maps to one NAND/NOR.
                # Pushing through two of these would require two positive
                # lattice implementations and increase the cell count.
                and (arg.args[0].op not in {"min", "max"} or arg.args[0].primitive)
                for arg in args
            ):
                inner = make("max" if op == "min" else "min", tuple(arg.args[0] for arg in args), source=node)
                result = make("neg", (inner,), source=node)
            else:
                result = make(op, args, source=node)
        cache[node] = result
        return result

    return Design(design.top, design.ports, {name: visit(node) for name, node in design.outputs.items()},
                  design.inputs, design.params.copy())
