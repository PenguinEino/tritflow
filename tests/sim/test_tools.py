"""The evidence runner must not silently pick a different ngspice release."""

from pathlib import Path
import pytest
from tritflow.sim.tools import ngspice_binary


@pytest.mark.parametrize("version", ["41", "42+", "46", "46+", "47"])
def test_unqualified_version_is_rejected(tmp_path, version):
    binary = tmp_path/"ngspice"
    binary.write_text(f'#!/bin/sh\necho "ngspice-{version} : test"\n')
    binary.chmod(0o755)
    with pytest.raises(RuntimeError, match="requires Ubuntu ngspice-42"):
        ngspice_binary(str(binary))


def test_environment_selects_absolute_release_without_path_search(tmp_path, monkeypatch):
    binary = tmp_path/"ngspice"
    binary.write_text('#!/bin/sh\necho "ngspice-42 : test"\n')
    binary.chmod(0o755)
    monkeypatch.setenv("NGSPICE_BINARY",str(binary))
    monkeypatch.setenv("PATH","")
    assert ngspice_binary() == str(binary)
    monkeypatch.setenv("NGSPICE_BINARY","ngspice")
    with pytest.raises(RuntimeError, match="Pinned Ubuntu ngspice-42 is missing"):
        ngspice_binary()
