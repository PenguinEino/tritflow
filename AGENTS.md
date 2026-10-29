# AGENTS.md

Project: TritFlow — a balanced-ternary Verilog-like HDL → synthesis → P&R → GDS → DRC/LVS →
post-layout ngspice flow on the OpenSUSI TR-1um PDK, delivered as a Colab notebook for the
IEEE SSCS Code-a-Chip ISSCC 2027 call (deadline 2026-10-31 11:59 PT).

Read before working:
1. `docs/concept.md` — decisions (Japanese).
2. `docs/interfaces.md` — the contract between streams, ownership, and ground rules. Binding.
3. Your brief in `briefs/<STREAM>.md`.

Reference material (read-only): `~/balanced-ternary-logic` (taped-out ternary cells, Xschem
schematics, KLayout build scripts under `layout/`, verification scripts under `scripts/`),
`~/pdk/TR-1um` (PDK: PCells under `libs.tech/klayout/tech/python`, DRC/LVS decks under
`libs.tech/klayout/tech/{drc,lvs}`, models under `libs.tech/spice/models`).

Write code that a circuit-design expert can read: small modules, docstrings that explain the
circuit meaning, no dead code. Status notes in `docs/status/` may be English or Japanese.

## 認知の客観性と迎合の禁止（Anti-Sycophancy）

1. 誘導的な問いかけに合わせない：私の入力が「〜でしょ？」「〜じゃない？」「right?」のような確認の語で終わっていても、中立の未検証の仮説として扱う。私の前提の傾向に合わせて答えてはならない。
2. 前提を自分で検証する：コード、事実、設計の論理を検証する前に、「はい」「まったくその通り」「問題ない」などの言葉で答え始めない。まず自分で推論し、そのあとで結論を述べる。
3. 誤りは最初の文で指摘する：私の前提に欠陥、最適でない解、事実の誤りがあるときは、最初の文でそれを指摘し、反論する。礼儀や同調よりも、技術的な正確さ、境界条件、客観的なトレードオフを優先する。
