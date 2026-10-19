"""Check that the delivered runtime can be verified without a package resolver."""

from hashlib import sha256
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]


def test_simulator_uses_official_snapshot_packages_on_both_architectures():
    pins = json.loads((ROOT/"notebook/setup_pins.json").read_text())
    assert re.fullmatch(r"[0-9a-f]{40}", pins["pdk_commit"])
    for arch, name in pins['ngspice_dependency_locks'].items():
        lock = json.loads((ROOT/'notebook'/name).read_text())
        assert lock['architecture'] == arch
        package = next(p for p in lock['packages'] if p['package'] == 'ngspice')
        assert package['version'] == pins['ngspice_package']['version'] == '42+ds-3build1'
        assert package['url'].startswith('https://snapshot.ubuntu.com/ubuntu/'+pins['ubuntu_snapshot'])
        assert re.fullmatch(r'[0-9a-f]{64}', package['sha256'])
    assert not list((ROOT/'notebook/assets/runtime').glob('*'))


def test_ubuntu_closure_and_python_packages_have_exact_versions_and_hashes():
    lock = json.loads((ROOT/"notebook/ubuntu-24.04-lock.json").read_text())
    packages = lock["packages"]
    assert len(packages) == len({p["package"] for p in packages}) >= 190
    assert {"libc6","libpython3.12-stdlib","libruby3.2","libqt5core5t64"} <= {p["package"] for p in packages}
    for package in packages:
        assert lock["snapshot"] in package["url"]
        assert package["version"] and re.fullmatch(r"[0-9a-f]{64}",package["sha256"])
    for name in ("requirements-lock.txt","requirements-minimum-lock.txt","requirements-colab-host-lock.txt",
                 "requirements-colab.txt"):
        text = (ROOT/"notebook"/name).read_text()
        entries = re.findall(r"(?m)^[a-zA-Z0-9_-]+==[^\n]+(?:\n[ \t]+[^\n]*)*",text)
        assert entries
        assert all("--hash=sha256:" in entry for entry in entries)
