## 付録C. 再利用と拡張

### ローカルで実行する

空の作業ディレクトリから、ソースと同梱データを含むチェックアウトを作ります。Pythonパッケージだけではセルや例題のファイルは揃いません。

```sh
python3 -m pip install --src ./src -e "git+https://github.com/PenguinEino/tritflow.git@{reuse.source_ref}#egg=tritflow"
cd src/tritflow
bash notebook/colab_setup.sh --source "$PWD"
```

セットアップは対応するUbuntu amd64環境向けです。既存ツールを使う場合は`TR1UM_PDK`と、必要なら`KLAYOUT_BINARY`を設定します。対応環境は`notebook/README.md`を参照してください。

```python
from tritflow import flow
net = flow.load("examples/adder2.tv", "adder2").synthesize()
layout = net.place_and_route(output_dir="build/adder2")
assert layout.drc()["clean"] and layout.lvs()["matched"]
vectors = [tuple(0 for p in net.ports if p.dir == "input")]
post = layout.extract().simulate(vectors, load=100e-15)
```

この例は全入力0の動作確認です。`load`はF単位、入力の順序は`net.ports`です。算術の検証では独立した参照関数を`expected=`へ渡し、調べる経路を通る入力遷移を指定します。結果は`post["measurements"]`で確認します。`extract(wire_c=False)`は追加の配線容量を外します。

配置前の回路図は`net.schematic(expand="*")`、文字列のHDLは`flow.loads(source, top=..., params=...)`で扱えます。CLIからも合成と配置配線を実行できます。

```sh
python3 -m tritflow.synth examples/adder2.tv --top adder2 -o build/adder2
python3 -m tritflow.pnr build/adder2/adder2.json -o build/adder2 --seed 7
```

### セルを追加する

回路・端子・真理値を`tritflow/cells/circuits.py`、形状を`compact.py`、PDK素子の呼出しを`primitives.py`で定義します。共通高さ、格子、電源順、ピンの接続位置を保ち、内部の配線障害物を抽象情報へ含めます。

合成には`tritflow/synth/simulate.py`の評価と`mapping.py`の割当規則、SPICEには`tritflow/sim/spice.py`のピン順と`characterize.py`の論理値を追加します。HDLプリミティブならparserとelaborator、STAを使うなら`tritflow/sta/logic.py`と遷移特性、回路図には`tritflow/schematic/render.py`も更新します。

配布セルを置き換える前に試作用の出力先で生成し、独立した真理値照合、DRC/LVS、DC、負荷付き過渡解析、突き当て配置、試験回路の配線を確認してください。

```sh
python3 -m tritflow.cells build --out build/cell_trial
python3 -m tritflow.cells verify --out build/cell_trial
python3 -m tritflow.sim.characterize INV --spice build/cell_trial/INV/INV.ext.spice --destination build/INV.char.json
```

### 演算子を追加する

既存演算のHDLモジュールで書けるかを先に検討します。構文を増やす場合は`tritflow/hdl/parser.py:GRAMMAR`、`elaborate.py:Elaborator.expression`、`ir.py:Design.evaluate`を更新し、`tritflow/synth/optimize.py`に三値で成立する書換え、`mapping.py:Mapper.map`に割当規則を追加します。

小さい演算子は全入力で独立した定義と照合し、不正な記述の診断も試します。影響するテストに加え、新しい素子を使う場合は抽出デッキも見直してください。

```sh
python3 -m pytest tests/hdl tests/synth -q
python3 -m pytest tests/cells tests/pnr tests/sim tests/extract -q
python3 -m pytest tests/sta tests/schematic -q
```
