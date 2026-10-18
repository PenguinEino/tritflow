#!/usr/bin/env bash
# Install into a fresh Colab Ubuntu runtime; --plan never modifies the machine.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/setup_colab.py" "$@"
