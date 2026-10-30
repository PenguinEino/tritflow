"""Validate notebook v3 structure and Python cells, optionally execute locally.

Validation checks the unexecuted source document. Execution uses the same cells
and setup as Colab, with generated flow artifacts under TRITFLOW_NOTEBOOK_BUILD.
"""

import argparse
import json
import os
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent


def validate(path):
    """Require chapters 1–7, unique cell IDs, and compilable output-free code."""
    document = json.loads(Path(path).read_text())
    assert document["nbformat"] == 4 and document["nbformat_minor"] == 5
    ids = [cell["id"] for cell in document["cells"]]
    assert len(ids) == len(set(ids))
    source = lambda cell: "".join(cell["source"])
    markdown = "\n".join(source(cell) for cell in document["cells"] if cell["cell_type"] == "markdown")
    assert re.findall(r"(?m)^## (\d+)\.", markdown) == [str(n) for n in range(1, 8)]
    for index, cell in enumerate(document["cells"]):
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None and cell["outputs"] == []
            compile(source(cell), f"notebook-cell-{index}", "exec")
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--language", choices=("en", "ja"), default="en")
    args = parser.parse_args()
    document = validate(HERE / "v3" / f"tritflow_{args.language}.ipynb")
    print(f"Validated {len(document['cells'])} cells and chapters 1–7 ({args.language})")
    if args.execute:
        os.environ["TRITFLOW_NOTEBOOK_HEADLESS"] = "1"
        namespace = {"__name__": "__notebook__"}
        for index, cell in enumerate(document["cells"]):
            if cell["cell_type"] == "code":
                print(f"Executing cell {index}", flush=True)
                exec(compile("".join(cell["source"]), f"notebook-cell-{index}", "exec"), namespace)


if __name__ == "__main__":
    main()
