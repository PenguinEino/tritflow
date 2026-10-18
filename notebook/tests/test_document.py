"""The submission draft is a reproducible, executable Python notebook document."""

import importlib.util
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("tritflow_notebook_validation", ROOT/"notebook/validate_notebook.py")
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


def test_notebook_chapters_code_and_generator_reproducibility():
    path = ROOT/"notebook/tritflow_tr1um.ipynb"
    before = path.read_bytes()
    document = validation.validate(path)
    assert "lay.extract()" in "\n".join(c["source"] for c in document["cells"])
    subprocess.run([sys.executable, str(ROOT/"notebook/make_notebook.py")], check=True)
    assert path.read_bytes() == before
