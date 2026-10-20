"""Optional live progress events from placement and routing.

Nothing is reported unless a caller installs a listener with :func:`listening`;
the notebook uses it to redraw a status line and a live layout while a step
runs. Reporting never changes a result.
"""

from contextlib import contextmanager

_listener = None


@contextmanager
def listening(callback):
    """Send progress events (dicts) to ``callback`` for the duration of the block."""
    global _listener
    previous, _listener = _listener, callback
    try:
        yield
    finally:
        _listener = previous


def active():
    """True while someone listens; lets callers skip building costly events."""
    return _listener is not None


def report(**event):
    """Describe the work in progress, e.g. ``report(kind="route", done=3, total=8)``."""
    if _listener is not None:
        _listener(event)
