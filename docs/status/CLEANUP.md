# CLEANUP status

Date: 2026-10-23. Worktree: `/home/ishi-kai/code-a-chip-cleanup`, branch `notebook-v3-cleanup`.
No commits, pushes, or git-state changes are authorized or performed.

## Complete

Removed 1,049 obsolete tracked files (84.91 MiB) and moved three retained helpers into v3. The repository's notebook entry path is v3; the English landing page links both languages on `main`. Dependency/removal/reference audits, both-language execution and final regressions are complete.
The only allowed edit to the parallel v3 builder is its helper import path. Parallel narratives, views, scale_views and reuse remain untouched.

## Dependency decisions

- Roots: both generated v3 notebooks and their builder; Colab setup and runtime locks; `notebook/reuse.py`; `notebook/scale_views.py`; dot4 shuttle build/verify; `examples/dot_scaling.py`; submission builder/capture/export; cell generation and the TritFlow library, with their tests.
- Keep the entire `tritflow/` library and its own regression tests and examples. They exercise public flow, HDL, simulation, layout and timing APIs beyond the notebook's default circuit.
- Keep `cells/` unchanged: v3 reads cell GDS, abstracts, schematic/extracted SPICE, truth/characterization/timing tables, qualification files, source devices and INV/NANY sizing grids. Producers and tests also use the native qualification evidence.
- Keep `results/dot_scaling.json` and its companion directory, including the archived producer and native payload hash reports; its reader verifies explicit source and artifact hashes. Keep STA propagation characterization tables and their native runs, used to build and check those tables.
- `notebook/cache.py` is a hashed scaling input. Preserve its exact bytes and the presentation module its cache-progress API imports; removal must not bypass recorded-data checks.
- Keep dot4's shuttle assets, evidence archive and `reuse_before_english.py`; the latter is an explicitly checked historical producer snapshot, not an executable alternate notebook.
- Move required v2 setup/table helpers and the compact schematic exporter to v3; retain compact SVGs, editable Xschem sources and their electrical verifier. Remove obsolete gallery variants and gallery-only checks.
- Preserve referenced briefs/status notes; remove only five unreferenced retired v1 notes (listed below). In particular `docs/notebook-v2/STORYBOARD.md` remains binding. Historical path mentions in these read-only records are not current runtime dependencies.

## Done

- Read `AGENTS.md`, `docs/concept.md`, `docs/interfaces.md`, `briefs/CLEANUP.md`, `briefs/V3.md`, and both storyboard rules.
- Baseline tracked-file hashes and import audit are kept under ignored `build/cleanup/`.

## Blockers

None.

## Interface requests

None. The integrator must rebuild and publish final source pins and the submission payload after merging parallel streams.

## Validation

- Final library + notebook suite: **924 passed, 2 skipped** in 624.73 s.
- V3 language suite: **45 passed**.
- Submission suite: **19 passed; exactly 2 expected stale-payload failures** (details below).
- Both notebooks: **31/31 code cells passed**, with ngspice-42.
- Native schematic verifier, retained publication readers, active-path reference audit and `git diff --check`: passed.

## Removal ledger

Each group below states its reason and enumerates every removed tracked path. Moves are recorded separately.

### Moves (preserved functionality)

- `notebook/v2/setup_cell.py` → `notebook/v3/setup_cell.py`: required setup/table generation or compact schematic regeneration for v3.
- `notebook/v2/make_tables.py` → `notebook/v3/make_tables.py`: required setup/table generation or compact schematic regeneration for v3.
- `notebook/v2/compact_schematics.py` → `notebook/v3/compact_schematics.py`: required setup/table generation or compact schematic regeneration for v3.

### Removal group 1 (11 files)

Figure producer/helper for removed v1/v2-only figures; not imported by either retained v3 figure producer.

<details><summary>Removed paths</summary>

- `figures/data.py`
- `figures/fig_cell.py`
- `figures/fig_flow.py`
- `figures/fig_gates.py`
- `figures/fig_pnr.py`
- `figures/fig_postlayout.py`
- `figures/fig_scaling.py`
- `figures/fig_sizing.py`
- `figures/fig_sta.py`
- `figures/fig_synth.py`
- `figures/gdsdraw.py`

</details>

### Removal group 2 (27 files)

Figure output used only by superseded notebook/paper views; v3 retains its two opening/flow figures in both required languages.

<details><summary>Removed paths</summary>

- `figures/out/fig_cell.pdf`
- `figures/out/fig_cell.png`
- `figures/out/fig_cell.svg`
- `figures/out/fig_flow.pdf`
- `figures/out/fig_flow.png`
- `figures/out/fig_flow.svg`
- `figures/out/fig_gates.pdf`
- `figures/out/fig_gates.png`
- `figures/out/fig_gates.svg`
- `figures/out/fig_pnr.pdf`
- `figures/out/fig_pnr.png`
- `figures/out/fig_pnr.svg`
- `figures/out/fig_postlayout.pdf`
- `figures/out/fig_postlayout.png`
- `figures/out/fig_postlayout.svg`
- `figures/out/fig_scaling.pdf`
- `figures/out/fig_scaling.png`
- `figures/out/fig_scaling.svg`
- `figures/out/fig_sizing.pdf`
- `figures/out/fig_sizing.png`
- `figures/out/fig_sizing.svg`
- `figures/out/fig_sta.pdf`
- `figures/out/fig_sta.png`
- `figures/out/fig_sta.svg`
- `figures/out/fig_synth.pdf`
- `figures/out/fig_synth.png`
- `figures/out/fig_synth.svg`

</details>

### Removal group 3 (8 files)

Recorded v1 adder, four-design campaign, paper evidence or ngspice-migration archive; v3 uses live circuits plus dot-product/shuttle records.

<details><summary>Removed paths</summary>

- `notebook/assets/chip/adder4/README.md`
- `notebook/assets/chip/adder4/signoff.json`
- `notebook/assets/chip/adder4/tr_1um_adder4.gds`
- `notebook/assets/chip/adder4/tr_1um_adder4.png`
- `notebook/assets/four_designs.zip`
- `notebook/assets/ngspice42_changes.json.gz`
- `notebook/assets/ngspice42_summary.json`
- `notebook/assets/paper_evidence.json`

</details>

### Removal group 4 (13 files)

Obsolete light/dark gallery SVG or gallery manifest; v3 reads the four compact Xschem SVGs and the INV table schematic instead.

<details><summary>Removed paths</summary>

- `notebook/assets/schematics/INV.dark.svg`
- `notebook/assets/schematics/INV.svg`
- `notebook/assets/schematics/NAND.dark.svg`
- `notebook/assets/schematics/NAND.svg`
- `notebook/assets/schematics/NANY.dark.svg`
- `notebook/assets/schematics/NANY.svg`
- `notebook/assets/schematics/NOR.dark.svg`
- `notebook/assets/schematics/NOR.svg`
- `notebook/assets/schematics/full_adder.dark.svg`
- `notebook/assets/schematics/full_adder.svg`
- `notebook/assets/schematics/half_adder.dark.svg`
- `notebook/assets/schematics/half_adder.svg`
- `notebook/assets/schematics/manifest.json`

</details>

### Removal group 5 (19 files)

Superseded v1 notebook, orchestration, evidence reader, migration/portability harness or evidence-only lock; not consumed by any retained v3 root.

<details><summary>Removed paths</summary>

- `notebook/campaign.py`
- `notebook/check_portability.py`
- `notebook/colab_evidence.py`
- `notebook/colab_verified.json`
- `notebook/editorial.py`
- `notebook/experiments.py`
- `notebook/learning.py`
- `notebook/make_notebook.py`
- `notebook/markdown_support.py`
- `notebook/methods.py`
- `notebook/paper_evidence.py`
- `notebook/pin_changes.py`
- `notebook/requirements-evidence-lock.txt`
- `notebook/requirements-evidence.in`
- `notebook/routing_identity.py`
- `notebook/schematics.py`
- `notebook/stages.py`
- `notebook/tritflow_tr1um.ipynb`
- `notebook/tritflow_tr1um_ja.ipynb`

</details>

### Removal group 6 (38 files)

Superseded v1 narrative and caption/geometry inputs; the v3 bilingual narratives are the submission source.

<details><summary>Removed paths</summary>

- `notebook/narrative/00_intro.md`
- `notebook/narrative/01_gates.md`
- `notebook/narrative/02_sizing.md`
- `notebook/narrative/03_cells.md`
- `notebook/narrative/04_hdl.md`
- `notebook/narrative/05_synthesis.md`
- `notebook/narrative/06_pnr.md`
- `notebook/narrative/07_results.md`
- `notebook/narrative/08_your_circuit.md`
- `notebook/narrative/09_next.md`
- `notebook/narrative/A_limits.md`
- `notebook/narrative/B_evidence.md`
- `notebook/narrative/C_reuse.md`
- `notebook/narrative/captions.md`
- `notebook/narrative/figures.md`
- `notebook/narrative/pitch.md`
- `notebook/narrative/placeholders.md`
- `notebook/narrative/pr_description.md`
- `notebook/narrative/predict_first.md`
- `notebook/narrative/readme_draft.md`
- `notebook/narrative/readme_final.md`
- `notebook/narrative/reference_geometry.json`
- `notebook/narrative/teaser.md`
- `notebook/narrative_ja/00_intro.md`
- `notebook/narrative_ja/01_gates.md`
- `notebook/narrative_ja/02_sizing.md`
- `notebook/narrative_ja/03_cells.md`
- `notebook/narrative_ja/04_hdl.md`
- `notebook/narrative_ja/05_synthesis.md`
- `notebook/narrative_ja/06_pnr.md`
- `notebook/narrative_ja/07_results.md`
- `notebook/narrative_ja/08_your_circuit.md`
- `notebook/narrative_ja/09_next.md`
- `notebook/narrative_ja/A_limits.md`
- `notebook/narrative_ja/B_evidence.md`
- `notebook/narrative_ja/C_reuse.md`
- `notebook/narrative_ja/captions.md`
- `notebook/narrative_ja/labels.json`

</details>

### Removal group 7 (8 files)

Tests of removed v1/v2-only orchestration, prose, campaign provenance, migration ledger or recorded Colab publication; current runtime, source pins, assets and v3 language checks remain.

<details><summary>Removed paths</summary>

- `notebook/tests/test_bootstrap.py`
- `notebook/tests/test_campaign.py`
- `notebook/tests/test_colab_presentation.py`
- `notebook/tests/test_editorial.py`
- `notebook/tests/test_experiments.py`
- `notebook/tests/test_japanese.py`
- `notebook/tests/test_pin_changes.py`
- `notebook/tests/test_routing_identity.py`

</details>

### Removal group 8 (10 files)

Superseded v2 notebook, prototype, generator or prose; required helpers have moved to v3.

<details><summary>Removed paths</summary>

- `notebook/v2/make_notebook.py`
- `notebook/v2/make_prototype.py`
- `notebook/v2/narrative/00_opening.md`
- `notebook/v2/narrative/01_first.md`
- `notebook/v2/narrative/02_cells.md`
- `notebook/v2/narrative/03_hdl.md`
- `notebook/v2/narrative/04_pnr.md`
- `notebook/v2/narrative/05_verify.md`
- `notebook/v2/prototype_live.ipynb`
- `notebook/v2/tritflow_ja.ipynb`

</details>

### Removal group 9 (909 files)

Historical v1/v2 adder/load/corner/audit/timing result or superseded-run archive; absent from v3 reads and retained regression fixtures. Current STA propagation characterization and dot-product evidence remain.

<details><summary>Removed paths</summary>

