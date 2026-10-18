# EDITOR — narrative authoring in progress

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

## In progress

Chapters, appendices, exact placeholder sources, prediction derivations, figure
specifications, teaser and pitch. Only notebook/narrative/ and this file are owned.

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

## Blockers

None for authoring. Final measured substitutions and clean-Colab runtime depend
on the existing qualification/release work; no successful Colab claim is made.

## Interface requests

FRONTEND: consume narrative files after completion; preserve data-source and
missing-result rules in placeholders.md. No shared-interface change requested.

## Validation

Editorial and source-resolution checks pending. No packages installed; no git
write commands; no code, notebook generator, .ipynb or foreign paths changed.
