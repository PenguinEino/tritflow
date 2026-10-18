"""Use identical input edges and loads to compare pre/post-layout settling."""
from .bench import simulate


def compare_layout(pre_subckts, post_subckts, top, inputs, outputs, vectors, expected,
                   *, pre_nodeset=None, post_nodeset=None, **kwargs):
    """Return both measurement sets and post-minus-pre delay per output/transition.

    Different extracted pin orders are resolved from their declarations. Unsettled
    transitions keep a None delta rather than reporting a misleading zero.
    """
    vectors = list(vectors)
    pre = simulate(pre_subckts, top, inputs, outputs, vectors, expected,
                   nodeset=pre_nodeset, **kwargs)['measurements']
    post = simulate(post_subckts, top, inputs, outputs, vectors, expected,
                    nodeset=post_nodeset, **kwargs)['measurements']
    rows = []
    for a, b in zip(pre['rows'][1:], post['rows'][1:]):
        delta = {}
        for pin in outputs:
            before, after = a['outputs'][pin]['settling_s'], b['outputs'][pin]['settling_s']
            delta[pin] = None if before is None or after is None else after - before
        rows.append({'input_trits': b['input_trits'], 'previous_trits': b['previous_trits'],
                     'settling_difference_s': delta})
    return {'passed': pre['passed'] and post['passed'], 'pre': pre, 'post': post, 'transitions': rows}
