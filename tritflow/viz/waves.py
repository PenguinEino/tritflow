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


def _bands(fig, row=None, levels=None):
    axes = {'row': row, 'col': 1} if row is not None else {}
    for voltage in (TRIT_VOLTS if levels is None else levels).values():
        fig.add_hrect(y0=voltage-PASS_BAND, y1=voltage+PASS_BAND,
                      fillcolor='#6eae89', opacity=.12, line_width=0, exclude_empty_subplots=False, **axes)
        fig.add_hline(y=voltage, line_width=.7, line_dash='dot', line_color='#89949b', exclude_empty_subplots=False, **axes)


def waveform_figure(result: dict, outputs=None, *, pre: dict | None = None,
                    title='Ternary transient', annotate_settling='worst',
                    pre_label='pre-layout',post_label='post-layout') -> go.Figure:
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
    levels = result.get('measurements',{}).get('ideal_volts')
    if levels is None:
        supplies=result['stimulus'].get('supplies_v',{'VDD':5.,'VMID':0.,'VSS':-5.})
        levels={-1:supplies['VSS'],0:supplies['VMID'],1:supplies['VDD']}
    voltages=sorted(levels.values())
    for index, pin in enumerate(outputs, 1):
        _bands(fig, index, levels)
        if pre is not None:
            fig.add_trace(go.Scatter(x=pre['waveforms']['time']*1e9,
                y=signal_waveform(pre['waveforms'], pin), name=f'{pin}: {pre_label}',
                mode='lines', line={'color':'#3478ad', 'dash':'dash', 'width':1.5}), row=index, col=1)
        fig.add_trace(go.Scatter(x=result['waveforms']['time']*1e9,
            y=signal_waveform(result['waveforms'], pin), name=f'{pin}: {post_label}' if pre else pin,
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
                    target=measured.get('ideal_voltage_v',measured['ideal_trit']*5)
                    fig.add_annotation(x=start+delay, y=target,
                        ax=start, ay=target,
                        xref=f'x{axis}', yref=f'y{axis}', axref=f'x{axis}', ayref=f'y{axis}',
                        text=f'{delay:.2f} ns', showarrow=True, arrowhead=3,
                        bgcolor='rgba(255,255,255,.85)', font={'size':10})
        fig.update_yaxes(title_text='Voltage (V)', range=[voltages[0]-.85,voltages[-1]+.85], tickvals=voltages, row=index, col=1)
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


SCOPE_COLORS = ('#ffd23f', '#4cc9f0', '#ff6b81', '#7cfc6a', '#ffa94d', '#9ec5ff')


def _netlist_census(netlist: str) -> dict:
    """Count MOSFETs, resistors and wire capacitors the simulated top instantiates."""
    bodies, current = {}, None
    for line in netlist.splitlines():
        word = line.split()[0].upper() if line.split() else ''
        if word == '.SUBCKT':
            current = line.split()[1]
            bodies[current] = []
        elif word == '.ENDS':
            current = None
        elif current and word[:1] in ('X', 'M', 'R', 'C'):
            bodies[current].append(line.split())
    def count(name):
        total = {'mos': 0, 'res': 0, 'wire_c': 0, 'cells': 0}
        for fields in bodies.get(name, []):
            model = fields[-1] if fields[0][0].upper() == 'X' else None
            if fields[0].upper().startswith('XM') or fields[0][0].upper() == 'M':
                total['mos'] += 1
            elif fields[0].upper().startswith('XR') or fields[0][0].upper() == 'R':
                total['res'] += 1
            elif fields[0].upper().startswith('CTFWIRE'):
                total['wire_c'] += 1
            elif fields[0][0].upper() == 'X':
                callee = next((f for f in reversed(fields) if f in bodies), model)
                if callee in bodies:
                    sub = count(callee)
                    total['cells'] += 1
                    for key in ('mos', 'res', 'wire_c'):
                        total[key] += sub[key]
        return total
    top = next((l.split()[-1] for l in netlist.splitlines() if l.upper().startswith('XDUT')), None)
    return count(top) if top else {'mos': 0, 'res': 0, 'wire_c': 0, 'cells': 0}


def waveform_scope(result: dict, *, title='Post-layout transient', currents=('VDD',)) -> go.Figure:
    """Simulator-viewer rendering of a simulate() result: every node in its own lane.

    Inputs, outputs and supply current are drawn from the raw ngspice vectors on a
    dark scope background, with a cursor, a time range slider and a header that
    names the simulator run (version, analysis card, extracted device census).
    """
    import re
    stimulus, waves = result['stimulus'], result['waveforms']
    signals = [('v', pin) for pin in stimulus['inputs']] + [('v', pin) for pin in stimulus['outputs']]
    signals += [('i', rail) for rail in currents if f'i({rail.lower()})' in waves]
    time_us = np.asarray(waves['time'])*1e6
    fig = make_subplots(rows=len(signals), cols=1, shared_xaxes=True, vertical_spacing=.025)
    levels = sorted((result.get('measurements', {}).get('ideal_volts') or
                     {-1: -5., 0: 0., 1: 5.}).values())
    outputs = set(stimulus['outputs'])
    for row, ((kind, name), color) in enumerate(zip(signals, SCOPE_COLORS*3), 1):
        if kind == 'v':
            y, unit, label = signal_waveform(waves, name), 'V', f'v({name})'
            for level in levels:
                # The lane has no trace yet; without exclude_empty_subplots the band is dropped.
                fig.add_hrect(y0=level-PASS_BAND, y1=level+PASS_BAND, fillcolor='#1f6f4a', opacity=.25,
                              line_width=0, row=row, col=1, exclude_empty_subplots=False)
            fig.update_yaxes(range=[levels[0]-1.2, levels[-1]+1.2], tickvals=levels, row=row, col=1)
        else:
            y, unit, label = np.abs(np.asarray(waves[f'i({name.lower()})']))*1e3, 'mA', f'|i({name.lower()})|'
        fig.add_trace(go.Scatter(x=time_us, y=y, mode='lines', name=label,
                                 line={'color': color, 'width': 1.3},
                                 hovertemplate=f'{label} %{{y:.4g}} {unit}<extra></extra>'), row=row, col=1)
        rows = result.get('measurements', {}).get('rows', [])
        if kind == 'v' and name in outputs and rows:
            # The verifier's own sample points: where each settled level was checked.
            ok = [r['outputs'][name]['passed'] for r in rows]
            fig.add_trace(go.Scatter(x=[r['check_s']*1e6 for r in rows], y=[r['outputs'][name]['voltage_v'] for r in rows],
                mode='markers', marker={'symbol': ['circle-open' if p else 'x' for p in ok], 'size': 8,
                                        'color': ['#7ee787' if p else '#ff4d4f' for p in ok], 'line': {'width': 1.5}},
                customdata=[[r['outputs'][name]['error_v']*1e3, str(r['input_trits']), 'PASS' if p else 'FAIL']
                            for r, p in zip(rows, ok)],
                hovertemplate='check %{customdata[2]}: %{y:.4f} V, error %{customdata[0]:.2f} mV, inputs %{customdata[1]}<extra></extra>'),
                row=row, col=1)
        fig.add_annotation(text=f'<b>{label}</b>{"  out" if name in outputs and kind == "v" else ""}',
                           x=0.005, y=1, xref=f'x{row if row > 1 else ""} domain', yref=f'y{row if row > 1 else ""} domain',
                           xanchor='left', yanchor='top', showarrow=False,
                           font={'color': color, 'size': 13, 'family': 'DejaVu Sans Mono, monospace'})
        fig.update_yaxes(title_text=unit, row=row, col=1)
    version = re.search(r'ngspice-([0-9][^\s:]*)', result.get('log', '') or '')
    census = _netlist_census(stimulus.get('netlist', ''))
    header = (f"ngspice{' '+version[1] if version else ''} · .{stimulus.get('commands', 'tran')} · "
              f"extracted layout: {census['cells']} cells, {census['mos']} MOSFETs, {census['res']} resistors, "
              f"{census['wire_c']} wire C · T = {stimulus.get('temperature_c', 27)} °C · {len(time_us):,} points")
    mono = {'family': 'DejaVu Sans Mono, monospace', 'color': '#c9d1d9'}
    grid = {'gridcolor': '#2b333d', 'zerolinecolor': '#3a4450', 'linecolor': '#5b6675', 'showline': True,
            'tickfont': mono, 'title_font': mono, 'mirror': True, 'showspikes': True,
            'spikecolor': '#e6edf3', 'spikethickness': 1, 'spikedash': 'dot', 'spikemode': 'across'}
    fig.update_xaxes(**grid)
    fig.update_yaxes(**grid)
    fig.update_xaxes(title_text='time (µs)', rangeslider={'visible': True, 'thickness': .06, 'bgcolor': '#161b22'},
                     row=len(signals), col=1)
    fig.update_layout(height=150*len(signals)+170, paper_bgcolor='#0d1117', plot_bgcolor='#000000',
                      font=mono, showlegend=False, hovermode='x unified',
                      hoverlabel={'bgcolor': '#161b22', 'font': mono, 'bordercolor': '#5b6675'},
                      title={'text': f"{title}<br><span style='font-size:14px;color:#d0d7de'>{header}</span>",
                             'font': {**mono, 'size': 17, 'color': '#e6edf3'}, 'x': .01, 'xanchor': 'left'},
                      margin={'t': 95, 'l': 70, 'r': 25, 'b': 40})
    return fig
