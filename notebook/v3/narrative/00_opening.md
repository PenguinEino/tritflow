# TritFlow：オープンソースPDK TR-1umで、三値のHDLからGDSへ

Einosuke Okazaki (岡崎 英之介)<br>
Information and Communication Engineering Course, Department of Monozukuri Engineering, Tokyo Metropolitan College of Industrial Technology (KOSEN), Tokyo, Japan

TritFlowは、三つの電圧レベルをそのまま扱うCMOSセルを用い、三値のHDLからGDSまでをOpenSUSI TR-1umの上で通す設計フローである。本ノートブックの題材は、三値の重み $w_i$ と入力 $x_i$ の4項の内積 $y = \sum_{i=0}^{3} w_i x_i$ を計算する回路dot4である。dot4を論理合成、2層メタルの配置配線、DRC/LVS、ポストレイアウトシミュレーション、三値のタイミング解析の順に通し、HDLを書き換えて同じフローを再実行する。

<!-- figure: fig_flow_v2 -->

TritFlowが扱うのは平衡三値である。各桁は−1・0・+1のいずれかをとり、桁の重みは3のべき（1, 3, 9, …）である。回路の上ではそれぞれ−5 V・0 V・+5 Vに対応する。平衡三値は1958年にモスクワ大学で作られた三値計算機[Setun](https://doi.org/10.1007/978-3-642-22816-2_10)も用いた数の表し方である。重みをこの三値に絞った大規模言語モデル[BitNet b1.58](https://doi.org/10.48550/arXiv.2402.17764)の線形層では、重みとの積が入力、その符号反転、0のいずれかとなり、積和を加算と減算で実行できる（入力は8ビット）。三値のデータを三値のまま計算する回路は、改めて意味を持ち始めている。それでも、こうした計算を担っているのは二値の回路である。三値の論理回路はCNTFET、メモリスタ、CMOSなどの上で数多く研究されている（例：[CNTFET](https://doi.org/10.1109/TNANO.2009.2036845)、[メモリスタ](https://doi.org/10.1109/TCSI.2020.3027693)、[CMOS](https://doi.org/10.1038/s41928-019-0272-8)）。一方で設計ツールは[ゲートの回路網の生成](https://doi.org/10.1109/ACCESS.2025.3597293)で止まるか、三値を二値の信号で符号化して実装する（[MRCS](https://github.com/aiunderstand/MixedRadixCircuitSynthesis/tree/0865cee1f49fe9a803b4910b570f4e96e514c61b)、[Takahe](https://github.com/Zaneham/takahe/blob/e7123ea60269922acb283d576678a3aabe51f4f4/designs/setun70_physical.sv)、[Ankhdjet](https://doi.org/10.48550/arXiv.2608.26206)）。製造可能なオープンソースPDK上で、三つの電圧レベルをそのまま扱うCMOSセルを用い、三値のHDLからGDSまでを通す設計フローは、我々の知る限り報告されていない。

本ノートブックではこの設計フローをTritFlowとして、日本の商用ファブが公開したオープンソースPDKである[OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um/tree/5d963db9d44e192d37a0489c208bfccf2e2f690c)の上で実現する。TritFlowは、著者がテープアウトした三値論理回路をスタンダードセルにして、三値の専用HDLから論理合成、配置配線、PDKのDRC/LVS、ポストレイアウトシミュレーションまでを一つのフローで行う。

スタンダードセルの元になった三値回路は、TR-1umを使うOpenSUSI-MPWの初回シャトル（2026年、OpenSUSI-TR10）でテープアウトした、$X + A \times B + C_{in} = \mathrm{Sum} + 3\,C_{out}$ を満たす[1トリットの積和回路](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic/tree/8a60b97868cad008ff21fefca5da13dcd06063f8)であり、3章以降で扱うdot4の1項にあたる。チップは2027年1月に届く。採択されれば、2月のISSCCでTritFlowを発表し、元になったセルの最初の実測結果を合わせて報告する。そしてTritFlowで設計した回路を、次のOpenSUSIシャトルで製造する。

設計、製造、実測、報告を一巡させることで、TritFlowとTR-1umが、Code-a-Chipの掲げる三つの価値を実現できることを実証する。そして、日本における半導体設計の民主化を大きく前進させることを目指す。

**再現性**　後に続く研究者がTritFlowを中身まで理解し、自分で作り直し、説明できること。そのためにTritFlowはセルの回路、論理合成のアルゴリズム、配置配線のいずれも、読んで追える単純さに保ちながら、PDKのDRC/LVSとポストレイアウトSPICEで検証したコアのGDSを出力するように設計した。本ノートブックは各段がなぜそう動くのかを説明し、その場で動かして確かめられるようにしている。セルは実際に製造し実測する回路をもとにしているため、理解した内容をシリコンの実測と突き合わせることもできる（1〜5章）。

**再利用性**　そうして得た理解をもとに、TritFlowを独自に発展させられること。HDLを書き換えると、同じフローで検証済みのコアを再生成できる。dot4についてはMPWのフレームに載せた最上位レイアウトまで示す。構成が単純なので、セルを足したり、合成や配置配線のアルゴリズムを置き換えたりすることもできる。セル、フロー、ノートブックはApache-2.0で公開しており、次の研究や次のシャトルの出発点になる（6章）。

**教育性**　この理解から発展までの道筋は、そのまま入門者の学びの道筋にもなる。すべてがノートブックの上で対話的に動き、各段で何が起きたかを図と数値で示すので、基本的なCMOS論理とHDLを知る読者であれば、HDLを書いてからGDSができるまでを自分の手で一通りたどれる。しかもそれは実際の製造と実測につながるフローである。
