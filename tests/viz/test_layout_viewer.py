"""KLayout crops and notebook fallbacks use real geometry and TR-1um colours."""
from base64 import b64decode
from html.parser import HTMLParser
import io
from pathlib import Path
import sys
import types

import klayout.db as db
import numpy as np
from PIL import Image
import pytest

from tritflow.viz._gds_viewer import _GdsRenderer, _SESSIONS
from tritflow.viz.layout import _pdk_layer_properties, gds_viewer

ROOT = Path(__file__).resolve().parents[2]


def pixels(tile):
    return np.array(Image.open(io.BytesIO(b64decode(tile['image'].split(',', 1)[1]))).convert('RGB'))


@pytest.fixture
def gds(tmp_path):
    """Separated metal/poly rectangles make crop, y direction and scale observable."""
    layout = db.Layout()
    layout.dbu = .001
    cell = layout.create_cell('crop_fixture')
    for layer, box in [((13, 0), (10, 20, 30, 40)), ((8, 1), (65, 60, 85, 80))]:
        cell.shapes(layout.layer(*layer)).insert(db.DBox(*box))
    path = tmp_path/'crop.gds'
    layout.write(str(path))
    return path


def test_visible_box_crop_and_pdk_colours_are_physical(gds):
    if _pdk_layer_properties() is None:
        pytest.skip('Pinned TR-1um LYP unavailable')
    renderer = _GdsRenderer(gds)
    try:
        full = renderer.render([0, 0, 100, 100], 500, 500)
        image = pixels(full)
        # Pixel y increases down; physical y increases up. Rectangles are 20 µm wide.
        assert np.all(image[450, 450] == 0)
        metal = (0, 128, 255)  # M1 from the actual pinned PDK, not the fallback palette.
        poly = (255, 124, 37)
        assert np.count_nonzero(np.all(image[300:400, 50:150] == metal, axis=2)) > 600
        assert np.count_nonzero(np.all(image[100:200, 325:425] == poly, axis=2)) > 600
        crop = renderer.render([0, 10, 50, 60], 500, 500)
        detail = pixels(crop)
        assert crop['box'] == [0, 10, 50, 60]
        assert not np.any(np.all(detail == poly, axis=2))
        assert np.count_nonzero(np.all(detail[200:400, 100:300] == metal, axis=2)) > 2000
        ys, xs = np.where(np.all(detail == metal, axis=2))
        assert (xs.min(), xs.max(), ys.min(), ys.max()) == (100, 300, 199, 399)
        assert not np.array_equal(image, detail)  # real re-render, not the overview URL.
        assert renderer.render([0, 10, 50, 60], 500, 500)['cached']
        assert renderer.render_count == 2
        adjusted = renderer.render([0, 0, 100, 100], 600, 300)
        assert adjusted['box'] == [-50, 0, 150, 100]
        assert (adjusted['box'][2] - adjusted['box'][0]) / 600 == pytest.approx(100 / 300)
    finally:
        renderer.close()


def test_render_limits_cache_and_invalid_requests(gds):
    renderer = _GdsRenderer(gds)
    try:
        for width, height in ((10000, 10000), (4000, 3000), (5000, 1000)):
            tile = renderer.render([0, 0, 100, 100], width, height)
            assert max(tile['width'], tile['height']) <= 2048
            assert tile['width'] * tile['height'] <= 2_000_000
        for n in range(8):
            renderer.render([n, 0, n + 100, 100], 120, 120)
        assert len(renderer.cache) == 6 and renderer.cache_bytes < 16 * 1024 * 1024
        for box in ([0, 0, 0, 1], [1, 0, 0, 1], [0, 0, float('nan'), 1], [0, 0, float('inf'), 1]):
            with pytest.raises(ValueError, match='Visible box'):
                renderer.render(box, 100, 100)
        with pytest.raises(ValueError, match='Pixel'):
            renderer.render([0, 0, 100, 100], 0, 100)
    finally:
        renderer.close()
    with pytest.raises(RuntimeError, match='expired'):
        renderer.render([0, 0, 100, 100], 100, 100)
    with pytest.raises(ValueError, match='No GDS top'):
        gds_viewer(gds, top='missing')


class Overview(HTMLParser):
    def handle_starttag(self, tag, attrs):
        row = dict(attrs)
        if tag == 'img' and row.get('data-gds-overview') == '1':
            self.image = row['src']


def test_local_html_embeds_overview_and_no_remote_assets(gds, monkeypatch):
    monkeypatch.setitem(sys.modules, 'google.colab', None)
    html = gds_viewer(gds, width=700, height=500).data
    assert 'data-gds-viewer="1"' in html and 'data-gds-overview="1"' in html
    assert '"callback": null' in html
    assert 'kernel.invokeFunction' in html and "addEventListener('wheel'" in html
    assert "addEventListener('dblclick'" in html and 'µm' in html
    assert 'cdn.' not in html and '<script src=' not in html
    parser = Overview(); parser.feed(html)
    image = Image.open(io.BytesIO(b64decode(parser.image.split(',')[1])))
    assert image.width >= 1000 and image.height >= 700
    assert len(image.getcolors(2_000_000)) > 2


def test_registered_callback_json_and_independent_sessions(gds, monkeypatch):
    callbacks = {}
    module = types.ModuleType('google.colab')
    module.output = types.SimpleNamespace(register_callback=lambda name, callback: callbacks.update({name:callback}))
    monkeypatch.setitem(sys.modules, 'google.colab', module)
    previous = dict(_SESSIONS)
    _SESSIONS.clear()
    try:
        for _ in range(9):
            gds_viewer(gds, width=500, height=300)
        assert len(_SESSIONS) == 8 and len(callbacks) == 9
        names = list(callbacks)
        with pytest.raises(RuntimeError, match='expired'):
            callbacks[names[0]]([0, 0, 100, 100], 100, 100)
        first = callbacks[names[-2]]([0, 0, 100, 100], 300, 300).data
        second = callbacks[names[-1]]([0, 0, 50, 50], 300, 300).data
        assert first['box'] != second['box'] and first['image'] != second['image']
        assert first['render_count'] == second['render_count'] == 2
    finally:
        for renderer in _SESSIONS.values():
            renderer.close()
        _SESSIONS.clear(); _SESSIONS.update(previous)


def test_method_cells_use_viewer_keep_download_and_validate():
    import importlib.util
    spec = importlib.util.spec_from_file_location('viewer_validation', ROOT/'notebook/validate_notebook.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    document = module.validate(ROOT/'notebook/tritflow_tr1um.ipynb')
    for cell in document['cells']:
        if cell['id'] in ('method-pnr', 'method-custom_layout', 'method-shuttle'):
            assert 'gds_viewer(' in cell['source'] and 'gds_download(' in cell['source']
            assert 'render_gds(' not in cell['source']
            assert len(cell['source'].strip().splitlines()) <= 14