- `results/adder_scaling.html`
- `results/adder_scaling.json`
- `results/adder_scaling_fit.html`
- `results/cell_pinned_lvs.json`
- `results/corners/BUF.html`
- `results/corners/INV.html`
- `results/corners/NAND.html`
- `results/corners/NANY.html`
- `results/corners/NOR.html`
- `results/corners/cases/05f71b1df7c30c5e909cd076808980e6d4520046d50c45d9cf526b43b8cfe7fb.json.gz`
- `results/corners/cases/08e8dd73c8078c3944d48c53d6c3b3ebfca167f463bb15377e35576eda28dd6a.json.gz`
- `results/corners/cases/09042c155fe42ba9ccf10b1eb77eacbff9df5400d5efc526a4c68764ef692bf0.json.gz`
- `results/corners/cases/0daa06e8db1542aa2416dc78cb7e43e09b4a91622f977fdb5275c25736addba0.json.gz`
- `results/corners/cases/0f871c14d4ed93f3be3ed6b98c5dab3b3ae9b51d9fce19a7df16da87e1983be4.json.gz`
- `results/corners/cases/140281528f1a9fd8e7822ba35ba39e64698f1ed833f74c122900bfd5e49368f1.json.gz`
- `results/corners/cases/155da2f91bbb227b67474260efa7470bf0896adcbf15cb25ca631d177471af5c.json.gz`
- `results/corners/cases/1b746f47386bc086eed3792a2909659c10c63d866e7de4aef43b608f333a3e8c.json.gz`
- `results/corners/cases/1d2c4d0e81bf067d128596fd5ce325947fa5ce8d72ae3ee5e15a9d0d1c4d62d2.json.gz`
- `results/corners/cases/1e4f88761151d22a092c9841ab389a2a35677e9725fa35dbed2d52a4c2211ea1.json.gz`
- `results/corners/cases/20ac2216451f248bcb038a65a84c87dc9ef5440066bbfeb4f2e0b07ef460c01f.json.gz`
- `results/corners/cases/20e1f8bd96928ceb6aba09a1a613c76fe1e45abac4157b72b7225d28e3955833.json.gz`
- `results/corners/cases/23d639ee4090eedde1813a255f0146f9d706c55a8f86d75d115cfb4aff231aa6.json.gz`
- `results/corners/cases/250347a4ae6f5132d05347f3fdcdab3d85f6f976508e9a7e047ad4ca416c96c8.json.gz`
- `results/corners/cases/254eb5b73d15cb3477fcc2d9c80e56b8f5da8f3d3d2ccd492855214b59555620.json.gz`
- `results/corners/cases/2681078f59c76fbb8f6f703850cd4ffed3ce8812b74b2168cdaff3f1b1d7f0c6.json.gz`
- `results/corners/cases/27305c213603734f9f650147846010821d1609e6e5d36f4a17522d6fa3f83b35.json.gz`
- `results/corners/cases/28b71a3b8d5e2faef09fecb3230e76e512ab0500fd13acb412b8bfc452f0d861.json.gz`
- `results/corners/cases/2a2badb30c5755079395c639ee2fb637ebd19f411d35a30a6262d9433c1202fe.json.gz`
- `results/corners/cases/31ad4ee9276bfbd390c7f5adfc1384906193ea045963e9b979d6fc2f03f255b8.json.gz`
- `results/corners/cases/33fab4dd142bdbe7a220002fa9846e3a41a58657824dc538bffc4646302cd5ed.json.gz`
- `results/corners/cases/36237cdb8c2c396c976e95edb13e3dd88e39c6643d030d5a814d3f8a6d109843.json.gz`
- `results/corners/cases/36eb331e924e0bb93cfeea72da437479dca7254d9bb1a75cfc135489e3e87cc5.json.gz`
- `results/corners/cases/381946cd15008e8bd9cd49983c8fcb4802987d57f63165b557308e432b27079a.json.gz`
- `results/corners/cases/38a80c2390caa611e30579b4c1955404aa250ed6f4138849c684ef10082c20f4.json.gz`
- `results/corners/cases/38f38ac7bf3d0142f79962876175c38d6230257a4c9582cafe48aeb533c1ece2.json.gz`
- `results/corners/cases/39f912998f51837cc73f970cdc81def6cbf151c79a99cb3969d167c36b938e6c.json.gz`
- `results/corners/cases/3bdc9f3a021dd877c95250b43b85ca34e998310280c1d0768e3a7f0d8bfd88f1.json.gz`
- `results/corners/cases/3d19fae115144c4c0aad8fa6c31f3bb4a59e20c2a8734f6605472c2f6cd8c91a.json.gz`
- `results/corners/cases/3d583db4e1ac204c7178eed7d758c84c57db5c1820ea6cf9a44f8553d6d78d0b.json.gz`
- `results/corners/cases/41e8577c8cb3aca5aad6caf09d857efcc8a46e241cc1397faca7003a11d2dcd6.json.gz`
- `results/corners/cases/44431b252f8caa03092c0e452420c3d11322eb768845a8fac81beac39dccece4.json.gz`
- `results/corners/cases/464bc44a76bc1fe281973fefaa32509c612d55067e0cde087f12ef9104fedc3d.json.gz`
- `results/corners/cases/466b9ab12c4b49792b2b66cfbf63f2f0b3efec09db9349775c025efd634c7fc6.json.gz`
- `results/corners/cases/476b65187d55ccfb073ec8b717baac94352f52675d5e2d61e025e9d3a0be8983.json.gz`
- `results/corners/cases/49eeb23093b3bdad1a604bb0ef3d12fe154b4f9ac41fbef2b8ea1a1e7a6c1099.json.gz`
- `results/corners/cases/4b0f8843f3beb3f9b15784cc3f7fe55724afb153991a6639d093607f00e89971.json.gz`
- `results/corners/cases/4f59add457699f5e5c56b8a13eed17c1ab64d72399e25022a635cda4b36fa164.json.gz`
- `results/corners/cases/5102ecc5b4c3b8de0c45adf4f637ce1433a36431a5491f86dcfc01ecc72424c7.json.gz`
- `results/corners/cases/53295e5fd6baad305e460fa56fda2e5dfee37acc504d7379768a5ce3fcd2b3c1.json.gz`
- `results/corners/cases/5358fb1d90da020df493ebfe64804c88e0e5b7397301634698ca274be5cd89e0.json.gz`
- `results/corners/cases/55df73723038295bcde789fe229e2281d3122cea9e0716e31f37db1aabf88fe2.json.gz`
- `results/corners/cases/597933bb22a130cb7dd68e6f60fe510ad3c92687ff0927b90a0f98197f365391.json.gz`
- `results/corners/cases/598c0e58b35af46577e5ef0718d1c0c24d0c4af3c6338cec0e2bf455532d6ee5.json.gz`
- `results/corners/cases/5d9c721d3c512cbee41d5bc39e22c3ce4568c64ddd67a5811df943354d525187.json.gz`
- `results/corners/cases/6290a6d11dbcb7b2949d6db26a2857d9779d9f7d4b7af03da8fd83442f2d1fc8.json.gz`
- `results/corners/cases/6356dc89aef084697d5dfc643a012b1583611b90b43b82ede3bb67580f3e5822.json.gz`
- `results/corners/cases/64f842e80e5e510ec34bfc30280906b4a13ee39c5a7bf6e45abf9ec53cb31cf7.json.gz`
- `results/corners/cases/6885f87c80613c45ca16c69d00616720e8b04bf839ffc88f04092904cfed096c.json.gz`
- `results/corners/cases/6a034a12bc9d4b94f9ab37bd039ec66951e21d78a581ba67e5c75a0af58c9143.json.gz`
- `results/corners/cases/6eaba9bb60f0ad9dd6778cddf97043785da5e78efe989ecc25aca24c47902478.json.gz`
- `results/corners/cases/718f27980268f52ba15df4bc112dc795e6582bb9ee48023d90b5b8c37a69607e.json.gz`
- `results/corners/cases/71df02f36ffef0cc7a1cb0ca65309d85a459d4105366fd7f1d8f69fb535f7b5c.json.gz`
- `results/corners/cases/750e4b5680f91cb9268f3ee9431b076fb665327897ed8bbf3a9762a271b1777f.json.gz`
- `results/corners/cases/7d818be3532d91d7b40735f9bccdbd6a179a6f36e4ff6205e562031c98d301b4.json.gz`
- `results/corners/cases/7e23ea960bd159aa7b23855dc445ca7f9014459b28a8d0f232cca9495a595b22.json.gz`
- `results/corners/cases/7f0f19e0b000a3975cf077898f4db9bb8c4f89cc3534ee35509f5d32e2b4bd65.json.gz`
- `results/corners/cases/81d5395bb0e8b635da3a6c1ab0b7de80f3033cb6d51cc0cec4eea4106d35a32f.json.gz`
- `results/corners/cases/87a3e9aeedbd1406a29645169a44365323af39586ce291cff4255b3b23d744e8.json.gz`
- `results/corners/cases/8987a0a5c6580f992d0542d981a3c2035f39e2cccd69b2c11a9222f64808aac6.json.gz`
- `results/corners/cases/9139542191ad65229c04af6b6389a013d166f377b77b88f5cc241bec5e7df2c0.json.gz`
- `results/corners/cases/91b3a9f53329a5519bbfeb264caa5a8bea24fccdeb875513f6dbd645e6812572.json.gz`
- `results/corners/cases/95cd7d8727c343df38dccfe75ee3d2f2d304618859abc0ca388b295933d55ce7.json.gz`
- `results/corners/cases/9766c297d9dcc20cfa7fff2a76953a8c181cd9c5d4244d351bcf5aae2efc26d4.json.gz`
- `results/corners/cases/9be1260e7da2954004ee14e725e2bff4f0837bea82fa921d01a49052081e204d.json.gz`
- `results/corners/cases/9c6e29147e4cdf9bb31d4284bc5adf8f23992854e3562e988026044154dc70ae.json.gz`
- `results/corners/cases/a2889398899af93fe783fa7e6e6e93febd240f14b62e1f9421558aad16e058fc.json.gz`
- `results/corners/cases/a54ca625ff95ece55c468e1a0a685bee622a04801414ec35a52e4df6c5cc867b.json.gz`
- `results/corners/cases/a54cf95eb22211a218b2e0884dba01af7efc192a0b8963180bb86b663daeb9bf.json.gz`
- `results/corners/cases/a669366ed1dcebed2289b7b726392e656d6a84b7b77e154363fce126ad779a33.json.gz`
- `results/corners/cases/a97a8ead89c9db378687ce30bd1f15ff0b50eb94cd70e874f51f66dafd4b1de8.json.gz`
- `results/corners/cases/aa837713eb46eaf479ff9d5dadab16b3b538d2b43dbb412bd457fe2fe4d9fcd6.json.gz`
- `results/corners/cases/ac6d9fb29254fd70dc440e1398669e5a85c40ffde2a946f9694d515d179a6b98.json.gz`
- `results/corners/cases/ad833f2f5132f9285c7bdb3971868fa1d8368e8ebc6dd4a3502f0abac913906c.json.gz`
- `results/corners/cases/ae0d7002c90047603267a2348ebdd0841aaf69371f11c7ab6b60538a098ec767.json.gz`
- `results/corners/cases/ae45a13730c4ff8aaada9ea2aa859db91e212e98358a2f87eb77987baa16e751.json.gz`
- `results/corners/cases/b057b993b9ce6ec01239ca1d15055cfe6428f94d7c8c7b5140dfc4e8ab53e86a.json.gz`
- `results/corners/cases/b15c100aa81f02ab414110d6cd4659be746df69046d9c8ac7de0a601aae13832.json.gz`
- `results/corners/cases/b5956eade0ef72655e4d4bd25c9cdab97ca8c63bbfc76d5eecec02f4201e96b1.json.gz`
- `results/corners/cases/b5982c52c9fdb6a7749bbf29919e6e65e4ef5ffee3357cd175928ffd33aec9b9.json.gz`
- `results/corners/cases/b625d0cb6bd94f000ad6ace7ee0715b8ec7d3639134e9bf0db7d1a9447fcf760.json.gz`
- `results/corners/cases/b945a489fc70b1e25492d21e0b93058c890849d0ccf310d4007ecebfd314447c.json.gz`
- `results/corners/cases/bbc4162f121bf52fc44266a89757f9da34b31fe020b6faebdd5f947f09b51c66.json.gz`
- `results/corners/cases/bc0cc07061b91adf0a2b2feb54cc087754ad746134517dd22d9199aa276d5507.json.gz`
- `results/corners/cases/bc6057db30c31321bb88af5acd9dd22a8875af488c69a07ffe837ec19733c887.json.gz`
- `results/corners/cases/be395ec5718b15d4658bfd60c7abda87ddc256d2229a6ad7107a0504fbfdbebd.json.gz`
- `results/corners/cases/bf5e2c221bfefa94c1842f08cbbf9e62229204bcf1917a16509af49cd48a2b18.json.gz`
- `results/corners/cases/c328b664b73e462c7a6c8285af4b9d3d7377b5437d51c62fd73f38809cdc0236.json.gz`
- `results/corners/cases/c4523558c02d7a1e5fe308317d9f24cc3b9b609c13628735a4bc21b30592617c.json.gz`
- `results/corners/cases/c744fc8998e67bd5311bf0f675870f2db9b73e42ff3e0b06aba09623f90528c3.json.gz`
- `results/corners/cases/cbf1fdc48f2b12ac89ead2d01ab5122d1e55e1502b112435672c8e40d5872b2a.json.gz`
- `results/corners/cases/cbff4a494a54bb1e63da2b2c14364d677acc8090f34e09700904e397d1cd7a3a.json.gz`
- `results/corners/cases/cece3a2254a0145942bce5eb3bfe5e4311c98a41583e25bd363e89b7bfd90ce7.json.gz`
- `results/corners/cases/d10c4a4e260011a14071bde3ac024fd7dc1054b57727013c44d39a84fe657ea0.json.gz`
- `results/corners/cases/d5b33f54989a72fce992f1122c2aa3f74efb98455aa258a090519a49498c58a7.json.gz`
- `results/corners/cases/db7ba5fbee4444721520020184805fcd9007787e801276d02b3cc43159c0c658.json.gz`
- `results/corners/cases/e5647e0d571a40d01c363481b404583803fe39a3ddc0172e52565f97fd2d629b.json.gz`
- `results/corners/cases/e618bc1730863629de767a3ca8b753702c882b174528622f815d6b113fe3b3aa.json.gz`
- `results/corners/cases/e8462b002a1528330ce904a537cc999b6ab96d2a4feb06c15210c2dfe079d8cd.json.gz`
- `results/corners/cases/eaae46c9f867fa74d93fbf67b3cb546e52643195165e02d86f95848706d00439.json.gz`
- `results/corners/cases/ed94f9ac5209f8c0cd3a21c8db114b357bdb1c4605003c0ff882757eb8f70130.json.gz`
- `results/corners/cases/f089d07f0d083bc56e8e1ef507e2ce944bce175e2af5133b8623ece748012d86.json.gz`
- `results/corners/cases/f3bb7739f50d3379cebb5eedb9bec690b94d64f34cd6dabb2e6c566e18e7cc7d.json.gz`
- `results/corners/cases/f4564d5404783fe876fae22cce2136d540cafbe158fc5064d641d3a9732dd272.json.gz`
- `results/corners/cases/f665311354118840c3ae366becdc119b5e83e15d3df0dfedb8896eca54318fe0.json.gz`
- `results/corners/cases/f680308c2236eab97056dc9943bc593ba4c7d42e947ef34f2b4f4deb32dc6b63.json.gz`
- `results/corners/cases/fbe0da894536ebd44c51f9cc2d14913feb9ba4bea6d108edfabf5dbd8ce45e43.json.gz`
- `results/corners/cases/fc7a291015c9973fc680e4ca13a810ffec444ad79428c68f74da14bf648d0a60.json.gz`
- `results/corners/full_add.html`
- `results/corners/summary.json`
- `results/dc_bias_before/cells/out/BUF/BUF.char.json.gz`
- `results/dc_bias_before/cells/out/BUF/BUF.poly.timing.json.gz`
- `results/dc_bias_before/cells/out/BUF/BUF.timing.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_00_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_00_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_00_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_00_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_00_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_00_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_00_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_00_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_01_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_01_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_01_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_01_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_01_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_01_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_01_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_01_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_02_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_02_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_02_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_02_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_02_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_02_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_02_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_02_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_03_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_03_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_03_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_03_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_03_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_03_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_03_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/BUF/timing/ramp_03_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/FILL/FILL.poly.timing.json.gz`
- `results/dc_bias_before/cells/out/FILL/FILL.timing.json.gz`
- `results/dc_bias_before/cells/out/INV/INV.char.json.gz`
- `results/dc_bias_before/cells/out/INV/INV.poly.timing.json.gz`
- `results/dc_bias_before/cells/out/INV/INV.timing.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_00_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_00_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_00_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_00_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_00_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_00_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_00_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_00_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_01_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_01_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_01_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_01_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_01_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_01_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_01_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_01_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_02_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_02_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_02_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_02_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_02_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_02_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_02_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_02_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_03_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_03_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_03_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_03_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_03_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_03_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_03_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/INV/timing/ramp_03_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/NAND.char.json.gz`
- `results/dc_bias_before/cells/out/NAND/NAND.poly.timing.json.gz`
- `results/dc_bias_before/cells/out/NAND/NAND.timing.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_00_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_00_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_00_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_00_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_00_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_00_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_00_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_00_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_01_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_01_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_01_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_01_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_01_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_01_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_01_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_01_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_02_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_02_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_02_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_02_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_02_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_02_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_02_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_02_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_03_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_03_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_03_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_03_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_03_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_03_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_03_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NAND/timing/ramp_03_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/NANY.char.json.gz`
- `results/dc_bias_before/cells/out/NANY/NANY.poly.timing.json.gz`
- `results/dc_bias_before/cells/out/NANY/NANY.timing.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_00_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_00_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_00_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_00_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_00_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_00_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_00_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_00_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_01_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_01_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_01_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_01_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_01_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_01_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_01_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_01_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_02_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_02_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_02_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_02_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_02_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_02_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_02_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_02_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_03_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_03_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_03_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_03_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_03_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_03_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_03_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NANY/timing/ramp_03_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/NOR.char.json.gz`
- `results/dc_bias_before/cells/out/NOR/NOR.poly.timing.json.gz`
- `results/dc_bias_before/cells/out/NOR/NOR.timing.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_00_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_00_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_00_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_00_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_00_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_00_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_00_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_00_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_01_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_01_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_01_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_01_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_01_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_01_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_01_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_01_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_02_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_02_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_02_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_02_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_02_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_02_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_02_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_02_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_03_load_00/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_03_load_01/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_03_load_02/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_03_load_03/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_03_load_04/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_03_load_05/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_03_load_06/measurements.json.gz`
- `results/dc_bias_before/cells/out/NOR/timing/ramp_03_load_07/measurements.json.gz`
- `results/dc_bias_before/cells/out/TIEN/TIEN.char.json.gz`
- `results/dc_bias_before/cells/out/TIEN/TIEN.poly.timing.json.gz`
- `results/dc_bias_before/cells/out/TIEN/TIEN.timing.json.gz`
- `results/dc_bias_before/cells/out/TIEP/TIEP.char.json.gz`
- `results/dc_bias_before/cells/out/TIEP/TIEP.poly.timing.json.gz`
- `results/dc_bias_before/cells/out/TIEP/TIEP.timing.json.gz`
- `results/dc_bias_before/cells/out/TIEZ/TIEZ.char.json.gz`
- `results/dc_bias_before/cells/out/TIEZ/TIEZ.poly.timing.json.gz`
- `results/dc_bias_before/cells/out/TIEZ/TIEZ.timing.json.gz`
- `results/dc_bias_before/cells/out/equivalence_report.json.gz`
- `results/dc_bias_before/cells/out/generation.json.gz`
- `results/dc_bias_before/cells/out/library.json.gz`
- `results/dc_bias_before/cells/out/pdk_provenance.json.gz`
- `results/dc_bias_before/cells/out/poly_timing_report.json.gz`
- `results/dc_bias_before/cells/out/sizing/INV.grid.json.gz`
- `results/dc_bias_before/cells/out/sizing/NANY.grid.json.gz`
- `results/dc_bias_before/cells/out/template.json.gz`
- `results/dc_bias_before/cells/out/timing_report.json.gz`
- `results/dc_bias_before/cells/out/timing_validation.json.gz`
- `results/dc_bias_before/cells/out/verify_report.json.gz`
- `results/dc_bias_before/initial_git_status.txt`
- `results/dc_bias_before/manifest.json`
- `results/dc_bias_before/notebook/assets/paper_evidence.json.gz`
- `results/dc_bias_before/results/adder_scaling.json.gz`
- `results/dc_bias_before/results/cell_pinned_lvs.json.gz`
- `results/dc_bias_before/results/corners/summary.json.gz`
- `results/dc_bias_before/results/delay_annotation_bug.json.gz`
- `results/dc_bias_before/results/delay_diagnosis.json.gz`
- `results/dc_bias_before/results/delay_refined.json.gz`
- `results/dc_bias_before/results/environment.json.gz`
- `results/dc_bias_before/results/frozen_synth_requalification.json.gz`
- `results/dc_bias_before/results/full_add_load_sweep.json.gz`
- `results/dc_bias_before/results/operating_point_audit.json.gz`
- `results/dc_bias_before/results/pdk_parameters.json.gz`
- `results/dc_bias_before/results/phase4_comparison.json.gz`
- `results/dc_bias_before/results/pinned_requalification.json.gz`
- `results/dc_bias_before/results/rail_current_audit.json.gz`
- `results/dc_bias_before/results/rail_margin_change.json.gz`
- `results/dc_bias_before/results/sta/example_adder4.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/example_adder4.timing.json.gz`
- `results/dc_bias_before/results/sta/example_full_add.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/example_full_add.timing.json.gz`
- `results/dc_bias_before/results/sta/example_mac1.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/example_mac1.timing.json.gz`
- `results/dc_bias_before/results/sta/example_mul1.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/example_mul1.timing.json.gz`
- `results/dc_bias_before/results/sta/propagation/summary.json.gz`
- `results/dc_bias_before/results/sta/propagation/tables/BUF.propagation.json.gz`
- `results/dc_bias_before/results/sta/propagation/tables/INV.propagation.json.gz`
- `results/dc_bias_before/results/sta/propagation/tables/NAND.propagation.json.gz`
- `results/dc_bias_before/results/sta/propagation/tables/NANY.propagation.json.gz`
- `results/dc_bias_before/results/sta/propagation/tables/NOR.propagation.json.gz`
- `results/dc_bias_before/results/sta/resolution/comparison.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder1.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder1.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder2.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder2.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder3.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder3.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder4.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder4.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder5.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder5.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder6.tested.timing.json.gz`
- `results/dc_bias_before/results/sta/scaling_adder6.timing.json.gz`
- `results/dc_bias_before/results/sta/validation.json.gz`
- `results/dc_bias_gate_curves.json`
- `results/delay_annotation_bug.json`
- `results/delay_diagnosis.json`
- `results/delay_refined.json`
- `results/dev_before_pinned/README.md`
- `results/dev_before_pinned/cells/out/BUF/BUF.char.json`
- `results/dev_before_pinned/cells/out/INV/INV.char.json`
- `results/dev_before_pinned/cells/out/NAND/NAND.char.json`
- `results/dev_before_pinned/cells/out/NANY/NANY.char.json`
- `results/dev_before_pinned/cells/out/NOR/NOR.char.json`
- `results/dev_before_pinned/cells/out/TIEN/TIEN.char.json`
- `results/dev_before_pinned/cells/out/TIEP/TIEP.char.json`
- `results/dev_before_pinned/cells/out/TIEZ/TIEZ.char.json`
- `results/dev_before_pinned/cells/out/sizing/INV.grid.json`
- `results/dev_before_pinned/cells/out/sizing/NANY.grid.json`
- `results/dev_before_pinned/earlier_corner_cases/00b4d1213bf5900da27319a6ae40fa77090a4a90a42a1831a9f8cdfc15c4832a.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/01139798291484f7cdd05ffed712c10147da5e59be4b9073fdc8ed6e1e7fea08.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/0309ac1aacb6b52f7131aac9d874245d4bf8a467c7b7639ae19dfc8dc062d664.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/0343ba233506d46709c30b9a5a2bd84069d03a149ea4e3b8efe90931c6c3349a.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/0678538723b67e1293bf86333fc1e1731a941a38b880e4fe21f61656f1f51af8.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/06e0502ba9f58c54e58441de7dfddaf404c7199b342e62cce08db6d4a060e44e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/076192e157d091bd657e0c9607aea3b51498df8cc7adc43665aac7f32192a4ec.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/07909b9fd434ab723611f479f882949730790bf02d4d29188dbdd1c53a6913b5.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/086af1ebb283052d5b2a7438e8a66cc0c49db48e0bada036e69d28ebdddd450b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/088318f450f011b48a8734e6346a6d8213f641591a46c327dcc07dae245bea3c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/0bcc6867255f1e229ea6a8bf69d13dc8b545ca5ecfedd1c000efdb6c6d53b310.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/0be04e98e87efcfbb188421548860d81222772030d9fd9651cbafb3dd63fa42e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/0be334a726420b1df63057a58ff69d8dbad2da4037c47b9337837d9d82992ef7.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/0e572471187e2fe5e1abb42594026b2beedf6a1bcc084eb66700a94df058590c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/0ec9e51eebb10752bffb6fee5f222bb04033e39665681861d592a1981cfa19f9.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/10236d0094e0c4fcb65b396018fa2b40d3fc317d7f9db2518410617ea6894263.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/106003bd3d6281f8b37834b770c3d80b48e542216e1d8315f99c28cb53c5bec7.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/10999fd3feecb7d34a35e93b96619802980e02f5d59b29f7e10b737fb8609ff1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1144ae8b5ee07b12eba94f079ae51885b7a100f93105a3a2bcf5e5993ca09922.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1255f5e44d4fd4af6385b890d894320851031707f59335bfab7d9ceb3e08481c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/138d34a51eee55e87f8a6e7d106c6e884d97b58178029f22d0efb1ed53adfda2.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/13ba0937b72fca3cc04bad0f6c33452af1fdd70db9cfced95afad62f2e4ab78f.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1463a3e4b45a3b98e003d07916d3788bece56e1bbead846f45ee526c44602763.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/16f649d82e8e2f39de4b3fa48697d911a622cd3283dab15462263e7663127a34.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1848b32dfc57c0523d2d76115cfd677fc3d8c782f04917e01b0ae9a055e892a1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1941ce1c5331f00b38ef6ce9a404e7855df17ab6ae754f75740dd67c3c1a3b6e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1a452b5f055f1355a0c258b6c31423b63d29833119527bb45bba2dbe8529f3f1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1bdc6acc532cec09f583c35d1eda2c7f6c5a3066a6e1ccc81314f285d8105920.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1bef694cacc43e401d1865124a9f4bfdd83830996e855ae6d1de0f21837ea038.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1c75d57e7cf0f7f611e836548dfdf79595f6a08fa2df2448230d1a6e144c4da3.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1d66ec11cedf179fe5d2a440f8eaee2cc1359b038cad91654a05890a6359fd9b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1f1a5efe8a7ea7de2deac437bc732e13726009efa244862cbde7050f06adfc60.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/1f542c29b1cef9bf9da8ba8e8992ffb50ebfd90a489441d8f23de68665722193.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/200cb64557c6efe873b83b168da1f57e43f7eae1ff496cda79326d8e21f54a5d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/20908e1e4f3ca47493ffa451d50b8beb43cc2e386e9e0dedf975fc1613fb00fc.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/21829fda98d021b4ea559ab5e0c403c735947931241e149dbd096a90cdabf6b1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/21865e3a7badb5a39d64a7df87dd3d3c48f7e7b315df49d2974010160660fd9e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/220037de201a862a3f61e8ed321a2235ac2db995a9798755804405ddf44db349.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/222b889e58a6ad66385f9942209431889a2510e6ef9ade7f38ad95088944a87b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/22463f098dec625317c3f3c539e533227fe3b1d421111315b1cace105bc6a66f.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/229efdab4996c2b6555666bc4a9341f542ac8863974795247cbb15ce3e0b1666.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2400d0244efe7234edbc289e08339c33a88a3dc5d6989c7738cb3ee279c735fb.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2425aaa25616fff04602495a5fbe19e400b945ddba3c73a8e189ddd172fd7ed3.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/249e9b30d9e9793fed69583965e779fd78ef51974bd62b3264331d08140d1f5f.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2654536b6a3eb7cd44f9e3e4d6baeef6f525667143ce64cb9f7c47cd7ab096f3.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/27100251abad1716e5b60032d994cb3df043a4177a613eeb7a1fad394b3623a4.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2759c51dca93f410fb798c0874c67b9bbb255feeba6eef7544e2be710318ade4.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2768e00fcbcdfb467b955682497bc1c4fa8e3e20eef43a57662b6e947bd3bd9d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/283942c01ee28d28c8cbc798869bca917c02dad45f679a62e068ea25325befd3.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/28f8b18233aefcaea137f47f410eafadfefbeaaadacb91c3af0770163ab5b238.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2ae997d653167d58eb024899d618206476a71861eda6149b14cd7abee6ad657b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2b88510544feba2a939c674babad2a10bb838ad77427a1941741d2b63a8a56b7.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2c61b8903b976f29a0e942356880e0009ba39576d03cfe41f97ac68f7580a486.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2e3c513d6dcb4ff7a1c062aa8967f8611372cde837d5b9100d413df2ced309d1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/2e8f7bc7d45d7ad83d83492a37f3a421305d7625f7ce7fcb777a493b445a313c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/30797e17a85a76109b74167095bd652d16cc9a2c94dd2f0925d74778227db082.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/3133371883dc4c6ed1f44456b30f9533484fc6b94db3a476dbecddb7f63d62b8.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/3239db78855073f40dc2737c2d5376142e311b9b42b16c55dd9fc47ab465125b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/32ea48beed4752d9ab66ab11e7783291df71099d8cfd8b445c92106b4d69c579.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/338289c162368b193b731b4bd9e9e90654fe3bc4c09318a3419481ec987d3f3d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/34fc78b7856c2001f26aaef82cf9abd3e9bad09366b01b2935352428fd8cde90.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/351f5eed8bf6ce9ec9d465c7347104f3e439e7def59b89a35e333d20af7df98c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/37a8c55605ad31ca6e5efbd64848bc03ec2ce502191309ca04b4dc9e183beabb.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/38cf86c7710c27b34b54700f61e3895b7577a728e65581515e1d22e9ee794e83.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/39bdc9c55e8d1205b81d15d8b27f015ec069c09ea53e2c2e55dab0dbfcfb2ff2.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/3ae1eed2957957bf4a10ad926fbdc4dc4a673e9d288b8617b0ef2ca51239a3f9.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/3b29d0125073cd3ebab01e8814b5054ef77ed8b3a25fe1a5c3f3001e980c2cbd.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/3dca2e0550b5235b7bad9140c2da9bc609ead9544868a4e53d05a07ff48e9b0b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/3ee3476d9e2178aadb9811f0e46c3c1470adfdecd12b8db5552d0cc2dc9c22be.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/3f25ed065fe5a2c1585339953188f438aa86fb22d4ebb59dd393da56f4a423cd.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/3fc1621b2cc9f593330a24f370ce7fa029b5e47fa4f02d5ceb41dd7f4953822d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/421d4453e6469fcd428050404830ea5b5e43b82551984addf2f8a7b024773060.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/4272f5048f7ef9ac668371ca137840fe25e8fec91ff05fc69537cf0da32de518.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/44883107743a397244812094f04ad1b4550f316c8134583f58d6671fef96a048.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/458d265ac2bc6156dee15da68638543c3b4b881ad6e1c22ab7bd35c5b3183765.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/476699fa8c1680490da62177f352c380ccb762479fb9f405574538431a995eb2.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/477dae1492897500ca4d828fdeb7ed6940d56be6d6be19ca70b9d1f011d2a83c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/487b33bd8e9631eab8e059d0ff66de879c4646137426db76c384d065149257b2.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/49f173e3bb457daeb8019ebfef2a7708e7e467b78840b2302c29ce21d89bc533.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/4a3636dad50dfc4215bfd419901d91836aea041aab09a3d714dc0b032aecdb9f.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/4a98d70bfdb1c77520f09c48abc93b0fa74bec3a2c652b9e7176a3e80595c99c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/4b908ba9f74efd7972904167703a358b538df751848b54c771b4de7604623d65.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/4f6bc797eda34179a5218aa25675319bd8e7d6ae84fb0ecc1cddea11a98286ca.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/4fa788b2b1307b30795dae4b1d31969dfa09741dec785c572efe979533fc5935.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/4faaac766d748448a6e5597408209a4fcfe501571e86d42ddfc06162ae2fe14d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/4fbd6bf604e4b40b50dd67290570f60222dc24edbfaccab0a12acbe02f5c57fc.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/50d93bb55785d68ee154333aca52344bed08487eff986164518a6d4ab2b32dcf.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/51576d1e820b91758ae05262288114e8ac688cd156e37868f6df151263eac30b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/51588983e6f2b4b65e1cf70a58a773a7c3dc663cd3b7d1071b1f1c3fad732b44.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/52a84a56e675cf10202af3918c1a4744c426abb4ca6db78fe9c6a87452891808.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/52f589344f8edc90648df2c49b3223d90d2e66ff133166b839b290640aedddb3.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/532fd7a5eca00bb27723068d3cfaa10ec72d06be6f80e36d29d154579c4a17ca.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/534e3f9019f1b9e296d08df0912237b4984848c7ee7644b335b2abbc8dc3ed7d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/53a14e34034ac4dc22e745076a1ca0d20769e955c11ed3a2294604e827e9af62.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/53c530bba1c7dbff390ac25c3237c5327e6669c7e0a123cef633366c831acba7.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/540b0a1c7271f55b3498d0fc394f47320f62328825ddac484217f3039e93acd1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/56045ca5b344fcaed48e0d2c7a351b2a9cb9d5d9d0e96a56668f02eca07d7067.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/56b2a882abe0c541141c3202ed7ec8d49b5a19633debe9a88b896fb7a28433df.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5720a9b02efba3c6ead716c3230ef82ed47d164dccc7321db535a8d7d4c8bcc8.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/573b6d820d391839bcb20437868b3b2e4a6144076a03a2c4cec935fa4ed72e1d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5748d78e40cecf381c54b8feda760d8093a2d4439b728ecb8171bd10d03d6ab1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5a041068bd1501a4602f9075995b832dbfebe276552a108ab1b1f61331f7f4f5.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5ad2ab8e0c93420ab7666f9ace5bbbc42670a57a0ef55b9fd3263c1769cc4415.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5bdb8e4c382facf1fea4d7185a2f5f84ab9a18fb2bea024bce00bb34b3e3af9b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5c2794c46f27fc702621e47c71d7b11c2bec3fff073afdaed2903a90161a015c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5cf2b1ca14374397340ba01d64c6511628c28e82b2a5ffcc332dc8180905dcc5.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5da32272d66ff2d9a525e8a94df7b454062aa3ad017235a45811b80f9a9bc10c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5dbcf6ba957a0fc97ce82d619b4e26c014f980246554355bbae33afe88319290.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5e0c9cf5f807a33ed58175c38a654ad2faddf4120dfc6a10288dc7ce2a1fa79e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5eddbf19fe454fb5903dd77564bbcdf971c74206ba6c252f4773075e44fc79f6.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5f52fce8f3d216d8974bc29b420ae2a67a16b531d09ceb0b786ffa84b71e3a7c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/5f8cd8eb7fd3a81e6c6598a293313f87632d69848a61d0b822edf4ca9db21421.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/60a7a1713abd96ff971ab4e0397475ff26554cbf4a4b0bbdf0c4c8cae2f29a8b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/6224051065dbfbe1f971228e71245ba2767e1eb53baafdfda9caef0731227f28.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/62a49f5528e13726e447725d417cc385f846b07468c6f69791ba1646b6656da1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/635ec918920cc30ced6b8a4fd4d518aac4f8a572287b48895f6bbec8a56bdf59.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/6393f23794887706f9028df35be35c8a2eb53ae256ef206da300449dc2063809.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/63abfb74f41eddec2d1716ad43bc49ea515f63f704801c59bcbb0e01c189cdac.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/64ba864e5656e4c8633cd52e2ef11901ac2b1ac49c3afd1078ac2b32d3f5d702.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/65e405ada7cc359e92deea5750b0bff7101623a2ce45c9eeb506116830994c38.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/663357a7a57a5c5cba4705b84308882daf021f2e558d728dff365158256c8a87.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/665be26a89a30a01ea3b130237d8383773d6aca66fe396f787f3eea92b9770e9.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/66645a145722618ed892dd06dcf0f366f96f7f4916a4f331828a68f05293db7c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/67e4acbae27c56b38db6cc9a33e6375c9059d60729dbfbcfffde9f405f58beeb.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/69d3b2a19734d1662a8c375d524865d282a09aaed8f5834deb67cd3e33a6c69d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/6aebea41f96943e68465d4bf6cc0b49934a700f3fe7cbe5629538c03e12e7395.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/6b2cbfd34208f2bb260bdcf01f79a1b009fab2d971f5ab53eb1a1ae8c4afea47.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/6cae24c92c17a83388b5f210f6a3ce9cc84026539d79393b894a0171be2f7434.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/6dad04f3007c84070efbe691737a6faf0cab4fc7e209ffe928b7b8712feb989e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/6dcd641cc063234d6a8a1db17ec9c7e788c0961c505caa4d89be1bb090d11732.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7005131ba5d0e8d7606b6fbbd306e53f06c41eb6d9398d3ab26ecb3bbfdef830.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7048d1c9d52f432b3f6a97302d1cc7ae9c219b6a60b2664b9890badd4908086a.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/707876a22795257536055e7723f759ef5ae3ebbaf389b60765ad98f9346ebd9e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7087237f3d3b6720ee958ecc14b856c03048853c7ceb899bda2193a8028bc28b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/72811311407c8dd32036165662e877c1c0203239cc4a8ffcfae20d15065b4a1c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/72b9d844da43cc204ef728146762ac624437682e0cf3c1a4b10a41898cdc516b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/72ec36afab419a98d36990a2c71da3bcbf78fd507433c22cbaf84aac363a63f9.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/73d9ba98f344858cfddbb8e2b166f4845d84c0f26c4dc8798e1cecb69a12cf85.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/745593cfe3e0dc2352a219d634702dd794b4fa9d0e66ac90632c85c3870d3033.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/74920d1ff05772dfe613e5b307dbb257807ac5e1ed84fd3bf75f077676b44a81.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7564d417b936e196d36b155e3e2ca838339480b065bfd899627506592da8875e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/75bf3a400bcb32f2f701546b94d03d5f453f26d55efece118038da2a8b270547.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/75f1b50eb5adda2cc7afac00dedf972fb03b12620f18c366b6c7c3de997d29eb.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/76eb0e43c4769dac215b09cb03e50f5e66fc4b1ff7a6b52f9c3fbdfcb18059ff.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/771c914403e866691af10d4205f2c032dd871263a9a9bae79eddc0a92d51adfc.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7777df6b18f73ef9abbbedd642223cf3f3f4ddad2edbc8ce129e979b0ee92ad1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/780b6ebe5ebb2c80ef1a8d6a4c32921b21e15b92cccd6c3975561f2345e41969.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/78c000746b58a830422ded68088e2afa94c6327158868b21c5e66f67e7fe6ac6.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7903f65ee71e161a9ab518cb8dfe874358221dcc05ff992dd0a8f1bb7254e334.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/79165927d1c02027b17d27e5cf85dd4e5b0aac877caad3e8ecd3d88dafc5a6dd.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/792f8719950dc8f053dc80fd6e37bd398f580d7726460dbf69de01eb80b6ceab.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7994878a06968b2d22b474dae9e37cddee98484bc3d2d3fc161ec26e507d01ab.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/79b7eeda2faa8ec0edaeb8070015e9f8169636e3ce9bace27becdff98b402e26.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7bea52dcc7dc2f14ef194994b4c9899d39945a76d24701a2d1d81a3853fa667e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7bf9e87a1732486ea5d659bcc3aa39aebef68b01623d885ef0cc9b087bac87fd.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7cc8934d22f9895a798d42740d803d4addb4d6c2b2a75813e2df3346bfd67cca.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7d58528ce39a4c9d370208ab3731fa7ad62edb16ec7591fa48c4a02e496bcccd.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7d9d9d33a1030997bfaa569cf7d05089ad5d81f497611e84b353f906c44d650b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7ebb10bfe272fb6d7da5c0de16a1b08013202f0f699e31a87e85fed26a61b975.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7ed5adb752156cee7fbfebeb70d7513a0b69baf665dda94c06e57bae53ac095e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7f4553b724f01f4a78e15afb1e3af8961d308e16967515d0b68dd932edcaaa68.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/7f738a6dc4959f08f022f46d8df0eb0ec24b8adc445f62d5821adbf1c9cef42d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/80d52b4ffb0226ac7e80d3d3ee7c0be648dc77e67dadc1b5ccda115b001a2202.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/80d65cdd09e062b7a4fc897de3f779b92937677deda6fc636ce7ded05992b9d0.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/813fa6aab928702a0b1e6aa091e3dfae75c5b30ec2af3ca41b45559a60f41460.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/82c5e98556f58e689c5752f83f1e2f6c19eea279825a90f60e5c0b9238e64418.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/82ef228842c6e2a69523f7b4a207882b4e10f504cb18ba2671c836a6192355c9.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/84aebdc565e8dcb07e31f69b709b9bd126d022f6b19619eb1172ae6158af5eb3.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/8566aaa6aa3b814e82d9f2ff50bc157a1571c460b09ca9596a93a821de1b3d0d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/85851240d8684930d0bb98ff06d08000dd20e3b5c6cc87837de568cc5fb1a693.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/86529043ede4ada02fed142a839e574d46d471a1ea0e74ce08f521268e4b85d2.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/8701c168111c6b29dbe09d85c545ab2f4cd29b9387e03e2fdd18843af01a13bb.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/88ae7b4b085b8660af8f23e9f2570527ec3b2d3f22b2109229b6715389bb6d19.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/8acf2505a22ee84c5d96ec4aa0cfc8376d89d9e5c12aeb3a13ef1da651790d40.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/8b30fd0f1516365fceda30fba170aabaa213b5acd17af9d548b98bc767bb8e88.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/8bbe9ae53a547391c529a1dac46ab14dd9e60d8ddacc31575f3f3cb41657e20b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/8d6124677b79f2bf6fae2da4d0e896c1b3c39165cf5a51bc5cdf4778eacf138c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/8e45541c90ff32ebec63d7687a4b9f56d92449518d9593a2e2e6d2b26d46a449.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/8f25ebb18fb26c8a0360e36acde9985a1613c510263bf044afd0f4eb5e09abc2.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/914707a8679bc756c07cc50bcbbf46b33f3ae7fae8f3fdb9ff9e7154a6728d08.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/930d38ac3e9f805d6ad290522998eb8d040a54f9a8b057f13dbc6acc87374a7b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/9351b266b7d5e88731916023cca46f3cff2bcc710335bc9beacd9ffc3734a62a.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/943dfd6c954f69488161affd0b2167e86425334d1df277ec26e1a1a63f63306d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/959d0805f5559915188176593f45446fda2f34c36c13f6d123fcfe65dad795d8.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/95e880e9719dcfdec3056e4c2da7f3d1dd02981adc643830208d2e841a9e23ae.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/963799a7e3af0c927e9c65c137a3ff7b763e491b024e1aa3bf3f11d49ca94eba.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/96a32803df4d06526b2e6c1f25feb6dad7d782991e3a486226bfdfc36bef6273.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/96f19f5cf42b00e61f13c8f9ad2be7ae1a6208f1541ee7a77a2c5ffabe1630df.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/993211523de3ae9b87d48832f9359df9e0d1b150340690f5e16eddb34f1d4e42.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/9c7f370eaf8df0f34ea824d0e453c4207037729a91dd0c916b98eefdb48be054.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/9dbea3aadd0b344bd7e830fd23ec340de6c6525b1cc6d6f78a1bfdcf022a799c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/9dc8e709dd75b9894deb07d95a614ef62a66b683650fe4268a279a05a9e852c8.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/9ec291323c5981a62fd114362d88ce0756b442943cd4fad62d2360254617ed15.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a0c96b55b39556d3f32443c0a0d687c179a948f3993617d5b0ca093ddbf15fbc.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a19506c498d2be6c576d65c0e626c8958cb7834c986060f83069c7f222adab2a.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a25d9b6a0bd3045c2b89afa6f56988895095de627a6e0a6083816217cd6cbc76.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a44b1e1371d7bbe36fc646d675efb6ec9a7b4c295010dacead0be9a01d98d8a2.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a4511b5a3dc04751a754f5807f7938f6d33f1a1fd2f5dc2b83eac0522eb7f611.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a47f263eef809c34dd1175397e05134f3a473e36f1e6f72925bf6947771216fa.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a4cad2478bd972fce219a2eacc43d06df3485f28358736cf1936d5073f5c2304.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a586a2cff51d8acdd696680faea27c205a1409dfef5a73e1eb60a097c13fc23c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a63b6abf27210fab591bae945253ff8001ef1ef9911b9f1e160d2d6cdd227e88.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a6a22250aa6c4e0bc9b8cee7594a09faacfd632e0730666967229bf4aba1c9dd.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a7ca35ba1efa75f147c68eed7b3d749d5d9b59eb4183891100ff73321f4095b9.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/a90b010a361d71d459f0c0665d341704ab22956ec8483561264ffc6a97acea8c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ab51ac92189b19c5a23ae3a2061b24db2d71f0f34b958b3a01f9c4c94dbf7253.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/abf50c3fee90ca7d50526dfd35888b41d97b93205c71a11ce8444bbd40f44616.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/acb9b13a1e2ecb27a673ed558e089603487469ebb422a8079d7fcc42cd0f2b81.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/acefae518d29e4765ed1b51d19b09ae44a03fd68187c97c40417d19a1c9c1b3e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/adb3daa34f21f8040e2a62c6441740fbe7f51c7e36f3f69eeb106abea51d1e8e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/adbda5e508d1a7a66ee097ca7b45cfdbc4313b7ee8fea71494c8d338b436d31e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/adfefead2f71bbaf1668784c54f2ed6057cc817bcf9a975c5365bdd67d671753.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ae260fc074ea7979acde8eb29287f405ac60a611da32a69a5d5242546a971508.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/aeeec1ec69cdb93a049131e2bca3a822e53b81e50b6a2586ed10c66b5d916cf2.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/af295d6940772fc7382ab3295067549b480ca5ccea2cc728ca11ab18b3b540bb.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/afe836f8e06bafb827bd2c06f1bdd17817ed8801de2dd076eb6338dfa3659ad9.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b1273d3f0c153ec2c415a8269c30c16c124d44f43e83a58299c412325ecb0668.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b160b1229afda92a732380842fc29d37cb3b53e4417ac2c82ea7ad733b9fe16e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b1abc198ddf5b3d3df7642b713fa092aa34269417707279befc6bded108aea66.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b1f5626bae31eeb3912614b84a294af61dbe1c99947e9b61364c7ca097cbb502.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b2a6eb6a04c1d6a0006546f25fe39300ba6235c64f516751c0a2925f94920549.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b36b55a51cc3194b1567c668b49618a1f494a743ce7ecbcfce260c77b33f33f0.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b3dd2eebe18f20befce352b90eb7c30159d9955c5164cae61454c004e39f53ab.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b44efadb1caa764535e4ad944a4f442ced87c0b210849654e086427601aa2887.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b656d27eed61badf530c74927f3c9348feb0c39f529505d9cc368e0c94294aea.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b8bab2c03c30faa809dc46277ae43b34c8eb4a2bd2dd7d66352402b2416f06f7.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b8ea48c2d1431bb19f2c5218d5353344e9c0d937b66984970d6acb6718d07bfd.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b923c2b752ddb99d3002df260176d54ce127820b65fd544c2a7a1b44626d2079.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/b9c179cff925a31428b5a50d2572ee8c50329684792defc7625a7a3d648e546c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/bacf441770ac35e67cd34ddec028cc867904d576217d0e9008373e4509418945.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/bc335c9ab9f0848744bffbb9d3fc0afea05d78386f7fdea1514252b3804c4d25.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/be1eb8fba30ac195543bce8c77518f111e66834aa1bbd9226e191aad09af98d5.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/be2f02cd3284f7b4ee349164e851fb88dda621eb3fa34924ca75e5622db12b32.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/bead3d07bf0ad1fab0a9d532336cc61a4a4dc303d9d2b41b56ede911c37c6d9c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/c0ec68f37bc3e8611eee12a0b12c28b848a826611fc12d9287435303fdebe28c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/c245fdfdaa84239e86ad58f1d702389ccf178815bc7f5987544feda1292c1a4d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/c2b5fe1b045e88035cb056193b4ce3804402ec5aeda8d0cd36add03e73a4e50c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/c50c076c13a4506bb8226807b3b4f2c393b22d6130febf999d4c89c8d9595bd8.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/c65a85ada97ccc36c40c4fbaac23f41ecd81b6e5c265b834ff1bac98e3ca9e7d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/c73a3669f07858cc89a18c2155ff5576bbd7e43b325684919e976125fac53bc0.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/c74ea2d818b903dc626431c8bec0da7e59377ba4686ff9964e697e9822ed189a.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/c78c711d1c21f430ca5fa463852cfa2928b88bf1acbeaa4d1521c4719d332d6c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/caa5c225cfcd607d16d8ea9ed32d98f691d5ef40dedb91f755aafd9c87615af5.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/cb2600a19b216e245cfd812c00599874624a3ac49998c31a5d664e4f7fa7a75a.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/cbe013fbd4628c54c6f1fa9c341f4a733ea174f96439c6ca470e1ca946d47dce.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/cc548c80cc2d72f46a9d1c31165c4ded08e24d2728f33438b3363d2c779f18d3.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ccd7a9108d816441f2a8161f79e547aceb0d7957479157173ea41bed0192b4a4.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ce202ddf368b326d575c2815f7a6470708a4c42d0b049cf57b13278fb783390b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ce359712e2a8854e00f4491f1e02211ee9f3af1e6146da06e5cf4f478e48e050.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ce423cba4524303c865ef445929942241011594a6ac54d031e887e3cf2c98753.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/cf8262ccce1e4251277dd4138bbedabe56bbb0c1f0802ee17202f16c22271144.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d0389ec402344ef386d1ed061c53871f893ce0a2851f8557199e91c565f47950.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d16cad705babd43854c75175544a812f8d65658dbbf5ea2d1e5f60efe6b293cf.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d17e18318dc40234086815853004e75321ca805c2bb142d431660babec9f21ca.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d32c37289e563febbb5400dbdfc0becbbe6fd208858f2d395f944001dc0d33e3.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d4e0bfea8ac6fcbcbd151a5ffc22e066052565ce3e969305dc176010f3b19072.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d5dc1767dae967db3c4e2bd73fa194302b307d328768abb4db0ea9916b14d6ea.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d67493170027b7e22c521692f0a4a1142f34a1e14863b9826a7cd5db6f3b4470.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d7c99f3f52125470a218c288c5b83374fd413906e065a5c6934071148eed3121.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d8a15081215837b86a572ede1b8745992abd5d1480f59beaf3e1e5861f8d0e0c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d97c13f708a8bcd25b70bd734f51761664b2d03cefe44dd4d98cde7e6088d549.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/d9fbf990f7fe6664e73d00988a65c161b556a94f505653b3ba1f142a07cff1fe.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/da74cbf20b3c4de8571beb658262fb19f7e75612dbeecc97434e4e1271b55392.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/db78bf66d2eb84c133b596a7150aaa1ae63e619335325b9b2375589a6f118bd1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/dba8e5df20aaa9c8655dfa44a8012d4701965b4cda687eccb7c2ebcc069e8646.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/dbe7cfeae899505188cddceb9a807f1ad9cf3c4b7ed84004118c977b9a73751c.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/dcba1392cac3d6acbb74c17365865bc9cdbade69960849ca15ecd776da4307c1.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/dcdb6a9f07144c9b4d7041b7b1c80adb54df61ad11b2b298b2050eb80336bd3d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/de61f492a77aa3a411f6333ce4fcf9abda2d05bd23880fcc3759fd67d1f1fd18.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/dedefa1b14490793306c98a0ec78a295d5e42683ec5467a4bfc795ed1d13de8e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/df7d4e5f557ed523e5d8db3f0f02ae57762330558d409aa1de1ba7f2b8f43623.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/dfc1892d560ba98e0faaea731c30f0e3da0611e11994bf2602936b94fa0b01a2.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e03a12d7bc12ad974ec82f1f5d50f0c4d2efdd933c005ba894ff8d2a393a03ed.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e10f03dc8fbf994699a6be19d752127c2636b2529336248113803a4f0355f40d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e41047a257ea546d7af9d995e811a08896ed74c8f0a054e247a12c07b0b31e24.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e46915540e6b7beb2e43872f09d1517a5dcfabc74e61fafccc37085bb434ccd0.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e4937b39f80ea0d0b2f05a581ec8da2ede6da859b20037813f52450307079225.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e54c4b09d42a5783552d8b4380bd259337cca5f49d2670294500a1edd18eb341.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e56ca7c8794fad4572413d9fadc3a61bdab855f543abf08016bf4189cd83f9da.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e6128a4c880a07485acf2a16f1e14350e6fc68b0dd2c612886907cfdcf016fa9.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e6c0ffba8f581a5caa2e86c528cddd1d00872a2c02c6d93e158fc00755c20a01.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e72c251a23f600f490780c5fed73318ee3147520760741bbe6855ee7062e1bf3.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e77759d8a4bcdfcb96b79484c9eee2bacabae38223884acdf7c6adf14770aa5e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e7831e11634f3ba638adbde869eee225e66afecb8ffd39120df68d13629030aa.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e7cbcbb12626bd866d902acae5c861efc0a555bab9b3b2ad92488b952052e194.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/e8703c391e85d2f51d80bcd5b92128568b722dc8674ae2d1ad8cd5641938a295.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ed6d66cb7f807b5114db9a51be5505326a655ca2a8fc395ec5547751e353442f.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ed9d642d36c41fbec00138dcbe559a0b03bec39418cbb2bd084196e43dc35ad9.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ee2e0d0cc7dd80c6cfd16c420346ec6b5c6ebdd3853791b7a4e08cbb6e9408e4.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/eedc88bdc9147968488189ee3240e1540855925771dd7c796ccb7a3f55693c91.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ef09d581f7d364ac9c7186425fe8285cfe8f4a2dadf65618a39a159ebd0a7400.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/f080499a352712caa28f72e18bc300b7393c245bdbbecb4eb1cd6df4bd407f68.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/f10c9efa74a24680cb41c13bad8c0fb2ce3b19658175e59eec7f4682a8b86b42.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/f127f6e2edcf2e65f2402c7a2afea7e353d600ff1ef66504a54d1803cc89c66e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/f27a81cf6cf439ed847a3af5711a788b25a829121e70d8ad0ce65530eac15274.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/f56e5fc318833a363f075d61b940fe10df422ae1925f6ebc70750a9d70a70320.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/f5c736586968cf28e7f65bcee52e997a521c25bbbed5dfda5b6b7cc2ea9e0920.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/f60f6ca715ac5520990bc628b23e4dc3086b7ea54ecabac064429deee72e9fce.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/f74d6d4630558ac09f90b51248bb65e2c7345806a4da3e728ca102b940dfd6e5.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/f8c1903d4fe9e47cddabba691bc8a4b32cf3d7f7d75c8780eba69c83e2d50e13.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/fb10433a430259a944ec3e30e7cd041e153ec271ac95b0374817b5bf25d7608b.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/fbe2b1e11592f15f9d1935e069ee7502e1c2f459174ea7433908a3d5a0172b6e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/fc63f9df920ab59f2bbbbb2cdd296868381a79c03877d8da7c44c3cd834b365e.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/fc8c75e1c92392fa6bd93898d3f565b4b46e3e2632eace57cd36177ca25d688d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/fc9638d20b456cbb9af956f0d85fab0e86838416b63555f0d2bc5a76c66941f7.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/fd6e2b768e7127edc9d09b1932cc2deada605876aee068e49f8cb8ffc933f012.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/feb58f2bd6549e4fee2fa4d12dfa807582154a92f872cc249899c3d163e8e1eb.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ff5d7c172b0d2bc98d0f0bf075dd9104ed8987a819616eb349bbde41ba998f9d.json.gz`
- `results/dev_before_pinned/earlier_corner_cases/ffd386601c0ac6c04e066571911d2a2f01cb27a1957282010e1ae51c61b18aa8.json.gz`
- `results/dev_before_pinned/mul1_unseeded/post/measurements.json`
- `results/dev_before_pinned/mul1_unseeded/post/ngspice.log`
- `results/dev_before_pinned/mul1_unseeded/post/simulation.json`
- `results/dev_before_pinned/mul1_unseeded/pre/measurements.json`
- `results/dev_before_pinned/mul1_unseeded/pre/ngspice.log`
- `results/dev_before_pinned/mul1_unseeded/pre/simulation.json`
- `results/dev_before_pinned/results/adder_scaling.json`
- `results/dev_before_pinned/results/corners/summary.json`
- `results/dev_before_pinned/results/delay_diagnosis.json`
- `results/dev_before_pinned/results/full_add_load_sweep.json`
- `results/dev_before_pinned/results/pdk_parameters.json`
- `results/dev_before_pinned/results/phase4_comparison.json`
- `results/environment.json`
- `results/frozen_synth_before/results/adder_scaling.json`
- `results/frozen_synth_before/results/corners/summary.json`
- `results/frozen_synth_before/results/delay_diagnosis.json`
- `results/frozen_synth_before/results/delay_refined.json`
- `results/frozen_synth_before/results/full_add_load_sweep.json`
- `results/frozen_synth_before/results/operating_point_audit.json`
- `results/frozen_synth_before/results/pinned_requalification.json`
- `results/frozen_synth_before/results/rail_current_audit.json`
- `results/frozen_synth_before/snapshot.json`
- `results/frozen_synth_requalification.json`
- `results/full_add_load_sweep.html`
- `results/full_add_load_sweep.json`
- `results/operating_point_audit.json`
- `results/pdk_parameters.json`
- `results/phase3_assumed/adder4.postlayout.json`
- `results/phase3_assumed/adder_scaling.json`
- `results/phase3_assumed/full_add.postlayout.json`
- `results/phase3_assumed/full_add_load_sweep.json`
- `results/phase3_assumed/mac1.postlayout.json`
- `results/phase3_assumed/mul1.postlayout.json`
- `results/phase4_before_matched/adder4.postlayout.json`
- `results/phase4_before_matched/adder_scaling.json`
- `results/phase4_before_matched/full_add.postlayout.json`
- `results/phase4_before_matched/full_add_load_sweep.json`
- `results/phase4_before_matched/mac1.postlayout.json`
- `results/phase4_before_matched/mul1.postlayout.json`
- `results/phase4_before_matched/pdk_parameters.json`
- `results/phase4_before_matched/phase4_comparison.json`
- `results/phase4_comparison.json`
- `results/pinned_requalification.json`
- `results/rail_current_audit.json`
- `results/rail_margin_change.json`
- `results/sta/charge/BUF/measurements.json`
- `results/sta/charge/BUF/ngspice.log`
- `results/sta/charge/BUF/tb.spice`
- `results/sta/charge/BUF/waveforms.npz`
- `results/sta/charge/INV/measurements.json`
- `results/sta/charge/INV/ngspice.log`
- `results/sta/charge/INV/tb.spice`
- `results/sta/charge/INV/waveforms.npz`
- `results/sta/charge/NAND/measurements.json`
- `results/sta/charge/NAND/ngspice.log`
- `results/sta/charge/NAND/tb.spice`
- `results/sta/charge/NAND/waveforms.npz`
- `results/sta/charge/NANY/measurements.json`
- `results/sta/charge/NANY/ngspice.log`
- `results/sta/charge/NANY/tb.spice`
- `results/sta/charge/NANY/waveforms.npz`
- `results/sta/charge/NOR/measurements.json`
- `results/sta/charge/NOR/ngspice.log`
- `results/sta/charge/NOR/tb.spice`
- `results/sta/charge/NOR/waveforms.npz`
- `results/sta/diagnosis/adder2/measurements.json`
- `results/sta/diagnosis/adder2/ngspice.log`
- `results/sta/diagnosis/adder2/outlier.json`
- `results/sta/diagnosis/adder2/simulation.json`
- `results/sta/diagnosis/adder2/tb.spice`
- `results/sta/diagnosis/adder2/waveforms.npz`
- `results/sta/diagnosis/adder6/measurements.json`
- `results/sta/diagnosis/adder6/ngspice.log`
- `results/sta/diagnosis/adder6/simulation.json`
- `results/sta/diagnosis/adder6/tb.spice`
- `results/sta/diagnosis/adder6/waveforms.npz`
- `results/sta/diagnosis/full_add/measurements.json`
- `results/sta/diagnosis/full_add/ngspice.log`
- `results/sta/diagnosis/full_add/simulation.json`
- `results/sta/diagnosis/full_add/tb.spice`
- `results/sta/diagnosis/full_add/waveforms.npz`
- `results/sta/diagnosis/phase1_audit.json`
- `results/sta/diagnosis/phase3_audit.json`
- `results/sta/example_adder4.tested.timing.json`
- `results/sta/example_adder4.timing.json`
- `results/sta/example_full_add.tested.timing.json`
- `results/sta/example_full_add.timing.json`
- `results/sta/example_mac1.tested.timing.json`
- `results/sta/example_mac1.timing.json`
- `results/sta/example_mul1.tested.timing.json`
- `results/sta/example_mul1.timing.json`
- `results/sta/pessimism.html`
- `results/sta/phase1/example_adder4.tested.timing.json`
- `results/sta/phase1/example_adder4.timing.json`
- `results/sta/phase1/example_full_add.tested.timing.json`
- `results/sta/phase1/example_full_add.timing.json`
- `results/sta/phase1/example_mac1.tested.timing.json`
- `results/sta/phase1/example_mac1.timing.json`
- `results/sta/phase1/example_mul1.tested.timing.json`
- `results/sta/phase1/example_mul1.timing.json`
- `results/sta/phase1/scaling_adder1.tested.timing.json`
- `results/sta/phase1/scaling_adder1.timing.json`
- `results/sta/phase1/scaling_adder2.tested.timing.json`
- `results/sta/phase1/scaling_adder2.timing.json`
- `results/sta/phase1/scaling_adder3.tested.timing.json`
- `results/sta/phase1/scaling_adder3.timing.json`
- `results/sta/phase1/scaling_adder4.tested.timing.json`
- `results/sta/phase1/scaling_adder4.timing.json`
- `results/sta/phase1/scaling_adder5.tested.timing.json`
- `results/sta/phase1/scaling_adder5.timing.json`
- `results/sta/phase1/scaling_adder6.tested.timing.json`
- `results/sta/phase1/scaling_adder6.timing.json`
- `results/sta/phase1/validation.json`
- `results/sta/phase2/example_adder4.tested.timing.json`
- `results/sta/phase2/example_adder4.timing.json`
- `results/sta/phase2/example_full_add.tested.timing.json`
- `results/sta/phase2/example_full_add.timing.json`
- `results/sta/phase2/example_mac1.tested.timing.json`
- `results/sta/phase2/example_mac1.timing.json`
- `results/sta/phase2/example_mul1.tested.timing.json`
- `results/sta/phase2/example_mul1.timing.json`
- `results/sta/phase2/scaling_adder1.tested.timing.json`
- `results/sta/phase2/scaling_adder1.timing.json`
- `results/sta/phase2/scaling_adder2.tested.timing.json`
- `results/sta/phase2/scaling_adder2.timing.json`
- `results/sta/phase2/scaling_adder3.tested.timing.json`
- `results/sta/phase2/scaling_adder3.timing.json`
- `results/sta/phase2/scaling_adder4.tested.timing.json`
- `results/sta/phase2/scaling_adder4.timing.json`
- `results/sta/phase2/scaling_adder5.tested.timing.json`
- `results/sta/phase2/scaling_adder5.timing.json`
- `results/sta/phase2/scaling_adder6.tested.timing.json`
- `results/sta/phase2/scaling_adder6.timing.json`
- `results/sta/phase2/validation.html`
- `results/sta/phase2/validation.json`
- `results/sta/phase3/example_adder4.tested.timing.json`
- `results/sta/phase3/example_adder4.timing.json`
- `results/sta/phase3/example_full_add.tested.timing.json`
- `results/sta/phase3/example_full_add.timing.json`
- `results/sta/phase3/example_mac1.tested.timing.json`
- `results/sta/phase3/example_mac1.timing.json`
- `results/sta/phase3/example_mul1.tested.timing.json`
- `results/sta/phase3/example_mul1.timing.json`
- `results/sta/phase3/pessimism.html`
- `results/sta/phase3/propagation_tables/BUF.propagation.json`
- `results/sta/phase3/propagation_tables/INV.propagation.json`
- `results/sta/phase3/propagation_tables/NAND.propagation.json`
- `results/sta/phase3/propagation_tables/NANY.propagation.json`
- `results/sta/phase3/propagation_tables/NOR.propagation.json`
- `results/sta/phase3/scaling_adder1.tested.timing.json`
- `results/sta/phase3/scaling_adder1.timing.json`
- `results/sta/phase3/scaling_adder2.tested.timing.json`
- `results/sta/phase3/scaling_adder2.timing.json`
- `results/sta/phase3/scaling_adder3.tested.timing.json`
- `results/sta/phase3/scaling_adder3.timing.json`
- `results/sta/phase3/scaling_adder4.tested.timing.json`
- `results/sta/phase3/scaling_adder4.timing.json`
- `results/sta/phase3/scaling_adder5.tested.timing.json`
- `results/sta/phase3/scaling_adder5.timing.json`
- `results/sta/phase3/scaling_adder6.tested.timing.json`
- `results/sta/phase3/scaling_adder6.timing.json`
- `results/sta/phase3/validation.html`
- `results/sta/phase3/validation.json`
- `results/sta/phase3_tests.log`
- `results/sta/phase3_validation.log`
- `results/sta/phase4/attribute.py`
- `results/sta/phase4/attribution.json`
- `results/sta/phase4/attribution.log`
- `results/sta/phase4/audit.json`
- `results/sta/phase4/audit.log`
- `results/sta/phase4/audit.py`
- `results/sta/phase4/bin_convergence.json`
- `results/sta/phase4/exact_witness.log`
- `results/sta/phase4/exact_witness.py`
- `results/sta/phase4/exact_witness/measurements.json`
- `results/sta/phase4/exact_witness/ngspice.log`
- `results/sta/phase4/exact_witness/tb.spice`
- `results/sta/phase4/exact_witness/waveforms.npz`
- `results/sta/phase4/extend.py`
- `results/sta/phase4/extension.json`
- `results/sta/phase4/extension.log`
- `results/sta/phase4/neighbors.json`
- `results/sta/phase4/tests.log`
- `results/sta/phase4/tightening.html`
- `results/sta/phase4/validation.log`
- `results/sta/phase4/windows.json`
- `results/sta/phase4/windows.log`
- `results/sta/phase4/windows.py`
- `results/sta/phase4/witnesses.json`
- `results/sta/phase4/witnesses.log`
- `results/sta/phase4/witnesses.py`
- `results/sta/phase4/witnesses/adder2/measurements.json`
- `results/sta/phase4/witnesses/adder2/ngspice.log`
- `results/sta/phase4/witnesses/adder2/tb.spice`
- `results/sta/phase4/witnesses/adder2/waveforms.npz`
- `results/sta/phase4/witnesses/adder6/measurements.json`
- `results/sta/phase4/witnesses/adder6/ngspice.log`
- `results/sta/phase4/witnesses/adder6/tb.spice`
- `results/sta/phase4/witnesses/adder6/waveforms.npz`
- `results/sta/resolution/comparison.json`
- `results/sta/resolution/runs/INV/r1e-09_c1e-13/measurements.json`
- `results/sta/resolution/runs/INV/r1e-09_c1e-13/ngspice.log`
- `results/sta/resolution/runs/INV/r1e-09_c1e-13/tb.spice`
- `results/sta/resolution/runs/INV/r1e-09_c1e-13/waveforms.npz`
- `results/sta/resolution/runs/NANY/r1e-09_c1e-13/measurements.json`
- `results/sta/resolution/runs/NANY/r1e-09_c1e-13/ngspice.log`
- `results/sta/resolution/runs/NANY/r1e-09_c1e-13/tb.spice`
- `results/sta/resolution/runs/NANY/r1e-09_c1e-13/waveforms.npz`
- `results/sta/review3_full_tests.log`
- `results/sta/scaling_adder1.tested.timing.json`
- `results/sta/scaling_adder1.timing.json`
- `results/sta/scaling_adder2.tested.timing.json`
- `results/sta/scaling_adder2.timing.json`
- `results/sta/scaling_adder3.tested.timing.json`
- `results/sta/scaling_adder3.timing.json`
- `results/sta/scaling_adder4.tested.timing.json`
- `results/sta/scaling_adder4.timing.json`
- `results/sta/scaling_adder5.tested.timing.json`
- `results/sta/scaling_adder5.timing.json`
- `results/sta/scaling_adder6.tested.timing.json`
- `results/sta/scaling_adder6.timing.json`
- `results/sta/validation.html`
- `results/sta/validation.json`

