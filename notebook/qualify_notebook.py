"""Execute notebook v3 in fresh local kernels and retain outputs and reports.

The default run checks both languages. It uses the installed tools and PDK;
no dependencies are installed and no source files or release pins are changed.
"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def qualify(root, output, language="en"):
    """Execute one language with this interpreter; report every cell error."""
    import nbformat
    from nbclient import NotebookClient

    class PinnedKernelClient(NotebookClient):
        def create_kernel_manager(self):
            manager = super().create_kernel_manager()
            manager.kernel_spec.argv[0] = sys.executable
            return manager

    if language not in ("en", "ja"):
        raise ValueError(f"unknown language: {language}")
    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    path = root / "notebook/v3" / f"tritflow_{language}.ipynb"
    document = nbformat.read(path, as_version=4)

    def progress(cell, cell_index, execute_reply):
        status = execute_reply.get("content", {}).get("status")
        print(language, "executed", cell_index, cell.get("id"), status, flush=True)

    environment = {"TRITFLOW_ROOT": str(root), "TRITFLOW_NOTEBOOK_BUILD": str(output / "flow"),
                   "TRITFLOW_NOTEBOOK_HEADLESS": "1"}
    previous = {name: os.environ.get(name) for name in environment}
    started = time.monotonic()
    try:
        os.environ.update(environment)
        PinnedKernelClient(document, timeout=1200, kernel_name="python3", allow_errors=True,
                           on_cell_executed=progress,
                           resources={"metadata": {"path": str(root)}}).execute()
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    ansi = re.compile(r"\x1b\[[0-9;]*m")
    rows = []
    for index, cell in enumerate(document.cells):
        if cell.cell_type != "code":
            continue
        errors = [ansi.sub("", "\n".join(result.get("traceback", [])))
                  for result in cell.outputs if result.output_type == "error"]
        rows.append({"index": index, "id": cell.id,
                     "status": "ERROR" if errors else "ok", "tracebacks": errors})
        for error in errors:
            print(error, flush=True)
    revision = (subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
                if (root / ".git").exists() else "source export")
    report = {"source_base_commit": revision, "language": language,
              "notebook_sha256": sha256(path.read_bytes()).hexdigest(),
              "seconds": time.monotonic() - started,
              "kernel_python": document.metadata.get("language_info", {}).get("version"),
              "interpreter": sys.executable, "prefix": sys.prefix,
              "cells": rows, "passed": all(row["status"] == "ok" for row in rows)}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    nbformat.write(document, output / "executed.ipynb")
    print(json.dumps({key: value for key, value in report.items() if key != "cells"}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("build/qualification"))
    parser.add_argument("--language", choices=("en", "ja", "both"), default="both")
    args = parser.parse_args()
    languages = ("en", "ja") if args.language == "both" else (args.language,)
    reports = [qualify(args.root, args.output / language, language) for language in languages]
    return 0 if all(report["passed"] for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
