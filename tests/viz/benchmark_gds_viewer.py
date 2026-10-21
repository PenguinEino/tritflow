"""Measure warm KLayout callbacks on routed layouts, without frontend latency.

Run from the repository root with TR1UM_PDK set to the pinned PDK:
  PYTHONPATH=. python3 tests/viz/benchmark_gds_viewer.py --baseline /tmp/viewer_before.py
The optional baseline is a saved pre-change tritflow/viz/_gds_viewer.py.
Layouts must already exist at build/{full_add,alu}/{name}.gds.
"""
from base64 import b64decode
import argparse
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time
from unittest.mock import patch

from IPython.display import JSON

from tritflow.viz import _gds_viewer as current
from tritflow.viz.layout import _pdk_layer_properties


def measure(function, repeats=9):
    durations = []
    for _ in range(repeats):
        start = time.perf_counter()
        data = function()
        durations.append((time.perf_counter() - start) * 1000)
    return data, round(statistics.median(durations), 3)


def benchmark(baseline=None):
    rows = []
    for name in ('full_add', 'alu'):
        for mode in ('before-quick', 'before-sharp', 'after-quick', 'after-sharp', 'after-png'):
            module = baseline if mode.startswith('before') else current
            if module is None:
                continue
            renderer = module._GdsRenderer(f'build/{name}/{name}.gds')
            try:
                # The visible view is a centred 70% crop of the isotropic die box.
                bounds = current._aspect_box(renderer.bounds, 700, 490)
                cx, cy = (bounds[0] + bounds[2])/2, (bounds[1] + bounds[3])/2
                dx, dy = (bounds[2] - bounds[0])*.7, (bounds[3] - bounds[1])*.7
                margin = 1.5 if mode == 'before-quick' else 1
                box = [cx-dx*margin/2, cy-dy*margin/2, cx+dx*margin/2, cy+dy*margin/2]
                width, height = (1400, 980) if mode.endswith('sharp') else (1050, 735) if mode == 'before-quick' else (700, 490)
                encoding = 'webp' if mode in ('after-quick', 'after-sharp') else 'png'
                args = [box, width, height] + ([encoding] if module is current else [])
                callback_name = module._register(renderer)
                if callback_name:
                    from google.colab.output import _js
                    def callback():
                        return _js._invoke_function(callback_name, json.dumps(args), '{}').data
                else:
                    def callback():
                        return JSON(renderer.render(*args)).data
                def uncached():
                    renderer.cache.clear(); renderer.cache_bytes = 0
                    return callback()
                uncached()  # Warm imports/encoder/renderer before timing.
                data, elapsed = measure(uncached)
                _, cached = measure(callback)
                rows.append(dict(layout=name, mode=mode, median_ms=elapsed,
                                 cached_ms=cached, json_bytes=len(json.dumps(data).encode()),
                                 image_bytes=len(b64decode(data['image'].split(',')[1])),
                                 mime=data['image'].split(';')[0][5:], width=width, height=height,
                                 callback_registered=bool(callback_name)))
            finally:
                renderer.close()
    return rows


def benchmark_tiles():
    """Evaluate a six-tile batch and a one-column pan at the same pixel scale.

    Labels follow the complete viewport's 1 mm threshold, rather than each
    tile's span. This is an optimistic lower bound: a generic unaligned view
    needs more tiles, and Colab transport/frontend work is excluded.
    """
    rows = []
    for name in ('full_add', 'alu'):
        renderer = current._GdsRenderer(f'build/{name}/{name}.gds')
        try:
            bounds = current._aspect_box(renderer.bounds, 700, 490)
            span = (bounds[2] - bounds[0]) * .35
            side = span / 700 * 256
            def labels(view, box):
                visible = span <= 1000 and _pdk_layer_properties() is not None
                view.set_config('text-visible', 'true' if visible else 'false')
                return visible
            def tile(x, y):
                return renderer.render([x*side, y*side, (x+1)*side, (y+1)*side], 256, 256, 'webp')
            with patch('tritflow.viz.layout._gds_text_visibility', labels):
                for mode, columns in [('viewport', None), ('tiles-cold', range(3)), ('tiles-pan-column', range(3, 4))]:
                    def render():
                        renderer.cache.clear(); renderer.cache_bytes = 0
                        if columns is None:
                            return [renderer.render([0, 0, span, span*490/700], 700, 490, 'webp')]
                        return [tile(x, y) for x in columns for y in range(2)]
                    render()
                    data, elapsed = measure(render)
                    rows.append(dict(layout=name, mode=mode, median_ms=elapsed,
                                     new_tiles=len(data), json_bytes=len(json.dumps(data).encode())))
        finally:
            renderer.close()
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--tiles', action='store_true', help='Measure the candidate 256-pixel tile grid instead')
    args = parser.parse_args()
    baseline = None
    if args.baseline:
        spec = importlib.util.spec_from_file_location('tritflow.viz._viewer_before', args.baseline)
        baseline = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = baseline
        spec.loader.exec_module(baseline)
    result = json.dumps(benchmark_tiles() if args.tiles else benchmark(baseline), indent=2)
    print(result)
    if args.output:
        args.output.write_text(result + '\n')
