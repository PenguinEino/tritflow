"""Install the pinned notebook runtime, or print its non-mutating --plan.

Official package index: https://www.klayout.de/build.html
PDK source: https://github.com/OpenSUSI/TR-1um
The Ubuntu release is detected at runtime; only explicit tested package mappings
are accepted. This script never installs software during --plan or its tests.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from urllib.request import urlopen

from runtime_support import MINIMUM_VERSIONS, SETUP_SCHEMA, check_minimum_versions, print_tool_versions, setup_identity
from native_runtime import install_native
from font_runtime import install_fonts


HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE/"setup_pins.json").read_text())


def ubuntu_version(path=Path("/etc/os-release")):
    values = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = shlex.split(value)[0] if value else ""
    if values.get("ID") != "ubuntu":
        raise ValueError("setup requires Ubuntu; --plan --ubuntu permits local planning")
    return values.get("VERSION_ID")


def package_for(version, architecture):
    if architecture not in {"amd64", "x86_64"}:
        raise ValueError("the pinned official KLayout packages require amd64")
    if version not in PINS["ubuntu_dependency_lock"]:
        raise ValueError(f"no qualified native runtime for Ubuntu {version}; use notebook/Dockerfile")
    return PINS["klayout_deb"][version]


def download(url, destination, checksum=None):
    destination = Path(destination)
    for attempt in range(4):
        try:
            with urlopen(url, timeout=120) as response, destination.open("wb") as stream:
                total, done, shown = int(response.headers.get("Content-Length") or 0), 0, 0.
                for chunk in iter(lambda: response.read(1 << 18), b""):
                    stream.write(chunk)
                    done += len(chunk)
                    if time.monotonic()-shown > .25:
                        progress(done, total, Path(url).name)
                        shown = time.monotonic()
                progress(done, total or done, Path(url).name)
            if checksum and sha256(destination.read_bytes()).hexdigest() != checksum:
                raise RuntimeError(f"SHA-256 mismatch: {url}")
            return
        except Exception:
            destination.unlink(missing_ok=True)
            if attempt == 3:
                raise
            time.sleep(1)


def unpack_archive(archive, destination):
    """Use Python's data filter and reject traversal on older supported runtimes."""
    destination = Path(destination).resolve()
    with tarfile.open(archive) as stream:
        for member in stream.getmembers():
            target = (destination/member.name).resolve()
            link = target.parent/member.linkname if member.issym() else destination/member.linkname
            if (not target.is_relative_to(destination)
                    or ((member.issym() or member.islnk()) and not link.resolve().is_relative_to(destination))):
                raise ValueError("archive contains an unsafe path/link")
        stream.extractall(destination, filter="data")


def bootstrap_pip(prefix):
    """Use a checked official wheel instead of Colab's changing pip installer."""
    pin = PINS["pip_wheel"]
    directory = Path(prefix)/("pip-"+pin["version"])
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory/"pip.whl"
    if not archive.is_file() or sha256(archive.read_bytes()).hexdigest() != pin["sha256"]:
        download(pin["url"], archive, pin["sha256"])
    with zipfile.ZipFile(archive) as wheel:
        wheel.extractall(directory)
    return directory/"pip"


def say(english, japanese):
    """Start a setup stage, named in the notebook's language.

    ``@stage``, ``@files`` and ``@progress`` lines are read by the notebook's progress view
    (notebook/live.py); in a terminal they are plain, readable log lines.
    """
    japanese_notebook = os.environ.get("TRITFLOW_NOTEBOOK_LANGUAGE") == "ja"
    print(f"@stage {japanese if japanese_notebook else english}", flush=True)


