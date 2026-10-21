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


class Line:
    """One status line, redrawn by a background thread until :meth:`close`."""

    def __init__(self, title, view=None):
        self.title, self.detail, self.summary, self.view = title, "", "", view
        self.handle = display(_line(SPINNER[0], CYAN, title, "", 0.0), display_id=True)
        self.picture = display(HTML(""), display_id=True) if view else None
        self.started, self.stop = time.monotonic(), threading.Event()
        self.ticker = threading.Thread(target=self._redraw, daemon=True)
        self.ticker.start()

    def done(self, summary):
        """Set the closing summary shown after the check mark."""
        self.summary = summary

    def _redraw(self):
        frame, drawn = 0, -1
        while not self.stop.wait(0.1):
            frame += 1
            self.handle.update(_line(SPINNER[frame % len(SPINNER)], CYAN, self.title, self.detail,
                                     time.monotonic()-self.started))
            if self.view and self.view.version != drawn and frame % 6 == 0:
                drawn = self.view.version
                self.picture.update(HTML(self.view.svg()))

    def close(self, error=None):
        self.stop.set()
        self.ticker.join()
        seconds = time.monotonic()-self.started
        if error is None:
            self.handle.update(_line("✓", GREEN, self.title, self.summary, seconds))
        else:
            self.handle.update(_line("✗", RED, self.title, f"{type(error).__name__}: {error}"[:160], seconds))
        if self.view:
            self.picture.update(HTML(self.view.svg()))


Step = Line


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
    # Imported here: setup loads this module before TritFlow's runtime settings exist.
    from tritflow import progress
    line = Line(title, view)

    def listen(event):
        line.detail = describe(event)
        if view:
            view.add(event)

    try:
        with progress.listening(listen), _streamed_tools(lambda text: setattr(line, "detail", text)):
            yield line
    except BaseException as error:
        line.close(error)
        raise
    line.close()


