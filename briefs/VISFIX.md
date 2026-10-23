# VISFIX stream brief: fix the adopted visual defects from docs/status/VISUAL.md

Work in `~/code-a-chip-v3`, only on: `notebook/scale_views.py`, `notebook/views.py`, `notebook/reuse.py`,
`tritflow/viz/`, `tritflow/schematic/` (display only), tests for these, `notebook/assets/chip/dot4/provenance.json`
(only the hash of `notebook/reuse.py`, see below), and `docs/status/VISFIX.md`. Do not edit narratives,
`notebook/v3/*`, `notebook/style.py`, `notebook/live.py`, or anything under `tritflow/pnr`, `tritflow/sim`,
`tritflow/sta`, `tritflow/synth`, `tritflow/hdl`, `tritflow/extract`, `tritflow/flow.py`, `notebook/cache.py`.
Do not commit.

Adopted findings (read their evidence and suggested fix in `docs/status/VISUAL.md`): V01, V02, V04, V05,
V06, V08, V09, V10. Not adopted, do not touch: V03, V07.

Constraints:
- Recorded results hash source files. Before editing any file, grep `results/*.json`,
  `notebook/assets/**/provenance.json` and other recorded JSON for its path; if a recorded campaign hashes
  it, do not edit it and find another place for the fix (the scaling record broke today this way).
  `notebook/reuse.py` is hashed by the dot4 snapshot provenance: follow the existing language mechanism
  (`reuse_before_english.py` and the AST comparison in the tests) and update only reuse.py's
  `source_sha256` entry. The FIXSCALE stream is editing that provenance file right now: do V09/V10 last
  and wait until `pgrep -f "FIXSCALE stream"` returns nothing before touching provenance.json; re-read it then.
- Japanese strings: plain technical Japanese, である調, matching the terms already used in the notebook
  (e.g. 提出可否 is not used; look at how the narrative and other ja outputs say it). Keep layer codes and
  net names as identifiers.
- V02: prefer allowing header wrap and smaller padding; do not split, fold or add columns.
- V04: keep the detailed drawing at a readable text size inside its existing local scroll viewport.
- V05: change only the overview label visibility, not GDS content.
- Verify: rebuild the affected outputs locally (a temporary executed copy of the notebooks, or the view
  functions directly), screenshot at 1140 and 800 px with headless Chrome, and look at them; put
  screenshots under `notebook/v3/.work/visfix/`. Run `python3 -m pytest -q tests notebook/tests` at the end.
  Report each finding: fixed / not fixed (why), with screenshot paths.
