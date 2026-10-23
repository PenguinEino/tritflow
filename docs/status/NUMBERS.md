# NUMBERS — numeric and result-claim audit

Completed 2026-10-24 (JST), against checkout `88cbd26c2bb22059cf9f75e8b5f5bd8e9fa3ba06` and the files present during this audit. Report only; no source, notebook, result, or chip artifact was edited. No commit or push.

## Scope and decisions

Read `AGENTS.md`, `docs/concept.md`, `docs/interfaces.md`, `briefs/NUMBERS.md`, every Japanese and English v3 narrative, all code cells in `notebook/v3/make_notebook.py`, the root README, and the three requested submission templates. Compared their quantities and result claims with both executed notebooks, `results/dot_scaling.json` and its archived native measurements, cell sizing/characterization and timing tables, the computation code, and the current dot4 chip README/signoff/pad map/GDS/evidence archive. Checked the two editions against each other, including generated tables. The reference catalogue and primary external sources supplied the historical/date checks.

The current chip publication takes precedence over the older captured shuttle cell. A published delivery estimate is treated as an estimate; no newer dated project-specific delivery confirmation was found in the audited sources. Approximate prose values are compared at their stated precision. Timing comparisons retain their own stimulus sequences; results from different sequences are not substituted for each other. Runtime differences between separate language executions are not translation errors.

Checked-and-consistent displayed numeric occurrences: **588**. This count covers numeric tokens in the quantitative synthesis/scaling, power, wire-penalty, INV-delay and divider-comparison table bodies, once per edition; narrative repetitions are not counted again. Other checked prose, formula, unit and coverage claims are reported below only when they disagree with their sources. No style suggestions are included.

## Mismatches

### NUM-01 — delivery month and the resulting measurement promise

Locations:

- `notebook/v3/narrative/00_opening.md:10`
- `notebook/v3/narrative_en/00_opening.md:14`
- Captured copies: `notebook/v3/tritflow_ja_output.ipynb:17` and `notebook/v3/tritflow_en_output.ipynb:21`.

Stated: chips will arrive in **January 2027**, followed by an unconditional promise of first measurements at the February ISSCC if selected.

Source value: the shuttle operator's [2026-10-16 announcement](https://prtimes.jp/main/html/rd/p/000000014.000182004.html), under “OpenSUSI-MPW に関して,” estimates delivery **around February 2027**. That does not establish that measurements will be available before ISSCC. The same discrepancy was already recorded in `docs/references.md:321` and `docs/status/REFS.md:43`.

Exact replacement for the two affected Japanese sentences:

> OpenSUSIの2026年10月16日の発表では、チップの到着は2027年2月頃の予定である。採択されれば、2月のISSCCでTritFlowを発表し、実測が間に合えば元になったセルの最初の実測結果も報告する。

Exact English replacement:

> OpenSUSI's announcement of October 16, 2026 estimates chip delivery around February 2027. If selected, the author will present TritFlow at ISSCC in February and report the first measurements of its underlying cells if they are available in time.

### NUM-02 — router retry limit

Locations:

- `notebook/v3/narrative/04_pnr.md:17`
- `notebook/v3/narrative_en/04_pnr.md:17`
- Captured copies: `notebook/v3/tritflow_ja_output.ipynb:3330` and `notebook/v3/tritflow_en_output.ipynb:3340`.

Stated: rerouting happens “最大3回” / “up to 3 times.”

Source value: the notebook calls `dot4.place_and_route(..., seed=0)` without overriding the retry settings (`notebook/v3/make_notebook.py:220`). The public flow defaults to `ripup_passes=8` and `max_expansions=5` (`tritflow/pnr/flow.py:94`). It explicitly passes the former into `route` (`tritflow/pnr/flow.py:190`). The router's `range(ripup_passes)` includes the initial attempt (`tritflow/pnr/router.py:337`): **8 attempts, hence at most 7 reroutes per floorplan**, followed on failure by channel/corridor expansion, up to **5 expansions**. The router helper's standalone default of 3 is not the notebook's setting.

Exact replacement for the Japanese sentence beginning “端子が多く”:

> 端子が多く広がりの大きいネットから順に引き、引けないネットが出たら、すべての配線を外し、そのネットを先頭にして残りの順を入れ替えてやり直す。同じフロアプランでは初回を含め最大8回試し、それでも引けなければ配線チャネルと外周の通り道を広げる。拡張は最大5回である。

