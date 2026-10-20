## 付録B. 検証結果と再実行

下の表は今回計算した結果と保存済みの実験を区別し、HDL、ライブラリ、PDK、ツール、入力条件、ネイティブのレポートを対応づけます。保存済みレポートの表示だけでは新しい検査を実行しません。

<!-- colab-record -->

### 配線結果の区別

同じ回路でも配置配線が異なれば遅延は別の測定です。各表の配線識別子と負荷・入力条件を揃えて比較してください。

| 図・結果 | 配線識別子 |
|---|---|
| 冒頭と配置の加算器 | {paper_adder.run_id} |
| 全加算器の波形と負荷掃引 | {paper_post.run_id} |
| 桁数の掃引 | {paper_scaling.run_id} |
| 保存済み4回路のadder4 | {archive.adder_run_id} |
| 保存済み4回路のfull_add | {archive.full_add_run_id} |
| 保存済み4回路のmac1 | {archive.mac1_run_id} |
| 保存済み4回路のmul1 | {archive.mul1_run_id} |

アナログ試験の表には入力順序、訪れた状態数、保持時間、エッジ時間、最大刻み、温度、負荷、初期化区間、出力ごとの誤差と整定時間を残します。初期化は遷移最大値から除きます。Newton法の初期推定値は収束の開始点で、過渡電圧を固定する条件ではありません。

STAは同じ遷移集合の`tested_predicted_s`と`simulated_s`を比べます。別の保守的推定`predicted_s`とは列を分けています。トップの表も描画DRC、描画LVS、マスクDRC、MPW事前チェック、`submission_ready`を別々に示します。

<details>
<summary>実行環境と再計算</summary>

Colabではセットアップセルの`TRITFLOW_REF`が指定するコミットを`/content/tritflow`へ取得します。PDKとネイティブツールは`notebook/setup_pins.json`に固定し、Python環境とフォントも確認します。章の途中で失敗したときは、その章の前提となるセルを再実行してください。

`TRITFLOW_FORCE_RUN=1`で重い処理と4回路の保存結果を使う処理を再計算します。これは別途保存しているセル特性、寸法、桁数、負荷の掃引を再生成しません。追加実験は`TRITFLOW_EXTENDED=1`、出力先は`TRITFLOW_NOTEBOOK_BUILD`で指定します。

```sh
python3 -m tritflow.sim.sizing
python3 examples/postlayout_all.py
python3 examples/adder_scaling.py --jobs 1
python3 -m tritflow.sim.publication
python3 -m pytest tests/sim tests/extract -q
```

既存のSPICE出力からSTAの比較だけを再計算するには`python3 -m tritflow.sta.validate`を使います。トップの`chip.signoff(force=True)`は全体の検査を再実行します。各設計のそばにDRC/LVSレポート、SPICEデッキ、ログ、波形を保存します。

</details>

<details>
<summary>出典とライセンス</summary>

設計ソースは[TritFlow](https://github.com/PenguinEino/tritflow)、[著者の三値セル](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic)、[OpenSUSI TR-1um](https://github.com/OpenSUSI/TR-1um)です。KLayoutは[公式配布](https://www.klayout.de/build.html)を使います。TritFlowと著者が公開した回路図はApache-2.0です。PDKのライセンスと帰属表示はNOTICEに残しています。

</details>