def run_stages(command, **options):
    """Run an installer that prints ``@stage``, ``@files`` and ``@progress`` lines, one ✓ line per stage."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1, **options)
    line, tail, files, expected = None, [], {}, 0
    for text in process.stdout:
        text = text.rstrip("\n")
        tail = (tail+[text])[-80:]
        if text.startswith("@stage "):
            if line:
                line.close()
            line, files, expected = Line(text[7:]), {}, 0
        elif text.startswith("@files "):
            expected = int(text.split()[1])
        elif text.startswith("@progress ") and line:
            done, total, label = text.split(" ", 3)[1:]
            files[label] = (int(done), int(total))
            finished = sum(1 for d, t in files.values() if t and d >= t)
            megabytes = sum(d for d, _ in files.values())/1e6
            # After the last download the installer unpacks; say so instead of a frozen counter.
            unpacking = " · 展開中" if expected > 1 and finished >= expected else ""
            line.detail = (f"{finished}/{max(expected, len(files))} ファイル · {megabytes:.1f} MB{unpacking}" if expected > 1
                           else f"{label} · {megabytes:.1f} MB")
        elif line and (found := re.match(r"\s*(Collecting|Downloading)\s+(\S+)", text)):
            line.detail = f"pip · {found[2]}"
        elif line and text.startswith("Installing collected packages"):
            line.detail = "pip · 展開してインストール中"
    process.wait()
    if process.returncode:
        error = subprocess.CalledProcessError(process.returncode, command, "\n".join(tail))
        if line:
            line.close(error)
        print("\n".join(tail))
        raise error
    if line:
        line.close()


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
        # Only DRC/LVS decks (-r) and batch simulations (-b) are streamed; version probes are not.
        if args or not (options.get("capture_output") and options.get("text")) or not (
                ("klayout" in name and "-r" in command) or ("ngspice" in name and "-b" in command)):
            return original(command, *args, **options)
        if "klayout" in name:
            # -d 11 makes KLayout log each DRC/LVS operation; the results are unchanged.
            parse, launched = _klayout_progress(), [command[0], "-d", "11", *command[1:]]
        else:
            parse, launched = _ngspice_progress(options.get("cwd")), list(command)
        # Both tools are silent for a few seconds while they load decks or the operating point.
        report("KLayout · 起動中" if "klayout" in name else "ngspice · 動作点を計算中")
        timeout, check = options.pop("timeout", None), options.pop("check", False)
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
        result = subprocess.CompletedProcess(command, process.returncode,
                                             "".join(captured["out"]), "".join(captured["err"]))
        if check:
            result.check_returncode()
        return result

    subprocess.run = run
    try:
        yield
    finally:
        subprocess.run = original


# --- live placement and routing picture, drawn like KLayout ---------------------------------

def _style():
    # Imported on use: setup loads this module before TritFlow's runtime settings exist.
    from tritflow.viz.layers import LAYER_STYLE
    return tuple((key, color, hatch, opacity) for key, _, color, hatch, opacity in LAYER_STYLE)


def _patterns(unit):
    """SVG hatches sized to the view, one per layer."""
    defs = []
    for (layer, datatype), color, hatch, _ in _style():
        key, size = f"L{layer}_{datatype}", 4*unit
        if hatch == "fwd":
            body = f'<path d="M0,{size} L{size},0" stroke="{color}" stroke-width="{unit*.7}"/>'
        elif hatch == "back":
            body = f'<path d="M0,0 L{size},{size}" stroke="{color}" stroke-width="{unit*.7}"/>'
        elif hatch == "dots":
            body = f'<circle cx="{size/2}" cy="{size/2}" r="{unit*.6}" fill="{color}"/>'
        elif hatch == "cross":
            body = (f'<path d="M0,0 L{size},{size} M0,{size} L{size},0" stroke="{color}" '
                    f'stroke-width="{unit*.5}"/>')
        else:
            continue
        defs.append(f'<pattern id="{key}" width="{size}" height="{size}" patternUnits="userSpaceOnUse">{body}</pattern>')
    return "".join(defs)


def _layer_paths(shapes, unit):
    """One <path> per layer holding all its polygons; hatched fill, outline in the layer color."""
    by_style = {}
    for style, points in shapes:
        by_style.setdefault(style, []).append("M" + " L".join(f"{x:.6g},{y:.6g}" for x, y in points) + "Z")
    out = []
    for style in _style():
        if style not in by_style:
            continue
        (layer, datatype), color, hatch, opacity = style
        d = "".join(by_style[style])
        if opacity:
            out.append(f'<path d="{d}" fill="{color}" fill-opacity="{opacity}"/>')
        fill = f"url(#L{layer}_{datatype})" if hatch else "none"
        out.append(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{unit*.6:.3g}"/>')
    return "".join(out)


class LayoutView:
    """The real cell GDS, placed as annealing moves it, then each net routed at its drawn width."""

    def __init__(self, cells_dir=None):
        from tritflow import CELLS_DIR
        self.cells_dir = cells_dir or CELLS_DIR
        self.geometry = {}
        self.placements, self.routes, self.version, self.caption = [], {}, 0, ""
        self.newest = None

    def _cell(self, name):
        """Polygons of one standard cell per drawn layer, read once from its GDS."""
        if name not in self.geometry:
            import klayout.db as db
            layout = db.Layout()
            layout.read(str(self.cells_dir/f"out/{name}/{name}.gds"))
            top, shapes = layout.top_cell(), []
            for style in _style():
                index = layout.find_layer(*style[0])
                if index is None:
                    continue
                for item in top.begin_shapes_rec(index).each():
                    polygon = item.shape().polygon.transformed(item.trans()).to_dtype(layout.dbu)
                    shapes.append((style, [(p.x, p.y) for p in polygon.each_point_hull()]))
            self.geometry[name] = shapes
        return self.geometry[name]

    def add(self, event):
        if event["kind"] == "place":
            self.placements, self.routes = event["placements"], {}
            self.caption = f"配置 {event['step']}/{event['steps']} · 配線長 {event['hpwl']/1e3:.2f} mm"
        elif event["kind"] == "route":
            if event["done"] == 1:
                self.routes = {}
            self.routes[event["net"]] = event["segments"]
            self.newest = event["net"] if event["done"] < event["total"] else None
            self.caption = f"配線 {event['done']}/{event['total']} 本 · {event['net']}"
        self.version += 1

    def svg(self, width=760):
        if not self.placements:
            return ""
        xs = [v for p in self.placements for v in (p["x"], p["x"]+p["width"])]
        ys = [v for p in self.placements for v in (p["y"], p["y"]+p["height"])]
        for route in self.routes.values():
            for _, a, b, c, d in route["wires"]:
                xs += [a, c]
                ys += [b, d]
        pad = 8
        x0, x1, y0, y1 = min(xs)-pad, max(xs)+pad, min(ys)-pad, max(ys)+pad
        unit = max(x1-x0, y1-y0)/400
        # Each cell type is drawn once and reused; MY mirrors it about the cell's own width.
        cells = sorted({p["cell"] for p in self.placements})
        symbols = "".join(f'<g id="tf-{name}">{_layer_paths(self._cell(name), unit)}</g>' for name in cells)
        uses = "".join(
            f'<use href="#tf-{p["cell"]}" transform="translate({p["x"]+p["width"]:g},{p["y"]:g}) scale(-1,1)"/>'
            if p["orient"] == "MY" else f'<use href="#tf-{p["cell"]}" transform="translate({p["x"]:g},{p["y"]:g})"/>'
            for p in self.placements)
        from tritflow.viz.layers import WIRE_WIDTH, VIA_SIZE
        m1, v1, m2 = _style()[7], _style()[8], _style()[9]
        wires, newest = [], []
        for net, route in self.routes.items():
            target = newest if net == self.newest else wires
            for layer, a, b, c, d in route["wires"]:
                half = WIRE_WIDTH[layer]/2
                left, right, low, high = min(a, c)-half, max(a, c)+half, min(b, d)-half, max(b, d)+half
                target.append((m1 if layer == "M1" else m2, [(left, low), (right, low), (right, high), (left, high)]))
            for x, y in route["vias"]:
                h = VIA_SIZE/2
                target.append((v1, [(x-h, y-h), (x+h, y-h), (x+h, y+h), (x-h, y+h)]))
        # The net just routed glows, so each frame shows what changed.
        glow = "".join(f'<path d="M{" L".join(f"{x:.6g},{y:.6g}" for x, y in points)}Z" fill="#ff8a00" '
                       f'fill-opacity=".55" stroke="#ff8a00" stroke-width="{unit*2.5:.3g}"/>' for _, points in newest)
        return (f'<div style="{FONT};color:{DIM}">{escape(self.caption)}</div>'
                f'<svg viewBox="{x0:g} {-y1:g} {x1-x0:g} {y1-y0:g}" style="width:100%;max-width:{width}px;'
                f'height:auto;background:#fff;border:1px solid #d5d7db;border-radius:6px">'
                f'<defs>{_patterns(unit)}{symbols}</defs>'
                f'<g transform="scale(1,-1)">{uses}{_layer_paths(wires, unit)}{glow}'
                f'{_layer_paths(newest, unit)}</g></svg>')


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
        + (f'<div style="color:{DIM}">{escape(why)}</div>' if why else "") + '</div>')


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


# --- controls in the figures: quiet, print-like buttons and sliders --------------------------

def control_style(scope):
    """CSS for radio-button labels and range sliders under ``scope``: thin rules, no fill colour,
    the selected choice in ink, like the controls of a figure rather than an app."""
    ink, rule = "#2b2f36", "#b9bdc4"
    return (f"{scope} input[type=radio]{{display:none}}"
            f"{scope} input[type=radio] + label{{display:inline-block;padding:.12em .8em;margin:0 -1px .5em 0;"
            f"border:1px solid {rule};border-radius:0;cursor:pointer;font-size:13px;color:{ink};background:#fff}}"
            f"{scope} input[type=radio]:checked + label{{background:{ink};border-color:{ink};color:#fff}}"
            f"{scope} input[type=range]{{-webkit-appearance:none;appearance:none;width:100%;height:14px;"
            f"background:transparent;margin:.2em 0}}"
            f"{scope} input[type=range]::-webkit-slider-runnable-track{{height:1px;background:{rule}}}"
            f"{scope} input[type=range]::-moz-range-track{{height:1px;background:{rule}}}"
            f"{scope} input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;width:9px;height:9px;"
            f"margin-top:-4px;border-radius:50%;background:{ink};border:0}}"
            f"{scope} input[type=range]::-moz-range-thumb{{width:9px;height:9px;border-radius:50%;background:{ink};border:0}}")
