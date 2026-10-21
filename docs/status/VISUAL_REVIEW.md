# VISUAL_REVIEW

更新：2026-10-22 JST。作業場所：`~/code-a-chip-look`、開始時HEAD：`89a19bfa20ebb5b91457c05f6fd84ecd9df0450e`。

## 完了した範囲

現在のv2生成器に含まれる冒頭・1章・2章・3章の全セルを実行し、幅1100px・700pxで確認した。変更ごとに描画し直して画像を開き、最後に全章の35枚と操作後の27枚を確認した。4〜7章と付録は、このworktreeのv2には本文もコードセルもまだないため、確認対象を作れない。全Notebookの提出可否を承認するものではない。

変更は許可された表示コードと生成SVGのみ。本文、HDL、合成・配置配線・抽出・シミュレーション、`tritflow/`、記録済み結果、他worktree、PDK、元回路は変更していない。追加パッケージなし。commit・pushなし。開始時から未追跡だった `briefs/VISUAL_REVIEW.md` はそのまま。

## 章ごとの確認と判断

### 冒頭

- 確認画像：`build/visual-review/before/ch0-{1100,700}-*.png`、最終 `build/visual-review/final/ch0-{1100,700}-*.png`。準備セルのコードも展開して確認した。
- 見出しと本文の折り返し、図1の全体の配置には重なりがない。図1のゲート名と注記は700pxでは小さい。図そのものを作る `figures/` は今回の編集許可範囲外なので、FIGURES／integratorへの依頼とした。
- 本文の修正候補：再利用性の末尾が「7・8章」だが、現行STORYBOARDでは自作回路は6章、提出物と測定計画は7章。再現性の「1〜6章」も含め、新章立てとの参照をEDITORが確認すること。

### 1章：最初の回路

- 確認画像：`build/visual-review/final/ch1-{1100,700}-*.png`。入力変更後：`build/visual-review/interactive/pick-{1100,700}-{0,1,2}-00.png`。
- 小さな回路図、真理値表、3段の波形は読める。700pxでは回路図の下に真理値表が移り、本文の外へはみ出さない。
- 波形のPlotlyモードバーを隠し、操作アイコンと軸の混雑を解消した。範囲スライダー、ドラッグ、ダブルクリックによる操作は残した。
- 入力−1／0／+1の全ボタンについて、回路図の配線色、真理値表の選択行、出力電圧の表示、波形の強調区間が一致することをブラウザ上で検証した。
- ラジオボタンは見た目を保ったままキーボード操作可能にし、フォーカス位置を墨色の細い枠で示した。
- 残る表示問題：GDSビューアの黒背景、サンセリフの操作欄、英語の状態表示、密集した電源ラベル。`tritflow/viz/` 側の実装なので変更していない。静的フォールバックでズームとFitが実際に表示範囲を変えることは確認した。末尾のフロー図も700pxでは内部注記が細かい（FIGURESへの依頼）。

### 2章：セル

- 確認画像：`build/visual-review/final/ch2-{1100,700}-*.png`。変更途中の比較：`build/visual-review/layout/`、`build/visual-review/layout-final/`。
- INVの静的回路図では、W/Lの注記が約10pxと小さかった。`make_tables.py` のXschem出力処理で約12pxに拡大し、Lの行を下げて重なりを防いだ。文字列と寸法値はそのまま。
- INVの動作点表とグラフのグリッドに `minmax(0, 1fr)` と `min-width:0` を指定し、Plotlyの内部幅による押し出しを防いだ。700pxでは動作点表を中央に置き、2枚のグラフのモードバーを隠した。
- セルの真理値表を同じ幅のグリッドにそろえた。開いたXschem回路図は狭い出力でも収まる列定義にし、最大幅を540pxに制限して中央配置した。折りたたみを開いても表の列は変わらない。
- スタンダードセルは、全体を縮小する2枚のSVGから、共通縮尺で折り返すセルごとのSVGへ変更した。1100pxではINV・NAND・NOR・NANYが一列、700pxでは2個ずつ並ぶ。名前14px、幅12px、電源レール11px。実際の形状、素子の囲み、寸法、縮尺の比較は維持した。
- 書体の候補に `Noto Serif CJK JP` を追加し、Linuxの日本語明朝フォントを明示した。墨色と三値の配色は変更していない。
- 操作後画像：`build/visual-review/interactive/inv-*.png`。3入力、90候補すべてのマスタースライダー、MP幅・MN幅・MOS長・抵抗長の4スライダーを操作し、表の寸法、曲線、動作点、誤差と電流の選択点が更新されることを確認した。
- 本文の修正候補：2.1の「90通り」は実行結果の重複であり、STORYBOARDの「本文の数字はセルの出力として見せる」と照合してEDITORが扱いを決めること。本文は変更していない。

### 3章：HDLと論理合成

