"""Regress the real round-3 failure: presentation must not gate science."""

from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'notebook'))
from markdown_support import colab_math
from paper_evidence import load_paper, refresh_presentation
import colab_evidence


def fixture_record(root, legacy):
    asset = root/'figures/out/fig_cell.svg'
    asset.parent.mkdir(parents=True)
    asset.write_text('<svg><metadata>date one</metadata></svg>')
    measurement = root/'results/measurement.json'
    measurement.parent.mkdir(); measurement.write_text('{"passed":true}')
    hashes = {str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in (asset,measurement)}
    record = {'schema':1 if legacy else 2,'repository_sha256':hashes if legacy else {
        k:v for k,v in hashes.items() if not k.startswith('figures/')}}
    if not legacy:
        record['presentation_sha256'] = {k:v for k,v in hashes.items() if k.startswith('figures/')}
    path = root/'notebook/assets/paper_evidence.json'
    path.parent.mkdir(parents=True); path.write_text(json.dumps(record))
    return record,asset,measurement


@pytest.mark.parametrize('legacy',[False,True])
def test_regenerated_or_missing_figure_warns_without_rejecting_measurements(tmp_path,legacy):
    record,asset,measurement = fixture_record(tmp_path,legacy)
    asset.write_text('<svg><metadata>date two</metadata></svg>')
    with pytest.warns(UserWarning,match='computation continues'):
        assert load_paper(tmp_path) == record
    asset.unlink()
    with pytest.warns(UserWarning,match='fig_cell.svg'):
        assert load_paper(tmp_path) == record
    measurement.write_text('{"passed":false}')
    with pytest.raises(RuntimeError,match='measurement inputs changed'):
        load_paper(tmp_path)


def test_refresh_preserves_science_and_needs_no_native_build(tmp_path):
    record,asset,measurement = fixture_record(tmp_path,True)
    expected = record['repository_sha256']['results/measurement.json']
    asset.write_text('<svg><metadata>new deterministic drawing</metadata></svg>')
    refreshed = refresh_presentation(tmp_path)
    assert refreshed['repository_sha256'] == {'results/measurement.json':expected}
    assert refreshed['presentation_sha256']['figures/out/fig_cell.svg'] == sha256(asset.read_bytes()).hexdigest()
    assert load_paper(tmp_path) == refreshed and not (tmp_path/'build').exists()


def test_math_is_colab_dollar_markdown_and_fenced_code_is_unchanged():
    source = r'''Use \(R_u\) and \(R_d\).

\[
\operatorname{INV}(a)=-a,\qquad I=\frac{V}{R}.
\]

```python
literal = r"\[not math\]"
```'''
    rendered = colab_math(source)
    assert '$R_u$' in rendered and '$$\n' in rendered
    assert r'\mathrm{INV}' in rendered and r'\frac{V}{R}' in rendered
    assert rendered.split('```python')[1] == source.split('```python')[1]


def test_chapter_math_is_outside_html_and_paper_images_are_responsive():
    document = json.loads((ROOT/'notebook/tritflow_tr1um.ipynb').read_text())
    for cell in document['cells']:
        if cell['cell_type'] != 'markdown': continue
        text = cell['source']
        assert all(token not in text for token in (r'\[',r'\]',r'\(',r'\)',r'\operatorname'))
        for details in re.findall(r'<details>.*?</details>',text,re.S):
            assert '$$' not in details
        for tag in re.findall(r'<img\b[^>]+>',text):
            assert 'max-width:100%' in tag and 'height:auto' in tag
        if text.startswith(('## 1.','## 2.','## 7.')):
            assert text.count('$$') >= 4
        if text.startswith('## Appendix A.'):
            # Colab drops inline styles and truncates long table cells, so the
            # scope list is rendered as bold-labelled Markdown paragraphs.
            assert '<table' not in text
            assert '**Silicon.**' in text and '**Manufacturing.**' in text


def test_scoped_real_pass_and_missing_verification_note(monkeypatch):
    note = colab_evidence.run_note()
    assert '405 s' in note and 'successful second Run all' in note
    assert 'initial setup attempt excluded' in note
    assert 'If Run all stops after setup, choose Run all again.' in note
    monkeypatch.setattr(colab_evidence,'CURRENT_EVIDENCE',None)
    assert colab_evidence.run_note() == ''
    # Explicit unit fixture for a completed first-attempt run.
    monkeypatch.setattr(colab_evidence,'CURRENT_EVIDENCE',{
        'commit':'a'*40,'passed_code_cells':18,'run_all_seconds_including_setup':120})
    assert 'aaaaaaaa' in colab_evidence.run_note()


def test_long_label_description_tables_become_paragraphs_short_tables_stay():
    from markdown_support import colab_markdown
    prose = "| Topic | Scope |\n|---|---|\n| Silicon | " + "word "*40 + "|\n"
    assert '<table' not in colab_markdown(prose) and '**Silicon.**' in colab_markdown(prose)
    short = "| Quantity | Hand | SPICE |\n|---|---|---|\n| I | 1 | 2 |\n"
    assert '<table' in colab_markdown(short)
