"""Language selection must preserve circuits, analysis settings and the Japanese reading path."""

import ast
import importlib.util
from io import StringIO
from pathlib import Path
import re
import sys
import tokenize

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
spec = importlib.util.spec_from_file_location("v3_builder", HERE/"make_notebook.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

import live
import views

CJK = re.compile(r"[ぁ-んァ-ヶ一-龠]")


@pytest.fixture(autouse=True)
def japanese_default():
    live.set_language("ja")
    yield
    live.set_language("ja")


def executable_tokens(source):
    prose = {tokenize.STRING, tokenize.COMMENT, tokenize.FSTRING_MIDDLE}
    return [(t.type, t.string) for t in tokenize.generate_tokens(StringIO(source).readline)
            if t.type not in prose]


def circuit_literals(source):
    """Keep HDL bodies and dictionary lookups: neither is presentation prose."""
    nodes = ast.walk(ast.parse(source))
    return [n.value for n in nodes if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and "\nmodule " in n.value] + [
                n.slice.value for n in ast.walk(ast.parse(source))
                if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
                and isinstance(n.slice.value, str)]


@pytest.mark.parametrize("name", builder.CODE)
def test_translation_preserves_circuit_and_analysis_tokens(name):
    japanese = builder.CODE[name]
    english = builder.code_source(japanese, "en")
    compile(english, name, "exec")
    assert executable_tokens(japanese) == executable_tokens(english)
    assert circuit_literals(japanese) == circuit_literals(english)
    assert not CJK.search(english)


def test_both_editions_have_the_same_cell_structure_and_local_assets():
    japanese = builder.cells("PIN", "ja")
    english = builder.cells("PIN", "en")
    assert [kind for kind, _ in japanese] == [kind for kind, _ in english]
    assert builder.cells("PIN") == japanese
    for kind, source in english:
        if kind == "code":
            compile(source, "English cell", "exec")
            assert not CJK.search(source)
        else:
            # Keep the author's exact name and the original titles of Japanese references.
            prose = source.split("### References", 1)[0].replace("岡崎 英之介", "")
            assert not CJK.search(prose)
            for path in re.findall(r"/PIN/(.*?\.png)", source):
                assert (builder.ROOT/path).is_file(), path
            for path in re.findall(r"@PIN/([^\"]+\.svg)", source):
                assert (builder.ROOT/path).is_file(), path
    setup = next(source for kind, source in english if kind == "code")
    assert 'set_notebook_language("en")' in setup
    assert 'set_language("en")' in setup
    assert 'TRITFLOW_NOTEBOOK_LANGUAGE"] = "en"' in setup


def test_colab_entry_point_and_original_bibliography_are_preserved():
    opening = (HERE/"narrative_en/00_opening.md").read_text()
    assert "blob/notebook-v3/notebook/v3/tritflow_en.ipynb" in opening
    assert "Run all takes 6 to 8 minutes on a fresh Colab runtime, including setup." in opening
    japanese = (HERE/"narrative/06_results.md").read_text().split("### 参考文献\n\n", 1)[1]
    english = (HERE/"narrative_en/06_results.md").read_text().split("### References\n\n", 1)[1]
    without_link_labels = lambda text: re.sub(r"\[[^\]]+\]\(([^)]+)\)", r"[](\1)", text)
    assert without_link_labels(japanese) == without_link_labels(english)


@pytest.mark.parametrize("name", builder.CHAPTERS)
def test_narrative_keeps_equations_and_cell_figure_directives(name):
    japanese = (HERE/"narrative"/name).read_text()
    english = (HERE/"narrative_en"/name).read_text()
    assert re.findall(r"<!--.*?-->", japanese) == re.findall(r"<!--.*?-->", english)
    assert re.findall(r"\$.*?\$", japanese, re.S) == re.findall(r"\$.*?\$", english, re.S)


def test_new_untranslated_code_is_reported_and_invalid_language_is_rejected():
    with pytest.raises(ValueError, match="Missing English"):
        builder.code_source('note("未翻訳")', "en")
    with pytest.raises(ValueError, match="unknown language"):
        builder.cells("PIN", "de")
    with pytest.raises(ValueError, match="unknown language"):
        live.set_language("de")


def test_progress_and_error_box_switch_back_without_changing_event_data():
    event = {"kind": "route", "done": 2, "total": 3, "net": "a[0]", "attempt": 1}
    before = dict(event)
    japanese = live.describe(event)
    assert japanese == "配線 2/3 本 · a[0] · やり直し1回目"
    live.set_language("en")
    assert live.describe(event) == "Routing 2/3 nets · a[0] · retry 1"
    box = live._box("1-2 <synthesis>", "The netlist is not defined.").data
    assert "Run <b>1-2 &lt;synthesis&gt;</b> first." in box
    assert "This cell is not ready" in box
    assert not CJK.search(box)
    assert str(live.NotReady("1-2 Synthesis", "Missing netlist.")) == 'Run "1-2 Synthesis" first. Missing netlist.'
    live.set_language("ja")
    assert live.describe(event) == japanese
    assert event == before


def test_simulation_conditions_keep_the_actual_values_in_both_languages(monkeypatch):
    output = []
    monkeypatch.setattr(views, "display", lambda html: output.append(html.data))
    post = {
        "stimulus": {"inputs": ["w0"], "supplies_v": {"VDD": 5, "VMID": 0, "VSS": -5},
                     "temperature_c": 27, "hold_s": 1e-6, "edge_s": 1e-9, "step_s": 2e-9},
        "waveforms": {"v(w0)": [5, 5]},
    }
    views.transient_conditions(post, load_f=100e-15)
    japanese = output[-1]
    live.set_language("en")
    views.transient_conditions(post, load_f=100e-15)
    english = output[-1]
    assert not CJK.search(english)
    for value in ("27 °C", "+5 V / 0 V / −5 V", "1 µs", "1 ns", "100 fF", "2 ns", "w0 = +5 V"):
        assert value in english
        assert value in japanese
    assert "nominal SPICE models" in english
    assert "Fixed throughout (waveforms omitted)" in english
    live.set_language("ja")
    views.transient_conditions(post, load_f=100e-15)
    assert output[-1] == japanese


def test_note_font_names_are_one_valid_html_style_attribute(monkeypatch):
    from html.parser import HTMLParser
    from style import SERIF, MUTED

    output = []
    monkeypatch.setattr(views, "display", lambda html: output.append(html.data))
    views.note("Recorded conditions: 27 °C, 100 fF.")

    class Paragraph(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == "p":
                self.attrs = dict(attrs)

    paragraph = Paragraph()
    paragraph.feed(output[0])
    assert paragraph.attrs == {"class": "tf-note", "style": f"font-family:{SERIF};font-size:12.5px;color:{MUTED};margin:.4em 0 0"}


def test_scaling_views_translate_labels_and_preserve_every_series():
    import json
    import scale_views

    data = json.loads((builder.ROOT/"results/dot_scaling.json").read_text())
    tables = [scale_views.synthesis_table, scale_views.scaling_table, scale_views.power_table,
              scale_views.timing_table, scale_views.layout_penalty_table]
    japanese = [table(data).data for table in tables]
    plots = [scale_views.scaling_figure(data), scale_views.power_figure(data)]
    live.set_language("en")
    assert all(not CJK.search(table(data).data) for table in tables)
    for original, view in zip(plots, [scale_views.scaling_figure, scale_views.power_figure]):
        english = view(data)
        assert not CJK.search(english.to_json())
        assert [(list(t.x), list(t.y)) for t in english.data] == [(list(t.x), list(t.y)) for t in original.data]
    power = scale_views.power_figure(data)
    assert power.layout.legend.y < 0 and power.layout.margin.b >= 100
    live.set_language("ja")
    assert [table(data).data for table in tables] == japanese


def test_reuse_translation_preserves_the_recorded_producer():
    import hashlib
    import json

    folder = builder.ROOT/"notebook/assets/chip/dot4"
    provenance = json.loads((folder/"provenance.json").read_text())
    original = (folder/"reuse_before_english.py").read_bytes()
    assert hashlib.sha256(original).hexdigest() == provenance["producer_source_sha256"]["notebook/reuse.py"]

    class WithoutLabels(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            # shuttle_view only displays the recorded snapshot; it does not produce it.
            return None if node.name in ("_label", "shuttle_view") else self.generic_visit(node)

        def visit_Assign(self, node):
            if any(isinstance(target, ast.Name) and target.id == "LABELS_EN" for target in node.targets):
                return None
            return self.generic_visit(node)

        def visit_ImportFrom(self, node):
            if node.module == "live":
                node.names = [alias for alias in node.names if alias.name != "_text"]
            return node

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id in ("_text", "_label"):
                return self.visit(node.args[0])
            node = self.generic_visit(node)
            # Progress-step and error-box titles are display text, not producer logic.
            if isinstance(node.func, ast.Name) and node.func.id in ("step", "_box") and node.args \
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                node.args[0] = ast.Constant("")
            return node

    current = (builder.ROOT/"notebook/reuse.py").read_text()
    normalized = WithoutLabels().visit(ast.parse(current))
    assert ast.dump(normalized) == ast.dump(WithoutLabels().visit(ast.parse(original)))
