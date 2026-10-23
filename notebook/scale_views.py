"""Recorded dot-product scaling for chapter 6; views never run physical tools.

``data = load_scaling()`` verifies the portable publication. Only an explicit
``load_scaling(recompute=True)`` starts the producer. Tables return IPython HTML
objects; figures return Plotly figures, so callers choose their display order.
"""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
import sys

from IPython.display import HTML

from live import _text
from style import ACCENT, INK, MUTED, TRIT_COLOR, figure_css, paper_axes, paper_layout, table_css

ROOT = Path(__file__).resolve().parents[1]

LABELS_EN = {
    "積和の記録が未完了、または計算条件が変更されている。": "The dot-product record is incomplete or its calculation conditions have changed.",
    "項数 N": "Terms N", "セル数": "Cells", "ダイ寸法<small>mm × mm</small>": "Die size<small>mm × mm</small>",
    "ダイ面積<small>mm²</small>": "Die area<small>mm²</small>", "行数": "Rows",
    "実配線長<small>mm</small>": "Routed length<small>mm</small>", "信号ビア": "Signal vias",
    "配置配線<small>s</small>": "Place and route<small>s</small>", "積和の規模と配置配線": "Dot-product size and place and route",
    "出力桁数": "Output trits", "検証入力数": "Input vectors checked", "等価性": "Equivalence",
    "全入力": "Exhaustive", "乱数": "Random", "未検証": "Unchecked", "等価": "Equivalent",
    "一致": "Matched", "不一致": "Mismatch", "積和の論理合成": "Dot-product logic synthesis",
    "未完了": "Incomplete", "計算中": "Running", "未実施": "Not run", "合格": "Pass", "不合格": "Fail",
    "出力": "Output", "STAの誤差<small>%</small>": "STA error<small>%</small>",
    "STAとポストレイアウトSPICE": "STA and post-layout SPICE",
    "|I(VDD)|<small>mA・x=0</small>": "|I(VDD)|<small>mA · x=0</small>",
    "|I(VSS)|<small>mA・x=0</small>": "|I(VSS)|<small>mA · x=0</small>",
    "静的電力<small>mW・x=0</small>": "Static power<small>mW · x=0</small>",
    "時間平均<small>mW</small>": "Time average<small>mW</small>",
    "静的/セル<small>mW・x=0</small>": "Static/cell<small>mW · x=0</small>",
    "平均/セル<small>mW</small>": "Average/cell<small>mW</small>",
    "DCの範囲<small>mW</small>": "DC range<small>mW</small>", "保持時間<small>µs/区間</small>": "Hold time<small>µs/interval</small>",
    "積和の静的電流と電力": "Dot-product static current and power",
    "STA・配線容量なし<small>ns</small>": "STA, no wire C<small>ns</small>",
    "STA・配線容量あり<small>ns</small>": "STA, with wire C<small>ns</small>",
    "SPICE・配線容量なし<small>ns</small>": "SPICE, no wire C<small>ns</small>",
    "SPICE・配線容量あり<small>ns</small>": "SPICE, with wire C<small>ns</small>",
    "増加率<small>%</small>": "Increase<small>%</small>", "配線容量による整定時間の増加": "Settling-time increase from wire capacitance",
    "ダイ面積": "Die area", "STA（配線容量あり）": "STA (with wire C)", "STA（配線容量なし）": "STA (no wire C)",
    "積和の項数 N": "Dot-product terms N", "ダイ面積 (mm²)": "Die area (mm²)",
    "最大整定時間 (ns)": "Max. settling time (ns)", "測定した入力状態の範囲": "Observed DC state range",
    "x=0（重み固定）": "x=0 (fixed weights)", "時間平均（11区間）": "Time average (11 intervals)",
    "静的電力 (mW)": "Static power (mW)",
    "N=%{x}<br>最大 %{y:.2f} mW<extra></extra>": "N=%{x}<br>Max. %{y:.2f} mW<extra></extra>",
    "seed 0。HPWLは配置後のセル端子間の見積もり。実配線長とビア数は信号配線のみ。配置配線時間はPDKのDRCを含み、LVSを含まない。DRC欄は違反件数。":
        "Seed 0. HPWL estimates wire length between placed cell terminals. Routed length and vias cover signal routing only. Place and route time includes PDK DRC and excludes LVS. DRC reports violation counts.",
    "重みと入力は各1トリット。乱数検証はseed 0。出力桁数は−N〜+Nを表す最小値。":
        "Weights and inputs are one trit each. Random equivalence checks use seed 0. Output width is the minimum needed for −N through +N.",
    "誤差 = (STA / SPICE − 1) × 100。初期状態を除く同じ10組の入力遷移について出力別の最大整定時間を比較する。STAはこの入力列に対する推定であり、全入力遷移の上界ではない。":
        "Error = (STA / SPICE − 1) × 100. Each output's maximum settling time uses the same 10 input transitions, excluding the initial state. STA estimates this sequence; it is not an upper bound over all input transitions.",
    "P = −Σ(Vrail × Irail)。電源は+5 / 0 / −5 V、IrailはSPICEの電圧源に流れ込む向きを正とする。静的電力とDCの範囲は独立した動作点解析。時間平均は11区間の供給電力波形の積分から求める。入力駆動源の電力は含めず、スイッチング分のエネルギーは分離していない。":
        "P = −Σ(Vrail × Irail), with +5 / 0 / −5 V supplies and Irail positive into each SPICE voltage source. Static power and the DC range use separate operating-point analyses. Time-average power integrates supply power over 11 intervals. Input-source power is excluded; switching-only energy is not separated.",
    "同じ入力遷移の集合について出力別の最大整定時間を比較する。STAの誤差 = (STA / SPICE − 1) × 100（ともに配線容量あり）。素子の寄生容量と100 fFの出力負荷は両方に含む。SPICEで配線容量を除く比較はN=4のみ。配線容量は形状からの推定値である。":
        "Each output's maximum settling time uses the same input transitions. STA error = (STA / SPICE − 1) × 100, with wire C in both. Both cases include intrinsic device capacitance and the 100 fF output load. The SPICE comparison without wire C is available only for N=4. Wire capacitance is estimated from geometry.",
}


