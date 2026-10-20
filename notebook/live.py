"""Live progress for notebook cells, in the style of a modern command-line tool.

Each ``with step("...")`` block shows one line that is redrawn while the work
runs (spinner, what is happening, real progress, elapsed time) and then settles
to ``✓ title  summary  time``. Progress comes from TritFlow's placement and
routing events and, for KLayout and ngspice, from their own output, read while
they run. Nothing here changes a result.

``need()`` states what a cell requires; running cells out of order then shows
which cell to run first and why, ahead of the traceback.
"""

from contextlib import contextmanager
from html import escape
import os
import re
import subprocess
import threading
import time

from IPython.display import HTML, display

from tritflow import progress

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
FONT = "font:13px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
GREEN, RED, CYAN, DIM = "#1a9c4a", "#d0342c", "#0b8fb3", "#8a8f98"


def _line(mark, color, title, detail, seconds):
    return HTML(
        f'<div style="{FONT};display:flex;gap:.9em;align-items:baseline;white-space:pre;overflow:hidden">'
        f'<span style="color:{color};font-weight:700;width:1em">{mark}</span>'
        f'<span style="font-weight:600">{escape(title)}</span>'
        f'<span style="color:{DIM};flex:1;overflow:hidden;text-overflow:ellipsis">{escape(detail)}</span>'
        f'<span style="color:{DIM}">{seconds:.1f}s</span></div>')


class Step:
    """Handle for one running step: ``done()`` sets the closing summary."""

    def __init__(self, title):
        self.title, self.detail, self.summary = title, "", ""

    def done(self, summary):
        self.summary = summary


def describe(event):
    """One line of real progress for a placement or routing event."""
    if event["kind"] == "place":
        return f"焼きなまし {event['step']}/{event['steps']} · 配線長 {event['hpwl']/1e3:.2f} mm"
    if event["kind"] == "route":
        retry = f" · やり直し{event['attempt']}回目" if event["attempt"] else ""
        return f"配線 {event['done']}/{event['total']} 本 · {event['net']}{retry}"
    return event.get("text", "")


@contextmanager
def step(title, *, view=None):
    """Show ``title`` with live progress until the block ends.

    ``view`` (for example a :class:`LayoutView`) receives every progress event
    and is redrawn below the line while the step runs.
    """
    current = Step(title)
    line = display(_line(SPINNER[0], CYAN, title, "", 0.0), display_id=True)
    picture = display(HTML(""), display_id=True) if view else None
    started, stop = time.monotonic(), threading.Event()

    def listen(event):
        current.detail = describe(event)
        if view:
            view.add(event)

    def redraw():
        frame, drawn = 0, -1
        while not stop.wait(0.1):
            frame += 1
            line.update(_line(SPINNER[frame % len(SPINNER)], CYAN, title, current.detail,
                              time.monotonic()-started))
            if view and view.version != drawn and frame % 3 == 0:
                drawn = view.version
                picture.update(HTML(view.svg()))

    ticker = threading.Thread(target=redraw, daemon=True)
    ticker.start()
    try:
        with progress.listening(listen), _streamed_tools(lambda text: setattr(current, "detail", text)):
            yield current
    except BaseException as error:
        stop.set()
        ticker.join()
        line.update(_line("✗", RED, title, f"{type(error).__name__}: {error}"[:160],
                          time.monotonic()-started))
        raise
    stop.set()
    ticker.join()
    line.update(_line("✓", GREEN, title, current.summary, time.monotonic()-started))
    if view:
        picture.update(HTML(view.svg()))


# --- KLayout and ngspice: read their output while they run ---------------------------------

def _klayout_progress():
    count = 0
    def parse(text):
        nonlocal count
        match = re.match(r'"([^"]+)" in: ([\w.]+):\d+', text)
        if match:
            count += 1
            return f"KLayout · 処理 {count} · {match[2]}"
    return parse


def _ngspice_progress(folder):
    deck = os.path.join(folder or ".", "tb.spice")
    stop = None
    if os.path.isfile(deck):
        found = re.search(r"(?im)^\s*\.?tran\s+\S+\s+([0-9.eE+-]+)", open(deck).read())
        stop = float(found[1]) if found else None
    def parse(text):
        match = re.search(r"Reference value\s*:\s*([-+0-9.eE]+)", text)
        if match:
            now = float(match[1])
            return f"ngspice · t = {now*1e6:.2f}" + (f" / {stop*1e6:.2f} µs" if stop else " µs")
    return parse


@contextmanager
def _streamed_tools(report):
    """While a step runs, KLayout and ngspice report from their output as they work."""
    original = subprocess.run

    def run(command, *args, **options):
        name = os.path.basename(str(command[0])) if isinstance(command, (list, tuple)) and command else ""
        if args or not (options.get("capture_output") and options.get("text")) or \
                not ("klayout" in name or "ngspice" in name):
            return original(command, *args, **options)
        if "klayout" in name:
            # -d 11 makes KLayout log each DRC/LVS operation; the results are unchanged.
            parse, launched = _klayout_progress(), [command[0], "-d", "11", *command[1:]]
        else:
            parse, launched = _ngspice_progress(options.get("cwd")), list(command)
        # Both tools are silent for a few seconds while they load decks or the operating point.
        report("KLayout · 起動中" if "klayout" in name else "ngspice · 動作点を計算中")
        timeout = options.pop("timeout", None)
        options.pop("capture_output"), options.pop("text")
        process = subprocess.Popen(launched, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, **options)
        captured = {"out": [], "err": []}

        def drain(stream, key):
            pending = ""
            for chunk in iter(lambda: stream.read(512), ""):
                captured[key].append(chunk)
                *lines, pending = re.split(r"[\r\n]", pending+chunk)
                for text in lines:
                    if (detail := parse(text)):
                        report(detail)

        readers = [threading.Thread(target=drain, args=(process.stdout, "out"), daemon=True),
                   threading.Thread(target=drain, args=(process.stderr, "err"), daemon=True)]
        for reader in readers:
            reader.start()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise
        for reader in readers:
            reader.join()
        return subprocess.CompletedProcess(command, process.returncode,
                                           "".join(captured["out"]), "".join(captured["err"]))

    subprocess.run = run
    try:
        yield
    finally:
        subprocess.run = original


