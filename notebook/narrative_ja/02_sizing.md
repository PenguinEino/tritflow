## 2. 中間レベルと静的電力を調整する

プルダウンを強くすれば中間出力は下がり、プルアップを強くすれば上がります。両側の直列抵抗を長くすると電流は減りますが、出力誤差も変わります。図の丸印はテープアウトした設計の採用寸法です。スライダーでW/Lと抵抗長を選び、伝達特性と誤差・電流の点を動かしてください。

### 寸法からの予測

導通中のMOSのオン抵抗を\(W/L\)に反比例すると近似し、前章の分圧式に戻して計算します。

\[
r_{\rm on}'\simeq r_{\rm on}\frac{(W/L)_{\rm adopted}}{(W/L)'},\qquad
\Delta V_Y\simeq(V_{DD}-V_{SS})\frac{R_u\Delta R_d-R_d\Delta R_u}{(R_u+R_d)^2}.
\]

> **ここから分かること。** 採用したINVの最大レベル誤差は{sizing.adopted_error_mv} mV、最大電源電流の絶対値は{sizing.adopted_current_ua} µAです。NANYではそれぞれ{paper_sizing.nany_error_mv} mV、{paper_sizing.nany_current_ua} µAとなります。加算器の測定入力で得た静的電力の近似は1セル当たり{scaling.power_per_cell_mw} mWで、{scaling.selected_n}トリットでは{scaling.max_power_mw} mWです。

MOS寸法を固定し、INVの両抵抗を{sizing.adopted_rr_um}から{sizing.selected_rr_um} µmに伸ばすと、最大電流は{sizing.adopted_current_ua}から{sizing.selected_current_ua} µAへ減り、最大誤差は{sizing.adopted_error_mv}から{sizing.selected_error_mv} mVへ増えます。中間電圧の変化は手計算が{sizing.predicted_shift_mv} mV、SPICEが{sizing.spice_shift_mv} mVで、符号が一致しません。手計算は抵抗のバイアス依存性とMOSの非線形性を省いています。F_RRの基板端子は両方ともVDDですが、信号端子の電圧が異なるため、抵抗値の補正も異なります。

この電流は入力を固定しても流れます。動作周波数を下げるだけでは、中間レベルを保つ電力はなくなりません。
