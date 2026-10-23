"""Exercise the shipped JavaScript against a controlled Colab queue and clock.

QuickJS is an optional development tool; no JavaScript engine is needed at runtime.
"""
import json
from pathlib import Path

import pytest

from tritflow.viz._gds_viewer import _LABELS, _SCRIPT
from tritflow.viz.layout import _TEXT_LABEL_SPAN_UM

quickjs = pytest.importorskip('quickjs')


class Browser:
    def __init__(self, *, ratio=1, live=True, language="en"):
        self.context = quickjs.Context()
        self.context.eval(Path(__file__).with_name('viewer_browser_harness.js').read_text())
        self.context.eval(f'window.devicePixelRatio = {ratio};')
        self.context.eval(f'config.labels = {json.dumps(_LABELS[language])};'
                          f'config.labelSpanUm = {_TEXT_LABEL_SPAN_UM};')
        if not live:
            self.context.eval('delete window.google;')
        self.context.eval(_SCRIPT)
        self.advance(0)

    def run(self, source):
        result = self.context.eval(source)
        while self.context.execute_pending_job():
            pass
        return result

    def value(self, source):
        return json.loads(self.run(f'JSON.stringify({source})'))

    def advance(self, ms):
        target = self.run('clock') + ms
        for _ in range(1000):
            timer = self.value('nextTimer() || null')
            if timer is None or timer['at'] > target:
                break
            self.run(f'runTimer({timer["id"]});')
        else:
            pytest.fail('Viewer timer loop did not become idle')
        self.run(f'clock = {target};')

    def reply(self, index=-1, *, fail=False):
        if index == -1:
            index = self.run('calls.length - 1')
        self.run(f'reply({index}, {str(fail).lower()});')


def test_continuous_drag_is_throttled_and_coalesces_latest_view():
    browser = Browser()
    assert browser.run('calls.length') == 0  # Embedded overview already supplies fit.
    browser.run("event('pointerdown');")
    for x in range(360, 460, 10):
        browser.run(f"event('pointermove', {{clientX:{x}}});")
        browser.advance(8)
    assert browser.run('calls.length') == 1  # No starvation; no duplicate queued work.
    first = browser.value('calls[0].args[0]')
    latest = browser.value('box')
    assert latest != first
    browser.advance(180_000)  # Busy Run all must leave this request alive.
    assert browser.run('calls.length') == 1
    browser.reply(0)
    assert browser.value('imageBox') == first  # Stale response keeps physical coordinates.
    browser.advance(0)
    assert browser.run('calls.length') == 2
    assert browser.value('calls[1].args[0]') == pytest.approx(latest)
    assert browser.value('calls[1].args.slice(1)') == [700, 490, 'webp']
    browser.reply(1)
    browser.run("event('pointerup');")
    browser.advance(1000)
    assert browser.run('calls.length') == 2  # No redundant 1x refinement.
    assert browser.run('fakeRoot.dataset.waiting') == '0'


def test_wheel_continues_to_receive_pixels_and_refines_only_after_idle():
    browser = Browser(ratio=2)
    browser.run("event('wheel', {deltaY:-1000});")
    browser.advance(0)
    browser.reply()
    for _ in range(6):
        browser.run("event('wheel', {deltaY:-150});")
        browser.advance(32)
        assert browser.value('calls[calls.length - 1].args.slice(1, 3)') == [700, 490]
        browser.reply()
    assert browser.run('liveRenders') >= 4
    browser.advance(87)
    assert browser.value('calls[calls.length - 1].args.slice(1, 3)') == [700, 490]
    browser.advance(1)
    assert browser.value('calls[calls.length - 1].args.slice(1, 3)') == [1400, 980]
    browser.reply()
    browser.advance(1000)
    assert browser.run('fakeRoot.dataset.waiting') == '0'


def test_retry_backoff_survives_new_pointer_events_and_recovers():
    browser = Browser()
    browser.run("event('wheel', {deltaY:-1000});")
    browser.advance(0)
    for delay in [500, 1000, 2000, 4000, 8000, 10000, 10000]:
        before = browser.run('calls.length')
        browser.reply(fail=True)
        for _ in range(4):
            browser.run("event('wheel', {deltaY:-20});")
            browser.advance(delay / 4 - .25)
        assert browser.run('calls.length') == before
        browser.advance(1)
        assert browser.run('calls.length') == before + 1
    browser.reply()
    browser.advance(500)
    assert browser.run('fakeRoot.dataset.retryCount') == 0
    assert browser.run('fakeRoot.dataset.waiting') == '0'


def test_cached_view_and_fit_return_without_a_kernel_round_trip():
    browser = Browser()
    browser.run("event('wheel', {deltaY:-1000});")
    browser.advance(0)
    requested = browser.value('box')
    browser.reply()
    browser.run('fit();')
    browser.advance(1000)
    assert browser.value('imageBox') == browser.value('config.box')
    browser.run(f'box = {json.dumps(requested)}; changed();')
    browser.advance(1000)
    assert browser.run('calls.length') == 1
    assert browser.value('imageBox') == pytest.approx(requested)


