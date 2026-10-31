"""Progress-label adapter used by the source-checked notebook cache.

The v3 displays live in views.py and the specialized view modules. This small
adapter preserves cache.py's recorded import without retaining the old figure,
gallery and narrative display layer.
"""

from live import _text


def label(value):
    """Translate cache progress prefixes; leave circuit and artifact names intact."""
    japanese = {"Computing: ": "計算中: ",
                "Reusing the result computed earlier in this runtime: ": "この実行で求めた結果を再利用: "}
    return _text(japanese.get(value, value), value)
