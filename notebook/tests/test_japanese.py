"""Japanese reading path, cell-basis proof and shared executable structure."""

from itertools import product
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "notebook"))
from completeness import (TRITS, inv, nand, nor, nany, unary_closure,
                          surjective_and_depends_on_both)
from editorial import context, render, TOKEN
from localization import localize_source, localize_svg, localize_html
from make_notebook import build
from validate_notebook import validate


def test_cell_basis_closes_exact_unary_functions_and_slupecki_premise():
    complete = unary_closure(binary=(nany,), constants=(-1, 1))
    zero = unary_closure(binary=(nany,), constants=(0,))
    minmax = unary_closure(unary=(inv,), binary=(nand, nor), constants=TRITS)
    assert complete == set(product(TRITS, repeat=3))
    assert zero == {TRITS, (0, 0, 0), (1, 0, -1)}
    assert len(minmax) == 11 and (0, 1, 0) not in minmax
    assert surjective_and_depends_on_both(nany)
    assert not surjective_and_depends_on_both(lambda a, b: a)
    assert not surjective_and_depends_on_both(lambda a, b: int(a == b))
    assert all(nany(-a, -b) == -nany(a, b) for a, b in product(TRITS, repeat=2))


def test_completeness_then_synthesis_cells_keep_display_helper_callable():
    import methods
    from tritflow import flow
    namespace = {"flow": flow, "ROOT": ROOT, "display_label": lambda text: text, "step": print,
                 "display": lambda value: None,
                 "value_selector": lambda net, **kwargs: kwargs}
    exec(methods.COMPLETENESS, namespace)
    namespace["fa"] = flow.load(ROOT / "examples/full_add.tv", "full_add")
    exec(methods.SYNTHESIS, namespace)
    assert callable(namespace["display_label"])
    assert namespace["half_counts"] == {"NANY": 5, "INV": 2}


def test_japanese_build_is_complete_unexecuted_and_language_option_is_repeatable():
    path = ROOT / "notebook/tritflow_tr1um_ja.ipynb"
    before = path.read_bytes()
    doc = validate(path)
    subprocess.run([sys.executable, str(ROOT / "notebook/make_notebook.py"),
                    "--language", "ja"], check=True)
    assert path.read_bytes() == before
    assert doc["metadata"]["tritflow_editorial"]["language"] == "ja"
    assert doc["metadata"]["colab"]["name"] == path.name
    cells = {c["id"]: c for c in doc["cells"]}
    order = list(cells)
    assert order.index("opening") < order.index("method-gds") < order.index("method-gates")
    assert order.index("method-completeness") < order.index("completeness") < order.index("method-sizing")
    assert order.index("custom_check") < order.index("method-custom_layout")
    assert "half_counts" in cells["method-completeness"]["source"]
    for c in doc["cells"]:
        if c["cell_type"] == "code" and c["source"].startswith("#@title"):
            assert re.search(r"[\u3040-\u9fff]", c["source"].splitlines()[0])
        if c["cell_type"] == "code" and c["id"].startswith("method-"):
            assert len(c["source"].strip().splitlines()) <= 16
    english = build("en")
    assert [c["id"] for c in english["cells"] if c["cell_type"] == "code"] == [
        c["id"] for c in doc["cells"] if c["cell_type"] == "code"]
    with pytest.raises(ValueError, match="Unsupported"):
        build("invalid")


def test_japanese_story_has_resolved_measurements_and_single_historical_colab_record():
    doc = json.loads((ROOT / "notebook/tritflow_tr1um_ja.ipynb").read_text())
    intro = re.sub(r'<img\b[^>]*>', '', doc["cells"][0]["source"])
    assert "mW" not in intro and "0.4 W" not in intro
    assert "実測はまだありません" in intro and "採択された場合" in intro
    record = json.loads((ROOT / "notebook/colab_verified.json").read_text())
    markdown = "\n".join(c["source"] for c in doc["cells"] if c["cell_type"] == "markdown")
    assert "世界初" not in markdown and "初めて" not in markdown
    minutes = max(1, round(record["run_all_seconds_including_setup"] / 60))
    assert f"約{minutes}分" in intro
    assert "## 付録A." in markdown and "## 付録C." in markdown
    assert not TOKEN.search(markdown)
    assert markdown.count("すべてのセルを実行」を選んでください") == 1   # one run note, in the intro
    for removed in ("generate", "まだありません。セットアップ", "submission_ready"):
        assert removed not in markdown
    author = (ROOT / "docs/author.md").read_text()
    block = author[author.index("- Name:"):].split("\n\n", 1)[0]
    assert block in intro
    values = context(ROOT)
    for path in (ROOT / "notebook/narrative_ja").glob("*.md"):
        if path.name == "08_your_circuit.md":
            continue  # runtime output, resolved after the edited circuit runs
        assert not TOKEN.search(render(path.read_text(), values)), path


def test_translation_preserves_expressions_identifiers_hdl_and_svg_geometry():
    source = 'value = "Output"\n# Output\nprint(f"Output {data[\"output\"]}")\n'
    translated = localize_source(source, {"Output": "出力"})
    assert 'value = "出力"' in translated and '# Output' in translated
    assert 'data["output"]' in translated
    compile(translated, "localized", "exec")
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M 0 0"/><text>Cells 64</text><text style="font-family:monospace">Cells</text></svg>'
    translated = localize_svg(svg, {"Cells": "セル"})
    assert 'd="M 0 0"' in translated and 'セル 64' in translated
    assert '>Cells</text>' in translated
    html = '<div>Output</div><script>let Output = 1;</script><img src="data:image/png;base64,Output"><pre>Output</pre>'
    translated = localize_html(html, {"Output": "出力"})
    assert '<div>出力</div>' in translated
    assert '<script>let Output = 1;</script>' in translated
    assert 'base64,Output' in translated and '<pre>Output</pre>' in translated


def test_japanese_progress_lines_are_translated():
    """Every visible progress line names its work in Japanese."""
    doc = json.loads((ROOT / "notebook/tritflow_tr1um_ja.ipynb").read_text())
    source = "\n".join(c["source"] for c in doc["cells"] if c["cell_type"] == "code")
    messages = re.findall(r'step\(f?"([^"]*)"', source)
    assert len(messages) >= 30
    for message in messages:
        assert re.search(r"[぀-鿿]", message), message
