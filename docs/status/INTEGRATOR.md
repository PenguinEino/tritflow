# Integrator queue

Pending hand-offs (send when the stream's current run finishes):

- CELLS (after timing tables): requalify all cells against the pinned PDK
  (~/pdk/TR-1um-pinned, commit 5d963db): DRC, LVS, abutment, equivalence; republish atomically.
- FRONTEND (after submission packaging): REVIEW findings 4 (flow facade LVS → pnr.strict_lvs),
  5 (cache fingerprint must hash abstracts/manifest), 7 (opening demo vectors exercise every
  output incl. MSB), 8 (labelled schematic-to-layout presentation), 6 (writer side of shared
  naming if SIM requests it), add `signoff()` delegate (PNR status), use docs/author.md.
- Integrator after all republish: move tag colab-v0 to the new head (REVIEW finding 1),
  re-run REVIEW on the new head.