Exact replacement for the English sentences beginning “Nets with more terminals” and “If a net fails”:

> Nets with more terminals and greater extent are routed first. If a net fails, all routing is removed, the failed net is moved to the front, and the remaining order is changed before retrying. Each floorplan permits up to 8 attempts including the first. If routing still fails, the channels and outer routing corridors are widened, with up to 5 expansions.

### NUM-03 — placement probabilities are conditional

Locations:

- `notebook/v3/narrative/04_pnr.md:11`
- `notebook/v3/narrative_en/04_pnr.md:11`
- Captured copies: `notebook/v3/tritflow_ja_output.ipynb:3324` and `notebook/v3/tritflow_en_output.ipynb:3334`.

Stated: every trial chooses swap/move/mirror with probabilities **60% / 30% / 10%**, without qualifying operation availability.

Source value: `tritflow/pnr/placement.py:170` uses thresholds 0.6 and 0.9 **with guards and fall-through**. A swap requires a nonempty destination row; a move to another row requires more than one cell in the source row. For example, for a singleton source row and a different nonempty destination row, the actual probabilities are **60% / 0% / 40%**. The stated percentages apply when the relevant operations are available.

Exact replacement for the Japanese sentence beginning “1回の試行では”:

> 1回の試行では、一様乱数 r が0.6未満で交換先の行が空でなければ2つのセルを入れ替える。それ以外では、r が0.9未満で移動が可能なら1つのセルを移し、残りは左右反転する。60%・30%・10%は、交換と移動がともに可能な場合の選択確率である。

Exact replacement for the English sentence beginning “Each trial”:

> Each trial draws a uniform random number r. It swaps two cells when r < 0.6 and the destination row is nonempty; otherwise, it moves a cell when r < 0.9 and the move is allowed, and mirrors the cell in the remaining cases. The 60% / 30% / 10% probabilities apply when both swap and move are available.

### NUM-04 — captured chapter 6.5 still describes custom probe pads

Locations: `notebook/v3/tritflow_ja_output.ipynb:4725` and `notebook/v3/tritflow_en_output.ipynb:4735`, markdown cell `cells[61]`.

Stated: “プローブ用パッド” / “probe pads,” with a custom probe-pad arrangement requiring approval of that arrangement and ESD provisions.

Source value: `notebook/assets/chip/dot4/signoff.json:19` records the **unmodified stock OSS_FRAME with 16 pads**; its ESD supply arrangement is recorded at lines 23–25. `notebook/assets/chip/dot4/README.md:3` and `:6` describe the same frame and supply connections. The current source narratives at `notebook/v3/narrative/06_results.md:49` and `notebook/v3/narrative_en/06_results.md:49` have already been updated; the executed copies have not.

Exact Japanese replacement for the captured paragraph (the current narrative text):

> dot4に、パッド、電源配線、PDKの標準MPWフレームを付けた最上位レイアウトを示す。これは3〜5章で扱った重みを入力に持つdot4であり、6.4の定数重みの回路とは別である。フレームのESD（静電気放電）保護の電源は、VSSを回路のVSS（−5 V）と共通にし、VDDには別の端子から+5 Vを与える。これで−5〜+5 Vの3値の信号がESD保護の電源の範囲に収まり、標準のパッドをそのまま使える。テープアウトしたチップも同じ接続である。提出には、シャトル運営者による2500 µm角の領域の割り当てとボンディング図の合意を必要とする。

Exact English replacement:

> The top-level layout adds pads, power routing and the PDK's stock MPW frame to dot4. It is the circuit with weight inputs used in chapters 3–5, distinct from the fixed-weight circuit in section 6.4. The frame's electrostatic discharge (ESD) supply shares VSS with the circuit's VSS (−5 V) and takes VDD at +5 V from a separate terminal. The −5 to +5 V ternary signals then stay within the ESD supply range, so the stock pads are used as they are. The taped-out chip uses the same connection. Submission requires the shuttle operator to allocate a 2500 µm square slot and agree on the bond diagram.

### NUM-05 — captured pad count, assignments, coordinates and GDS are obsolete

Locations:

- Pad table: `notebook/v3/tritflow_ja_output.ipynb:5016`, `notebook/v3/tritflow_en_output.ipynb:5026`; `cells[62].outputs[2]`.
- Embedded GDS download: `notebook/v3/tritflow_ja_output.ipynb:4745`, `notebook/v3/tritflow_en_output.ipynb:4755`; `cells[62].outputs[0]`.

