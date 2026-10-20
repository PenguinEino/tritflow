# 図の説明

## fig_flow

TritVerilogからセル、GDS、抽出後波形へ。{paper_adder.hdl_lines}行のトップと共有モジュールから、{paper_adder.nany} NANYと{paper_adder.inv} INVを生成します。{paper_adder.width}トリット版のGDSは{paper_adder.die_um} µm、DRCは{paper_adder.drc_items}件、LVSは{paper_adder.lvs_status}です。右端は配線容量込みの和と桁上がりです。

## fig_gates

抽出後セルのDC伝達特性とVDD電流。横軸は入力A、2入力セルのBは各論理レベルに固定します。帯は出力の許容範囲±{levels.band_v} Vです。

## fig_sizing

INVの抵抗長{paper_sizing.resistor_lengths_um} µmでの伝達特性と、INV/NANYの最大レベル誤差・電流。丸印が採用寸法、塗りつぶしと白抜きが許容範囲の内外です。逆三角は表示下限{paper_sizing.error_floor_mv} mV未満を示します。

## fig_cell

元のNANY、共通高さに作り直したNANY、突き当てた{paper_cell.row_count}セルの行。素子のグループと3本の電源レールを示します。

## fig_synth

半加算器と全加算器のHDL、半加算器のセル、全加算器の階層。配線色は入力に対する定常トリット値で、青が−1、灰色が0、赤が+1です。

## fig_pnr

信号順の初期配置、配置配線後のGDS、HPWLの変化。セル色は加算器の桁、横の配線はチャネル内M1、縦はセル上も通るM2です。

## fig_postlayout

全加算器の{paper_post.states}入力状態と負荷掃引。保持{paper_post.hold_ns} ns、出力負荷{paper_post.load_ff} fFで、和の最も遅い遷移は配線容量の追加により{paper_post.pre_sum_ns}から{paper_post.post_sum_ns} nsへ変わります。負荷掃引は{load.last_pass_pf} pFで合格、{load.first_fail_pf} pFで不合格です。

## fig_scaling

同じパラメータ付きHDLから作る{paper_scaling.width_min}〜{paper_scaling.width_max}トリット加算器。上から桁上がり経路の整定時間、測定入力での静的電力の最大値、GDS面積とセル数です。

## fig_sta

同じ入力遷移集合に対するSTAと抽出後SPICEの最大出力遅延。対角線は一致、帯は±{sta.target_pct}%です。{sta.output_count}出力のうち{sta.within_target}出力が帯内に入り、平均絶対百分率誤差は{sta.mape_pct}%です。
