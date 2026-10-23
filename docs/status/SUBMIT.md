# SUBMIT — v3 reviewer package

Updated: 2026-10-23. Scope: `submission/` and this file only. No commit or push.

## Done

- Replaced v1 input with `notebook/v3/tritflow_en.ipynb` as the default primary
  and `notebook/v3/tritflow_ja.ipynb` as the companion. Until EN exists, JA is
  executed once and explicitly labelled a development preview; it is never
  renamed as English. The previous v1 payload notebook is removed on rebuild.
- Both languages follow the same independent execution, unchanged-source,
  output-portability, manifest, license/NOTICE, and combined 8 MiB budget gates.
  Source edits during execution or packaging invalidate the capture.
- Added a self-contained executed evidence cell for synthesis, logic coverage,
  routed dimensions, drawing DRC, strict LVS, post-layout SPICE and STA. README
  and abstract numbers are generated from that JSON output. Numerical results
  are never copied from the storyboard or typed into the templates.
- Chapter 6 tables are discovered from its heading and actual executed HTML
  tables, without hard-coded cell IDs. They feed README and build-info. Until
  the source contains the evaluation, the documents state its absence and do
  not quote scaling/power numbers. Preserved metadata retains tables before
  interactive outputs become static images.
- Rewrote English README, ABSTRACT and three-sentence PITCH around native
  balanced-ternary HDL → GDS, the taped-out 1-trit multiply-add cells and the
  ternary-weight dot product. README contains Colab/local instructions and a
  single limits paragraph; no binary-advantage claim is made.
- Authors, affiliation, student status, email and GitHub follow `docs/author.md`
  and `submission/team.json` exactly. Every packaged notebook starts with the
  author table, license and recommended tools. References/provenance appear
  in additional appendix cells. No telephone information is included.
- The default final gate (`--check --require-final`) rejects a Japanese-only
  preview, missing chapter 6 evaluation, incompatible source pin, different
  execution commit, changed commit during execution or unpublished runtime
  inputs. Plain `--check` validates a development preview without promoting it.
- Saved figures preserve actual selected views: exact-pixel KLayout overview
  and Chromium snapshots of initialized v3 controls/Plotly, using local Plotly
  JavaScript. Pinned Markdown figures are embedded from immutable Git objects.
  PNG compression is lossless, including preservation of transparency.
- Staged publication validates the entire payload before replacing the previous
  directory. The complete manifest covers both notebooks and all documents;
  total bytes include build-info itself. License and NOTICE are verbatim.
- All disposable EDA outputs, Jupyter state, browser profiles, caches and raw
  notebooks are contained under `submission/.build/`. The sizing helper's
  disposable cache is redirected there; original published sizing records are
  copied read-only. Chromium's temporary profile uses the shorter
  `submission/.build/tmp/` path to avoid Unix socket path limits.

## Official-rules audit

Re-fetched the official default-branch head and immutable README, FAQ,
`howtoapply.md`, ISSCC27 instructions and submission-folder instructions using
GitHub's read-only connector. Also re-fetched the older accepted-event README
examples and independently checked the current IEEE award page. Head remains
`a502a6ba01260d3492df9137dddae0bb5fabeb3c`.

