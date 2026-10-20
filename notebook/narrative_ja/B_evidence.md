## 付録B. 検証結果と再実行

下のセルは、セルの特性、4つの回路の物理検査と遅延、この実行で計算した結果と保存済みの結果の内訳を表にします。表はすべて折りたたんであります。

<!-- colab-record -->

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