</details>

### Additional removal (1 file)

Tests of removed v1 presentation tables, figure controls and evidence display helpers; v3 uses the shared live/views/style modules instead.

- `notebook/tests/test_presentation.py`

## Retained-file cleanup

- `notebook/v3/make_notebook.py`: only the helper search path and its explanatory comment changed (`HERE` instead of the removed v2 directory). No cells, translations or narrative behavior changed.
- `notebook/export_schematics.py`: retain the SVG-theme helper used by the moved v3 exporters; remove the obsolete full/dark-gallery batch exporter, its manifest producer and CLI.
- `notebook/presentation.py`: retain only the cache progress-label adapter; remove the old narrative localization, paper figures, downloads, evidence tables and Plotly display layer. The hashed `cache.py` bytes remain unchanged.
- `notebook/validate_notebook.py` and `qualify_notebook.py`: target the two v3 editions and chapters 1–6; remove the v1-only patched-Colab adapter. Docker/CI still call the same qualifier path, which now executes both languages.
- Notebook tests: replace v1 document checks with both-language reproducibility and asset checks; keep runtime compatibility, source-pin identity, cache invalidation, pinned setup, cell qualification and sizing checks. Remove only the v1-specific portions of the runtime/publication tests. Replace obsolete gallery tests with compact-source/native-symbol checks.
- `tests/viz/test_layout_viewer.py`: migrate its obsolete method-cell check to both v3 layout viewers. All other library tests and every library implementation stay intact.
- Submission SVG packaging test now consumes the compact INV SVG used by v3. Remove the builder's allowlist exception for the obsolete v1 payload filename. The saved submission payload is untouched; its two stale-source failures are expected by the brief.
- Root, notebook and figure guides now describe v3. Figure regeneration retains only the two notebook figures, including their original asset names; runtime/dependency guide invokes the v3 builder.

