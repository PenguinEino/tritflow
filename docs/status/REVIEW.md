# REVIEW — independent audit

Review in progress. Baseline cloned at 2026-10-18 09:03 UTC:
`37034be20dc02d8ee82d15170b955b6ef2777d70`. Other streams continue editing;
findings will identify this snapshot and separately note subsequent changes.

## Reproduction decisions

- Only this file and `logs/review/` are written in the shared checkout. The
  explicitly requested local clone is `/tmp/tritflow-review-wox2aqgy/source`.
  No checkout/reset/stash/commit is performed. Generated runs stay in scratch.
- Fresh Python 3.12 venv, pinned `notebook/requirements-colab.txt`, editable
  package, pytest, nbconvert and ipykernel. System ensurepip is unavailable, so
  `venv --without-pip` plus system pip's `--python <venv>/bin/python` installs
  into that isolated venv. No shared interpreter packages are changed.
- Fresh PDK archive at pinned commit
  `5d963db9d44e192d37a0489c208bfccf2e2f690c`; SHA-256 verified against
  `notebook/setup_pins.json`. No HOME PDK/reference files are modified.
- Host is Ubuntu 24.04/aarch64. The checksum-correct official Ubuntu 24.04
  KLayout 0.30.6 binary is amd64 and fails with `Exec format error`. Therefore
  the native runs use installed KLayout executable 0.30.9 and fresh Python
  klayout 0.30.6, plus installed ngspice 46+. This is explicitly not a clean
  amd64 Colab installation test.
- Run the whole `tests` **and** `notebook/tests` suite, and execute every
  notebook cell with nbconvert in its own venv kernel. `--allow-errors` preserves
  error outputs and lets later independent cells run; errors, not nbconvert's
  exit status alone, determine success.

## In progress

Full suite and cold notebook execution. Detailed evidence and final ranked
findings will replace this section when both finish. Reproduction metadata,
source-file hashes, notebook text, status snapshots and independent probes are
already in `logs/review/`.

## Interface requests

Provisional, independently reproduced:

- FRONTEND: `flow.Layout.lvs()` must use PNR's physically proved unused-input
  handling. `assign y=~a` with an unused input b fails through the facade but
  matches through `pnr.strict_lvs`. See `logs/review/interface_probes.json`.
- FRONTEND: include physical abstracts in notebook cache fingerprints. Changing
  `INV.abstract.json` leaves `runtime_fingerprint` identical in the probe.
- SIM: published scaling/load sources differ from the **pinned** public PDK
  extraction deck; all six widths and the load sweep fail publication-source
  validation in the fresh environment. See `logs/review/publication_audit.json`.

## Blockers

No input from the user is required. Pinned amd64 binary execution cannot be
established on this aarch64 host; the limitation will remain in the final report.
