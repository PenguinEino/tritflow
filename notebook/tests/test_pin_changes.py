"""A changed result must not disappear when a producer adds/removes a metric."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('pin_changes', Path(__file__).parents[1]/'pin_changes.py')
changes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changes)


def test_failed_or_missing_delays_are_not_zero_delay_measurements():
    rows = list(changes.differences({'settling_s':1e-9, 'passed':True},
                                    {'settling_s':None, 'passed':False}))
    assert {r['path'] for r in rows} == {'/settling_s','/passed'}
    assert all(r['delta'] is None for r in rows)


def test_added_removed_metrics_and_vector_tail_remain_visible():
    rows = list(changes.differences({'old_metric':2.,'rows':[1.,2.],'waveforms':[4.]},
                                    {'new_metric':3.,'rows':[1.],'waveforms':[8.]}))
    by_path = {r['path']:r for r in rows}
    assert by_path['/old_metric']['kind'] == 'removed'
    assert by_path['/new_metric']['kind'] == 'added'
    assert by_path['/rows/1']['before'] == 2.
    assert by_path['/rows/length']['after'] == 1
    assert '/waveforms/0' not in by_path