- 確認画像：`build/visual-review/before/ch3-{1100,700}-*.png`、`build/visual-review/final/ch3-{1100,700}-*.png`。
- 構文一覧は元の1020px幅では、700pxで文字が約11pxに縮み、条件演算子の説明が隣の列へ重なった。640px幅・本文16px・コード13pxの表にし、行ごとの高さと折り返しを導入した。英数字の語は途中で分断しない。booktabsの3本の罫線を維持した。
- セル数の比較表は左右の余白を調整し、各セルを折り返さないようにした。700pxでも「全9入力で一致」が一行に収まる。さらに狭い場合は表の中だけ横スクロールする。
- 全加算器のゲート名は700pxで約8pxまで小さくなっていた。表示呼び出しを `schematic_view(...)` で包み、1000pxの描画幅を保って横スクロールできるようにした。狭い出力にだけ案内を表示する。左端・右端の両方を実際に操作して確認した。画像：`build/visual-review/interactive/full-adder-*.png`、`counts-*.png`。
- 既知の担当外エラーは再現した。3-5：`No clear schematic channel for 's[0]' at (1024, 960)`。3-7：`No clear schematic channel for '_n17' at (1120, 1504)`。長いトレースバックも確認画像に残しており、隠したり例題を差し替えたりしていない。
- 3-5の実際のadd2操作画面は、このエラーで生成されない。`bus_picker` 自体の操作は、一時的な2トリットINVの実ネットリストで−4〜+4の9通りを検証した。整数表示と配線色が変わることを確認したが、add2の回路図を検証済みとは扱わない。画像：`build/visual-review/interactive/bus-*.png`。
- 本文の修正候補：特になし。ラッチの説明例の診断文は英語のままなので、最終日本語版で統一するならFRONTENDに依頼すること。

### 4〜7章・付録

`make_notebook.py` の `CHAPTERS` は4ファイルだけで、これらの章は生成されない。旧Notebookを代わりに確認したことにはしない。章が統合された時点で、同じ幅と操作条件で追加レビューが必要。

## 検証結果

- `python3 -m pytest tests/viz -q`：**79 passed**。
- nbclientで17個のコードセルすべてを実行。例外は上記3-5と3-7のみ。1章の配置配線、DRC、LVS、抽出、SPICE、2章のDC解析と寸法記録の照合も実行した。
- 4枚の表SVGについて、変更前後の全 `<text>` の内容をXMLから比較し、文字列と数値が完全一致することを確認した。
- 全8ページの画像がローカルで読み込め、折りたたみがすべて開き、Plotlyが初期化済みで、ページ全体に横方向のはみ出しがないことを確認した。回路図と比較表の必要なスクロールは局所的。
- 操作検証の詳細は `build/visual-review/interactive/results.json`。最終ページの検査結果は `build/visual-review/final/metadata.json`。
- 実行時に表示された環境：Python 3.12、KLayout 0.30.9、ngspice 42、NumPy 2.4.3、SciPy 1.17.1、Plotly 7.1.0。PDKは指定どおり `~/pdk/TR-1um-pinned`。契約文のツール版（KLayout 0.30.6／ngspice 46）とは差があるので、ここでの結果は視覚確認の記録であり、実行環境の凍結証拠の更新には使わない。

## 再実行方法と成果物

```sh
mkdir -p build/v2 build/visual-review
python3 notebook/v2/make_tables.py
python3 notebook/v2/make_notebook.py --out build/v2/local.ipynb
python3 build/visual-review/execute.py
python3 build/visual-review/render.py
python3 build/visual-review/interactive.py
python3 build/visual-review/final_capture.py
python3 -m pytest tests/viz -q
```

`execute.py` は `TR1UM_PDK` と `TRITFLOW_ROOT` を指定し、python3カーネル・cwd `build/v2`・既知エラーを保存する `allow_errors=True` で実行する。実行済みNotebookは `build/visual-review/executed.ipynb`。

`build/visual-review/chapter-{0,1,2,3}.html` はmarkdown-itのHTML・表を有効にして、コードを灰色の枠、出力を元の順序で描画する。リモート画像URLはローカルの資産に置換し、Plotlyもインストール済みのJSを使う。TeXはレビュー用にローカルのmathtextで描画したため、ColabのMathJaxと厳密には同じではない。Colabへのログイン・公開・ネットワークサービスは利用していない。

ChromeのCDPを標準ライブラリだけで操作して実寸の画像を取得し、長いページは重複する1500px以下の断片に切って確認した。1100px／700pxは指定したビューポート幅で、通常の縦スクロールバー分だけ出力画像が狭くなる場合がある。生画像は各 `raw/`、確認用の断片は `final/` と `interactive/` 直下。これらと再実行スクリプトはgit管理外の `build/` に置いた。

## Interface requests

1. **SCHEM_ROUTE**：3-5／3-7の配線エラーを修正し、実際のadd2とcase乗算器の描画を再確認する。修正後の複雑な図にも今回の `schematic_view` と同様の文字サイズの扱いが必要か確認すること。
2. **PNR／integrator**：`gds_viewer(..., theme="paper")` 相当の白背景対応を公開APIに追加する。画像・canvas背景・文字・スケール・操作欄を一緒に切り替え、墨色と明朝系の操作欄にそろえる必要がある。CSSの反転フィルターではPDKの色まで変わるため採用しなかった。電源名の密集も同時に確認すること。
3. **FIGURES／integrator**：図1と1章末尾のフロー図について、700px表示でゲート名と細かな注記を読める拡大版または分割版を用意する。元図・本文の編集は今回の担当外。
4. **EDITOR／integrator**：上記の旧章番号と本文中の実行結果の重複を整理する。4〜7章と付録の統合後に追加の視覚確認を行う。
