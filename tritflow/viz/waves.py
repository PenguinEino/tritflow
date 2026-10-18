"""Plotly voltage-band views of measured ternary transient and DC data.

Functions return Figure objects without opening a browser or selecting a global
renderer. Voltages remain volts, time is displayed in ns, source current in uA.
"""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tritflow import PASS_BAND, TRIT_VOLTS
from tritflow.sim.spice import signal_waveform


def _bands(fig, row=None):
    axes = {'row': row, 'col': 1} if row is not None else {}
    for trit, voltage in TRIT_VOLTS.items():
        fig.add_hrect(y0=voltage-PASS_BAND, y1=voltage+PASS_BAND,
                      fillcolor='#6eae89', opacity=.12, line_width=0, exclude_empty_subplots=False, **axes)
        fig.add_hline(y=voltage, line_width=.7, line_dash='dot', line_color='#89949b', exclude_empty_subplots=False, **axes)


def waveform_figure(result: dict, outputs=None, *, pre: dict | None = None,
                    title='Ternary transient', annotate_settling='worst') -> go.Figure:
    """Plot simulate() data, checkpoints and ideal bands; optionally overlay pre.

    result is the post-layout (or sole) simulate() result. The optional pre result
    shares its vectors and output names. Settling arrows run from ramp START to
    final band entry. annotate_settling is 'worst', 'all', or None; worst selects
    one transition per output to keep large vector sweeps legible.
    """
    if annotate_settling not in ('worst', 'all', None):
        raise ValueError("annotate_settling must be 'worst', 'all', or None")
    outputs = list(outputs if outputs is not None else result['stimulus']['outputs'])
    if not outputs:
        raise ValueError('Select at least one output')
    if pre is not None and (pre['stimulus']['vectors'] != result['stimulus']['vectors']
                            or pre['stimulus']['hold_s'] != result['stimulus']['hold_s']):
        raise ValueError('Pre/post overlays require identical vectors and hold times')
    fig = make_subplots(rows=len(outputs), cols=1, shared_xaxes=True,
                        vertical_spacing=min(.08, .3/len(outputs)), subplot_titles=outputs)
    rows = result.get('measurements', {}).get('rows', [])
    for index, pin in enumerate(outputs, 1):
        _bands(fig, index)
        if pre is not None:
            fig.add_trace(go.Scatter(x=pre['waveforms']['time']*1e9,
                y=signal_waveform(pre['waveforms'], pin), name=f'{pin}: pre-layout',
                mode='lines', line={'color':'#3478ad', 'dash':'dash', 'width':1.5}), row=index, col=1)
        fig.add_trace(go.Scatter(x=result['waveforms']['time']*1e9,
            y=signal_waveform(result['waveforms'], pin), name=f'{pin}: post-layout' if pre else pin,
            mode='lines', line={'color':'#bc5a22', 'width':1.7}), row=index, col=1)
        if rows:
            hold = result['stimulus']['hold_s']
            ideal = [r['outputs'][pin].get('ideal_voltage_v',r['outputs'][pin]['ideal_trit']*5) for r in rows]
            fig.add_trace(go.Scatter(x=np.arange(len(rows)+1)*hold*1e9,
                y=ideal+[ideal[-1]], name=f'{pin}: ideal', mode='lines',
                line={'color':'#566269', 'width':1, 'dash':'dot', 'shape':'hv'}), row=index, col=1)
            for passed, symbol, color in ((True,'circle','#198754'),(False,'x','#c43535')):
                selected = [r for r in rows if (r['outputs'][pin]['passed']
                            and r['outputs'][pin]['settling_s'] is not None) == passed]
                if selected:
                    fig.add_trace(go.Scatter(x=[r['check_s']*1e9 for r in selected],
                        y=[r['outputs'][pin]['voltage_v'] for r in selected], mode='markers',
                        name=f'{pin}: {"PASS" if passed else "FAIL"}',
                        marker={'symbol':symbol,'color':color,'size':8},
                        customdata=[[r['outputs'][pin]['error_v'],str(r['input_trits'])] for r in selected],
                        hovertemplate='check %{x:.3f} ns<br>%{y:.4f} V<br>error %{customdata[0]:.4f} V'
                                      '<br>input %{customdata[1]}<extra>%{fullData.name}</extra>'), row=index, col=1)
            candidates = [(k,r['outputs'][pin]) for k,r in enumerate(rows) if k and
                          r['outputs'][pin]['settling_s'] is not None]
            if annotate_settling == 'worst' and candidates:
                candidates = [max(candidates,key=lambda pair:pair[1]['settling_s'])]
            if annotate_settling:
                axis = '' if index == 1 else str(index)
                for k, measured in candidates:
                    start, delay = k*hold*1e9, measured['settling_s']*1e9
                    fig.add_annotation(x=start+delay, y=measured['ideal_trit']*5,
                        ax=start, ay=measured['ideal_trit']*5,
                        xref=f'x{axis}', yref=f'y{axis}', axref=f'x{axis}', ayref=f'y{axis}',
                        text=f'{delay:.2f} ns', showarrow=True, arrowhead=3,
                        bgcolor='rgba(255,255,255,.85)', font={'size':10})
        fig.update_yaxes(title_text='Voltage (V)', range=[-5.85,5.85], tickvals=[-5,0,5], row=index, col=1)
    fig.update_xaxes(title_text='Time (ns)', row=len(outputs), col=1)
    fig.update_layout(title=title, template='plotly_white', height=max(330,250*len(outputs)),
                      hovermode='x unified', legend={'orientation':'h'}, margin={'t':95})
    return fig


def transfer_figure(result: dict, input_pin: str, outputs, *, currents=('VDD',),
                    title='DC transfer and static rail current') -> go.Figure:
    """Plot dc_transfer() data with signed SPICE source current on a second axis."""
    data = result.get('data', result)
    x = signal_waveform(data, input_pin)
    fig = make_subplots(specs=[[{'secondary_y':True}]])
    _bands(fig)
    for pin in outputs:
        fig.add_trace(go.Scatter(x=x,y=signal_waveform(data, pin),name=f'V({pin})',mode='lines'), secondary_y=False)
    for rail in currents:
        fig.add_trace(go.Scatter(x=x,y=np.asarray(data[f'i({rail.lower()})'])*1e6,name=f'I({rail})',mode='lines',
                                line={'dash':'dash'}), secondary_y=True)
    fig.update_xaxes(title_text=f'V({input_pin}) (V)')
    fig.update_yaxes(title_text='Output voltage (V)',range=[-5.85,5.85],secondary_y=False)
    fig.update_yaxes(title_text='Static source current (µA)',secondary_y=True)
    fig.update_layout(title=title,template='plotly_white',hovermode='x unified',height=450)
    return fig


# Short notebook-facing names match the existing gate_graph/layout helpers.
waveform_plot = waveform_figure
dc_transfer_plot = transfer_figure
