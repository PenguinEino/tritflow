"""Band entry is the last crossing, including glitches and unresolved tails."""
import numpy as np
import pytest
from tritflow.sim import settling_time, input_vectors, measure_sequence


def test_final_entry_including_overshoot():
    t = np.arange(5.)
    assert settling_time(t, [0, 5, 6, 5, 5], 5, 0, 4) == pytest.approx(2.5)
    assert settling_time(t, [5, 5.5, 5, 5, 5], 5, 0, 4) == 0
    assert settling_time(t, [5, 5, 5, 5, 6], 5, 0, 4) is None
    assert settling_time(t, [0, 0, 0, 0, 0], 0, 1, 4) == 0


def test_incomplete_and_nonfinite_waveform():
    for y in ([0, float('nan'), 5], [0, 5]):
        with pytest.raises(ValueError):
            settling_time([0, 1, 2], y, 5, 0, 2)
    with pytest.raises(ValueError):
        settling_time([0, 1, 2], [0, 5, 5], 5, 0, 3)


@pytest.mark.parametrize('n', [1, 2, 3])
def test_all_directed_transitions_once(n):
    tour = input_vectors(n, transitions=True)
    edges = list(zip(tour, tour[1:]))
    assert len(edges) == (3**n)*(3**n-1)
    assert len(set(edges)) == len(edges)
    assert all(a != b for a, b in edges)
    assert tour[0] == tour[-1]
    assert len(set(tour)) == 3**n
    with pytest.raises(ValueError):
        input_vectors(6, transitions=True)


def test_checkpoint_and_tail_are_separate():
    time = np.array([0, 5, 9, 9.5, 10])*1e-9
    data = {'time': time, 'v(y)': np.array([0, 0, 0, 2, 2])}
    data.update({f'i({r})': np.zeros(5) for r in ['vdd','vmid','vss']})
    bench = dict(vectors=[(0,)], outputs=['y'], hold_s=10e-9, step_s=0.5e-9)
    result = measure_sequence(data, bench, lambda _: {'y': 0})
    assert result['rows'][0]['outputs']['y']['passed']
    assert not result['passed']  # glitch after checkpoint fails hold-band requirement
    assert result['unsettled'] == 1


def test_decimal_output_roundoff_at_final_time():
    end = 3*(2000*1e-9)
    assert settling_time([0,6e-6],[5,5],5,0,end)==0
    with pytest.raises(ValueError):settling_time([0,5.99e-6],[5,5],5,0,end)
