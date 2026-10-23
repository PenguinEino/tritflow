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
    assert all(not CJK.search(source) for _, source in english)
    for kind, source in english:
        if kind == "code":
            compile(source, "English cell", "exec")
        else:
            for path in re.findall(r"/PIN/(.*?\.png)", source):
                assert (builder.ROOT/path).is_file(), path
            for path in re.findall(r"@PIN/([^\"]+\.svg)", source):
                assert (builder.ROOT/path).is_file(), path
    setup = next(source for kind, source in english if kind == "code")
    assert 'set_notebook_language("en")' in setup
    assert 'set_language("en")' in setup
    assert 'TRITFLOW_NOTEBOOK_LANGUAGE"] = "en"' in setup


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
    assert "no corners" in english
    assert "Fixed throughout (waveforms omitted)" in english
    live.set_language("ja")
    views.transient_conditions(post, load_f=100e-15)
    assert output[-1] == japanese
