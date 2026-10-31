# TritFlow：オープンソースPDK TR-1umで、三値のHDLからGDSへ

Einosuke Okazaki (岡崎 英之介)<br>
Information and Communication Engineering Course, Department of Monozukuri Engineering, Tokyo Metropolitan College of Industrial Technology (KOSEN), Tokyo, Japan

**実行環境**

- 所要時間：新しいColabのランタイムでRun all、セットアップを含めて6〜8分
- Python：3.12
- PDK：OpenSUSI TR-1um（commit 5d963db）
- KLayout：0.30.6
- ngspice：42
- Pythonのパッケージ：最初のセルが固定したバージョンで導入

TritFlowは、三つの電圧レベルをそのまま扱うCMOSセルを用い、三値のHDLからGDSまでをOpenSUSI TR-1umの上で通す設計フローである。本ノートブックでは三値のHDLから論理合成、2層メタルの配置配線、GDSの出力、DRC/LVS、ポストレイアウトシミュレーション、三値のタイミング解析までを順に実行する。

<!-- figure: fig_flow_v2 -->

TritFlowが扱うのは**平衡三値**（Balanced Ternary）である。各桁（トリット）は −1・0・+1 の3値をとり、桁の重みは3のべき乗（1, 3, 9, …）となる。回路上の電圧としては、それぞれ −5 V・0 V・+5 V に対応する。平衡三値は、1958年にモスクワ大学で開発された初期の三値計算機「[Setun](https://doi.org/10.1007/978-3-642-22816-2_10)」でも採用された歴史ある表現形式である。近年では、重みをこの三値（−1・0・+1）に制約した大規模言語モデル「[BitNet b1.58](https://doi.org/10.48550/arXiv.2402.17764)」の登場により再び大きな注目を集めている。線形層における重みと8ビット入力との積は「入力そのまま」「符号反転」「ゼロ」のいずれかとなるため、乗算器を用いず加減算のみで積和演算（GEMM）を実行できる。三値のデータを中間の二値変換を挟まず、三値の電圧のままダイレクトに処理する専用ハードウェアは、高い効率を達成する可能性を秘めている。

しかし現在、三値演算を担っているハードウェアのほぼすべては、従来の二値論理回路上でのエミュレーションである。デバイスレベルではCNTFET（[Lin et al., 2011](https://doi.org/10.1109/TNANO.2009.2036845)）、メモリスタ（[Wang et al., 2021](https://doi.org/10.1109/TCSI.2020.3027693)）、新規CMOS構造（[Jeong et al., 2019](https://doi.org/10.1038/s41928-019-0272-8)）など多様な三値素子が研究されているものの、設計ツール環境は[ゲート回路網の生成](https://doi.org/10.1109/ACCESS.2025.3597293)にとどまるか、あるいは三値信号を複数の二値信号線に符号化して二値EDAを通すアプローチ（[MRCS](https://github.com/aiunderstand/MixedRadixCircuitSynthesis/tree/0865cee1f49fe9a803b4910b570f4e96e514c61b)、[Takahe](https://github.com/Zaneham/takahe/blob/e7123ea60269922acb283d576678a3aabe51f4f4/designs/setun70_physical.sv)、[Ankhdjet](https://doi.org/10.48550/arXiv.2608.26206)）に限られていた。商用ファブで製造可能なオープンソースPDK上で、3つの物理電圧レベルを直接扱うCMOSセルを用いて、HDLからGDSまでを完全自動で通すフィジカル設計フローは、我々の知る限り前例がない。

本ノートブックでは、日本で初めて商用の半導体ファブが公開したオープンソースPDK「[OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um/tree/5d963db9d44e192d37a0489c208bfccf2e2f690c)（東海理化）」を採用し、この三値設計フローを実証する。TritFlowのセルライブラリは、[著者が設計・テープアウトした三値論理回路](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic/tree/8a60b97868cad008ff21fefca5da13dcd06063f8)（2026年、第1回OpenSUSI-MPWシャトル「OpenSUSI-TR10」）の回路トポロジーと素子寸法をそのままスタンダードセル化したものである。三値専用HDL「TritVerilog」の記述から論理合成、配置配線、DRC/LVS検証、ポストレイアウトSPICEシミュレーションまでを一つの流れるようなパイプラインとして完結させている。

OpenSUSI-TR10のチップは2027年1月に届き、採択されれば2月のISSCCでTritFlowとともにセルの最初の実測結果を報告する。TritFlowで設計した回路は、次のOpenSUSIシャトルで製造する。TritFlowで設計、製造、実測、報告を一巡させることで、TR-1umがCode-a-Chipの掲げる三つの価値を実現するのに十分な能力を備えていることを実証する。そして、日本における半導体設計の民主化を大きく前進させることを目指す。

**再現性**　後に続く研究者がTritFlowを中身まで理解し、自分で作り直し、説明できること。そのためにTritFlowはセルの回路、論理合成のアルゴリズム、配置配線のいずれも、読んで追える単純さに保ちながら、PDKのDRC/LVSとポストレイアウトSPICEで検証したコアのGDSを出力するように設計した。本ノートブックは各段がなぜそう動くのかを説明し、その場で動かして確かめられるようにしている。セルは実際に製造し実測する回路をもとにしているため、理解した内容をシリコンの実測と突き合わせることもできる。

**再利用性**　そうして得た理解をもとに、TritFlowを独自に発展させられること。HDLを書き換えると、同じフローで検証済みのコアを再生成できる。dot4についてはMPWのフレームに載せた最上位レイアウトまで示す。構成が単純なので、セルを足したり、合成や配置配線のアルゴリズムを置き換えたりすることもできる。セル、フロー、ノートブックはApache-2.0で公開しており、次の研究や次のシャトルの出発点になる。

**教育性**　この理解から発展までの道筋は、そのまま入門者の学びの道筋にもなる。すべてがノートブックの上で対話的に動き、各段で何が起きたかを図と数値で示すので、基本的なCMOS論理とHDLを知る読者であれば、HDLを書いてからGDSができるまでを自分の手で一通りたどれる。しかもそれは実際の製造と実測につながるフローである。
