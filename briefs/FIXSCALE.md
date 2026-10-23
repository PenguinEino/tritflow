# FIXSCALE stream brief: restore chip_power.py so the recorded scaling stays valid

Work in `~/code-a-chip-v3`, only on `tritflow/pnr/chip_power.py`, `tritflow/pnr/chip_frame*.py`,
`notebook/assets/chip/dot4/` (provenance only, unless the GDS changes — it must not), `tests/` for these,
and `docs/status/FIXSCALE.md`. Do not commit.

Problem: FRAME (commit 0fd73b0) added `distribution_only` to `_power_header` in
`tritflow/pnr/chip_power.py`. `results/dot_scaling.json` records that file's SHA-256
(`a3f4b62f…`), so `notebook/scale_views.py` now raises "Recorded dot scaling is stale" and the
chapter 6 cell fails (tests/test_scale_views.py: 2 failures).

Fix: make `tritflow/pnr/chip_power.py` byte-identical to its version at `0fd73b0~1` (hash a3f4b62f…),
and give `chip_frame_power.py` what it needs without editing chip_power.py (factor the distribution
computation into chip_frame_power.py, or call the unchanged `_power_header` and use only its
distribution numbers — whichever is smaller and keeps the frame top byte-identical). Do not touch
`results/dot_scaling.json`. Rebuild the dot4 frame top only to prove the GDS SHA-256 is unchanged
(`6d2453708f58…` in provenance); update provenance source hashes for the files you changed.
Run the full suite (`python3 -m pytest -q tests notebook/tests submission`); the only acceptable
failures are the two submission payload tests that compare against the not-yet-rebuilt payload.
Report in `docs/status/FIXSCALE.md`.
