"""Publication gates, bilingual evidence, unchanged source and derived claims."""

from base64 import b64encode
import importlib.util
import io
import json
import re
from pathlib import Path

import nbformat
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('submission_builder', ROOT/'submission/build_submission.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
from results import chapter6, result_values


def fixture_notebook(tmp_path, name='source.ipynb', evaluation=False):
    """Explicit unit evidence; actual EDA is checked on the generated payload."""
    source = tmp_path/name
    cells = [nbformat.v4.new_markdown_cell('# Unit fixture', id='intro'),
             nbformat.v4.new_code_cell("print('unit fixture')", id='code')]
    if evaluation:
        cells += [nbformat.v4.new_markdown_cell('## 6. Evaluation', id='evaluation-heading'),
                  nbformat.v4.new_code_cell("print('unit evaluation')", id='future-evaluation')]
    document = nbformat.v4.new_notebook(cells=cells)
    nbformat.write(document, source)
    stream = io.BytesIO()
    Image.new('RGB', (2, 2), 'white').save(stream, format='PNG')
    data = {'image/png':b64encode(stream.getvalue()).decode(),
            'text/html':'<table><tr><td>fixture</td></tr></table>'}
    document.cells[1].execution_count = 1
    document.cells[1].outputs = [nbformat.v4.new_output('display_data', data=data) for _ in range(8)]
    if evaluation:
        document.cells[-1].execution_count = 2
        document.cells[-1].outputs = [nbformat.v4.new_output('display_data', data={'text/html':
            '<table><tr><th>Terms</th><th>Area (µm²)</th></tr><tr><td>2</td><td>12345</td></tr></table>'})]
    return document, source


def add_evidence(document, source):
    evidence = {'schema_version':1, 'source_ref':'a'*40, 'runtime_commit':'a'*40,
                'runtime':{'python':'unit-test'}, 'designs':{}}
    document.cells.append(nbformat.v4.new_code_cell(builder.CAPTURE_CODE, id='submission-evidence',
        execution_count=3, outputs=[nbformat.v4.new_output('display_data', data={'application/json':evidence})]))
    document.metadata['tritflow_submission_capture'] = {
        'completed':True, 'source_sha256':builder.digest(source), 'elapsed_s':1}
    return evidence


def test_rejects_unexecuted_changed_failed_or_reordered_evidence(tmp_path):
    document, source = fixture_notebook(tmp_path)
    assert builder.validate(document, source)['png_outputs'] == 8
    document.cells[1].execution_count = None
    with pytest.raises(ValueError, match='executed'):
        builder.validate(document, source)
    document.cells[1].execution_count = 1
    document.cells[1].source = "print('changed')"
    with pytest.raises(ValueError, match='changed'):
        builder.validate(document, source)
    document.cells[1].source = "print('unit fixture')"
    document.cells.reverse()
    with pytest.raises(ValueError, match='order'):
        builder.validate(document, source)
    document.cells.reverse()
    document.cells[1].outputs.append(nbformat.v4.new_output('error', ename='RuntimeError', evalue='failed', traceback=[]))
    with pytest.raises(ValueError, match='failed execution'):
        builder.portable_outputs(document, {})


def test_native_svg_gallery_is_embedded_without_local_assets():
    svg = (ROOT/'notebook/assets/schematics/INV.compact.svg').read_bytes()
    html = f'<img src="data:image/svg+xml;base64,{b64encode(svg).decode()}" alt="INV taped-out schematic">'
    output, = builder.gallery_outputs(html)
    assert output.data['image/svg+xml'].encode() == svg
    assert 'image/png' in output.data and 'INV' in output.data['text/plain']
    with pytest.raises(ValueError, match='gallery markup'):
        builder.gallery_outputs('<img>')


def test_bilingual_package_hashes_budget_top_identity_and_allowlist(tmp_path, monkeypatch):
    english, en_source = fixture_notebook(tmp_path, 'tritflow_en.ipynb', evaluation=True)
    japanese, ja_source = fixture_notebook(tmp_path, 'tritflow_ja.ipynb', evaluation=True)
    add_evidence(english, en_source)
    add_evidence(japanese, ja_source)
    team = json.loads((ROOT/'submission/team.json').read_text())
    monkeypatch.setattr(builder, 'release_status', lambda source: {'compatible':True, 'commit':'a'*40})
    target = tmp_path/'payload'
    sources = {'tritflow_en.ipynb':en_source, 'tritflow_ja.ipynb':ja_source}
    documents = {'tritflow_en.ipynb':english, 'tritflow_ja.ipynb':japanese}
    builder.package(documents, sources, target, team, {})
    info = builder.check(target, sources)
    assert info['file_count'] == 9 and info['submission_ready']
    assert info['total_bytes'] == sum(p.stat().st_size for p in target.iterdir())
    for name, source in sources.items():
        doc = nbformat.read(target/name, as_version=4)
        assert team['authors'][0]['email'] in doc.cells[0].source
        assert doc.cells[1].source == '# Unit fixture'
        assert info['notebooks'][name]['source_sha256'] == builder.digest(source)
    assert '12345' in (target/'README.md').read_text()
    assert '{{' not in (target/'ABSTRACT.md').read_text()
    assert (target/'LICENSE').read_bytes() == (ROOT/'LICENSE').read_bytes()
    assert (target/'NOTICE').read_bytes() == (ROOT/'NOTICE').read_bytes()
    (target/'README.md').write_text('changed')
    with pytest.raises(ValueError, match='hash mismatch'):
        builder.check(target, sources)


def test_preview_is_not_submission_ready_and_placeholders_are_rejected(tmp_path, monkeypatch):
    document, source = fixture_notebook(tmp_path, 'tritflow_ja.ipynb')
    add_evidence(document, source)
    monkeypatch.setattr(builder, 'release_status', lambda source: {'compatible':False, 'default_ref':'a'*40})
    team = json.loads((ROOT/'submission/team.json').read_text())
    info = builder.package({'tritflow_ja.ipynb':document}, {'tritflow_ja.ipynb':source}, tmp_path/'preview', team, {})
    assert not info['submission_ready'] and info['file_count'] == 8
    assert any('English' in reason for reason in info['readiness_notes'])
    assert any('chapter 6' in reason for reason in info['readiness_notes'])
    team['authors'][0]['name'] = '[AUTHOR_NAME]'
    with pytest.raises(ValueError, match='placeholders'):
        builder.package({'tritflow_ja.ipynb':document}, {'tritflow_ja.ipynb':source}, tmp_path/'bad', team, {})


def test_primary_selection_uses_english_when_available_and_japanese_once(tmp_path, monkeypatch):
    english = tmp_path/'tritflow_en.ipynb'
    japanese = tmp_path/'tritflow_ja.ipynb'
    japanese.write_text('{}')
    monkeypatch.setattr(builder, 'SOURCE', english)
    assert builder.selected_sources(japanese=japanese) == {'tritflow_ja.ipynb':japanese}
    english.write_text('{}')
    assert list(builder.selected_sources(japanese=japanese)) == ['tritflow_en.ipynb', 'tritflow_ja.ipynb']
    japanese.unlink()
    with pytest.raises(ValueError, match='Japanese companion'):
        builder.selected_sources(japanese=japanese)


def test_incomplete_stale_or_unexecuted_raw_capture_is_not_reused(tmp_path):
    document, source = fixture_notebook(tmp_path)
    raw = tmp_path/'raw.ipynb'
    add_evidence(document, source)
    document.metadata.tritflow_submission_capture.completed = False
    nbformat.write(document, raw)
    with pytest.raises(ValueError, match='incomplete'):
        builder.use_executed(raw, source)
    document.metadata.tritflow_submission_capture.completed = True
    document.metadata.tritflow_submission_capture.source_sha256 = '0'*64
    nbformat.write(document, raw)
    with pytest.raises(ValueError, match='different source'):
        builder.use_executed(raw, source)
    document.metadata.tritflow_submission_capture.source_sha256 = builder.digest(source)
    document.cells[1].execution_count = None
    nbformat.write(document, raw)
    with pytest.raises(ValueError, match='executed'):
        builder.use_executed(raw, source)


def test_pitch_three_sentences_and_rules_from_current_snapshot():
    pitch = builder.read_template('PITCH.md').split('\n\n', 1)[1]
    assert len([s for s in pitch.split('.') if s.strip()]) == 3
    checklist = builder.read_template('CHECKLIST.md')
    assert '2026-10-31 at 11:59 AM Pacific' in checklist
    assert 'ISSCC27/submitted_notebooks/TritFlow/' in checklist
    assert 'superseded' in checklist and '2025' in checklist
    from hashlib import sha256
    rules = json.loads((ROOT/'submission/official_sources.json').read_text())
    snapshot = json.loads((ROOT/'submission/official_snapshot.json').read_text())
    for path, record in snapshot.items():
        assert rules['sources'][path]['sha256'] == sha256(record['content'].encode()).hexdigest()
        assert rules['official_repository_commit'] in record['display_url']
    assert 'ISSCC27/submitted_notebooks/<project_name>/' in snapshot['README.md']['content']


def test_results_are_derived_from_execution_and_failures_cannot_be_claimed():
    evidence = {'designs':{'dot4':{'report':{'total_cells':17},
                'equivalence':{'passed':True, 'vectors':81},
                'drc':{'violations':0}, 'lvs':{'matched':True},
                'measurements':{'passed':True, 'rows':[{}, {}, {}], 'max_settling_s':{'y':20e-9}}}}}
    values = result_values(evidence, {})
    assert '17 cells' in values['RESULTS_SENTENCE'] and '81 input vectors' in values['RESULTS_SENTENCE']
    assert '3 stimulus intervals' in values['RESULTS_SENTENCE']
    assert '20.0 ns' in values['RESULTS'] and 'no chapter 6' in values['CHAPTER6_RESULTS']
    evidence['designs']['dot4']['measurements']['passed'] = False
    with pytest.raises(ValueError, match='post-layout'):
        result_values(evidence, {})


def test_future_chapter6_results_use_executed_tables_without_fixed_cell_ids(tmp_path):
    document, _ = fixture_notebook(tmp_path, evaluation=True)
    evaluation = chapter6(document)
    assert evaluation['executed_cell_ids'] == ['future-evaluation']
    assert '12345' in result_values({}, evaluation)['CHAPTER6_RESULTS']
    document.cells[-1].execution_count = None
    with pytest.raises(ValueError, match='unexecuted'):
        chapter6(document)


def test_actual_payload_has_readable_evidence_and_exact_bilingual_manifests():
    info = builder.check(builder.DESTINATION)
    assert info['total_bytes'] < 12*1024*1024
    assert 'tritflow_ja.ipynb' in info['notebooks']
    for name in info['notebooks']:
        document = nbformat.read(builder.DESTINATION/name, as_version=4)
        assert document.cells[0].id == 'submission-identity'
        for cell in document.cells:
            for output in cell.get('outputs', []):
                data = output.get('data', {})
                assert not any(key.startswith('application/vnd.plotly') for key in data)
                assert '<script' not in data.get('text/html', '').lower()
                if 'image/png' in data:
                    from base64 import b64decode
                    with Image.open(io.BytesIO(b64decode(data['image/png']))) as image:
                        assert image.width >= 500 and image.height >= 100
                        image.verify()


def test_author_identity_matches_integrator_record_and_asset_authorization():
    text = (ROOT/'docs/author.md').read_text()
    fields = {m[1].lower():' '.join(m[2].split()) for m in
              re.finditer(r'^- (Name|Affiliation|Status|Email|GitHub): (.*(?:\n  .*)*)', text, re.M)}
    team = json.loads((ROOT/'submission/team.json').read_text())
    assert team['authors'] == [fields]
    assert team['representative'] == fields['name']
    attendance = ' '.join(re.search(r'^- Representative: (.*(?:\n  .*)*)', text, re.M)[1].split())
    assert team['attendance_and_poster'] == attendance
    assert not builder.has_placeholders(team)
    readme = builder.render_readme(team)
    for value in fields.values():
        assert value in readme
    assert 'releases the derived assets' in readme and 'Apache-2.0' in readme
    assert not {'phone', 'telephone', 'tel'} & team.keys()
    assert 'local' in readme and 'no claimed real-Colab' in readme


def test_public_schematic_svg_gets_saved_png_fallback():
    from tritflow import flow
    net = flow.load('examples/half_add.tv', 'half_add').synthesize()
    svg = net.schematic(expand='*', inputs={'a':1, 'b':1}).svg
    document = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell('# unit drawing',
        outputs=[nbformat.v4.new_output('display_data', data={'image/svg+xml':svg})])])
    builder.portable_outputs(document, {})
    assert document.cells[0].outputs[0].data['image/svg+xml'] == svg
    assert 'image/png' in document.cells[0].outputs[0].data


def test_workspace_rejects_writes_outside_owned_directory(tmp_path):
    with pytest.raises(ValueError, match='inside submission'):
        builder.workspace(ROOT/'build/submit')
