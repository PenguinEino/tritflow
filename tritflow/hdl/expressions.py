"""Context sizing for balanced-ternary integers and scalar Kleene conditions.

Vectors are MSB first here. Arithmetic propagates max(context, operand widths)
through its operands; extension inserts zero trits. Concatenation members and
comparison operands are self determined. Truncation discards the high trits.
"""

from .ir import Node
from .parser import identifier


def digits(value):
    """Return the shortest MSB-first balanced representation of an integer."""
    out = []
    while value:
        digit = (value + 1) % 3 - 1
        out.append(digit)
        value = (value - digit) // 3
    return list(reversed(out or [0]))


class Expressions:
    def __init__(self, selected, env, module, hier, values=None, required=()):
        self.selected = selected
        self.env, self.module, self.hier = env, module, hier
        self.values = values or {}
        self.required = required

    def node(self, op, args=(), value=None, expr=None):
        return Node(op, tuple(args), value=value, hier=self.hier,
                    loc=self.module.location(expr))

    def literal(self, expr):
        width, text = str(expr.children[0]).split("'", 1)
        text = text[1:].replace('_', '').upper()
        if len(text) != int(width) or not text or set(text) - set('T01'):
            raise self.module.location(expr).error(
                'trit literal needs exactly its width in T/0/1 digits; x/z are unsupported')
        return [{'T': -1, '0': 0, '1': 1}[d] for d in text]

    def width(self, expr):
        op, c = str(expr.data), expr.children
        if op == 'ref':
            name = identifier(c[0])
            if name in self.env and len(c) == 1:
                return len(digits(self.env[name]))
            return len(self.selected(expr))
        if op == 'trit':
            return len(self.literal(expr))
        if op == 'integer':
            return len(digits(int(c[0])))
        if op == 'concat':
            return sum(self.width(e) for e in c)
        if op in {'shift_left', 'shift_right'}:
            return self.width(c[0])
        if op in {'comparison', 'logical_and', 'logical_or', 'logical_not'}:
            return 1
        if op == 'conditional':
            return max(self.width(c[1]), self.width(c[2]))
        if op == 'call':
            return max(self.width(e) for e in c[1:])
        return max(self.width(e) for e in c)

    def resize(self, nodes, width, expr):
        if width is None:
            return nodes
        return ([self.node('const', value=0, expr=expr)] * max(0, width-len(nodes)) + nodes)[-width:]

    def build(self, expr, context=None):
        op, c = str(expr.data), expr.children
        loc = self.module.location(expr)
        natural = self.width(expr)
        width = max(natural, context or 0)
        make = lambda kind, args=(), value=None: self.node(kind, args, value, expr)
        if op == 'ref':
            name = identifier(c[0])
            if name in self.env and len(c) == 1:
                out = [make('const', value=d) for d in digits(self.env[name])]
            else:
                out = []
                for bit in self.selected(expr):
                    if bit.name in self.required and bit.name not in self.values:
                        raise loc.error(f"read before blocking assignment to {bit.name!r}; would infer a latch")
                    out.append(self.values.get(bit.name) or Node('ref', name=bit.name, loc=loc, hier=self.hier))
        elif op in {'trit', 'integer'}:
            out = [make('const', value=d) for d in
                   (self.literal(expr) if op == 'trit' else digits(int(c[0])))]
        elif op == 'concat':
            out = [n for e in c for n in self.build(e)]
        elif op in {'neg', 'minus', 'plus', 'logical_not'}:
            if op == 'logical_not' and self.width(c[0]) != 1:
                raise loc.error('logical operators require single-trit operands')
            a = self.build(c[0], width if op != 'logical_not' else None)
            out = a if op == 'plus' else [make('neg', [n]) for n in a]
        elif op in {'add', 'sub', 'mul'}:
            a, b = (self.build(e, width) for e in c)
            out = [make(op, a+b, i) for i in reversed(range(width))]
        elif op in {'shift_left', 'shift_right'}:
            # The amount never supplies width to the data or receives its context.
            # Constant integer expressions retain their exact value (1+1 is 2).
            from .elaborate import integer
            from .parser import HDLError
            try:
                amount = integer(c[-1], self.env, self.module)
            except HDLError:
                b = self.build(c[-1])
            else:
                b = [make('const', value=d) for d in digits(amount)]
            a = self.build(c[0], width)
            out = [Node(op, tuple(a+b), value=i, width=width, loc=loc, hier=self.hier)
                   for i in reversed(range(width))]
        elif op in {'div', 'mod'}:
            raise loc.error('signal division / and remainder % are unsupported; integer parameters may use them')
        elif op == 'comparison':
            # Comparisons never truncate an operand to the one-trit result width.
            a, cmp, b = c
            w = max(self.width(a), self.width(b))
            args = self.build(a, w) + self.build(b, w)
            out = [make({'==':'eq', '!=':'ne', '<':'lt', '<=':'le', '>':'gt', '>=':'ge'}[str(cmp)], args)]
        elif op == 'conditional':
            if self.width(c[0]) != 1:
                raise loc.error('conditional requires a single-trit condition')
            cond = self.build(c[0])[0]
            a, b = (self.build(e, width) for e in c[1:])
            out = [make('mux', [cond, x, y]) for x, y in zip(a, b)]
        elif op in {'min_op', 'max_op', 'logical_and', 'logical_or', 'call'}:
            operands = c
            kind = {'min_op':'min', 'max_op':'max', 'logical_and':'min',
                    'logical_or':'max', 'call':'nany'}[op]
            if op == 'call':
                if identifier(c[0]) != 'nany':
                    raise loc.error('only the builtin nany(a, b) function is supported')
                operands = c[1:]
            if op.startswith('logical_') and any(self.width(e) != 1 for e in operands):
                raise loc.error('logical operators require single-trit operands')
            a, b = (self.build(e, width) for e in operands)
            out = [make(kind, [x, y]) for x, y in zip(a, b)]
        else:
            raise loc.error(f'unsupported signal expression {op!r}')
        return self.resize(out, context, expr)
