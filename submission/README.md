# Build the v3 Code-a-Chip reviewer package

The builder executes `notebook/v3/tritflow_en.ipynb` as the primary notebook
and `notebook/v3/tritflow_ja.ipynb` as its Japanese companion. Until English
exists, the Japanese notebook builds once as an explicitly labelled development
preview. It is never renamed to look like an English notebook.

```sh
python3 -m pip install --user --break-system-packages -r submission/requirements-build.txt
PYTHONDONTWRITEBYTECODE=1 python3 submission/build_submission.py
PYTHONDONTWRITEBYTECODE=1 python3 submission/build_submission.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest submission/tests -q
```

Use the existing Python/EDA installation and pinned `$TR1UM_PDK`. Static export
needs installed Chrome/Chromium and Cairo. No browser or system package is
installed by the builder. All disposable kernel, sizing, EDA and export files
stay in `submission/.build/`, including failed raw notebooks and diagnostics.
The source notebooks, bootstrap, PDK and other streams' paths are not edited.

Only `submission/ISSCC27/submitted_notebooks/TritFlow/` belongs in the eventual
official-repository PR. The bilingual payload has nine files: both notebooks,
README, ABSTRACT, PITCH, CHECKLIST, LICENSE, NOTICE and build-info.json. A Japanese
preview has eight. The complete payload must fit the self-imposed 12 MiB budget (two languages).

The first cell of each packaged notebook contains the exact team identity from
`team.json`, which follows `docs/author.md`, recommended runtime versions and
license information. References and execution provenance are added as appendix
cells. Original source cells stay in order and keep their code. Pinned images
in Markdown become embedded PNGs. Native KLayout overviews and real Chromium
captures of the controls' initial states make the saved output readable without
JavaScript. Re-execution restores the original controls.

An extra, self-contained evidence cell reads the actual kernel's synthesized
cell counts, equivalence coverage, layout dimensions, DRC/LVS outcomes, SPICE
measurements and STA estimates. README and abstract results come from that
cell's JSON output, never the storyboard. Future chapter 6 tables are discovered
by their chapter heading and copied from executed HTML outputs without a
cell-ID dependency; missing results produce an explicit scope statement rather
than guessed measurements. Raw capture hashes and per-notebook source/runtime
pins are retained in build-info.json. Runtime tools are recorded during
execution, separately from packaging-tool versions.

For packaging-only edits, reuse successful captures with identical source bytes:

```sh
python3 submission/build_submission.py \
  --from-executed submission/.build/submission_capture/tritflow_en/executed.raw.ipynb \
  --from-executed-ja submission/.build/submission_capture/tritflow_ja/executed.raw.ipynb
```

For a Japanese preview, supply its capture to `--from-executed` or
`--from-executed-ja`. A stale, incomplete or failed capture is rejected. Reuse
does not claim a new EDA run. `--source`, `--japanese-source`, `--output` and
`--workdir` support drafts; output and work directories must remain inside
`submission/`. Publication is staged and validated before replacing the old
payload. An oversized or failed build leaves the previous payload intact.

```sh
python3 submission/build_submission.py --check --require-final
```

The final gate requires English, an executed chapter 6 evaluation and source
pins compatible with the final notebooks; a preview cannot silently become a
final submission. Local execution does not claim a real-Colab v3 Run all, and
historical v1 Colab evidence is not promoted to v3. The integrator owns source
publication, final Colab qualification and filing the PR. This builder performs
no git-writing commands, commits, pushes or submissions.

The current official rules were re-fetched on 2026-10-23 using the official
repository's immutable default-branch head. `official_snapshot.json` retains
the fetched Markdown; `official_sources.json` records URLs, hashes and the
precedence of the current README over legacy event dates. The generated
checklist cites those sources and the IEEE award page.