# --- live placement and routing picture -----------------------------------------------------

CELL_FILL = {"INV": "#cfe3f7", "NAND": "#d8ecd2", "NOR": "#f3e2c7", "NANY": "#ead7f2",
             "BUF": "#e3e3e3", "TIEP": "#f7d0cf", "TIEZ": "#e0e0e0", "TIEN": "#cfd8f7", "FILL": "#f2f2f2"}


class LayoutView:
    """Cells as they are placed, then each net as it is routed (M1 blue, M2 red)."""

    def __init__(self):
        self.placements, self.routes, self.version, self.caption = [], {}, 0, ""

    def add(self, event):
        if event["kind"] == "place":
            self.placements = event["placements"]
            self.routes = {}
            self.caption = f"配置 {event['step']}/{event['steps']} · 配線長 {event['hpwl']/1e3:.2f} mm"
        elif event["kind"] == "route":
            if event["done"] == 1:
                self.routes = {}
            self.routes[event["net"]] = event["segments"]
            self.caption = f"配線 {event['done']}/{event['total']} 本"
        self.version += 1

    def svg(self, width=720):
        if not self.placements:
            return ""
        xs = [p["x"] for p in self.placements]+[p["x"]+p["width"] for p in self.placements]
        ys = [p["y"] for p in self.placements]+[p["y"]+p["height"] for p in self.placements]
        for segments in self.routes.values():
            for _, x0, y0, x1, y1 in segments:
                xs += [x0, x1]
                ys += [y0, y1]
        pad = 10
        x0, x1, y0, y1 = min(xs)-pad, max(xs)+pad, min(ys)-pad, max(ys)+pad
        stroke = max(x1-x0, y1-y0)/300
        parts = [f'<rect x="{p["x"]}" y="{p["y"]}" width="{p["width"]}" height="{p["height"]}" '
                 f'fill="{CELL_FILL.get(p["cell"], "#eee")}" stroke="#7a7f87" stroke-width="{stroke}"/>'
                 for p in self.placements]
        for segments in self.routes.values():
            for layer, a, b, c, d in segments:
                color = "#2f6fd6" if layer == "M1" else "#d6452f"
                parts.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{color}" '
                             f'stroke-width="{stroke*2.2}" stroke-linecap="round"/>')
        return (f'<div style="{FONT};color:{DIM}">{escape(self.caption)}</div>'
                f'<svg viewBox="{x0} {-y1} {x1-x0} {y1-y0}" style="width:100%;max-width:{width}px;'
                f'height:auto;background:#fbfbfa;border:1px solid #e3e3e0">'
                f'<g transform="scale(1,-1)">{"".join(parts)}</g></svg>')


# --- running cells out of order ------------------------------------------------------------

class NotReady(Exception):
    """A cell ran before the cell that makes what it needs."""

    def __init__(self, first, why):
        super().__init__(f"先に「{first}」を実行してください。{why}")
        self.first, self.why = first, why


PRODUCERS = {}


def provides(name, cell):
    """Record that ``cell`` defines notebook variable ``name``."""
    PRODUCERS[name] = cell


def need(*names, why=""):
    """Stop with a clear message when a variable this cell uses is not defined yet."""
    from IPython import get_ipython
    namespace = get_ipython().user_ns
    for name in names:
        if name not in namespace:
            raise NotReady(PRODUCERS.get(name, f"{name} を作るセル"), why)


def _box(first, why):
    return HTML(
        f'<div style="{FONT};border-left:4px solid {RED};background:rgba(208,52,44,.07);'
        f'padding:.6em 1em;margin:.3em 0">'
        f'<div style="color:{RED};font-weight:700">✗ このセルはまだ実行できません</div>'
        f'<div style="margin-top:.3em">先に <b>「{escape(first)}」</b> を実行してください。</div>'
        + (f'<div style="color:{DIM}">理由：{escape(why)}</div>' if why else "") + '</div>')


def install_error_view():
    """Show the 'run this first' box ahead of the traceback for out-of-order cells."""
    from IPython import get_ipython
    shell = get_ipython()
    if shell is None:
        return

    def show(shell, kind, value, traceback, tb_offset=None):
        if isinstance(value, NotReady):
            display(_box(value.first, value.why))
            shell.showtraceback((kind, value, traceback), tb_offset=tb_offset, exception_only=True)
            return
        missing = re.search(r"name '(\w+)' is not defined", str(value))
        if missing and missing[1] in PRODUCERS:
            display(_box(PRODUCERS[missing[1]], f"このセルは {missing[1]} を使います。"))
        shell.showtraceback((kind, value, traceback), tb_offset=tb_offset)

    shell.set_custom_exc((NotReady, NameError), show)
