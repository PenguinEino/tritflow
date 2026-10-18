# EDITOR — complete narrative handoff

Updated: 2026-10-18.

## Done

- Read AGENTS.md, concept, binding interfaces/editorial plan, EDITOR brief,
  current notebook source and its output inventory, and every stream's status.
- Read accepted ISSCC25 MARTIn and VLSI26 Wrøngm notebooks for presentation
  structure; checked ISSCC26's accepted-project list (no accepted .ipynb paths
  were present in that period's accepted folder in the public tree).
- Checked actual JSON schemas and public flow/simulation APIs for numerical
  substitutions. The current notebook has no saved outputs; historical executed
  outputs and the COLAB/REVIEW reports are evidence about their own revisions.
- Delivered all ten chapter files, Appendix A/B, two-sentence teaser, title
  options, three-sentence pitch and exactly 100-word abstract.
- Delivered concrete hero/control/static-fallback specifications for every
  chapter and appendix in `notebook/narrative/figures.md`.
- Delivered two/three-line chapter predictions and the detailed variable,
  model-parameter, units and source derivations in `predict_first.md`.
- Registered all **92** unique reader-facing placeholders in `placeholders.md`,
  with actual JSON fields/public API calls, transformations and missing/failure
  behavior. Main chapter text is **2,252 whitespace words**, about **15 minutes
  at 150 words/minute**, leaving figure time within the editorial reading target.
- Generated the four original GDS bounding-box areas into the small portable
  `reference_geometry.json`, with source SHA-256 and measurement method. All
  four hashes agree with the independent equivalence report. No reference GDS
  was modified; the snapshot avoids a Colab dependency on the author's checkout.

## In progress

None in EDITOR ownership. FRONTEND integrates text, predictions and controls;
the ongoing qualification/release work supplies final numerical substitutions.

## Decisions

- Numerical results resolve from validated current records; historical status
  tables are never the source of a notebook result. Pinned-PDK republishing is
  ongoing. Partial scaling results must retain failed/running widths visibly.
- The wiring experiment uses identical extracted devices with/without wire C.
  The old schematic-versus-extracted fit is unsuitable for that comparison.
- Main text will explain static power and report actual solved rail-current
  utilization, without repeating the old near-limit headline after power feeds
  have changed. Interpretations must follow current measurements.
- Chapter 0 counts top-level HDL lines and explicitly credits shared arithmetic
  modules; it will not imply those modules are contained in the displayed file.
- Hand estimates use a first-order INV divider and the pinned resistor model's
  correct width branch. Power uses signed rail powers, not the sum of absolute
  rail currents. Carry predictions use only a single slice as calibration.
- Figures and prose are deliverables; FRONTEND owns all plotting/notebook code.
- Structural constants (chapter numbers, trit equations, radix weights, syntax,
  unit conversions and product names) remain literal. Experimental values and
  context dates resolve through the registry. This interprets “numbers are never
  typed” as prohibiting copied result numbers, while preserving readable math.
- Chapter 1 starts at INV's middle input so the prediction precedes the measured
  comparison; NANY remains selectable. The top-level intro is below 150 words,
  other chapter openings below 80 words. Detailed limits occur only in Appendix A.
- Support cells have no fabricated taped-out area/timing counterpart. The main
  comparison caption applies to INV/NAND/NOR/NANY; BUF and ties/FILL get a
  scope-appropriate dimensions/qualification caption instead.
- Prediction/source checks confirm the simple baseline INV estimate is
  −0.0206603 V and 4.43238 mW versus source-level DC −0.0395421 V and
  4.07166 mW at the adopted bias. These are authoring validation observations,
  not frozen notebook constants. The model uses the special W=2.8 µm RR
  polynomial, nominal U0/TOX/VTH0, and stated SiO2-permittivity assumption.

## Blockers

None for EDITOR deliverables. Final measured substitutions and clean-Colab runtime depend
on the existing qualification/release work; no successful Colab claim is made.

## Interface requests

FRONTEND:

1. Insert `00_intro.md` … `09_next.md`, `A_limits.md`, `B_evidence.md` at
   their chapter/figure anchors. `teaser.md` is the caption at the top;
   `figures.md`, `placeholders.md`, `predict_first.md` are implementation notes,
   not extra reader chapters. Preserve existing author/license metadata.
2. Use exact-token substitution; whole-file `str.format` would damage LaTeX
   braces. Missing/stale/failed/running states replace the entire success box.
3. Width selection needs matching native GDS/PNR/waveforms, not just scaling
   summary JSON. Package verified native views for every offered width, or
   explicitly limit available views while retaining failed/running widths in
   the overview. The current four-design archive is a different experiment.
4. The zero-state power comparison needs each scaling run's hashed
   `postlayout/static.json` or a verified compact export. The summary contains
   maxima/means, not a named zero-state value. If absent, omit that measured
   comparison sentence rather than relabel the maximum. The independent cell
   sum is already fully specified and checked.
