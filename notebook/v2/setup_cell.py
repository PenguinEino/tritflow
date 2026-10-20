"""The v2 setup cell: fetch the pinned source, install tools, show progress throughout.

``SOURCE_REF`` is replaced with the implementation commit when a notebook is built.
"""

SETUP = r'''
import os, sys, json, time, subprocess, importlib.util, re
from pathlib import Path
SOURCE_URL = "https://github.com/PenguinEino/tritflow.git"
SOURCE_REF = os.environ.get("TRITFLOW_REF", "PINNED")
try:
    IN_COLAB = importlib.util.find_spec("google.colab") is not None
except ModuleNotFoundError:
    IN_COLAB = False

def git(*args, progress=None):
    """Run git; with ``progress``, redraw git's own counter on one line."""
    if progress is None:
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    process = subprocess.Popen(["git", *args], stderr=subprocess.PIPE, text=True)
    for chunk in iter(lambda: process.stderr.read(64), ""):
        last = re.split(r"[\r\n]", chunk.strip())[-1]
        if last:
            print(f"\r⠿ {progress}  {last[:70]:<70}", end="", flush=True)
    if process.wait():
        raise RuntimeError(f"git {' '.join(args[:2])} failed")
    print(f"\r✓ {progress}{' '*72}", flush=True)

if IN_COLAB:
    ROOT = Path("/content/tritflow")
    if not re.fullmatch(r"[0-9a-f]{40}", SOURCE_REF):
        raise ValueError("TRITFLOW_REF must be a full 40-character commit")
    if not ROOT.exists():
        git("clone", "--progress", "--no-checkout", "--depth", "1", "--filter=blob:none",
            SOURCE_URL, str(ROOT), progress="GitHubからソースを取得")
        git("-C", str(ROOT), "fetch", "--progress", "--depth", "1", "origin", SOURCE_REF,
            progress=f"コミット {SOURCE_REF[:7]} を取得")
        git("-C", str(ROOT), "switch", "--detach", SOURCE_REF, progress="ファイルを展開")
    if git("rev-parse", "HEAD") != SOURCE_REF or git("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("/content/tritflow differs from the pinned commit; connect a fresh runtime")
else:
    candidates = [Path(os.environ.get("TRITFLOW_ROOT", ".")), Path.cwd(), Path.cwd().parent]
    ROOT = next((p.resolve() for p in candidates if (p/"tritflow").is_dir() and (p/"notebook").is_dir()), None)
    if ROOT is None:
        raise RuntimeError("run from the TritFlow checkout or set TRITFLOW_ROOT")
sys.path[:0] = [str(ROOT), str(ROOT/"notebook")]
from live import step, run_stages
from runtime_support import SETUP_SCHEMA, setup_identity, check_runtime, print_tool_versions
runtime = ROOT/"notebook/runtime.json"
if IN_COLAB and (not runtime.is_file()
                 or json.loads(runtime.read_text()).get("TRITFLOW_SETUP_SHA256") != setup_identity(ROOT)):
    os.environ["TRITFLOW_NOTEBOOK_LANGUAGE"] = "ja"
    run_stages(["bash", str(ROOT/"notebook/colab_setup.sh"), "--source", str(ROOT)])
if runtime.is_file():
    os.environ.update(json.loads(runtime.read_text()))
    sys.path.insert(0, os.environ["TRITFLOW_PYTHON_TARGET"])
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
with step("ツールを確認") as s:
    check_runtime()
    tools = print_tool_versions()
    s.done(" · ".join(re.search(r"(KLayout [\d.]+|ngspice-\d+)", v)[1] for v in tools.values()))
BUILD = Path(os.environ.get("TRITFLOW_NOTEBOOK_BUILD", "/content/build" if IN_COLAB else ROOT/"build/notebook")).resolve()
'''
