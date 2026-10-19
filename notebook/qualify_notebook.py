"""Execute every code cell in a fresh kernel and retain a concise audit report.

--patched-colab tests a known uncommitted patch on a real Colab clone. Only
the bootstrap's dirty-tree rejection is relaxed; the actual Colab setup path
and all scientific cells execute as shipped. This is never release proof.
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


def qualify(root, output, patched_colab=False):
    import nbformat
    from nbclient import NotebookClient
    class PinnedKernelClient(NotebookClient):
        """Use this exact venv, retaining Colab's launcher when running there."""
        def create_kernel_manager(self):
            manager = super().create_kernel_manager()
            manager.kernel_spec.argv[0] = sys.executable
            return manager
    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    path = root/"notebook/tritflow_tr1um.ipynb"
    document = nbformat.read(path, as_version=4)
    setup = next(c for c in document.cells if c.get("id") == "setup")
    if patched_colab:
        before = 'if SOURCE_COMMIT != requested_commit or source_git("status", "--porcelain", "--untracked-files=no"):'
        if before not in setup.source:
            raise RuntimeError("Bootstrap changed; inspect the patch qualification adapter")
        setup.source = setup.source.replace(before,
            'if SOURCE_COMMIT != requested_commit:  # known working-tree patch qualification')
    probe = """import sys, json
print('QUALIFICATION_INITIAL_KERNEL '+json.dumps({
    'python': sys.version,
    'preloaded': {n: getattr(sys.modules[n], '__version__', None) for n in
                  ('numpy','scipy','matplotlib','plotly','PIL','IPython','ipywidgets',
                   'cycler','dateutil','kiwisolver','packaging','pyparsing','contourpy','fontTools')
                  if n in sys.modules}}))
"""
    setup.source = (probe+f"import sys\nassert sys.prefix == {sys.prefix!r}, 'Wrong qualification kernel'\n"
                    +setup.source)
    os.environ["TRITFLOW_ROOT"] = str(root)
    os.environ.setdefault("TRITFLOW_NOTEBOOK_BUILD", str(output/"flow"))
    os.environ.setdefault("TRITFLOW_NOTEBOOK_HEADLESS", "1")
    def progress(cell, cell_index, execute_reply):
        print("executed", cell_index, cell.get("id"),
              execute_reply.get("content",{}).get("status"),flush=True)
    started = time.monotonic()
    PinnedKernelClient(document, timeout=1800, kernel_name="python3", allow_errors=True,
                   on_cell_executed=progress,
                   resources={"metadata":{"path":str(root)}}).execute()
    rows = []
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    for index, cell in enumerate(document.cells):
        if cell.cell_type != "code":
            continue
        errors = [ansi.sub("", "\n".join(o.get("traceback",[])))
                  for o in cell.outputs if o.output_type == "error"]
        row = {"index":index,"id":cell.id,"status":"ERROR" if errors else "ok", "tracebacks":errors}
        rows.append(row)
        print(index,cell.id,row["status"],flush=True)
        for error in errors:
            print(error,flush=True)
    initial = None
    for result in setup.outputs:
        if result.output_type == "stream":
            for line in result.get("text", "").splitlines():
                if line.startswith("QUALIFICATION_INITIAL_KERNEL "):
                    initial = json.loads(line.split(" ", 1)[1])
    revision = (subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],text=True).strip()
                if (root/".git").exists() else "source export")
    report = {"source_base_commit":revision, "initial_kernel":initial,
              "notebook_sha256":sha256(path.read_bytes()).hexdigest(),
              "patched_colab_bootstrap":patched_colab,"seconds":time.monotonic()-started,
              "kernel_python":document.metadata.get("language_info",{}).get("version"),
              "interpreter":sys.executable,"prefix":sys.prefix,
              "cells":rows,"passed":all(r["status"] == "ok" for r in rows)}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    nbformat.write(document,output/"executed.ipynb")
    print(json.dumps({k:v for k,v in report.items() if k != "cells"}),flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path,default=Path("build/pin/notebook"))
    parser.add_argument("--patched-colab",action="store_true")
    args = parser.parse_args()
    result = qualify(args.root,args.output,args.patched_colab)
    raise SystemExit(0 if result["passed"] else 1)