def progress(done, total, label):
    print(f"@progress {done} {total} {label}", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--source", type=Path, default=HERE.parent,
                        help="local checkout to install, including cells/out and examples")
    parser.add_argument("--prefix", type=Path, default=Path("/content/tritflow-runtime"))
    parser.add_argument("--ubuntu", help="planning override; requires --plan")
    parser.add_argument("--arch", help="planning override; requires --plan")
    parser.add_argument("--python-lock", type=Path,
                        help="full hashed lock for an isolated Docker/venv interpreter")
    args = parser.parse_args(argv)
    if (args.ubuntu or args.arch) and not args.plan:
        parser.error("--ubuntu/--arch are only permitted with --plan")
    version = args.ubuntu or ubuntu_version()
    package = package_for(version, args.arch or platform.machine())
    source, prefix = args.source.resolve(), args.prefix.expanduser().resolve()
    if not (source/"pyproject.toml").is_file():
        raise FileNotFoundError("provide --source with the complete TritFlow git checkout")
    for name in ["cells/template.json", "cells/out/library.json", "cells/out/all.spice", "examples/adder.tv"]:
        if not (source/name).is_file():
            raise FileNotFoundError(f"source checkout must include committed cell/example assets: {name}")
    revision = PINS["pdk_commit"]
    pdk = prefix/f"TR-1um-{revision}"
    url = f"https://codeload.github.com/OpenSUSI/TR-1um/tar.gz/{revision}"
    lock = args.python_lock or HERE/"requirements-colab.txt"
    target = prefix/f"python-{sys.version_info.major}{sys.version_info.minor}-{sha256(lock.read_bytes()).hexdigest()[:16]}"
    commands = [[sys.executable, str(prefix/("pip-"+PINS["pip_wheel"]["version"])/"pip"),
                 "install", "--no-deps", "--require-hashes",
                 "--only-binary=:all:", "--target", str(target), "-r", str(lock)],
                [str(prefix/"bin/klayout"), "-b", "-r", str(HERE/"ruby_smoke.drc")]]
    plan = {"ubuntu": version, "klayout": package, "pdk_archive": url, "pdk_root": str(pdk),
            "source": str(source), "commands": commands,
            "ubuntu_dependency_lock": PINS["ubuntu_dependency_lock"][version],
            "ngspice": PINS["ngspice_package"], "python_target": str(target),
            "host_scientific_minimums": MINIMUM_VERSIONS,
            "scientific_packages_installed": True, "preloaded_packages_replaced": False}
    if args.plan:
        print(json.dumps(plan, indent=2))
        return 0
    if not args.python_lock:
        check_minimum_versions(("numpy", "matplotlib"))
    prefix.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "DEBIAN_FRONTEND": "noninteractive", "QT_QPA_PLATFORM": "offscreen",
                   "PIP_CACHE_DIR": str(prefix/"pip-cache"), "XDG_CACHE_HOME": str(prefix/"cache")}
    say("pip", "pipを準備")
    bootstrap_pip(prefix)
    say("KLayout and ngspice", "KLayoutとngspice")
    lock = json.loads((HERE/PINS["ubuntu_dependency_lock"][version]).read_text())
    print(f"@files {len(lock['packages']) + (1 if package else 0)}", flush=True)
    native, wrappers = install_native(package, HERE/PINS["ubuntu_dependency_lock"][version], prefix, download)
    say("Fonts for circuit labels", "回路図ラベル用のフォント")
    fonts = install_fonts(prefix, download)
    binary, ngspice = wrappers["klayout"], wrappers["ngspice"]
    payload = native/"usr/bin/ngspice"
    if not (pdk/".tritflow-commit").is_file():
        if pdk.exists():
            raise RuntimeError(f"refusing to overwrite an unrecognized PDK directory: {pdk}")
        with tempfile.TemporaryDirectory(dir=prefix) as staging:
            staging = Path(staging)
            archive = staging/"pdk.tar.gz"
            say(f"TR-1um PDK at commit {revision[:7]}", f"TR-1um PDK（コミット {revision[:7]}）")
            download(url, archive, PINS["pdk_archive_sha256"])
            unpack_archive(archive, staging)
            extracted = staging/f"TR-1um-{revision}"
            for name in ["libs.tech/spice/models/ip62_models", "libs.tech/klayout/tech/drc/run.drc",
                         "libs.tech/klayout/tech/lvs/run.lvs", "libs.tech/klayout/tech/python"]:
                if not (extracted/name).exists():
                    raise RuntimeError(f"pinned PDK archive lacks {name}")
            extracted.rename(pdk)
            (pdk/".tritflow-commit").write_text(revision+"\n")
    if (pdk/".tritflow-commit").read_text().strip() != revision:
        raise RuntimeError("PDK commit marker mismatch")
    say("Pinned Python packages", "Pythonパッケージ")
    subprocess.run(commands[0], check=True, env=environment)
    say("KLayout smoke test", "KLayoutの動作確認")
    subprocess.run(commands[1], check=True, env=environment)
    # All callers use KLAYOUT_BINARY from runtime.json. Keep installation
    # confined to prefix; a simulation-server run must not alter ~/bin.
    config = {"TR1UM_PDK": str(pdk), "TRITFLOW_ROOT": str(source), "KLAYOUT_BINARY": str(binary),
              "NGSPICE_BINARY": str(ngspice), "TRITFLOW_PYTHON_TARGET": str(target),
              "NGSPICE_PAYLOAD": str(payload),
              "TRITFLOW_FONT_ROOT": str(fonts),
              "TRITFLOW_SETUP_SHA256": setup_identity(source),
              "QT_QPA_PLATFORM": "offscreen", "XDG_CACHE_HOME": str(prefix/"cache"),
              "TRITFLOW_SETUP_SCHEMA": SETUP_SCHEMA}
    os.environ.update(config)
    sys.path[:0] = [str(target), str(source)]
    versions = print_tool_versions()
    if versions["KLayout"].strip() != "KLayout "+PINS["klayout_version"]:
        raise RuntimeError("Installed KLayout differs from setup_pins.json")
    temporary = HERE/"runtime.json.tmp"
    temporary.write_text(json.dumps(config, indent=2)+"\n")
    temporary.replace(HERE/"runtime.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
