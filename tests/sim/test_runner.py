from pathlib import Path
import shutil
import numpy as np
import pytest
from tritflow.sim import run_ngspice, read_ascii_raw, SimulationError


def test_ascii_raw(tmp_path):
    raw = tmp_path/'data.raw'
    raw.write_text('Title: test\nFlags: real\nNo. Variables: 2\nNo. Points: 2\n'
                   'Variables:\n0 time time\n1 v(y) voltage\nValues:\n0 0.0\n 5.0\n1 1e-9\n -5.0\n')
    result = read_ascii_raw(raw)
    np.testing.assert_equal(result['v(y)'], [5, -5])
    raw.write_text(raw.read_text().replace('-5.0', 'nan'))
    with pytest.raises(SimulationError): read_ascii_raw(raw)


@pytest.mark.skipif(not shutil.which('ngspice'), reason='ngspice required')
def test_batch_runner_real_waveforms_and_failure(tmp_path):
    good = 'RC check\nV1 a 0 5\nR1 a y 1k\nC1 y 0 1p\n'
    result = run_ngspice(good, 'tran 0.1n 10n\nset filetype=ascii\nwrite real.raw v(y)', ['v(y)', 'i(v1)'], workdir=tmp_path)
    assert result['data']['v(y)'][-1] == pytest.approx(5)
    assert (tmp_path/'ngspice.log').exists()
    raw = read_ascii_raw(tmp_path/'real.raw')
    np.testing.assert_allclose(raw['v(y)'], result['data']['v(y)'])
    # ngspice sometimes returns zero even when a requested vector is missing.
    with pytest.raises(SimulationError):
        run_ngspice(good, 'tran 0.1n 10n', ['v(absent)'], workdir=tmp_path)
    with pytest.raises(SimulationError):
        run_ngspice('bad deck\nX1 a b MISSING\n', 'op', ['v(a)'])


def test_timeout_and_missing_executable(tmp_path):
    fake = tmp_path/'fake'
    fake.write_text('#!/usr/bin/python3\nimport sys\nif "-v" in sys.argv:\n'
                    ' print("ngspice-42 : fixture");sys.exit(0)\nwhile True: pass\n'); fake.chmod(0o755)
    with pytest.raises(SimulationError, match='timeout'):
        run_ngspice('dummy', 'op', ['v(y)'], executable=str(fake), timeout=.05)
    with pytest.raises(RuntimeError, match='Pinned Ubuntu ngspice-42 is missing'):
        run_ngspice('dummy', 'op', ['v(y)'], executable=str(tmp_path/'missing'))
