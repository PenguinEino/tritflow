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
from urllib.request import urlopen

from runtime_support import MINIMUM_VERSIONS, SETUP_SCHEMA, check_minimum_versions, print_tool_versions


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
    if version not in PINS["klayout_deb"]:
        raise ValueError(f"no pinned official KLayout package for Ubuntu {version}; update setup_pins.json")
    return PINS["klayout_deb"][version]


def download(url, destination, checksum=None):
    destination = Path(destination)
    with urlopen(url, timeout=120) as response, destination.open("wb") as stream:
        shutil.copyfileobj(response, stream)
    if checksum and sha256(destination.read_bytes()).hexdigest() != checksum:
        destination.unlink()
        raise RuntimeError(f"SHA-256 mismatch: {url}")


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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--source", type=Path, default=HERE.parent,
                        help="local checkout to install, including cells/out and examples")
    parser.add_argument("--prefix", type=Path, default=Path("/content/tritflow-runtime"))
    parser.add_argument("--ubuntu", help="planning override; requires --plan")
    parser.add_argument("--arch", help="planning override; requires --plan")
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
    privilege = [] if os.geteuid() == 0 else ["sudo"]
    commands = [privilege+["apt-get", "update"],
                privilege+["apt-get", "install", "-y", "--no-install-recommends", "ngspice", "ca-certificates"],
                privilege+["apt-get", "install", "-y", str(prefix/"klayout.deb")],
                [sys.executable, "-m", "pip", "install", "--no-deps", "-r", str(HERE/"requirements-colab.txt"), "-e", str(source)],
                ["/usr/bin/klayout", "-b", "-r", str(HERE/"ruby_smoke.drc")]]
    plan = {"ubuntu": version, "klayout": package, "pdk_archive": url, "pdk_root": str(pdk),
            "source": str(source), "commands": commands,
            "host_scientific_minimums": MINIMUM_VERSIONS,
            "scientific_packages_installed": False}
    if args.plan:
        print(json.dumps(plan, indent=2))
        return 0
    check_minimum_versions()
    prefix.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "DEBIAN_FRONTEND": "noninteractive", "QT_QPA_PLATFORM": "offscreen"}
    for command in commands[:2]:
        subprocess.run(command, check=True, env=environment)
    download(package["url"], prefix/"klayout.deb", package["sha256"])
    subprocess.run(commands[2], check=True, env=environment)
    if not (pdk/".tritflow-commit").is_file():
        if pdk.exists():
            raise RuntimeError(f"refusing to overwrite an unrecognized PDK directory: {pdk}")
        with tempfile.TemporaryDirectory(dir=prefix) as staging:
            staging = Path(staging)
            archive = staging/"pdk.tar.gz"
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
    subprocess.run(commands[3], check=True, env=environment)
    subprocess.run(commands[4], check=True, env=environment)
    # Default stream paths expect ~/bin/klayout/klayout. Keep that compatibility
    # inside this fresh runtime without overwriting an existing installation.
    binary = Path("/usr/bin/klayout")
    legacy = Path.home()/"bin/klayout/klayout"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    if not legacy.exists():
        legacy.symlink_to(binary)
    config = {"TR1UM_PDK": str(pdk), "TRITFLOW_ROOT": str(source), "KLAYOUT_BINARY": str(binary),
              "QT_QPA_PLATFORM": "offscreen", "TRITFLOW_SETUP_SCHEMA": SETUP_SCHEMA}
    (HERE/"runtime.json").write_text(json.dumps(config, indent=2)+"\n")
    print(json.dumps(config, indent=2))
    os.environ["KLAYOUT_BINARY"] = str(binary)
    print_tool_versions()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