def test_browser_cache_evicts_and_pixel_limits_match_kernel():
    browser = Browser(ratio=4)
    for n in range(12):
        browser.run(f'box = [{n*2500},0,{n*2500+2000},1400]; changed();')
        browser.advance(32)
        if browser.run('pending'):
            browser.reply()
    assert browser.run('crops.size') <= 8
    assert browser.run('cacheBytes') <= 16 * 1024 * 1024
    assert browser.run('crops.has(JSON.stringify([[0,0,2000,1400],1400,980]))') is False
    browser.run('fakeViewport.clientWidth = 4000; fakeViewport.clientHeight = 3000; changed();')
    browser.advance(32)
    width, height = browser.value('calls[calls.length - 1].args.slice(1, 3)')
    assert max(width, height) <= 2048 and width * height <= 2_000_000


def test_static_fallback_and_detached_outputs_do_not_request():
    browser = Browser(live=False)
    browser.run("event('wheel', {deltaY:-200}); event('dblclick');")
    browser.advance(10000)
    assert browser.run('calls.length') == 0
    assert browser.run('fakeRoot.dataset.mode') == 'static'
    browser = Browser()
    browser.run("event('wheel', {deltaY:-1000});")
    browser.advance(0)
    browser.run('fakeRoot.isConnected = false;')
    browser.reply()
    browser.advance(10000)
    assert browser.run('calls.length') == 1


def test_labelled_cache_does_not_rescale_fixed_size_text_or_cross_threshold():
    browser = Browser()
    browser.run('crops.clear(); cacheBytes = 0;')
    browser.run('remember(fakeOverview, {box:[0,0,125,87.5], width:1400, height:980});')
    # Reusing this higher-resolution crop would halve the font size.
    assert browser.run('cachedCrop({crop:[0,0,125,87.5],width:700,height:490}) === null')
    assert browser.run('cachedCrop({crop:[0,0,125,87.5],width:1400,height:980}) !== null')
    browser.run('crops.clear(); cacheBytes = 0;')
    browser.run('remember(fakeOverview, {box:[0,0,554,388], width:1400, height:980});')
    assert browser.run('cachedCrop({crop:[100,100,225,187.5],width:300,height:210}) === null')


def test_japanese_status_survives_static_live_and_waiting_updates():
    status = 'elements[\'[data-role="status"]\'].textContent'
    browser = Browser(live=False, language="ja")
    assert browser.run(status) == _LABELS["ja"]["static"]
    browser = Browser(language="ja")
    assert browser.run(status) == _LABELS["ja"]["live"].format(count=0)
    browser.run("event('wheel', {deltaY:-1000});")
    browser.advance(0)
    assert browser.run(status) == _LABELS["ja"]["waiting"]
    browser.reply()
    assert browser.run(status) == _LABELS["ja"]["live"].format(count=1)


def test_browser_without_webp_decode_recovers_with_png():
    browser = Browser()
    browser.run('Image.prototype.decode = function() { '
                "return this.src.startsWith('data:image/webp;') ? Promise.reject(new Error('unsupported')) : Promise.resolve(); };")
    browser.run("event('wheel', {deltaY:-1000});")
    browser.advance(0)
    browser.reply()
    assert browser.run('encoding') == 'png'
    browser.advance(500)
    assert browser.value('calls[1].args.slice(1)') == [700, 490, 'png']
    browser.run("calls[1].resolve({data:{'application/json':{image:'data:image/png;base64,fixture',"
                'box:calls[1].args[0],width:700,height:490}}});')
    assert browser.run('fakeRoot.dataset.retryCount') == 0
    assert browser.run('fakeRoot.dataset.waiting') == '0'


def test_fit_during_a_busy_request_keeps_the_cached_overview_after_reply():
    browser = Browser()
    browser.run("event('wheel', {deltaY:-1000});")
    browser.advance(0)
    browser.run('fit();')
    assert browser.value('imageBox') == browser.value('config.box')
    browser.reply()
    assert browser.value('imageBox') == browser.value('config.box')
    browser.advance(1000)
    assert browser.run('calls.length') == 1
    assert browser.run('fakeRoot.dataset.waiting') == '0'


def test_cached_fit_after_transport_failure_has_no_unserved_work():
    browser = Browser()
    browser.run("event('wheel', {deltaY:-1000});")
    browser.advance(0)
    browser.reply(fail=True)
    browser.run('fit();')
    browser.advance(1000)
    assert browser.value('imageBox') == browser.value('config.box')
    assert browser.run('calls.length') == 1
    assert browser.run('fakeRoot.dataset.waiting') == '0'