### Unreferenced retired briefs/status notes (5 files)

- `briefs/EDITOR.md`: Retired v1 editorial brief; its narrative sources and integration path were removed, and no retained file references this brief.
- `briefs/FIGSYNTH.md`: Retired single-figure brief for the removed half/full-adder hero; no retained file references this brief.
- `briefs/REWRITE_JA.md`: Retired v1 rewrite brief; v3 has its own binding brief/storyboards and no retained file references this brief.
- `docs/status/COLABDIAG.md`: Unreferenced failed v1 Colab diagnosis; not a v3 runtime or qualification record.
- `docs/status/colab/round13.md`: Unreferenced v1 Colab run record formerly read only by the removed v1 verification publisher.

## Completed dependency set

The audit (`build/cleanup/dependencies.json`, ignored working evidence) resolves 152 local Python files from the v3 runtime/build roots, the preserved public library and submission roots, including imports inside generated/string-valued code cells. It checks 12 pinned Markdown image assets and 276 explicitly named source/evidence paths in the scaling and shuttle publications.

Shared notebook import closure: `cache.py`, `cell_views.py`, `completeness.py`, `export_schematics.py`, `font_runtime.py`, `inverter_views.py`, `live.py`, `localization.py`, `native_runtime.py`, `pnr_views.py`, `predictions.py`, `presentation.py`, `reuse.py`, `runtime_support.py`, `scale_views.py`, `setup_colab.py`, `style.py`, `views.py`.

