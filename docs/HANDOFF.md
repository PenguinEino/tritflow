# 引き継ぎメモ（2026-10-18、Mac上のClaude Codeから）

Code-a-Chip ISSCC 2027（締切 2026-10-31 11:59 AM PT）への応募準備。
決定事項はすべて `docs/concept.md` にある。まずそれを読むこと。

## これまでの流れ

1. 既存の4設計（平衡三値論理、ISHI VGA、SRAM512、Penguin inverter）とCode-a-Chipの募集・過去採択・審査者の傾向を調査。
2. 主題を「OpenSUSI TR-1umで、三値論理のHDLからGDSまでを通すパイプライン」に決定。募集窓口の方針確認でも、方向性は合致、GDSまで出せる点を強くアピールすべきと確認した。
3. Notebook構成、HDL（Verilog風・組合せ回路のみ）、スタセル（INV・NAND・NOR・NANY＋TIE3種＋FILL、レールは上からVDD／本体／VMID・VSS）、合成、P&R（行とチャネルを交互）、抽出・SPICE、特性評価、可視化、Colab環境を決定。

## ユーザーの好み

- 読者は専門家。教育目的でも、GDS・SPICEなどの低レイヤーの本物の成果物を見せる。
- 「二値を覆す」という切り口は不採用。教えすぎ（クイズ等）も不要。
- ±5 V電源は範囲内として扱う。PCellだけで作るのでフルカスタム用DRCの未整備は問題ない。
- タスクの大きさは一旦気にしない。迷う箇所は妥当な方法でどんどん決めてよい。

## 次の作業

`docs/concept.md` の「未決定・要確認」から：

1. ColabでPDK（OpenSUSI/TR-1um）のRuby製DRC/LVSデッキが動くか確認
2. PDK資料に、メタルの許容電流と配線容量の係数があるか確認
3. DRCルールから、スタセルのテンプレート寸法（高さ、レール幅、配線格子）の案を出す

## 参照

- PDK：https://github.com/OpenSUSI/TR-1um（Apache-2.0）
- 元設計：https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic
- 公式募集：https://sscs.ieee.org/membership/awards/ieee-sscs-code-a-chip-travel-grant-awards/
