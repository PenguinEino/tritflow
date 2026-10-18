"""Validate notebook structure/code, optionally execute its default local flow.

No setup/installation is performed outside Colab. --execute uses the normal
notebook cells and headless Plotly serialization, leaving cache/artifacts under
TRITFLOW_NOTEBOOK_BUILD (default build/notebook). An exception is a failed run.
"""

import argparse
import json
import os
from pathlib import Path
import re


def validate(path):
    document = json.loads(Path(path).read_text())
    assert document["nbformat"] == 4 and document["nbformat_minor"] == 5
    ids = [c["id"] for c in document["cells"]]
    assert len(ids) == len(set(ids))
    markdown = "\n".join(c["source"] for c in document["cells"] if c["cell_type"] == "markdown")
    assert re.findall(r"(?m)^## (\d+)\.", markdown) == [str(i) for i in range(10)]
    for index, item in enumerate(document["cells"]):
        if item["cell_type"] == "code":
            assert item["execution_count"] is None and item["outputs"] == []
            compile(item["source"], f"notebook-cell-{index}", "exec")
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    document = validate(Path(__file__).with_name("tritflow_tr1um.ipynb"))
    print(f"Validated {len(document['cells'])} cells and chapters 0–9")
    if args.execute:
        os.environ["TRITFLOW_NOTEBOOK_HEADLESS"] = "1"
        namespace = {"__name__": "__notebook__"}
        for index, item in enumerate(document["cells"]):
            if item["cell_type"] == "code":
                print(f"Executing cell {index}", flush=True)
                exec(compile(item["source"], f"notebook-cell-{index}", "exec"), namespace)


if __name__ == "__main__":
    main()
