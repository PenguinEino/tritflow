"""Both v3 editions must build reproducibly and keep their runtime assets."""

import importlib.util
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("tritflow_notebook_validation", ROOT / "notebook/validate_notebook.py")
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


@pytest.mark.parametrize("language", ["en", "ja"])
def test_notebook_chapters_code_and_generator_reproducibility(language, tmp_path):
    path = ROOT / "notebook/v3" / f"tritflow_{language}.ipynb"
    document = validation.validate(path)
    code = "\n".join("".join(cell["source"]) for cell in document["cells"] if cell["cell_type"] == "code")
    assert "dot4_layout.extract()" in code and "dot4_extracted.simulate(" in code
    ref = re.search(r'SOURCE_REF = os.environ.get\("TRITFLOW_REF", "([0-9a-f]{40})"\)', code)[1]
    output = tmp_path / path.name
    subprocess.run([sys.executable, str(ROOT / "notebook/v3/make_notebook.py"),
                    "--lang", language, "--ref", ref, "--out", str(output)], check=True)
    assert output.read_bytes() == path.read_bytes()
    for cell in document["cells"]:
        if cell["cell_type"] == "markdown":
            text = "".join(cell["source"])
            for asset in re.findall(rf"(?:/{ref}/|@{ref}/)([^\s\"<>\)]+\.(?:png|svg))", text):
                assert (ROOT / asset).is_file(), asset
