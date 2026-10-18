"""Build the four shared synthesis examples through the public CLI.

Run ``python3 examples/build_all.py`` from any directory. The default outputs
are build/{adder4,full_add,mac1,mul1}/ in this checkout. Existing P&R or simulation
files in those directories are left in place; only synthesis artifacts are
regenerated. Each CLI invocation performs its normal equivalence check.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BUILDS = (
    ("adder4", "adder", ("-P", "N=4")),
    ("full_add", "full_add", ()),
    ("mac1", "mac1", ()),
    ("mul1", "mul1", ()),
)


def main(argv=None) -> int:
    """Fail on the first CLI error; --output-root permits isolated rebuilds."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / "build")
    args = parser.parse_args(argv)
    output_root = args.output_root.resolve()
    for name, top, parameters in BUILDS:
        command = [sys.executable, "-m", "tritflow.synth", str(ROOT / "examples" / f"{top}.tv"),
                   "--top", top, *parameters, "-o", str(output_root / name)]
        print(f"Building {name} → {output_root / name}", flush=True)
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