Additional path-read dependencies (retained):

- Both `notebook/v3/tritflow_{en,ja}.ipynb`, the builder, bilingual narratives, `setup_cell.py`, `make_tables.py`, `compact_schematics.py`, `make_figures.py`, v3 assets and language tests.
- `notebook/colab_setup.sh`, setup/runtime/native/font helpers; `setup_pins.json`; Python/Ubuntu/ngspice/font locks, requirement inputs, runtime compatibility record, installer and lock-refresh CLI; Docker and qualification/validation commands still used by CI.
- `cells/template*.json`, `cells/source/` and all of `cells/out/`, including cell-level GDS/SPICE/extraction/abstracts, truth/DC/characterization/timing, qualification/manifests and sizing grids; their code and native evidence remain intact.
- `results/sta/propagation/` tables and their raw characterization; `results/dot_scaling.json` and all dot-scaling companion evidence, archived producer and native provenance reports. The existing readers and their hashes are preserved.
- `notebook/assets/schematics/{INV,NAND,NOR,NANY}.compact.svg`, all five editable `.sch` sources and `verify_compact.py`; eight table SVGs; the two v3 opening/flow figure families and their producers/style. The English flow-map SVG/PNG remain under `notebook/v3/assets/`.
- The complete `notebook/assets/chip/dot4/` publication: HDL/netlist, drawing/mask GDS, reference CIR, preview, signoff/pad/provenance reports, evidence archive, build/verify scripts and checked original reuse producer.
- All public `tritflow/` implementations and their `tests/`, the cell-generation CLI and supporting examples; submission capture, result extraction, static export, templates, identity/rules snapshots, tests and saved payload. Runtime external inputs are the pinned PDK and native tools, not any developer reference checkout; regeneration/equivalence tests explicitly read the permitted reference checkout.

