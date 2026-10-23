"""Regenerate the two static figures used by notebook v3 (PDF, PNG and SVG)."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fig_flow_map
import fig_flow_v2


if __name__ == "__main__":
    for language in ("en", "ja"):
        print(fig_flow_v2.make(language))
    print(fig_flow_map.make())