def _label(text):
    """Translate presentation labels, leaving recorded identifiers and numbers unchanged."""
    return _text(text, LABELS_EN.get(text, text))


def load_scaling(path=None, *, recompute=False, sizes=(2, 4, 8, 16, 32)):
    """Load source-checked evidence, or explicitly recompute the costly campaign."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from examples.dot_scaling import RESULT, run_scaling, verify_record

    data = run_scaling(sizes, result=Path(path or RESULT)) if recompute else json.loads(Path(path or RESULT).read_text())
    if data.get("schema_version") != 1 or not data.get("complete") or data.get("stale"):
        raise ValueError(_label("積和の記録が未完了、または計算条件が変更されている。"))
    return verify_record(data)


def _number(value, scale=1., precision=2):
    return "—" if value is None else f"{value * scale:,.{precision}f}"


def _rows(data):
    return sorted(data["rows"], key=lambda row: row["n"])


def _table(headings, rows, note, *, label):
    """Booktabs HTML follows notebook/style.py and scrolls within narrow outputs."""
    scope = ".tfscale"
    css = (figure_css(scope) + table_css(scope) +
           ".tfscale{max-width:100%;overflow-x:auto;padding:4px 0 8px}"
           ".tfscale th,.tfscale td{white-space:nowrap}"
           f".tfscale p{{font-size:12px;color:{MUTED};margin:.55em 0 0;max-width:1000px}}")
    header = "".join(f"<th>{_label(title)}</th>" for title in headings)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>" for row in rows)
    return HTML(f'<style>{css}</style><div class="tfscale" role="group" aria-label="{escape(_label(label))}">'
                f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table><p>{escape(_label(note))}</p></div>")


def scaling_table(data):
    """Die area and actual route cost for each recorded seed-0 dot product."""
    rows = []
    for row in _rows(data):
        pnr = row.get("pnr", {})
        stats = pnr.get("stats", {})
        die = stats.get("die_size_um")
        wire = stats.get("wirelength_um", {})
        drc = pnr.get("drc", {}).get("violations")
        lvs = row.get("lvs", {}).get("matched")
        rows.append([row["n"], row.get("synthesis", {}).get("total_cells", "—"),
                     " × ".join(_number(v, 1e-3) for v in die) if die else "—",
                     _number(stats.get("die_area_um2"), 1e-6), stats.get("row_count", "—"),
                     _number(stats.get("hpwl_after_um"), 1e-3),
                     _number(sum(wire.values()), 1e-3) if wire else "—",
                     stats.get("via_count", "—"), _number(stats.get("runtime_s", {}).get("total")),
                     f"{drc} / {_label('一致') if lvs else _label('不一致') if lvs is False else '—'}" if drc is not None else "—"])
    return _table(["項数 N", "セル数", "ダイ寸法<small>mm × mm</small>", "ダイ面積<small>mm²</small>", "行数",
                   "HPWL<small>mm</small>", "実配線長<small>mm</small>", "信号ビア", "配置配線<small>s</small>", "DRC / LVS"], rows,
                  "seed 0。HPWLは配置後のセル端子間の見積もり。実配線長とビア数は信号配線のみ。"
                  "配置配線時間はPDKのDRCを含み、LVSを含まない。DRC欄は違反件数。", label="積和の規模と配置配線")


def synthesis_table(data):
    """Cell mix and the actual exhaustive/random synthesis equivalence scope."""
    names = sorted({name for row in _rows(data) for name in row.get("synthesis", {}).get("cells", {})})
    rows = []
    for row in _rows(data):
        synth = row.get("synthesis", {})
        eq = synth.get("equivalence") or {}
        mode = _label({"exhaustive": "全入力", "random": "乱数"}.get(eq.get("mode"), "未検証"))
        result = _label("等価") if eq.get("passed") else _label("不一致") if eq.get("passed") is False else "—"
        rows.append([row["n"], row.get("output_trits", "—"), *[synth.get("cells", {}).get(name, 0) for name in names],
                     f"{mode} {eq.get('vectors', 0):,}", result])
    return _table(["項数 N", "出力桁数", *[escape(name) for name in names], "検証入力数", "等価性"], rows,
                  "重みと入力は各1トリット。乱数検証はseed 0。出力桁数は−N〜+Nを表す最小値。", label="積和の論理合成")


def timing_table(data):
    """Per-output worst settling on identical complete primary-input pairs."""
    rows = []
    for row in _rows(data):
        comparisons = row.get("timing_comparison", [])
        if not comparisons:
            status = _label({"failed": "未完了", "running": "計算中"}.get(row.get("state"), "未実施"))
            rows.append([row["n"], "—", "—", "—", "—", status])
        for comparison in comparisons:
            passed = comparison.get("passed")
            rows.append([row["n"], comparison["output"], _number(comparison["sta_s"], 1e9, 1),
                         _number(comparison["spice_s"], 1e9, 1), _number(comparison["signed_error_percent"], precision=1),
                         _label("合格") if passed else _label("不合格") if passed is False else _label("未実施")])
    return _table(["項数 N", "出力", "STA<small>ns</small>", "SPICE<small>ns</small>", "STAの誤差<small>%</small>", "±0.5 V"], rows,
                  "誤差 = (STA / SPICE − 1) × 100。初期状態を除く同じ10組の入力遷移について出力別の最大整定時間を比較する。"
                  "STAはこの入力列に対する推定であり、全入力遷移の上界ではない。", label="STAとポストレイアウトSPICE")


def power_table(data):
    """Zero-activation DC power and measured unique-state spread, per mapped cell."""
    rows = []
    for row in _rows(data):
        power = row.get("power", {})
        zero = power.get("zero", {})
        currents = zero.get("rail_current_a", {})
        average = (power.get("sequence") or {}).get("average_supply_power_w")
        rows.append([row["n"], row.get("synthesis", {}).get("total_cells", "—"),
                     _number(abs(currents["VDD"]) if "VDD" in currents else None, 1e3),
                     _number(abs(currents["VSS"]) if "VSS" in currents else None, 1e3),
                     _number(zero.get("static_power_w"), 1e3), _number(average, 1e3),
                     _number(zero.get("power_per_cell_w"), 1e3, 3),
                     _number(power.get("sequence_average_per_cell_w"), 1e3, 3),
                     f"{_number(power.get('minimum_w'), 1e3)}–{_number(power.get('maximum_w'), 1e3)}",
                     _number(row["conditions"]["hold_s"], 1e6)])
    return _table(["項数 N", "セル数", "|I(VDD)|<small>mA・x=0</small>", "|I(VSS)|<small>mA・x=0</small>",
                   "静的電力<small>mW・x=0</small>", "時間平均<small>mW</small>",
                   "静的/セル<small>mW・x=0</small>", "平均/セル<small>mW</small>",
                   "DCの範囲<small>mW</small>", "保持時間<small>µs/区間</small>"], rows,
                  "P = −Σ(Vrail × Irail)。電源は+5 / 0 / −5 V、IrailはSPICEの電圧源に流れ込む向きを正とする。"
                  "静的電力とDCの範囲は独立した動作点解析。時間平均は11区間の供給電力波形の積分から求める。"
                  "入力駆動源の電力は含めず、スイッチング分のエネルギーは分離していない。", label="積和の静的電流と電力")


def layout_penalty_table(data):
    """Wire-C penalty and matched STA error with identical devices and test loads."""
    rows = []
    for row in _rows(data):
        comparisons = {item["output"]: item for item in row.get("timing_comparison", [])}
        for item in row.get("layout_penalty", []):
            sta, spice = item["sta"], item["spice"]
            rows.append([row["n"], item["output"], _number(sta["device_only_s"], 1e9, 1),
                         _number(sta["wire_c_s"], 1e9, 1), _number(sta["increase_percent"], precision=1),
                         _number(spice["device_only_s"], 1e9, 1), _number(spice["wire_c_s"], 1e9, 1),
                         _number(spice["increase_percent"], precision=1),
                         _number(comparisons.get(item["output"], {}).get("signed_error_percent"), precision=1)])
    return _table(["N", "出力", "STA・配線容量なし<small>ns</small>", "STA・配線容量あり<small>ns</small>",
                   "増加率<small>%</small>", "SPICE・配線容量なし<small>ns</small>", "SPICE・配線容量あり<small>ns</small>",
                   "増加率<small>%</small>", "STAの誤差<small>%</small>"], rows,
                  "同じ入力遷移の集合について出力別の最大整定時間を比較する。"
                  "STAの誤差 = (STA / SPICE − 1) × 100（ともに配線容量あり）。素子の寄生容量と100 fFの出力負荷は両方に含む。"
                  "SPICEで配線容量を除く比較はN=4のみ。配線容量は形状からの推定値である。", label="配線容量による整定時間の増加")


def _maximum(row, field):
    values = [item[field] for item in row.get("timing_comparison", [])]
    return max(values) if values and all(value is not None for value in values) else None


def scaling_figure(data):
    """Measured die area and matched-set maximum output delay, against term count."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    rows = _rows(data)
    sizes = [row["n"] for row in rows]
    figure = make_subplots(rows=1, cols=2, horizontal_spacing=.16)
    area = [row.get("pnr", {}).get("stats", {}).get("die_area_um2") for row in rows]
    figure.add_trace(go.Scatter(x=sizes, y=[v * 1e-6 if v is not None else None for v in area], mode="lines+markers",
                                line={"color": INK, "width": 2}, marker={"size": 7}, name=_label("ダイ面積"), showlegend=False,
                                hovertemplate="N=%{x}<br>%{y:.3f} mm²<extra></extra>"), row=1, col=1)
    for field, name, color, symbol, dash in (("sta_s", _label("STA（配線容量あり）"), ACCENT, "square-open", "dash"),
                                            ("spice_s", "SPICE", TRIT_COLOR[-1], "circle", "solid")):
        values = [_maximum(row, field) for row in rows]
        figure.add_trace(go.Scatter(x=sizes, y=[v * 1e9 if v is not None else None for v in values],
                                    mode="lines+markers", name=name, connectgaps=False,
                                    line={"color": color, "width": 2, "dash": dash},
                                    marker={"size": 8, "symbol": symbol},
                                    hovertemplate="N=%{x}<br>%{y:.1f} ns<extra>" + name + "</extra>"), row=1, col=2)
    pre = [max(row["sta_device_only"]["arrival"].values()) * 1e9 if row.get("sta_device_only") else None for row in rows]
    figure.add_trace(go.Scatter(x=sizes, y=pre, mode="lines+markers", name=_label("STA（配線容量なし）"),
                                line={"color": MUTED, "width": 2, "dash": "dot"}, marker={"symbol": "triangle-up-open", "size": 8}), row=1, col=2)
    paper_axes(figure)
    figure.update_xaxes(type="log", tickvals=sizes, ticktext=[str(n) for n in sizes], title_text=_label("積和の項数 N"))
    figure.update_yaxes(title_text=_label("ダイ面積 (mm²)"), rangemode="tozero", row=1, col=1)
    figure.update_yaxes(title_text=_label("最大整定時間 (ns)"), rangemode="tozero", row=1, col=2)
    figure.update_layout(**paper_layout(height=370, width=940,
                                        margin={"t": 45, "b": 55, "l": 62, "r": 22},
                                        legend={"orientation": "h", "x": 0, "y": 1.15, "font": {"size": 13}}))
    return figure