Library documentation was also corrected where it described deleted archives as current bundled results or instructed execution of deleted phase-audit scripts. No library Python implementation, cell artifact, or runtime pin changed.

## Reference-audit interpretation

`git grep -n -I -F -f build/cleanup/removed-paths.txt -- README.md notebook submission figures ':!submission/ISSCC27'` returns status 1 with no matches. Thus the current landing page, notebook code/assets/tests/guides, figure producers and submission tooling contain no removed-path references.

A literal zero-match full-tree grep conflicts with the brief's required deletion ledger and preservation of `docs/notebook-v2/STORYBOARD.md`, which itself names removed historical files. The full-tree grep has 154 remaining lines: retained binding/historical briefs/status notes, public library producer destinations and optional historical-reader defaults, and synthetic STA fixture paths. These are classified in `build/cleanup/git-grep-all.log`; none is an input read by the v3 run. The library APIs and their defaults stay intact as required. Their guides now state that older adder/diagnostic records must be produced before those optional readers are called. No missing input has been replaced with a fabricated result or a bypass of freshness checks.

The preserved `cache.py` still contains optional `COMPUTING_MODULES` basenames for the old campaign/experiment/routing helpers. Each is guarded by `is_file()` and is absent from the explicit dot-product source set. They are inert optional manifest entries, not imports or failed reads. Removing those names would change a hash-qualified producer input; preserving the exact source was the reasonable choice.

