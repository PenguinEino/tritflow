## 1. 最初の回路：`a & ~a` をGDSにする

本章では、小さな三値回路の1つである `a & ~a` を、HDLからGDSとポストレイアウトシミュレーションまで一通り通し、TritFlowのフロー全体を見る。各段の中身は、2章以降で順に開ける。

二値の論理では、`a & ~a` はaが何であっても偽になる。三値ではそうならない。

<div style="display:flex;flex-wrap:wrap;gap:40px;align-items:flex-start;margin:8px 0"><table style="border-collapse:collapse;font-size:16px"><tr><th style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center;background:#f3f4f6">a</th><th style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center;background:#f3f4f6">~a</th><th style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center;background:#f3f4f6">a &amp; ~a</th></tr><tr><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">−1</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">+1</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">−1</td></tr><tr><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">0</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">0</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center"><b>0</b></td></tr><tr><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">+1</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">−1</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">−1</td></tr></table><table style="border-collapse:collapse;font-size:16px"><tr><th style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center;background:#f3f4f6">a &amp; b</th><th style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center;background:#f3f4f6">b = −1</th><th style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center;background:#f3f4f6">b = 0</th><th style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center;background:#f3f4f6">b = +1</th></tr><tr><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center"><b>a = −1</b></td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">−1</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">−1</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">−1</td></tr><tr><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center"><b>a = 0</b></td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">−1</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">0</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">0</td></tr><tr><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center"><b>a = +1</b></td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">−1</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">0</td><td style="border:1px solid #c9ccd1;padding:6px 14px;text-align:center">+1</td></tr></table></div>

TritFlowのHDL（TritVerilog）で書くと、次のようになる。

<!-- code: source -->

論理合成する。三値の式を三値のセルに直接写像し、全入力の網羅で元のHDLとの等価性を検証する。

<!-- code: hdl -->

配置配線する。三値セル用に作った配置配線器で、各セルを貫く3本の電源レール（VDD・VMID・VSS）を保ったまま、TR-1umのM1/M2の2層で配線する。

<!-- code: pnr -->

PDKの公式デッキでDRCとLVSを行う。TritFlow用の緩和や例外は入れていない。

<!-- code: check -->

ポストレイアウトシミュレーションを行う。GDSから見積もった配線容量を加え、各区間で出力が理想電圧（−5/0/+5 V）の±0.5 V以内に入るかを三値のテストベンチで判定する。ボタンで入力を選べる。

<!-- code: spice -->

橙はTritFlowの実装、灰は既存のツールである。

<!-- code: map -->
