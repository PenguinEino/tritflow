"""The released notebook's own source pin must not invalidate recorded experiments."""
import re
from pathlib import Path

from cache import notebook_hash

ROOT = Path(__file__).resolve().parents[2]


def test_source_pin_is_excluded_from_the_notebook_identity(tmp_path):
    text = (ROOT/"notebook/tritflow_tr1um.ipynb").read_text()
    pinned = re.sub(r'(TRITFLOW_REF\\", \\")[0-9a-f]{40}', lambda m: m[1]+"b"*40, text)
    assert pinned != text
    (tmp_path/"a.ipynb").write_text(pinned)
    assert notebook_hash(tmp_path/"a.ipynb") == notebook_hash(ROOT/"notebook/tritflow_tr1um.ipynb")
    (tmp_path/"b.ipynb").write_text(pinned.replace("## 1. Three levels", "## 1. Three  levels"))
    assert notebook_hash(tmp_path/"b.ipynb") != notebook_hash(ROOT/"notebook/tritflow_tr1um.ipynb")