No additional Python packages were installed.

## Verification details

- Both standard builds passed: `python3 notebook/v3/make_notebook.py --lang ja` and `--lang en`.
- Both structural validators passed: 64 total cells, chapters 1–6.
- `NGSPICE_BINARY=~/.local/opt/tritflow-ubuntu-24.04/bin/ngspice TR1UM_PDK=~/pdk/TR-1um-pinned python3 notebook/qualify_notebook.py --output build/cleanup/execution` passed both fresh local kernels, all 31 code cells each: EN 50.8 s, JA 54.8 s. The dot4 transient was 18.6 s / 20.0 s and all intervals reached the ±0.5 V band. Reports and saved outputs are under `build/cleanup/execution/{en,ja}/`.
- `python3 -m pytest notebook/v3/test_language.py -q`: 45 passed in 0.36 s. Run this suite separately from `tests/hdl/test_language.py`, since their basenames collide with pytest's default import mode.
- `python3 -m pytest notebook/tests tests/viz/test_layout_viewer.py -q`: 42 passed in 6.05 s on the final edited sources.
- `python3 -m pytest submission/tests -q`: 19 passed, exactly the two expected stale-payload failures. Both failures are `source notebook changed since capture: tritflow_ja.ipynb`, in `test_actual_payload_has_readable_evidence_and_exact_bilingual_manifests` and `test_final_check_refuses_a_preview_without_changing_payload`. Keep these fail-closed checks; do not change the old capture's hashes. Saved submission bytes remain untouched.
- `TR1UM_PDK=~/pdk/TR-1um-pinned python3 notebook/assets/schematics/verify_compact.py --out build/cleanup/schematic-verification`: INV/NAND/NOR/NANY passed ordered-terminal/net-bijection and embedded-symbol checks (4/6/6/10 devices).
- The initial broad run collected the viewer's old v1 test before its migration, so it finished with 928 passed, 2 skipped and that single obsolete-path failure (`build/cleanup/pytest-preflight.log`). The corrected viewer test passed, and the subsequent full stable-source run passed as recorded below.
- `git diff --check` passed. Every missing tracked file is in this removal/move ledger. All cell files, library Python, setup pins, protected narratives and parallel view modules match baseline hashes.

