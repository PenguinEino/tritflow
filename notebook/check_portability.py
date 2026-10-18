"""Run the default notebook from tracked files with fresh PDK and build outputs.

This uses read-only ``git ls-files``/``rev-parse`` rather than cloning: streams
may not change git state. Tracked working-tree edits are included and hashed;
untracked files, .git and ignored build outputs are excluded. The integrator
can run it again after committing to test exactly the release tree.

Python file access to the original checkout, HOME PDK/reference/tool directories
is denied. strace checks native children for accesses to those same paths.
System/user Python dependencies remain available; this is an asset-portability
check, not a clean Ubuntu installation or a kernel filesystem sandbox.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from setup_colab import PINS, download, unpack_archive


ROOT = Path(__file__).resolve().parent.parent


def export_tracked(destination):
    """Copy tracked working files, retaining only relative in-tree symlinks."""
    names = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"]).decode().split("\0")
    hashes = {}
    for name in filter(None, names):
        source, target = ROOT/name, destination/name
        if name.startswith("build/"):
            raise RuntimeError("build outputs must not be tracked runtime inputs")
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            link = os.readlink(source)
            if Path(link).is_absolute() or not source.resolve().is_relative_to(ROOT):
                raise RuntimeError(f"nonportable tracked symlink: {name}")
            target.symlink_to(link)
            hashes[name] = "symlink:"+link
        else:
            shutil.copy2(source, target)
            hashes[name] = sha256(target.read_bytes()).hexdigest()
    assert not (destination/"build").exists()
    return hashes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, help="new directory for tree, PDK, logs and report")
    parser.add_argument("--pdk-archive", type=Path, help="optional previously downloaded pinned archive")
    parser.add_argument("--klayout-binary", type=Path, default=shutil.which("klayout"))
    args = parser.parse_args(argv)
    if not shutil.which("strace"):
        parser.error("strace is required to audit native child file accesses")
    if not args.klayout_binary or not args.klayout_binary.is_file():
        parser.error("provide an installed KLayout Ruby-capable binary")
    scratch = args.workdir.resolve() if args.workdir else Path(tempfile.mkdtemp(prefix="tritflow-portable-"))
    if args.workdir:
        scratch.mkdir(parents=True, exist_ok=False)
    tree = scratch/"tritflow"
    hashes = export_tracked(tree)
    base = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    (scratch/"tracked-files.json").write_text(json.dumps(hashes, indent=2)+"\n")
    archive = args.pdk_archive or scratch/"pdk.tar.gz"
    if not args.pdk_archive:
        download(f"https://codeload.github.com/OpenSUSI/TR-1um/tar.gz/{PINS['pdk_commit']}",
                 archive, PINS["pdk_archive_sha256"])
    assert sha256(archive.read_bytes()).hexdigest() == PINS["pdk_archive_sha256"], "pinned PDK SHA256"
    unpack_archive(archive, scratch/"pdk")
    pdk = scratch/"pdk"/f"TR-1um-{PINS['pdk_commit']}"
    # The local KLayout distribution lives under HOME. Relocate its adjacent
    # shared libraries/plugins too, so no tool path can reach the reference tree.
    original_binary = args.klayout_binary.resolve()
    if original_binary.is_relative_to(Path.home()):
        shutil.copytree(original_binary.parent, scratch/"klayout", symlinks=True)
        binary = scratch/"klayout"/original_binary.name
    else:
        binary = original_binary
    forbidden = [ROOT, Path.home()/"balanced-ternary-logic", Path.home()/"pdk",
                 Path.home()/"bin/klayout"]
    guard = scratch/"guarded_execute.py"
    guard.write_text(
        "import os, sys, runpy\n"
        f"blocked = {list(map(str, forbidden))!r}\n"
        "def audit(event, args):\n"
        "    if event not in {'open', 'os.listdir', 'os.scandir', 'os.chdir'} or not args:\n"
        "        return\n"
        "    if not isinstance(args[0], (str, bytes, os.PathLike)):\n"
        "        return\n"
        "    path = os.path.realpath(os.fsdecode(args[0]))\n"
        "    if any(path == p or path.startswith(p + '/') for p in blocked):\n"
        "        raise PermissionError('nonportable reference access: ' + path)\n"
        "sys.addaudithook(audit)\n"
        "sys.argv = ['validate_notebook.py', '--execute']\n"
        f"runpy.run_path({str(tree/'notebook/validate_notebook.py')!r}, run_name='__main__')\n"
        f"assert sys.modules['tritflow'].__file__.startswith({str(tree)!r} + '/')\n"
    )
    environment = {k: v for k, v in os.environ.items()
                   if not k.startswith("TRITFLOW_") and k not in {"TR1UM_PDK", "KLAYOUT_BINARY", "PYTHONPATH"}}
    environment.update(TR1UM_PDK=str(pdk), KLAYOUT_BINARY=str(binary), TRITFLOW_ROOT=str(tree),
                       QT_QPA_PLATFORM="offscreen", KLAYOUT_HOME=str(scratch/"klayout-config"),
                       XDG_CACHE_HOME=str(scratch/"cache"), XDG_CONFIG_HOME=str(scratch/"config"),
                       IPYTHONDIR=str(scratch/"ipython"), MPLCONFIGDIR=str(scratch/"matplotlib"))
    # The developer shell adds its HOME KLayout to both search paths. Do not
    # let the relocated executable accidentally load the original shared libs.
    environment["PATH"] = str(binary.parent)+":/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    environment["LD_LIBRARY_PATH"] = str(binary.parent)
    trace, log = scratch/"files.strace", scratch/"execution.log"
    command = ["strace", "-f", "-qq", "-e", "trace=%file", "-o", str(trace), sys.executable, str(guard)]
    print(f"Tracked-tree base commit: {base}; files: {len(hashes)}; scratch: {scratch}", flush=True)
    started = time.monotonic()
    with log.open("w") as stream:
        result = subprocess.run(command, cwd=tree, env=environment, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=600)
    accesses = [line for line in trace.read_text().splitlines()
                if any('"'+str(p)+'"' in line or str(p)+"/" in line for p in forbidden)]
    report = {"base_commit": base, "tracked_working_files": len(hashes),
              "tree_sha256": sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
              "pdk_commit": PINS["pdk_commit"], "pdk_archive_sha256": PINS["pdk_archive_sha256"],
              "returncode": result.returncode, "elapsed_s": time.monotonic()-started,
              "forbidden_native_accesses": accesses, "blocked_paths": list(map(str, forbidden)),
              "initial_build_exists": False, "execution_log": str(log), "trace": str(trace)}
    report["klayout_version"] = subprocess.check_output([str(binary), "-v"], env=environment, text=True).strip()
    report["ngspice_version"] = subprocess.check_output(["ngspice", "-v"], env=environment, text=True).strip()
    (scratch/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({**report, "forbidden_native_accesses": accesses[:5],
                      "forbidden_native_access_count": len(accesses)}, indent=2))
    if result.returncode or accesses:
        raise RuntimeError(f"portability check failed; inspect {log} and {trace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
