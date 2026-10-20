## 8. 自分のHDLでGDSを作る

最初の編集例はmin/maxソーターです。minを`~((~a) | (~b))`で書き、合成した回路図、配線済みGDS、抽出後の波形まで実行します。コードの`CHOICE`を変えると符号検出器、比較器、乗算器も選べます。

等価な書き方を試す間は整数の参照関数を保ち、意図する機能を変えるときは参照関数も更新してください。例えばソーターのminをmaxへ変えると、配置配線に進む前に真理値表の照合が不一致の入力を示します。

> **ここから分かること。** `{custom.name}`は{custom.logic_states}入力状態で整数の参照関数と一致します。{custom.cells}セル、{custom.die_um} µmのGDSで、DRCは{custom.drc_items}件、LVSは{custom.lvs_status}です。抽出後SPICEは{custom.analog_states}入力状態を通り、出力判定は{custom.analog_status}です。

生成したHDL、SPICE、GDSを保存すれば、次の三値回路の設計に再利用できます。
