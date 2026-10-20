"""Signed ternary shifter: constant wiring leaves selected by amount trits.

Shannon expansion selects the *total* displacement before dropping digits.
Cascading opposite-direction digit shifts would lose information: amount
2 = 3 - 1 must shift by two, not truncate a shift by three and then shift back.
Branches whose entire remaining amount range overshifts the bus share zero.
"""


def shift_vector(worker, node):
    """Map a context-sized vector to MUX3s; a fixed amount needs no logic."""
    data = tuple(worker.visit(n) for n in node.args[:node.width])
    amount = tuple(worker.visit(n) for n in node.args[node.width:])
    zero = worker.const(0)
    zeros = (zero,) * node.width
    direction = 1 if node.op == 'shift_left' else -1
    cache = {}

    def choose(index, displacement):
        remaining = (3**(len(amount)-index)-1)//2
        if displacement-remaining >= node.width or displacement+remaining <= -node.width:
            return zeros
        if index == len(amount):
            # Data is MSB first; a positive displacement moves toward the MSB.
            return tuple(data[i+displacement] if 0 <= i+displacement < node.width else zero
                         for i in range(node.width))
        key = index, displacement
        if key not in cache:
            weight = direction * 3**(len(amount)-index-1)
            selector = amount[index]
            if selector.op == 'const':
                result = choose(index+1, displacement+selector.value*weight)
            else:
                arms = [choose(index+1, displacement+d*weight) for d in (-1, 0, 1)]
                result = tuple(worker.mux3(selector, *digits) for digits in zip(*arms))
            cache[key] = result
        return cache[key]

    return choose(0, 0)
