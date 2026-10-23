"""Render the canonical 16-pad stock-frame chip and shuttle_view with Chrome."""

from __future__ import annotations

from html import escape
from pathlib import Path
import os
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def verify(directory=None):
    import nbformat
    from nbclient import NotebookClient

    folder = Path(directory or HERE).resolve()
    work = HERE / ".work/frame_render"
    work.mkdir(parents=True, exist_ok=True)
    os.environ["JUPYTER_RUNTIME_DIR"] = str(work / "runtime")
    os.environ["IPYTHONDIR"] = str(work / "ipython")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    source = f"""import sys
sys.path[:0] = [{str(ROOT)!r}, {str(ROOT/'notebook')!r}]
from IPython.display import HTML, display
from live import set_language
from reuse import shuttle_view
set_language('en')
display(HTML('<p style="font-size:18px"><b>Programmable dot4 in the stock 16-pad OSS_FRAME</b></p>'))
chip = shuttle_view({str(folder)!r})
assert len(chip['pad_map']) == 16
assert chip['clean']
"""
    book = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(source)])
    book.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    NotebookClient(
        book, timeout=180, resources={"metadata": {"path": str(ROOT)}}
    ).execute()
    nbformat.write(book, work / "executed.ipynb")
    parts = []
    for output in book.cells[0].outputs:
        if output.output_type == "error":
            raise RuntimeError(str(output))
        if "text/html" in output.get("data", {}):
            parts.append(output.data["text/html"])
    style = "<meta charset='utf-8'><style>body{margin:24px;background:white;max-width:1120px}</style>"
    shuttle = work / "shuttle.html"
    shuttle.write_text("<!doctype html>" + style + "\n".join(parts))
    raster = work / "klayout.html"
    raster.write_text(
        "<!doctype html>"
        + style
        + "<h2>Stock OSS_FRAME: KLayout raster and layer legend</h2>"
        + f"<img width='1120' src='{escape((folder/'tr_1um_dot4.png').as_uri())}'>"
    )
    for label, page, height in (
        ("shuttle", shuttle, 2400),
        ("klayout_chrome", raster, 1000),
    ):
        result = subprocess.run(
            [
                "google-chrome",
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--user-data-dir={work/'chrome'}",
                f"--crash-dumps-dir={work/'crash'}",
                f"--window-size=1200,{height}",
                "--virtual-time-budget=8000",
                f"--screenshot={work/(label+'.png')}",
                page.as_uri(),
            ],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if result.returncode:
            raise RuntimeError(result.stderr[-4000:])
        print(f"Rendered {label}.png", flush=True)


if __name__ == "__main__":
    verify()
