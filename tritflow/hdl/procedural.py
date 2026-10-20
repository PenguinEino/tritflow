"""Turn blocking combinational statements into a definite-assignment SSA DAG.

Each branch has its own current-value map. Joining two branches inserts selects
only for definitely assigned bits; missing values cannot silently become storage.
Procedural if treats only +1 as true; the unknown trit takes the else branch.
"""

from .ir import Design, Node, reachable


def elaborate_block(elaborator, block, scope, env, module, hier):
    statement = block.children[0]
    written = {}

    def collect(stmt):
        if stmt.data == 'blocking':
            for bit in elaborator.targets(stmt.children[0], scope, env, module):
                written[bit.name] = bit
        else:
            for child in stmt.children:
                if hasattr(child, 'data'):
                    collect(child)

    collect(statement)

    def node(op, args, stmt):
        return Node(op, tuple(args), loc=module.location(stmt), hier=hier)

    def expression(expr, state, width=None):
        return elaborator.expression(expr, scope, env, module, hier, width, state, written)

    def merge(cond, yes, no, stmt):
        return {key: yes[key] if yes[key] is no[key] else node('select', [cond, yes[key], no[key]], stmt)
                for key in yes if key in no}

    def constants(values):
        if any(n.op in {'input', 'ref'} for n in reachable(values)):
            return None
        outputs = {str(i):n for i,n in enumerate(values)}
        result = Design('constant', [], outputs, {}).evaluate({})
        return tuple(int(result[str(i)]) for i in range(len(values)))

    def execute(stmt, state):
        state = state.copy()
        kind, c = str(stmt.data), stmt.children
        if kind == 'blocking':
            targets = elaborator.targets(c[0], scope, env, module)
            rhs = expression(c[1], state, len(targets))
            state.update((b.name, n) for b, n in zip(targets, rhs))
        elif kind == 'block':
            for child in c:
                state = execute(child, state)
        elif kind == 'if_stmt':
            cond = expression(c[0], state)
            if len(cond) != 1:
                raise module.location(c[0]).error('if requires a single-trit condition')
            fixed = constants(cond)
            if fixed is not None:
                if fixed[0] == 1:
                    return execute(c[1], state)
                return execute(c[2], state) if len(c) == 3 else state
            cond = node('is_true', cond, stmt)
            yes = execute(c[1], state)
            no = execute(c[2], state) if len(c) == 3 else state
            state = merge(cond, yes, no, stmt)
        elif kind == 'case_stmt':
            selector = expression(c[0], state)
            width = len(selector)
            seen, cases, default = set(), [], None
            for item in c[1:]:
                if item.data == 'default_case':
                    if default is not None:
                        raise module.location(item).error('duplicate default case item')
                    default = execute(item.children[0], state)
                    continue
                tests = []
                for label in item.children[:-1]:
                    values = expression(label, {}, width)
                    key = constants(values)
                    if key is None:
                        raise module.location(label).error('case labels must be constant trit/integer values')
                    values = [Node('const', value=d, loc=module.location(label), hier=hier) for d in key]
                    if key in seen:
                        raise module.location(label).error('duplicate case label after width conversion')
                    seen.add(key)
                    tests.append(node('eq', selector + values, item))
                cond = tests[0]
                for test in tests[1:]:
                    cond = node('max', [cond, test], item)
                cases.append((cond, execute(item.children[-1], state), item))
            # A fully enumerated table needs no default or fictitious latch path.
            if default is None and len(seen) == 3**width and cases:
                _, default, _ = cases.pop()
            result = default if default is not None else state
            for cond, branch, item in reversed(cases):
                result = merge(cond, branch, result, item)
            state = result
        elif kind != 'empty_stmt':
            raise module.location(stmt).error(f'unsupported procedural syntax: {kind} (use blocking = in always @*)')
        return state

    result = execute(statement, {})
    missing = set(written) - set(result)
    if missing:
        raise module.location(block).error(
            'incomplete combinational assignment would infer a latch: ' + ', '.join(sorted(missing)))
    elaborator.drive(list(written.values()), [result[k] for k in written], module.location(block))
