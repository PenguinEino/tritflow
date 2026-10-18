"""Setup planning, safe downloads/extraction and platform selection without apt."""

from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("tritflow_setup", ROOT/"notebook/setup_colab.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


@pytest.mark.parametrize("version", ["22.04", "24.04"])
def test_official_deb_plan_is_release_specific(version, capsys, monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("planning must not run commands or download")

    monkeypatch.setattr(setup.subprocess, "run", forbidden)
    monkeypatch.setattr(setup, "download", forbidden)
    assert setup.main(["--plan", "--ubuntu", version, "--arch", "amd64"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert f"Ubuntu-{version[:2]}/" in result["klayout"]["url"]
    assert len(result["klayout"]["sha256"]) == 64
    assert setup.PINS["pdk_commit"] in result["pdk_archive"]
    assert any("ngspice" in c for c in result["commands"])
    assert any("-e" in c for c in result["commands"])


@pytest.mark.parametrize("version,arch", [("26.04", "amd64"), ("24.04", "arm64")])
def test_unknown_platforms_fail_instead_of_guessing(version, arch):
    with pytest.raises(ValueError):
        setup.package_for(version, arch)


def test_os_release_and_override_guard(tmp_path):
    path = tmp_path/"os-release"
    path.write_text('ID=ubuntu\nVERSION_ID="24.04"\n')
    assert setup.ubuntu_version(path) == "24.04"
    path.write_text('ID=debian\nVERSION_ID="12"\n')
    with pytest.raises(ValueError, match="Ubuntu"):
        setup.ubuntu_version(path)
    with pytest.raises(SystemExit):
        setup.main(["--ubuntu", "24.04"])


def test_checksum_and_safe_tar_paths(tmp_path):
    source = tmp_path/"source"
    source.write_bytes(b"package")
    output = tmp_path/"download"
    setup.download(source.as_uri(), output, sha256(b"package").hexdigest())
    assert output.read_bytes() == b"package"
    with pytest.raises(RuntimeError, match="SHA-256"):
        setup.download(source.as_uri(), output, "0"*64)
    assert not output.exists()
    for name, link in [("../escape", None), ("root/link", "../../escape")]:
        archive = tmp_path/"bad.tar"
        with tarfile.open(archive, "w") as stream:
            member = tarfile.TarInfo(name)
            if link:
                member.type = tarfile.SYMTYPE
                member.linkname = link
            stream.addfile(member)
        with pytest.raises(ValueError, match="unsafe"):
            setup.unpack_archive(archive, tmp_path/"extracted")
    archive = tmp_path/"good.tar"
    with tarfile.open(archive, "w") as stream:
        member = tarfile.TarInfo("root/file")
        member.size = 4
        stream.addfile(member, io.BytesIO(b"test"))
        link = tarfile.TarInfo("root/link")
        link.type, link.linkname = tarfile.SYMTYPE, "file"
        stream.addfile(link)
    setup.unpack_archive(archive, tmp_path/"safe")
    assert (tmp_path/"safe/root/link").read_bytes() == b"test"


def test_bash_wrapper_syntax():
    subprocess.run(["bash", "-n", str(ROOT/"notebook/colab_setup.sh")], check=True)
