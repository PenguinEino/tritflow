# TritFlow：OpenSUSI TR-1umで平衡三値HDLからGDSへ

三値のHDLから、製造用のレイアウトまで作れるでしょうか。三値論理には新しいデバイスやシミュレーションを使う研究が多く、オープンな設計ツールの[MRCS](https://github.com/aiunderstand/MixedRadixCircuitSynthesis)も、通常のCMOS向けには三値を二値へ変換します。TritFlowは、著者がテープアウトした三値セルをもとに、公開PDKのOpenSUSI TR-1um上で三値HDLをDRC/LVSの通ったGDSへ変換します。HDLを書き換えれば、自分の回路でも同じ工程を実行できます。

[OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um)は日本の東海理化のプロセスを使う、NDA不要の{history.node_um} µm CMOS PDKです。TritFlowは三値スタンダードセル、Verilog風の言語、合成、2層の配置配線、PDKのDRC/LVS、抽出後ngspiceをつなぎます。ライブラリとフローはApache-2.0で公開しています。

元のセルは{history.tapeout_year}年にテープアウト済みで、チップは{history.delivery_month_ja}に届く予定です。実測はまだありません。採択された場合は、{history.isscc_dates_ja}のISSCCポスターで、このセルの最初の実測結果をノートブックの予測と並べる計画です。

「**ランタイム → すべてのセルを実行**」で加算器を作り、GDSを拡大して素子と配線を確認してください。本文は約20分で読める分量です。最後にHDLを編集する例を置いています。

## 0. HDLから配線済みGDSへ

図は{paper_adder.width}トリット加算器の全工程です。下のコードでは{adder.width}トリット版を作り、合成、配置配線、DRC/LVS、抽出後SPICEを続けて実行します。その直後のビューアで配線済みGDSを開き、同じファイルをダウンロードできます。

トリットの値−1、0、+1を、それぞれ{levels.negative_v}、{levels.zero_v}、{levels.positive_v} Vで表します。`trit`は独自の信号型で、Verilogの`x`や`z`とは別です。波形の帯は各出力の理想値±{levels.band_v} Vを示します。
