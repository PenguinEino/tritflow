## 6. 2層の配線でGDSを完成させる

セル行の間に配線チャネルを設け、焼きなまし法で配線長を縮めてから格子上で接続します。M1の信号配線はチャネル内を横に通り、M2は障害物のない場所でセル上を縦に通ります。3本の電源には静的電流を運べる幅と給電点が必要です。

配置の図は加算器の桁ごとに色を分けています。完成後はPDKのDRCで図形ルールを調べ、LVSで抽出した素子と接続を合成ネットリストに照合します。ビューアでは拡大と移動ができ、直下のリンクから配線済みGDSを保存できます。

> **ここから分かること。** 図の{paper_adder.width}トリット加算器は{paper_adder.die_um} µmです。セル端子のHPWLは{paper_pnr.initial_hpwl_mm}から{paper_pnr.final_hpwl_mm} mmへ、{paper_pnr.hpwl_reduction_pct}%縮みました。DRCは{paper_adder.drc_items}件、LVSは{paper_adder.lvs_status}です。

このGDSから素子接続と配線形状を抽出し、次章の電気的な比較に使います。
