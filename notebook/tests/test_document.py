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


def test_truth_tables_are_rendered_as_html_and_required_results_have_no_todo_fallback():
    import json
    document = json.loads((ROOT/"notebook/tritflow_tr1um.ipynb").read_text())
    source = "\n".join(c["source"] for c in document["cells"] if c["cell_type"] == "code")
    assert "display(truth_table_html" not in source
    assert source.count("display(HTML(truth_table_html") == 4
    assert "TODO SIM" not in source and "TODO CELLS" not in source
    assert "TRITFLOW_FORCE_RUN" in source
    assert "cell_figure" in source and "device_mapping" in source and "row_abutment" in source
    author = (ROOT/"docs/author.md").read_text()
    block = author[author.index("- Name:"):].split("\n\n",1)[0]
    assert block in document["cells"][0]["source"]
