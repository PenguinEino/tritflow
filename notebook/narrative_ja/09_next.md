## 9. GDSからシリコンとの比較へ

元のセルを載せたチップは{history.delivery_month_ja}に届く予定で、まだ実測していません。採択された場合は、{history.isscc_dates_ja}のISSCCポスターで、このセルの最初の実測結果とノートブックの予測を並べる計画です。

まずDC入力掃引で伝達特性と全電源の静的電流を測ります。次に入力エッジと負荷を記録して各レベル間の整定時間を測り、同じ条件のSPICEと比べます。電源電圧、温度、パッド・パッケージ・測定器の容量も記録します。

### シャトル向けトップの生成

配線済みコアにフレームと端子を加えるには、`layout.result.to_chip()`と、返されたチップの`signoff()`を使います。下のビューアとダウンロードは、図と同じ加算器をMPWのTEGフレームへ入れたGDSです。

```python
chip = layout.result.to_chip()
checks = chip.signoff()
chip.gds_path
```

> **ここから分かること。** 保存済みトップは{chip.die_um} µm、{chip.pad_count}パッドです。描画GDSのDRCは{chip.drawing_drc_items}件、厳密な端子照合を含むLVSは{chip.lvs_status}、マスク処理後のDRCは{chip.mask_drc_items}件、MPW事前チェックは{chip.precheck_status}です。

このトップの`submission_ready`は`{chip.submission_ready}`です。実際の提出には領域の割当、パッド・ボンド図、電源・基板接続、プロセスとESDの承認、シャトル側のCIが残ります。受動パッドにはESD回路がありません。条件と残作業は付録A/Bにまとめています。

ここまでに作った配線済みGDSとライブラリは、別のHDLでも使えます。付録Cにはローカル実行と拡張の手順を載せています。