Stated: a **17-pad** top, with P01–P03 as VDD, P04–P06 as VSS, P07 as VMID, P08–P15 as inputs, and P16/P17 as outputs. The table uses the old custom-pad coordinates. The embedded download is also the old layout, SHA-256 `3eebb7d03dcb7cd82817662b40d2b4f4055fb7fd6742b3f00e5017c6938ae7d4` in both editions.

Source value: `notebook/assets/chip/dot4/pad_map.json:1`, also duplicated identically in `notebook/assets/chip/dot4/signoff.json:80`, contains **16 pads**: 8 inputs, 2 outputs, 3 core VDD, 1 VMID, 1 common VSS and 1 separate ESD_VDD. The current GDS hashes to `6d2453708f58a442dbf151d4afe6bb77d4c9f3e1b813807a781c6068a592f6dd`, matching `notebook/assets/chip/dot4/signoff.json:1221`.

Exact replacement table body for both editions (retain their localized headings):

| Pad | Net | Direction | X (µm) | Y (µm) |
|---|---|---|---:|---:|
| P01 | VDD | power | -200.0 | 1040.0 |
| P02 | VDD | power | -600.0 | 1040.0 |
| P03 | x1 | input | -1040.0 | 600.0 |
| P04 | x0 | input | -1040.0 | 200.0 |
| P05 | w3 | input | -1040.0 | -200.0 |
| P06 | w2 | input | -1040.0 | -600.0 |
| P07 | w0 | input | -600.0 | -1040.0 |
| P08 | VSS | power | -200.0 | -1040.0 |
| P09 | x3 | input | 200.0 | -1040.0 |
| P10 | w1 | input | 600.0 | -1040.0 |
| P11 | y[1] | output | 1040.0 | -600.0 |
| P12 | y[0] | output | 1040.0 | -200.0 |
| P13 | VMID | power | 1040.0 | 200.0 |
| P14 | x2 | input | 1040.0 | 600.0 |
| P15 | VDD | power | 600.0 | 1040.0 |
| P16 | ESD_VDD | power | 200.0 | 1040.0 |

The GDS replacement is an artifact replacement, not a text substitution: regenerate the entire shuttle output from the current `notebook/assets/chip/dot4/tr_1um_dot4.gds`, signoff and pad map. Keep download name `tr_1um_dot4.gds`; replace its embedded bytes with the file having the current hash above, and regenerate the corresponding viewer image. `notebook/reuse.py:286` already reads and checks these current artifacts. Editing only the pad labels would leave a contradictory downloadable layout.

### NUM-06 — captured remaining-approval reason is obsolete

Locations: `notebook/v3/tritflow_ja_output.ipynb:5028` and `notebook/v3/tritflow_en_output.ipynb:5038`; `cells[62].outputs[3]`.

Stated, verbatim in both editions:

> Custom TEG pad/bond allocation and ESD/power/package approval still required

Source value: the current `notebook/assets/chip/dot4/signoff.json:1220` records slot allocation, final bonding and final CI as the remaining steps. `notebook/reuse.py:309` displays this field directly.

Exact replacement text, matching the current recorded field:

> Organizer allocation of a full 2500 um slot, final bond diagram and final CI remain

## Validation and handoff

Completed the comparisons using read-only Python/JSON/HTML parsing and source inspection. Re-synthesized the notebook's HDL examples in memory; checked their equivalence results and cell counts, independently enumerated the completeness closure, recomputed scaling area/power/percentage arithmetic, compared published timing and measurement data with the compressed native records, and decoded both embedded chip downloads to verify their hashes. Confirmed that the chip pad-map copies agree and the current GDS matches its signoff hash. No native flow, notebook execution, or Colab VM was launched for this report. No packages were installed.

No pytest area belongs to this report-only stream. Validation of the deliverable is `git diff --check -- docs/status/NUMBERS.md`, plus direct whitespace and source-location checks for this new file. Recheck recorded line numbers if another stream regenerates the notebooks.

Done: audit and exact replacement handoff. In progress: none. Blockers: none. Interface requests: none. Narrative/notebook owners apply the corrections and recapture the affected outputs; NUMBERS has left those files untouched as required.
