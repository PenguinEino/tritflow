## 6. 評価と応用

5章では4項の積和dot4をポストレイアウトシミュレーションで検証し、三値のSTAと比較した。本章では積和の項数を変えて面積・遅延・静的電力を評価する。続いて、HDLの変更から同じフローを実行し、シャトル用の最上位レイアウトを示す。

### 6.1 積和の規模と面積

評価する回路は1トリットの重みと入力による積和 y = w<sub>0</sub>x<sub>0</sub> + … + w<sub>N−1</sub>x<sub>N−1</sub> である。出力の桁数は−Nから+Nまでを表せる最小の桁数とする。重みはHDLの入力として残し、シミュレーションでは (+1, −1, +1, +1) を繰り返した値に固定する。加算は3.7と同じ書き方で合成し、項数に応じた構造の変更は加えない。

各回路の配置配線と検証の記録を示す。面積は配置配線したダイの外形から求める。

<!-- code: scale6 -->

項数が増えると積の回路だけでなく、和を表す桁数に応じて加算回路も増える。ダイ面積にはこれらのセルに加えて電源と信号の配線領域が含まれるため、項数だけに比例する面積増加にはならない。

### 6.2 静的電力と時間平均

抵抗分圧によって0 Vを保つ状態では、入力を切り替えなくても静的電流が流れる。NANYにはVDD・VSS側の直列MOS経路を遮断し、VMIDへのクランプで0 Vを出す状態もある。静的電力は記録した入力列に含まれる状態のDC動作点から求める。SPICEの電圧源に流れ込む向きを電流の正とすると、回路が消費する電力は P = −Σ<sub>r</sub> V<sub>r</sub>I<sub>r</sub> であり、正負両方の電源の寄与を含む。

時間平均の供給電力は入力列の全保持区間にわたって電力波形を積分し、全時間で除して求める。この値には入力状態ごとに異なる静的消費と遷移時の消費が含まれる。入力を駆動する電圧源の電力は含めない。

<!-- code: power6 -->

入力状態によって導通する分圧回路の数が変わるため、同じ項数でも静的電力が変わる。時間平均は保持時間と入力列に依存する。

### 6.3 STAとSPICE

各回路で、正負の桁上げの発生と解消を含む入力の列を用いる。4項の入力列は5章とは異なる。固定した重みの条件の下でSTAを行い、STAとSPICEには同じ入力遷移、出力負荷、入力の変化時間、配線容量を与える。比較する遅延はその列で得られた出力ごとの最大整定時間である。

配線容量の影響は同じ抽出回路について推定した配線容量だけを除いた場合と比較する。STAは各規模で、SPICEは4項で比較し、素子の寄生容量と100 fFの出力負荷は両方に含める。

16項では一部のNANYの負荷容量が特性表の上限2 pFを超え、最大2.862 pFとなるため、STAは負荷容量に対して線形に外挿する。

<!-- code: timing6 -->

5章のdot4ではSTAがSPICEよりy[1]で約10%、y[0]で約3%短い。項数を変えた比較では、規模と出力によって誤差の符号も変わる。STAは指定した入力遷移に対応するセルの特性表を使う見積もりであり、途中のグリッチを含むアナログ波形全体を計算していない。SPICEではグリッチ後に判定帯へ再び入るまでの時間も整定時間に含まれるため、STAを遅延の上界として扱うことはできない。

### 6.4 HDLの変更と再実行

推論時の重みをHDLの定数にすると、重みに応じた乗算回路が論理合成で簡単化される。次の回路はdot4の重みを (+1, −1, +1, +1) に固定したものである。式と入出力の宣言を変更しても、論理合成からポストレイアウトシミュレーションまでを同じセルで実行できる。

<!-- code: reuse_source -->

SPICEの入力は、全状態数が27以下なら全状態、それ以外はゼロ入力、全入力が−1または+1の状態、符号が交互になる状態、1入力だけが±1の状態から11状態を選ぶ。出力の期待値は合成した回路網からではなく、HDLの評価から求める。

<!-- code: reuse6 -->

### 6.5 シャトル用の最上位レイアウト

dot4に、パッド、電源配線、PDKの標準MPWフレームを付けた最上位レイアウトを示す。フレームのESD（静電気放電）保護の電源は、VSSを回路のVSS（−5 V）と共通にし、VDDには別の端子から+5 Vを与える。これで−5〜+5 Vの3値の信号がESD保護の電源の範囲に収まり、標準のパッドをそのまま使える。テープアウトしたチップも同じ接続である。

<!-- code: shuttle6 -->

### 6.6 結論

### 参考文献