5. Bundle the small generated `reference_geometry.json` when retaining area
   ratios. Verify it against current equivalence source hashes before display.
6. Preserve actual fresh/recorded distinctions in Appendix B. The old real-Colab
   failure/manual-follow-up elapsed time is not a successful runtime benchmark.

No shared Python/JSON interface modification is requested. Optional STA,
corner or chip-wrapper results have no required unconditional claim.

## Validation

All authoring checks passed:

- Ten chapter anchors and What-this-shows boxes; introduction/opening word
  limits; balanced display math/details; no internal process words in chapters;
  no trailing whitespace; every one of the 92 substitutions registered once.
- Exactly 100 abstract words, three pitch sentences and two teaser sentences.
- Four portable reference-GDS hashes/areas match independent evidence.
- All 90 INV sizing candidates admit positive branch resistances/overdrives
  in the specified hand model; source-level baseline dimensions match the grid.
- Actual public synthesis reports give HA = NANY×5 + INV×2 and
  FA = NANY×11 + INV×5. All 9/27 states pass independent integer arithmetic
  in both source and mapped simulation.
- The two-trit all-zero ideal network contains only zero-valued internal nets;
  its signed cell-DC sum resolves to 133.416 mW with the inspected char files.
  Single-slice carry-prediction paths resolve in the current scaling schema;
  this field check is not an all-width requalification claim.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest notebook/tests/test_presentation.py -q -p no:cacheprovider`
  — **1 passed in 0.13 s**. This checks the display formatting used by the
  narrative. No new implementation-mirroring unit tests were added.

There is no `tests/editor/` suite. Do not run the notebook document-generation
test for this text-only handoff: it writes the .ipynb owned and concurrently
edited by FRONTEND. No physical/analog rerun is necessary for a prose change.

Repeat the central editorial checks from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import json, re
p = Path('notebook/narrative')
chapters = sorted(p.glob('[0-9][0-9]_*.md'))
assert len(chapters) == 10
reader = chapters + [p/n for n in ('A_limits.md', 'B_evidence.md', 'pitch.md', 'teaser.md')]
pattern = r'\{([a-z][a-z_]*\.[a-z][a-z_0-9]*)\}'
used = set().union(*(set(re.findall(pattern, f.read_text())) for f in reader))
registered = re.findall(r'^\| `\{([a-z][a-z_]*\.[a-z][a-z_0-9]*)\}` \|',
                        (p/'placeholders.md').read_text(), re.M)
assert used == set(registered) and len(registered) == len(set(registered))
for f in chapters:
    s = f.read_text()
    assert 'What this shows' in s and re.search(r'<!-- figure: ch\d -->', s)
    assert not re.search(r'\b(?:TODO|fingerprint|producer|campaign|stream|integrator|content-keyed)\b', s, re.I)
    if f.name == '00_intro.md':
        assert len(s.split('## 0.')[0].split()) <= 150
    else:
        assert len(s.split('\n\n', 2)[1].split()) <= 80
for f in reader:
    s = f.read_text()
    assert s.count(r'\[') == s.count(r'\]')
    assert s.count('<details>') == s.count('</details>')
    assert not re.search(r'[ \t]+$', s, re.M)
pitch = (p/'pitch.md').read_text()
abstract = pitch.split('# Abstract — 100 words\n\n')[1].split('\n# Why')[0]
assert len(abstract.split()) == 100
assert len(re.findall(r'\.(?:\s|$)', (p/'teaser.md').read_text())) == 2
three = pitch.split('# Three-sentence pitch\n\n')[1].split('\n# Abstract')[0]
assert len(re.findall(r'\.(?:\s|$)', three)) == 3
reference = json.loads((p/'reference_geometry.json').read_text())
eq = json.loads(Path('cells/out/equivalence_report.json').read_text())
for cell, row in reference['cells'].items():
    assert row['source_sha256'] == eq['schematic_equivalence'][cell]['original_gds_sha256']
print('Narrative checks passed:', len(used), 'registered placeholders')
PY
```

Tone references inspected:

- [ISSCC25 MARTIn notebook](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/main/ISSCC25/accepted_notebooks/MARTIn/main_notebook.ipynb)
  — purpose → algorithms → physical implementation → verification/results.
- [VLSI26 Wrøngm notebook](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/main/VLSI26/accepted_notebooks/Wr%C3%B8ngm/Wr%C3%B8ngm.ipynb)
  — device insight and hand-analysis connection before simulation/design controls.
- [ISSCC26 accepted list](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/main/ISSCC26/README.md)
  — reviewed for scope; no claim that an unavailable accepted notebook was read.

No packages installed; no git write commands; no code, notebook generator,
.ipynb or foreign owned paths changed. Eighteen files are delivered under
`notebook/narrative/` plus this status file.
