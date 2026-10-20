## 7. 配線後の電圧と遅延を確かめる

出力が有効なトリットになる時刻を、入力ランプの開始から理想値±{levels.band_v} Vに入り、その入力区間の終わりまで留まるまでの時間とします。同じ抽出素子に配線容量を加えた場合と加えない場合を比べ、負荷と桁数を増やします。

### 桁数からの予測

1桁の桁上がり整定時間を\(t_{c,1}\)、和と桁上がりの遅い方を\(t_{e,1}\)とすると、リップル経路の予測は

\[
t_{\rm hand}(N)=t_{e,1}+(N-1)t_{c,1}.
\]

全入力0の静的電力は合成したセル数と各セルのDC電力から足し合わせます。SPICEの電源電流の符号を保って計算します。

\[
P_c(0)=-\sum_{r\in\{DD,MID,SS\}}V_rI_{r,c}(0),\qquad
P_{\rm hand}(N)=\sum_c n_c(N)P_c(0).
\]

> **ここから分かること。** 全加算器の{paper_post.states}入力状態を{load.hold_ns} nsずつ保持した負荷試験では、{load.last_pass_pf} pFで合格し、{load.first_fail_pf} pFで不合格となります。{paper_scaling.width_min}〜{paper_scaling.width_max}桁の桁上がり経路の近似直線は、素子のみで{scaling.device_slope_ns} ns/トリット、配線容量込みで{scaling.wired_slope_ns} ns/トリットです。

最大桁数での比較は次のとおりです。遅延は図と同じ和の最上位桁と桁上がりを使い、電力は別の全入力0のDC状態で比べています。

| 比較項目 | 手計算 | SPICE |
|---|---|---|
| 素子のみの経路整定時間（ns） | {scaling.predicted_ns} | {scaling.device_ns} |
| 全入力0の静的電力（mW） | {scaling.predicted_power_mw} | {scaling.zero_power_mw} |

### STAの予測とSPICEの比較

三値STAは変化前後の電圧の中点を使い、入力と出力の遷移方向、他の入力値、スルーに応じて遅延をつなぎます。最後の出力だけに中点から許容帯までの整定時間を加えます。下のコードは実行中の加算器の入力遷移、配線容量、外部負荷をSPICEと揃えて比べます。

> **ここから分かること。** 保存済みの比較では{sta.output_count}出力のうち{sta.within_target}出力がSPICEの±{sta.target_pct}%以内で、平均絶対百分率誤差は{sta.mape_pct}%です。例外の`{sta.outlier_endpoint}`は{sta.outlier_error_pct}%の過大評価で、イベントモデルにない部分的なパルス振幅と履歴が関係します。

別に求めた保守的な推定は平均{sta.bound_mean_factor}倍と余裕が大きく、保存済みの公称条件を覆うものです。未試験の波形やPVTまで保証する上限ではありません。
