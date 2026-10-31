# README_TRIM

Status: complete (2026-10-24). In progress: none. No commits or pushes.

## Decisions and completed edits

- Read AGENTS.md, docs/concept.md, docs/interfaces.md, briefs/README_TRIM.md,
  ACCEPTED findings 2 (front matter) and 3, and the recorded official call files
  in submission/official_snapshot.json at a502a6ba01260d3492df9137dddae0bb5fabeb3c
  (root README, howtoapply.md, FAQ, ISSCC27 README and submission-folder README).
- The call's [howtoapply.md](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/a502a6ba01260d3492df9137dddae0bb5fabeb3c/howtoapply.md) requires team names at the notebook top and recommended
  tool versions, but neither it nor the ISSCC27 instructions prescribe an authors
  table. Keep the original source opening's title, author and affiliation; the
  added submission-identity cell contains only Apache-2.0 and recommended versions.
  Reject packaging if a team member is missing from the source opening.
- Remove the duplicated concept paragraph, seven chapter 6 README tables and
  packaging commentary. Keep the dot4 summary, author information, license,
  reproduction instructions, badge, runtime versions and measurement scope.
  Chapter 6 links cover only notebooks actually packaged, including JA-only previews.
- Keep chapter6()/Tables: readiness and build-info.json still require their
  executed-table records. Remove only the Markdown expansion and its obsolete
  result_values() argument; preserve machine-readable evaluation evidence.
- Saved captures predate the current source notebooks, so the temporary build
  executed current sources rather than relabelling or reusing stale captures.

## Verification

The submission tests pass: 19 passed, 2 deselected. The two omitted tests compare
against the existing payload, which this stream is instructed not to rebuild.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q submission \
  -k 'not test_actual_payload_has_readable_evidence_and_exact_bilingual_manifests and not test_final_check_refuses_a_preview_without_changing_payload'
```

One fresh bilingual build completed successfully, followed by the builder's
read-only check. EN executed in 85.35 s and JA in 81.43 s, excluding static export.
The temporary package contains nine files, 64 executed code cells, 144 saved
outputs, 40 PNG outputs and 28 HTML tables. Each notebook's manifest retains all
seven chapter 6 tables. The dot4 README table still comes from captured evidence.
No packages were installed.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B submission/build_submission.py \
  --output submission/tests/build/readme_trim/payload \
  --workdir submission/tests/build/readme_trim/capture
PYTHONDONTWRITEBYTECODE=1 python3 -B submission/build_submission.py --check \
  --output submission/tests/build/readme_trim/payload
```

Read the generated README and both first-two-cell pairs. Each opening contains
one title and author/affiliation block, preceded only by the short license/version
cell. README has both chapter 6 links, the compact dot4 table, author information,
Colab/local instructions, recommended versions, license and measurement limits.
The unchanged-source validation passed, including the original notebook code.
Scoped `git diff --check` also passed.

Before counts and payload hashes, after counts, the build log, raw captures and
temporary package are in the ignored `submission/tests/build/readme_trim/`
directory. SHA-256 comparisons confirm all nine files under
`submission/ISSCC27/submitted_notebooks/TritFlow/` are byte-for-byte unchanged.

## Before and after counts

Before means the existing packaged files at task start; after means the fresh
temporary package. Template counts are also shown. Counts use `splitlines()`
(including blank lines) and whitespace-delimited `split()` on Markdown source,
not rendered-page line wrapping. Japanese word counts therefore are not linguistic
word counts. Embedded image data occupies one whitespace token.

| Artifact | Before lines | After lines | Before words | After words |
|---|---:|---:|---:|---:|
| Generated README | 236 | 106 | 2,166 | 840 |
| README template | 132 | 91 | 839 | 539 |
| EN cell 1: submission-identity | 16 | 3 | 127 | 25 |
| EN cell 2: original c0 | 22 | 22 | 592 | 592 |
| JA cell 1: submission-identity | 16 | 3 | 127 | 25 |
| JA cell 2: original c0 | 18 | 18 | 55 | 55 |

## Blockers

None for the scoped edits. The temporary package correctly has
`submission_ready: false`: both notebooks differ from their bootstrap release,
execution used a different repository commit, and parallel runtime edits were
present. These existing release conditions remain visible in README/CHECKLIST
and build-info.json; no gate was bypassed and no Colab verification is claimed.
The integrator must rebuild the final payload after the parallel streams and
source-pin publication are complete.

## Interface requests

No runtime/interface changes requested. The integrator retains the final
capture/payload rebuild and release gate.

Two documentation follow-ups are outside this stream's permitted paths:

- submission/README.md still describes the added first cell as containing the
  full team identity and says chapter 6 tables are copied into the README.
  Update those descriptions to reflect the preserved source opening and links.
- submission/templates/CHECKLIST.md says the first cell contains team members
  and the representative appears in each notebook. The README designates the
  representative; the original opening names the author in packaged cell 2.
  Adjust those evidence-location descriptions when rebuilding the final payload.