Local execution conditions printed by both setup cells: Python 3.12.3, native KLayout 0.30.9, ngspice-42, NumPy 2.4.3, SciPy 1.17.1, Matplotlib 3.10.8, Plotly 7.1.0, and the pinned public PDK. These are local working-tree checks, not a new Colab or pinned-Docker qualification. Both generated notebooks name local base commit `b8f4f660b69b44227b4ded188ee5e86a360c26a2`; publishing the integrated source and replacing that pin remains the integrator's release step.

The executed native reports were checked independently (`build/cleanup/physical-checks.json`): first/dot4 drawing DRC reports have no items and both LVS logs report a match in both languages. Both edited-HDL summaries and their electrical measurement JSON pass.

## Final full regression and handoff

The final stable-source run passed:

```sh
NGSPICE_BINARY=/home/ishi-kai/.local/opt/tritflow-ubuntu-24.04/bin/ngspice \
TR1UM_PDK=/home/ishi-kai/pdk/TR-1um-pinned \
python3 -m pytest tests notebook/tests -q --basetemp=build/cleanup/pytest-final-temp
# 924 passed, 2 skipped in 624.73s (0:10:24)
```

Full logs: `build/cleanup/pytest.log`, `language-tests.log`, `notebook-final-tests.log`, `submission-tests.log`, `execution.log`, and `schematic-verification.log`. Final audit data: `dependencies.json`, `baseline.json`, `removals.json`, `moves.json`, `physical-checks.json`, and the scoped/full-tree grep logs in the same ignored directory. The deletion ledger above is the durable record of every removed tracked file and its reason.

Final working-tree shape: 1,049 removals, 3 moves (old locations appear as deletions until staging), 24 modified retained files, and the new CLEANUP status file. The three new helper files must be included when the integrator stages the cleanup: `notebook/v3/setup_cell.py`, `notebook/v3/make_tables.py`, `notebook/v3/compact_schematics.py`. Both source notebooks were regenerated; their six changed lines each are source-pin/asset-URL stamps. The v3 builder diff is only its helper path/comment. All protected parallel narratives/views, library Python, published cells, runtime pins, license/NOTICE and saved submission payload retain baseline bytes.

No remaining CLEANUP work or interface change is required. The release handoff is to merge the parallel work, publish a compatible source commit, rebuild both notebook source pins and regenerate the saved submission payload; do not relabel the old payload as current. No commit or push was made.
