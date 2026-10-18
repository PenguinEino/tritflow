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
    assert source.count('details_html(') >= 4
    assert 'truth_table_html(custom' in source and 'truth_table_html(fa.design)' in source
    assert "TODO SIM" not in source and "TODO CELLS" not in source
    assert "TRITFLOW_FORCE_RUN" in source
    assert "device_mapping" in source and "ordered-pair/orientation abutments" in source
    author = (ROOT/"docs/author.md").read_text()
    block = author[author.index("- Name:"):].split("\n\n",1)[0]
    assert block in document["cells"][0]["source"]


def test_colab_note_matches_the_latest_published_verification():
    import json
    document=json.loads((ROOT/"notebook/tritflow_tr1um.ipynb").read_text())
    intro=document["cells"][0]["source"]
    record=json.loads((ROOT/"notebook/colab_verified.json").read_text())
    assert record["commit"].startswith("91f642d") and record["passed_code_cells"] == 34
    report=(ROOT/record["report"]).read_text()
    assert record["passed"] is True and record["commit"] in report
    assert f'{record["run_all_seconds_including_setup"]:.1f} s' in report
    assert record["publish"] is True and record['first_attempt_completed'] is True
    assert record['run_all_attempts'] == 1
    assert record["commit"][:7] in intro and 'including setup' in intro
    assert 'If Run all stops after setup, choose Run all again.' in intro
    assert all(text not in intro for text in ("Run all ≈", "384.1 s", "842afe2"))
    assert intro.count('top-level HDL lines') == 1
    assert all(text not in intro for text in ("Release TODO","predates","unverified","content-keyed","TRITFLOW_FORCE_RUN"))
    appendix=next(c["source"] for c in document["cells"] if c["source"].startswith("## Appendix B."))
    assert "TRITFLOW_REF" in appendix and "TRITFLOW_FORCE_RUN" in appendix
    assert "recorded" in appendix and "842afe2" not in appendix
