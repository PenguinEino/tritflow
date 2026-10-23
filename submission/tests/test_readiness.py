"""The final gate cannot be changed by an edited manifest or a reused result."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('readiness_builder', ROOT/'submission/build_submission.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_readiness_is_pure_and_dirty_execution_remains_a_preview():
    record = {'release':{'compatible':True},
              'results':{'source_ref':'a'*40, 'runtime_commit':'a'*40,
                         'tracked_working_changes_at_execution':['notebook/views.py'],
                         'untracked_runtime_sources_at_execution':['notebook/new_view.py']},
              'evaluation':{'executed_cell_ids':['evaluation'], 'tables':[{'rows':[['Measured'], ['17']]}]}}
    records = {'tritflow_en.ipynb':record, 'tritflow_ja.ipynb':deepcopy(record)}
    before = deepcopy(records)
    first = builder.readiness(records)
    assert first == builder.readiness(records) and records == before
    assert all('unpublished changes' in note for note in first)


def test_final_check_refuses_a_preview_without_changing_payload():
    folder = builder.DESTINATION
    before = builder.digest(folder/'build-info.json')
    info = builder.check(folder)
    if info['submission_ready']:
        pytest.skip('The actual package has already been finalized by its owners')
    with pytest.raises(ValueError, match='final submission gate'):
        builder.main(['--check', '--require-final'])
    assert builder.digest(folder/'build-info.json') == before
