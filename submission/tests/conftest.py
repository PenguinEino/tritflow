"""Keep test caches and temporary evidence inside the SUBMIT-owned directory."""
import os
from pathlib import Path
import sys
import tempfile

BUILD = Path(__file__).resolve().parents[1]/'.build/tests'
BUILD.mkdir(parents=True, exist_ok=True)
os.environ['TMPDIR'] = str(BUILD)
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True
tempfile.tempdir = str(BUILD)


def pytest_configure(config):
    config.option.basetemp = str(BUILD/'temporary')