- [Current root rules](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/a502a6ba01260d3492df9137dddae0bb5fabeb3c/README.md)
- [Application guide](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/a502a6ba01260d3492df9137dddae0bb5fabeb3c/howtoapply.md)
- [FAQ](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/a502a6ba01260d3492df9137dddae0bb5fabeb3c/FAQ.md)
- [IEEE award page](https://sscs.ieee.org/membership/awards/ieee-sscs-code-a-chip-travel-grant-awards/)

`official_sources.json` now records the 2026-10-23 check, immutable URLs, SHA-256
and Git blob identifiers. `official_snapshot.json` retains the fetched Markdown
outside the payload. Tests verify the snapshot hashes. The current root rules
and IEEE page supersede the ISSCC26 / November 27, 2025 event/deadline in the
older application guide. Its author-at-top, references and recommended-version
requirements are retained. Current filing folder is
`ISSCC27/submitted_notebooks/TritFlow/`; deadline is October 31, 2026, 11:59 AM
Pacific. No official numerical size or ten-minute runtime limit is invented.

## Verification

- Fresh local v3 execution completed without errors: 25 original code cells
  plus the executed evidence cell. Original source at this capture contains
  chapters 1–5. The supplied `tritflow_ja_output.ipynb` was not used as evidence.
- Executed dot4: 46 cells; exhaustive synthesis equivalence over 6,561 input
  vectors; routed core 1692 × 1206 µm; drawing DRC 0; strict LVS matched;
  all 11 nominal SPICE stimulus intervals pass. The sample campaign is not
  described as exhaustive transistor-level input/transition coverage.
- Output settling and STA numbers are read from the raw capture into the
  generated documents; source and bootstrap commits, PDK/model/deck hashes,
  observed runtime versions, capture times and raw capture SHA are recorded.
  Export-tool versions are explicitly separate, including for raw reuse.
- Visually inspected the saved INV DC/sizing controls, final dot4 routing view
  and post-layout waveform: labels, selected state, ±0.5 V bands, settling
  annotations, glitches and supply-current trace are visible.
- Submission tests currently pass: **21 passed**. They include bilingual inputs,
  JA fallback without duplication, dynamic future chapter 6 tables, failed and
  stale captures, exact source order/code, top identity, manifest/budget,
  official-source hashes, actual payload evidence, offline HTML execution,
  rejection of blank plots, transparent/opaque PNG pixel equality and final
  readiness without mutating captured evidence.
- Final provenance-enabled build and `--check` both pass. Payload: **8 files,
  3,913,064 bytes (3.732 MiB)**; 26 executed code cells, 46 saved outputs,
  14 native PNG outputs, 6 embedded Markdown figures and 5 HTML tables.
  Final EDA/kernel capture took **44.94 s** locally; this is not a Colab or
  installation-inclusive benchmark. `submission/.build/verified-build.log`
  records the final build; native evidence and raw execution stay in
  `submission/.build/submission_capture/tritflow_ja/`.
- Captured source notebook SHA-256:
  `90f3d62a16ab5c52ef4222374cbaeff7b1eab0d969e309059019c0e2b5b20781`.
  Execution start/end commit both
  `4361c38e1506621346e8e0a48f26f126899e335e`; bootstrap pin remains
  `71ba7253326c140441893f6be2752803d8fb51c9`. PDK qualified/checkout commit
  both `5d963db9d44e192d37a0489c208bfccf2e2f690c`; **40 model/deck hashes**
  are captured. The final validation reports **21 passed in 7.96 s** and
  `git diff --check -- submission docs/status/SUBMIT.md` passes.
- Extra packages installed: **none** (the existing build requirements suffice).

```sh
PYTHONDONTWRITEBYTECODE=1 python3 submission/build_submission.py
PYTHONDONTWRITEBYTECODE=1 python3 submission/build_submission.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest submission/tests -q
```

Packaging-only edits can reuse the source-hash-matched raw notebook:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 submission/build_submission.py \
  --from-executed-ja submission/.build/submission_capture/tritflow_ja/executed.raw.ipynb
```

## Handoff / interface requests

SUBMIT implementation and the permitted Japanese development build are
complete. `submission_ready` is intentionally **false**, for the inputs and
release-qualification reasons below; this is not a final filing artifact.

No changes to `docs/interfaces.md` are requested and no user input is required.
EN and chapter 6 remain owned by their respective streams. Rebuild after their
source notebooks are generated; both inputs will be selected automatically.
The integrator must publish/restamp a source commit compatible with the final
notebooks and execute that qualified revision before using the final gate.
At the present source revision the bootstrap still names
`71ba7253326c140441893f6be2752803d8fb51c9`, while local execution uses the current
working checkout. Both facts are disclosed instead of substituting a later
packaging commit for the executed source identity.

The builder does not promote historical v1 Colab evidence to v3. This payload
claims local execution only; V3's separate real-Colab qualification remains
with its owning stream. Final bilingual/chapter-6 content must still fit the
combined budget; an oversized build aborts without replacing the valid preview.
After integration, run `--check --require-final` and copy only the generated
project folder into the official fork. Filing the PR remains an integrator/user
step, as required by the brief.
