# Integrator queue

Pending hand-offs (send when the stream's current run finishes):

- CELLS (after timing tables): requalify all cells against the pinned PDK
  (~/pdk/TR-1um-pinned, commit 5d963db): DRC, LVS, abutment, equivalence; republish atomically.
- Integrator after all republish: move tag colab-v0 to the new head (REVIEW finding 1),
  re-run REVIEW on the new head.
- FRONTEND (after phase 8): copy root NOTICE into the submission folder and mention it in its README licence section.
