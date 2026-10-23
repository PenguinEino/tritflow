"""Execute chapter-6 helpers locally, export their outputs, and screenshot them.

Uses a real Jupyter kernel for live display updates and the same ngspice-42 as
Colab. The standalone HTMLs and PNGs are visual evidence, not cached tool results.
"""

from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
import subprocess
import sys

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def output_html(cell):
    """Preserve final rich outputs, including Plotly and the replay's scripts."""
    import plotly.io as pio

    parts = []
    for output in cell.get("outputs", []):
        data = output.get("data", {})
        if "text/html" in data:
            parts.append(data["text/html"])
        elif "application/vnd.plotly.v1+json" in data:
            parts.append(pio.to_html(data["application/vnd.plotly.v1+json"], include_plotlyjs=True, full_html=False))
        elif output["output_type"] == "error":
            raise RuntimeError(f"{output['ename']}: {output['evalue']}")
        elif output["output_type"] == "stream":
            parts.append(f"<pre>{escape(output['text'])}</pre>")
    return "\n".join(parts)


def verify():
    work = HERE / ".work/validation"
    work.mkdir(parents=True, exist_ok=True)
    sources = [
        f"""import sys
from pathlib import Path
sys.path[:0] = [{str(ROOT)!r}, {str(ROOT / 'notebook')!r}]
from reuse import DEFAULT_SOURCE, DOT4_SOURCE, run, shuttle_view
from live import install_error_view
install_error_view()
OUT = Path({str(work)!r})
""",
        "reuse_source = DEFAULT_SOURCE",
        """fixed = run(reuse_source, output_dir=OUT/'fixed')
assert fixed.summary['passed'], fixed.summary
assert fixed.summary['constant_folding']['cells_removed'] == 15
assert fixed.summary['stimulus']['unique_states'] == 81
""",
        """edited = run('''module edited(input trit a, b, c, d, e, f, output trit y);
  assign y = a & b & c & d & e & f;
endmodule''', output_dir=OUT/'edited', sample_size=13)
assert edited.summary['passed'], edited.summary
assert edited.summary['stimulus']['mode'] == 'sampled states'
assert edited.summary['stimulus']['unique_states'] == 13
""",
        """bad = run('''module broken(input trit a, output trit y);
  assign y = missing;
endmodule''', output_dir=OUT/'bad')
assert bad is None
""",
        "shuttle = shuttle_view()",
    ]
    book = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(s) for s in sources])
    book.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    os.environ["NGSPICE_BINARY"] = str(Path.home() / ".local/opt/tritflow-ubuntu-24.04/bin/ngspice")
    os.environ["TR1UM_PDK"] = str(Path.home() / "pdk/TR-1um-pinned")
    client = NotebookClient(book, timeout=900, resources={"metadata": {"path": str(ROOT)}},
                            on_cell_start=lambda cell, cell_index: print(f"Executing cell {cell_index}", flush=True))
    try:
        client.execute()
    finally:
        nbformat.write(book, work / "executed.ipynb")
    chrome = "google-chrome"
    for label, index in (("reuse", 2), ("reuse_edited", 3), ("reuse_error", 4), ("shuttle", 5)):
        html = ("<!doctype html><meta charset='utf-8'><style>body{margin:24px;background:white;max-width:1120px}"
                "pre{white-space:pre-wrap}</style>" + output_html(book.cells[index]))
        path = work / f"{label}.html"
        path.write_text(html)
        result = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                                 f"--user-data-dir={work / 'chrome'}", "--window-size=1200,3800",
                                 "--virtual-time-budget=8000", f"--screenshot={HERE / (label + '.png')}",
                                 path.as_uri()], capture_output=True, text=True, timeout=45)
        if result.returncode:
            raise RuntimeError(result.stderr[-4000:])
        print(f"Rendered {label}.png", flush=True)
    # Also retain a conventional GDS raster independent of the HTML viewer.
    sys.path.insert(0, str(ROOT))
    from tritflow.viz.layout import render_gds
    render_gds(HERE / "tr_1um_dot4.gds", HERE / "tr_1um_dot4.png", top="tr_1um_dot4")
    measurements = {label: json.loads((work / label / "summary.json").read_text()) for label in ("fixed", "edited")}
    (HERE / "reuse_validation.json").write_text(json.dumps(measurements, indent=2) + "\n")
    print("Local notebook execution and headless Chrome renders passed", flush=True)


if __name__ == "__main__":
    verify()
