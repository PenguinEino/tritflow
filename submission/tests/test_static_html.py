"""Offline snapshots execute real HTML; PNG compression preserves every pixel."""
from base64 import b64decode
import io
from pathlib import Path
import sys

from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from static_html import snapshots
from build_submission import optimize_png


def test_snapshot_executes_initial_control_state_without_a_network(tmp_path):
    html = ('<h1 id="value">Unset</h1><script>'
            'document.getElementById("value").textContent="Measured value: 17 ns";'
            '</script>')
    data, = snapshots([html], tmp_path/'views')
    assert 'Measured value: 17 ns' in data['text/plain']
    assert 'Unset' not in data['text/plain']
    with Image.open(io.BytesIO(b64decode(data['image/png']))) as image:
        assert image.width >= 500
        assert len(image.convert('RGB').getcolors(100000)) > 1


def test_unrendered_plot_is_rejected_instead_of_saving_an_empty_figure(tmp_path):
    with pytest.raises(ValueError, match='Plotly did not render'):
        snapshots(['<div class="plotly-graph-div"></div>'], tmp_path/'blank')


@pytest.mark.parametrize('alpha', [255, 128])
def test_png_optimization_preserves_opaque_and_transparent_pixels(alpha):
    source = Image.new('RGBA', (12, 12), (10, 90, 150, alpha))
    raw = io.BytesIO()
    source.save(raw, format='PNG')
    with Image.open(io.BytesIO(optimize_png(raw.getvalue()))) as optimized:
        assert optimized.convert('RGBA').tobytes() == source.tobytes()
