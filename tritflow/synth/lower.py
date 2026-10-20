"""Lower integer operators and arbitrary selections to the ternary cell basis.

Addition uses the reference five-NANY/two-INV half adder and two-half-adder
full adder. Multiplication forms one-trit products and shifted ripple sums.
Unary closure supplies all 27 one-input functions. Its crisp literal detectors
make a Shannon MUX3, so a complete case table can describe any finite function.
The closure cost is a tree estimate; these networks are not claimed minimal.
"""

from dataclasses import replace
from functools import lru_cache
from itertools import product

from tritflow.hdl.ir import Design, Node
from tritflow.hdl.semantics import EXTENDED


@lru_cache(maxsize=1)
def unary_networks():
    """Deterministically find a cell-basis expression for each unary truth table."""
    best = {(-1, 0, 1): (0, ('input',))}
    for value in (-1, 0, 1):
        best[(value,)*3] = (1, ('const', value))

    def offer(table, cost, expr):
        if table not in best or cost < best[table][0]:
            best[table] = cost, expr
            return True
        return False

    changed = True
    while changed:
        changed = False
        entries = list(best.items())
        for a, (ac, ae) in entries:
            changed |= offer(tuple(-x for x in a), ac+1, ('neg', ae))
        for (a, (ac, ae)), (b, (bc, be)) in product(entries, repeat=2):
            for op in ('nany', 'nand', 'nor'):
                table = tuple(-max(-1, min(1, x+y)) if op == 'nany' else
                              -min(x, y) if op == 'nand' else -max(x, y)
                              for x, y in zip(a, b))
                changed |= offer(table, ac+bc+1, (op, ae, be))
    if len(best) != 27:
        raise RuntimeError('ternary library closure did not reach all 27 unary functions')
    return {table: expr for table, (_, expr) in best.items()}