1. Shuming Ma et al., “The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits,” arXiv:2402.17764, 2024. [doi:10.48550/arXiv.2402.17764](https://doi.org/10.48550/arXiv.2402.17764).
2. Sheng Lin, Yong-Bin Kim, and Fabrizio Lombardi, “CNTFET-Based Design of Ternary Logic Gates and Arithmetic Circuits,” *IEEE Transactions on Nanotechnology*, 10(2), pp. 217–225, 2011. [doi:10.1109/TNANO.2009.2036845](https://doi.org/10.1109/TNANO.2009.2036845).
3. Xiao-Yuan Wang et al., “High-Density Memristor-CMOS Ternary Logic Family,” *IEEE Transactions on Circuits and Systems I: Regular Papers*, 68(1), pp. 264–274, 2021. [doi:10.1109/TCSI.2020.3027693](https://doi.org/10.1109/TCSI.2020.3027693).
4. Jae Won Jeong et al., “Tunnelling-based ternary metal–oxide–semiconductor technology,” *Nature Electronics*, 2(7), pp. 307–312, 2019. [doi:10.1038/s41928-019-0272-8](https://doi.org/10.1038/s41928-019-0272-8).
5. Hanmok Park, Seonghoon Kim, Sunmean Kim, and Taigon Song, “An RTL-Based General Synthesis Methodology for Device-Independent Ternary Logic Circuits,” *IEEE Access*, 13, pp. 163648–163660, 2025. [doi:10.1109/ACCESS.2025.3597293](https://doi.org/10.1109/ACCESS.2025.3597293).
6. Steven Bos and contributors, *MixedRadixCircuitSynthesis (MRCS)*, source snapshot `0865cee`, 2023. [Repository](https://github.com/aiunderstand/MixedRadixCircuitSynthesis/tree/0865cee1f49fe9a803b4910b570f4e96e514c61b).
7. Mohnish Pai, “Ankhdjet: An Open-Source Compiler for Mask-Programmed Ternary Compute-in-ROM on an Open PDK,” arXiv:2608.26206, 2026. [doi:10.48550/arXiv.2608.26206](https://doi.org/10.48550/arXiv.2608.26206).
8. Jerzy Słupecki, “Kryterium pełności wielowartościowych systemów logiki zdań,” *Comptes Rendus des Séances de la Société des Sciences et des Lettres de Varsovie, Classe III*, 32, pp. 102–109, 1939. [原文](https://rcin.org.pl/Content/50652/PDF/WA35_4821_cz167-r1939-t32_Spraw-TNW-wIII-art1.pdf#page=110).
9. Jean W. Butler, “On complete and independent sets of operations in finite algebras,” *Pacific Journal of Mathematics*, 10(4), pp. 1169–1179, 1960. [本文](https://msp.org/pjm/1960/10-4/pjm-v10-n4-p10-s.pdf).
10. Stephen Cole Kleene, *Introduction to Metamathematics*, North-Holland / P. Noordhoff, 1952, §64. [書誌情報](https://cir.nii.ac.jp/crid/1971712334708500134).
11. Francesco Paoli and Gavin St. John, “Editorial Introduction,” *Studia Logica*, 112, pp. 1201–1214, 2024. [doi:10.1007/s11225-024-10147-9](https://doi.org/10.1007/s11225-024-10147-9).
12. OpenSUSI, Tokai Rika, and contributors, *TR-1um Open Source PDK project*, commit `5d963db`, 2026. [使用したPDK](https://github.com/OpenSUSI/TR-1um/tree/5d963db9d44e192d37a0489c208bfccf2e2f690c).
13. Robin Lu and contributors, *TR-1um: an experiment to port TR-1um and OpenSUSI MPW template to LibreLane + ALIGN*, source snapshot `b14b3f5`, 2026. [Repository](https://github.com/luyanaa/TR-1um/tree/b14b3f5cca671fd86804e3cca434a0a728c73642).
14. Einosuke Okazaki, *平衡3値論理回路 — OpenSUSI TR-1um (opensusi-tr10-balanced-ternary-logic)*, source snapshot `8a60b97`, 2026. [元の回路と提出資料](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic/tree/8a60b97868cad008ff21fefca5da13dcd06063f8).
15. 一般社団法人OpenSUSI, “OpenSUSI-MPW第1回募集を完了 — 企業・大学・高専・高校・個人から49枠の申し込み,” 2026年10月16日. [発表](https://prtimes.jp/main/html/rd/p/000000014.000182004.html).
16. Matthias Köfferlein and the KLayout contributors, *KLayout Layout Viewer and Editor*, version 0.30.6, 2026. [Release](https://github.com/KLayout/klayout/releases/tag/v0.30.6).
17. Holger Vogt, Giles Atkinson, and Paolo Nenzi, *Ngspice User's Manual*, version 42, 2023. [Manual](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/old-releases/42/ngspice-42-manual.pdf/download).
18. ISHI会, “2025年12月イベント「東海理化シャトルのオープンPDK解説会」の参加者募集,” 2025年10月30日. [発表](https://ishi-kai.org/information/seminar/2025/10/30/DecEvent_1213.html).
19. Zane Hambly, *Takahe*, source snapshot `e7123ea`, 2026. [二値で符号化したSKY130の例](https://github.com/Zaneham/takahe/blob/e7123ea60269922acb283d576678a3aabe51f4f4/designs/setun70_physical.sv).
20. Nikolay P. Brusentsov and José Ramil Alvarez, “Ternary Computers: The Setun and the Setun 70,” in *Perspectives on Soviet and Russian Computing (SoRuCom 2011)*, IFIP AICT 357, Springer, pp. 74–80, 2011. [doi:10.1007/978-3-642-22816-2_10](https://doi.org/10.1007/978-3-642-22816-2_10)
