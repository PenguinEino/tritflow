"""Plotly figures for notebook chapter 7; all axes show physical units."""
from __future__ import annotations

import json
from pathlib import Path


def timing_figure(report):
    """Cell contributions along the critical, logically sensitized path."""
    import plotly.graph_objects as go
    path = report.critical_path
    figure = go.Figure(go.Bar(x=[s.instance for s in path], y=[s.delay_s*1e9 for s in path],
        customdata=[[s.cell, s.input_pin, s.transition, s.load_f*1e15, s.arrival_s*1e9] for s in path],
        hovertemplate="%{x}: %{customdata[0]}.%{customdata[1]}<br>Output %{customdata[2]}"
                      "<br>Load %{customdata[3]:.1f} fF<br>Arrival %{customdata[4]:.2f} ns<extra></extra>"))
    if path and path[-1].settling_tail_s:
        figure.add_bar(x=['Endpoint settling tail'],y=[path[-1].settling_tail_s*1e9],name='Endpoint tail')
    figure.update_layout(title=f"{report.top}: critical path to {report.critical_output}",
                         xaxis_title="Cell instance", yaxis_title="Timing contribution (ns)", template="plotly_white")
    return figure


def validation_figure(validation=None):
    """Predicted versus observed maxima; distinguish all-pair and tested-pattern STA.

    Error envelopes are empirical observations on this finite nominal dataset,
    not confidence intervals or promises for untested circuits.
    """
    import plotly.graph_objects as go
    if validation is None:
        from tritflow import ROOT
        validation = ROOT / "results/sta/validation.json"
    if isinstance(validation, (str, Path)): validation = json.loads(Path(validation).read_text())
    rows = [row for design in validation["designs"] for row in design.get("outputs", [])
            if row.get("simulated_s") is not None]
    figure = go.Figure()
    for field, label, symbol in (("predicted_s", "Global graph, fixed ramp", "circle"),
                                  ("tested_predicted_s", "SIM endpoint pairs, propagated slew", "diamond")):
        figure.add_scatter(x=[r["simulated_s"]*1e9 for r in rows], y=[r[field]*1e9 for r in rows],
            mode="markers", name=label, marker_symbol=symbol,
            text=[f"{r['design']}: {r['output']}" for r in rows],
            hovertemplate="%{text}<br>SPICE %{x:.2f} ns<br>STA %{y:.2f} ns<extra>%{fullData.name}</extra>")
    maximum = max([r[k]*1e9 for r in rows for k in ("simulated_s", "predicted_s", "tested_predicted_s")], default=1)
    figure.add_scatter(x=[0, maximum], y=[0, maximum], mode="lines", line=dict(dash="dash", color="gray"), name="Equality")
    figure.add_scatter(x=[0,maximum],y=[0,maximum*.8],mode='lines',line=dict(dash='dot',color='lightgray'),name='−20%')
    figure.add_scatter(x=[0,maximum],y=[0,maximum*1.2],mode='lines',line=dict(dash='dot',color='lightgray'),name='+20%')
    figure.update_layout(title="Nominal ternary settling: STA and post-layout SPICE",
        xaxis_title="Observed worst settling in SIM sequence (ns)", yaxis_title="Analytical settling estimate (ns)",
        template="plotly_white", meta={"scope": validation.get("scope"), "statistics": validation.get("statistics")})
    return figure