def power_figure(data):
    """State-dependent static draw; the filled interval is an observed spread."""
    import plotly.graph_objects as go

    rows = _rows(data)
    sizes = [row["n"] for row in rows]
    powers = [row.get("power", {}) for row in rows]

    def values(key):
        return [p[key] * 1e3 if p.get(key) is not None else None for p in powers]

    figure = go.Figure()
    figure.add_trace(go.Scatter(x=sizes, y=values("minimum_w"), mode="lines", line={"width": 0},
                                showlegend=False, hoverinfo="skip"))
    figure.add_trace(go.Scatter(x=sizes, y=values("maximum_w"), mode="lines", line={"width": 0},
                                fill="tonexty", fillcolor="rgba(235,104,52,.16)", name=_label("測定した入力状態の範囲"),
                                hovertemplate=_label("N=%{x}<br>最大 %{y:.2f} mW<extra></extra>")))
    figure.add_trace(go.Scatter(x=sizes, y=[p.get("zero", {}).get("static_power_w", 0) * 1e3
                                          if p.get("zero") else None for p in powers], mode="lines+markers",
                                line={"color": INK, "width": 2}, marker={"size": 7}, name=_label("x=0（重み固定）"),
                                hovertemplate="N=%{x}<br>%{y:.2f} mW<extra></extra>"))
    averages = [(p.get("sequence") or {}).get("average_supply_power_w") for p in powers]
    figure.add_trace(go.Scatter(x=sizes, y=[v * 1e3 if v is not None else None for v in averages],
                                mode="lines+markers", name=_label("時間平均（11区間）"),
                                line={"color": TRIT_COLOR[-1], "width": 2, "dash": "dash"},
                                marker={"symbol": "square-open", "size": 7}))
    figure.update_layout(**paper_layout(height=410, width=700,
                                        legend={"orientation": "h", "x": 0, "y": -.3, "yanchor": "top"},
                                        margin={"t": 25, "b": 120, "l": 62, "r": 22}))
    figure.update_xaxes(type="log", tickvals=sizes, ticktext=[str(n) for n in sizes], title_text=_label("積和の項数 N"))
    figure.update_yaxes(title_text=_label("静的電力 (mW)"), rangemode="tozero")
    return figure


