"""One independently rebuilt compact library for the CELLS qualification suite."""
import pytest
from tritflow.cells.layout import build
from tritflow.cells.verify import verify


@pytest.fixture(scope='session')
def library(tmp_path_factory):
    out=tmp_path_factory.mktemp('cells')
    manifest=build(out)
    report=verify(out)
    return out,manifest,report