class Lowerer:
    def __init__(self):
        self.cache, self.vectors, self.unaries = {}, {}, {}
        self.source = None

    def make(self, op, *args, value=None):
        return Node(op, tuple(args), value=value, hier=self.source.hier, loc=self.source.loc)

    def const(self, value):
        return self.make('const', value=value)

    def neg(self, a):
        if a.op == 'const':
            return self.const(-a.value)
        return self.make('neg', a)

    @staticmethod
    def zero(a):
        return a.op == 'const' and a.value == 0

    def sat(self, a, b):
        return self.neg(self.make('nany', a, b))

    def half(self, a, b):
        if self.zero(a):
            return b, self.const(0)
        if self.zero(b):
            return a, self.const(0)
        if a.op == 'const' or b.op == 'const':
            fixed, variable = (a, b) if a.op == 'const' else (b, a)
            # For x+1, carry=max(x,0); for x-1, carry=min(x,0).
            # Share this shorter carry path with the reference sum network.
            carry = self.make('max' if fixed.value == 1 else 'min', variable, self.const(0))
            t = self.make('nany', variable, fixed)
            d = self.make('nany', t, carry)
            return self.make('nany', self.neg(d), carry), carry
        t = self.make('nany', a, b)
        u = self.make('nany', b, t)
        carry = self.make('nany', self.neg(a), u)
        d = self.make('nany', t, carry)
        return self.make('nany', self.neg(d), carry), carry

    def full(self, a, b, c):
        if self.zero(c):
            return self.half(a, b)
        if self.zero(a):
            return self.half(b, c)
        if self.zero(b):
            return self.half(a, c)
        s, c1 = self.half(a, b)
        result, c2 = self.half(s, c)
        return result, self.sat(c1, c2)

    def add(self, a, b, c=None):
        """Ripple LSB to MSB; discard the carry beyond the context width."""
        carry, out = self.const(0), []
        for i in reversed(range(len(a))):
            if c is None:
                digit, carry = self.full(a[i], b[i], carry)
            else:
                # Three operands may produce two carry contributions per column.
                s, c1 = self.full(a[i], b[i], c[i])
                digit, c2 = self.half(s, carry)
                carry = self.sat(c1, c2)
            out.append(digit)
        return list(reversed(out))

    def product_digit(self, a, b):
        if a.op == 'const':
            return self.const(0) if a.value == 0 else b if a.value == 1 else self.neg(b)
        if b.op == 'const':
            return self.product_digit(b, a)
        # The taped-out MUL: NAND(a,b), NOR(a,b), INV, NAND.
        t1 = self.neg(self.make('min', a, b))
        t2 = self.neg(self.make('max', a, b))
        return self.neg(self.make('min', t1, self.neg(t2)))

    def unary(self, table, a):
        if a.op == 'const':
            return self.const(table[a.value+1])
        key = table, a
        if key in self.unaries:
            return self.unaries[key]

        def build(expr):
            op = expr[0]
            if op == 'input':
                return a
            if op == 'const':
                return self.const(expr[1])
            args = [build(e) for e in expr[1:]]
            if op == 'neg':
                return self.neg(args[0])
            if op in {'nand', 'nor'}:
                return self.neg(self.make('min' if op == 'nand' else 'max', *args))
            return self.make(op, *args)

        result = build(unary_networks()[table])
        self.unaries[key] = result
        return result

    def mux3(self, selector, minus, zero, plus):
        """Ternary Shannon expansion with crisp +/-1 literal indicators."""
        if minus is zero and zero is plus:
            return minus
        branches = []
        for index, branch in enumerate((minus, zero, plus)):
            table = tuple(1 if i == index else -1 for i in range(3))
            branches.append(self.make('min', self.unary(table, selector), branch))
        return self.make('max', self.make('max', branches[0], branches[1]), branches[2])

    def select(self, condition, yes, no):
        """Select on a crisp comparison output (+1/-1), requiring no middle arm."""
        if yes is no:
            return yes
        return self.make('max', self.make('min', condition, yes),
                         self.make('min', self.neg(condition), no))

    def arithmetic(self, node):
        key = node.op, node.args
        if key in self.vectors:
            return self.vectors[key]
        width = len(node.args)//2
        left, right = node.args[:width], node.args[width:]
        # Fuse (a+b)+c before mapping so the scalar full-adder idiom is the
        # verified full adder, rather than two independently truncated sums.
        chain = (node.op == 'add' and all(n.op == 'add' for n in left)
                 and len(left[0].args) == 2*width
                 and all(n.args == left[0].args and n.value == width-1-i
                         for i, n in enumerate(left)))
        if chain:
            inner = left[0].args
            a = [self.visit(n) for n in inner[:width]]
            b = [self.visit(n) for n in inner[width:]]
            c = [self.visit(n) for n in right]
            result = self.add(a, b, c)
        else:
            a, b = ([self.visit(n) for n in operand] for operand in (left, right))
            if node.op in {'add', 'sub'}:
                result = self.add(a, b if node.op == 'add' else [self.neg(n) for n in b])
            else:
                result = [self.const(0) for _ in range(width)]
                for shift, digit in enumerate(reversed(b)):
                    if self.zero(digit):
                        continue
                    row = [self.product_digit(n, digit) for n in a[shift:]]
                    row += [self.const(0) for _ in range(shift)]
                    result = self.add(result, row)
        self.vectors[key] = result
        return result

    def visit(self, node):
        if node in self.cache:
            return self.cache[node]
        previous = self.source
        self.source = node
        if node.primitive:
            # BUF/NAND/NOR have private functional helper nodes. Lower their
            # pins, retaining those helpers so primitive_inputs stays valid.
            from .optimize import primitive_inputs, primitive_node
            pins = primitive_inputs(node)
            args = tuple(self.visit(n) for n in pins)
            result = node if args == pins else primitive_node(node, args)
        elif node.op in {'add', 'sub', 'mul'}:
            result = self.arithmetic(node)[-1-node.value]
        elif node.op in {'shift_left', 'shift_right'}:
            from .shifts import shift_vector
            key = node.op, node.args, node.width
            if key not in self.vectors:
                self.vectors[key] = shift_vector(self, node)
            result = self.vectors[key][-1-node.value]
        else:
            args = tuple(self.visit(n) for n in node.args)
            if node.op == 'select':
                result = self.select(*args)
            elif node.op == 'mux':
                c, a, b = args
                # At c=0 preserve an agreed trit, otherwise return 0: median(a,b,0).
                consensus = self.make('min', self.make('max', self.make('min', a, b), self.const(0)),
                                      self.make('max', a, b))
                result = self.mux3(c, b, consensus, a)
            elif node.op == 'is_true':
                result = self.unary((-1, -1, 1), args[0])
            elif node.op in {'eq', 'ne'}:
                width = len(args)//2
                result = self.const(1)
                for a, b in zip(args[:width], args[width:]):
                    if b.op == 'const':
                        table = tuple(1 if d == b.value else -1 for d in (-1, 0, 1))
                        equal = self.unary(table, a)
                    elif a.op == 'const':
                        table = tuple(1 if d == a.value else -1 for d in (-1, 0, 1))
                        equal = self.unary(table, b)
                    else:
                        equal = self.unary((-1, 1, -1), self.sat(a, self.neg(b)))
                    result = self.make('min', result, equal)
                if node.op == 'ne':
                    result = self.neg(result)
            elif node.op in {'lt', 'le', 'gt', 'ge'}:
                width = len(args)//2
                sign = self.const(0)
                for a, b in zip(args[:width], args[width:]):
                    low = self.sat(a, self.neg(b))
                    sign = self.sat(sign, self.sat(sign, low))
                tables = {'lt':(1,-1,-1),
                          'le':(1,1,-1), 'gt':(-1,-1,1), 'ge':(-1,1,1)}
                result = self.unary(tables[node.op], sign)
            elif node.op == 'neg' and not node.primitive and args[0].op == 'const':
                result = self.const(-args[0].value)
            else:
                result = node if args == node.args else replace(node, args=args)
        self.source = previous
        self.cache[node] = result
        return result


def lower(design: Design) -> Design:
    """Leave legacy DAGs untouched; expand new operations before local rewriting."""
    if not any(n.op in EXTENDED for n in design.nodes):
        return design
    worker = Lowerer()
    return Design(design.top, design.ports, {k: worker.visit(n) for k, n in design.outputs.items()},
                  design.inputs, design.params.copy())