def render_views(data, directory=None):
    """Render every public view with headless Chrome; no simulation is launched."""
    import shutil
    import subprocess
    from examples.dot_scaling import COMPANIONS

    directory = Path(directory or COMPANIONS).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        raise RuntimeError("Headless Chrome is required to inspect the chapter-6 views")
    outputs = []
    for name, view in (("scaling_table", scaling_table), ("synthesis_table", synthesis_table),
                       ("timing_table", timing_table), ("power_table", power_table), ("layout_penalty_table", layout_penalty_table),
                       ("scaling_figure", scaling_figure), ("power_figure", power_figure)):
        rendered = view(data)
        is_table = isinstance(rendered, HTML)
        body = rendered.data if is_table else rendered.to_html(full_html=False, include_plotlyjs=True,
                                                              config={"displayModeBar": False, "responsive": False})
        html = directory / f"{name}.html"
        html.write_text(f'<!doctype html><html lang="{_text("ja", "en")}"><meta charset="utf-8">'
                        '<style>body{margin:24px;background:#fff}*{box-sizing:border-box}</style>' + body)
        png = directory / f"{name}.png"
        height = 680 if name in {"timing_table", "layout_penalty_table"} else 450 if not is_table else 340
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                        "--hide-scrollbars", "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
                        "--virtual-time-budget=5000", "--force-device-scale-factor=1.5",
                        f"--user-data-dir={directory / 'chrome-profile'}", f"--window-size=1200,{height}",
                        f"--screenshot={png}", html.as_uri()], capture_output=True, check=True, timeout=60)
        outputs.append(png)
    return outputs


if __name__ == "__main__":
    print("\n".join(str(path) for path in render_views(load_scaling())))
