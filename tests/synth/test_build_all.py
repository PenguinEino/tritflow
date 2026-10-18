"""Shared example artifacts rebuild identically without disturbing P&R files."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from tritflow.netlist import GateNetlist


ROOT = Path(__file__).resolve().parents[2]


def test_standard_build_script_from_another_directory(tmp_path):
    output = tmp_path / "build"
    marker = output / "full_add" / "keep.pnr.json"
    marker.parent.mkdir(parents=True)
    marker.write_text('{"owned_by": "PNR"}')
    command = [sys.executable, str(ROOT / "examples/build_all.py"), "--output-root", str(output)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    expected = {"adder4": (64, 19683), "full_add": (16, 27), "mac1": (23, 81), "mul1": (4, 9)}
    artifacts = []
    for top, (cells, vectors) in expected.items():
        for suffix in ["json", "gate.tv", "spice", "report.json", "report.txt"]:
            path = output / top / f"{top}.{suffix}"
            assert path.is_file()
            artifacts.append(path)
        net = GateNetlist.load(output / top / f"{top}.json")
        report = json.loads((output / top / f"{top}.report.json").read_text())
        assert net.top == top
        assert len(net.instances) == report["total_cells"] == cells
        assert report["equivalence"]["passed"]
        assert report["equivalence"]["vectors"] == vectors
    first = {path: sha256(path.read_bytes()).hexdigest() for path in artifacts}
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert first == {path: sha256(path.read_bytes()).hexdigest() for path in artifacts}
    assert json.loads(marker.read_text()) == {"owned_by": "PNR"}
