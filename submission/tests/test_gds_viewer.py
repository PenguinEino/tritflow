"""Saved submissions keep the real embedded KLayout overview without scripts."""
from base64 import b64decode
import importlib.util
import io
from pathlib import Path

import nbformat
from PIL import Image
import pytest

from tritflow.viz.layout import gds_viewer

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('viewer_submission_builder', ROOT/'submission/build_submission.py')
builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)


def test_portable_outputs_replaces_active_viewer_with_exact_embedded_png():
    html = gds_viewer(ROOT/'cells/out/INV/INV.gds', width=700, height=500).data
    expected, = builder.gds_viewer_outputs(html)
    doc = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell('# viewer', outputs=[
        nbformat.v4.new_output('display_data', data={'text/html':html})])])
    builder.portable_outputs(doc, {})
    actual, = doc.cells[0].outputs
    assert actual == expected and 'text/html' not in actual.data
    with Image.open(io.BytesIO(b64decode(actual.data['image/png']))) as image:
        assert image.width >= 1000
        image.verify()
    assert 'rerun in Colab' in actual.data['text/plain']


def test_missing_overview_fails_instead_of_dropping_evidence():
    with pytest.raises(ValueError, match='overview'):
        builder.gds_viewer_outputs('<div data-gds-viewer="1"></div>')
