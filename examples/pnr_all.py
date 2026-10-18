"""Build all shared PNR examples; --watch automatically follows cell changes.

Outputs, seed comparisons, verification reports and notebook views are saved to
build/<design>/. Content hashes invalidate stale results even if mtimes are
preserved. Use --force to rerun unchanged inputs and --seeds 0 7 19 to select
placement candidates. This script does not modify the source cell library.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tritflow.pnr.batch import main

if __name__ == "__main__":
    raise SystemExit(main())
