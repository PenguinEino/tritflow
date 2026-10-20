## 1. CMOSで作る三値ゲート

INVの中間出力はVDD側とVSS側の抵抗分圧で決まります。入力が0のときは両側のMOSが導通し、入力を固定しても電流が流れます。NANYにはVMIDへのクランプ経路があり、符号が逆の入力に対して出力を0 Vに保ちます。下のセルでは真理値表とテープアウトした回路図を切り替え、続いてDC特性を計算します。

\[
\operatorname{INV}(a)=-a,\quad \operatorname{NAND}(a,b)=-\min(a,b),\quad
\operatorname{NOR}(a,b)=-\max(a,b),\quad \operatorname{NANY}(a,b)=-\operatorname{clamp}(a+b,-1,1).
\]

### 分圧の予測

INVの入力を0 Vに置き、導通中のMOSをオン抵抗で近似します。直列抵抗を含む上側と下側の抵抗を\(R_u\)、\(R_d\)とすると、

\[
I_{\rm hand}=\frac{V_{DD}-V_{SS}}{R_u+R_d},\qquad
V_{Y,\rm hand}=V_{SS}+I_{\rm hand}R_d,\qquad
P_{\rm hand}=(V_{DD}-V_{SS})I_{\rm hand}.
\]

両側の抵抗が等しければ出力は0 Vです。寸法とPDKモデルから求めた\(R_u\)={divider.upper_kohm} kΩ、\(R_d\)={divider.lower_kohm} kΩを使うと、出力{divider.output_v} V、電流{divider.current_ma} mA、電力{divider.power_mw} mWと予測します。次に非線形の素子モデルを使うSPICEと比べます。

> **ここから分かること。** 抽出後のINVは入力0 V、{paper_gates.temperature_c} °Cで、出力{paper_gates.inv_zero_v} V、VDD電流{paper_gates.inv_current_ma} mA、全電源の合計電力{paper_gates.inv_power_mw} mWです。分圧の手計算に対応する回路図SPICEでは、出力{divider.spice_output_v} V、電力{divider.spice_power_mw} mWとなります。

### NANYと定数セル

二値のNANDと違い、三値のINV・NAND・NORは定数3つを加えても、1入力関数の一部しか作れません。下のコードは入力線と定数から始めてゲートを合成し、新しい真理値表が増えなくなるまで繰り返します。生成できる1入力関数はINV・NAND・NORと定数3つで{basis.minmax_count}/{basis.unary_total}、NANYとTIEZだけで{basis.zero_count}/{basis.unary_total}、NANYとTIEP/TIENで{basis.complete_count}/{basis.unary_total}です。

[Słupeckiの判定法](https://www.conferences.info.uaic.ro/mathematical-foundations-of-informatics/2019/PDF/MFOI2019_Volume.pdf)では全1入力関数を作れ、かつ両入力に本質的に依存して3値すべてを出す2入力関数があれば機能的完全です。NANYは後者を満たすので、NANYとTIEP/TIENの組は機能的完全です。NANYは\(f(-a,-b)=-f(a,b)\)を満たす奇関数で、0だけを足して合成しても奇関数のままです。±1の定数がこの制約を外します。

半加算器はNANY {arithmetic.ha_nany}個とINV {arithmetic.ha_inv}個になります。これも同じセルでHDLを合成して数えます。完全性はセルの組に関する性質です。TritFlowの合成は式をセルへ写す方式で、任意の真理値表から回路を自動生成する機能はありません。
