"""Plotly figures for cached real-layout scaling, loading and DC sizing."""
from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def scaling_figure(result, *, title='Balanced-ternary ripple-adder scaling'):
    """Measured area/cells, carry settling, representative DC power and IR shift."""
    rows = sorted((r for r in result['rows'] if r['state']=='complete'),key=lambda r:r['n'])
    fig = make_subplots(rows=2,cols=2,
        subplot_titles=('Actual PNR die area and cells','Full-length carry assertion / release',
                        'Worst representative static power','Estimated rail deviation and zero shift'),
        specs=[[{'secondary_y':True},{}],[{},{}]],vertical_spacing=.19,horizontal_spacing=.15)
    x = [r['n'] for r in rows]
    def trace(values,name,row,col,**kwargs):
        fig.add_trace(go.Scatter(x=x,y=values,name=name,mode='lines+markers'),row=row,col=col,**kwargs)
    trace([r['die_area_um2']/1e6 for r in rows],'Die area',1,1)
    trace([r['cell_count'] for r in rows],'Cells',1,1,secondary_y=True)
    for mode in ('pre','post'):
        trace([None if r['carry'][mode]['max_settling_s'] is None else r['carry'][mode]['max_settling_s']*1e9
               for r in rows],f'{mode}-layout carry',1,2)
    trace([r['static_power_worst_w']*1e3 for r in rows],'Static power',2,1)
    trace([r['max_rail_deviation_v']*1e3 for r in rows],'Rail deviation',2,2)
    trace([r['max_zero_shift_v']*1e3 for r in rows],'Zero-level shift',2,2)
    for row in (1,2):
        for col in (1,2): fig.update_xaxes(title_text='Adder width (trits)',dtick=1,row=row,col=col)
    fig.update_yaxes(title_text='mm²',row=1,col=1,secondary_y=False)
    fig.update_yaxes(title_text='cells',row=1,col=1,secondary_y=True)
    fig.update_yaxes(title_text='ns',row=1,col=2)
    fig.update_yaxes(title_text='mW',row=2,col=1)
    fig.update_yaxes(title_text='mV',row=2,col=2)
    failed = [str(r['n']) for r in result['rows'] if not r['passed']]
    if failed:
        fig.add_annotation(text='FAIL / incomplete widths: '+', '.join(failed),xref='paper',yref='paper',
                           x=0,y=-.17,showarrow=False,font={'color':'#bd3535'})
    fig.update_layout(title=title,height=730,template='plotly_white',legend={'orientation':'h','y':-.16},margin={'b':130})
    return fig


def load_sweep_figure(result, *, title='Full adder: post-layout output-load boundary'):
    """PASS/FAIL and null-safe settling with a 500 ns window and measured bracket."""
    fig = make_subplots(rows=1,cols=1,specs=[[{'secondary_y':True}]])
    rows = result['rows'];window = result['conditions']['hold_s']*1e9
    for pin in result['outputs']:
        fig.add_trace(go.Scatter(x=[r['load_f']*1e12 for r in rows],
            y=[None if any(f['output']==pin and f['settling_s'] is None for f in r['failures']) or r['max_settling_s'][pin] is None
               else r['max_settling_s'][pin]*1e9 for r in rows],
            mode='lines+markers',name=f'{pin} settling'),secondary_y=False)
    failed = [r for r in rows if not r['passed']]
    fig.add_trace(go.Scatter(x=[r['load_f']*1e12 for r in failed],y=[window]*len(failed),
        mode='markers',name='FAIL within window',marker={'symbol':'x','color':'#bd3535','size':12}),secondary_y=False)
    fig.add_trace(go.Scatter(x=[r['load_f']*1e12 for r in rows],y=[r['max_error_v'] for r in rows],
        mode='lines+markers',name='Worst check error',line={'dash':'dot'}),secondary_y=True)
    fig.add_hline(y=window,line_dash='dash',annotation_text=f'{window:g} ns window',secondary_y=False)
    fig.add_hline(y=.5,line_dash='dot',secondary_y=True)
    bound = result['boundary']
    if result['boundary_found']:
        fig.add_vrect(x0=bound['last_pass_f']*1e12,x1=bound['first_fail_f']*1e12,
                      fillcolor='#c77e3c',opacity=.2,line_width=0,
                      annotation_text=f'Measured PASS at {bound["last_pass_f"]*1e12:.3g} / FAIL at {bound["first_fail_f"]*1e12:.3g} pF')
    fig.update_xaxes(type='log',title_text='External load on each output (pF)')
    fig.update_yaxes(title_text='Settling (ns); missing when unsettled',secondary_y=False)
    fig.update_yaxes(title_text='Worst absolute check error (V)',secondary_y=True)
    fig.update_layout(title=title,template='plotly_white',height=460,legend={'orientation':'h','y':-.25})
    return fig


def sizing_figure(result, *, title=None):
    """Candidate error/current tradeoff, marking the actual adopted schematic."""
    rows = result['rows'];fig = go.Figure()
    for passed,symbol,color in ((True,'circle','#23865c'),(False,'x','#bd3535')):
        selected = [(i,r) for i,r in enumerate(rows) if r['passed']==passed and r['max_error_v'] is not None]
        fig.add_trace(go.Scatter(x=[r['max_static_current_a']*1e6 for _,r in selected],
            y=[r['max_error_v'] for _,r in selected],mode='markers',name='PASS' if passed else 'FAIL',
            marker={'symbol':symbol,'color':color},customdata=[i for i,_ in selected],
            text=[str(r['dimensions']) for _,r in selected],
            hovertemplate='candidate %{customdata}<br>%{text}<br>%{x:.3f} µA, %{y:.4f} V<extra>%{fullData.name}</extra>'))
    adopted = rows[result['adopted_index']]
    if adopted['max_error_v'] is not None:
        fig.add_trace(go.Scatter(x=[adopted['max_static_current_a']*1e6],y=[adopted['max_error_v']],
            mode='markers',name='Adopted taped-out dimensions',marker={'symbol':'star','size':17,'color':'#e9aa21','line':{'width':1,'color':'#353535'}}))
    failures = sum(r['error'] is not None for r in rows)
    if failures: fig.add_annotation(text=f'{failures} solver failures (metrics unavailable)',showarrow=False,xref='paper',yref='paper',x=0,y=1.1)
    fig.add_hline(y=.5,line_dash='dash',annotation_text='±0.5 V criterion')
    fig.update_layout(title=title or f'{result["cell"]}: nominal DC sizing',template='plotly_white',
                      xaxis_title='Worst absolute static rail current (µA)',yaxis_title='Worst discrete-state level error (V)')
    return fig


def scaling_fit_figure(result, *, title='Ripple carry and the DC-power cost of ternary dividers'):
    """Measured points and free-intercept OLS lines; no unmeasured extrapolation."""
    from tritflow.sim.scaling import fit_scaling
    fits = result.get('fits') or fit_scaling(result)
    rows = sorted((r for r in result['rows'] if r.get('passed') and r.get('state')=='complete'),key=lambda r:r['n'])
    fig = make_subplots(rows=1,cols=2,horizontal_spacing=.16,
                        subplot_titles=('Worst measured full-length carry','Worst representative static power'))
    annotations = []
    for mode,color in (('pre','#3478ad'),('post','#bc5a22')):
        selected = [r for r in rows if r['carry'][mode]['max_settling_s'] is not None]
        fig.add_trace(go.Scatter(x=[r['n'] for r in selected],
            y=[r['carry'][mode]['max_settling_s']*1e9 for r in selected],
            mode='markers',name=f'{mode}-layout measured',marker={'color':color,'size':9}),row=1,col=1)
        fit = fits['carry'][mode]
        if fit:
            fig.add_trace(go.Scatter(x=fit['x'],y=[v*1e9 for v in fit['predicted']],
                mode='lines',name=f'{mode}-layout fit',line={'color':color,'dash':'dash'}),row=1,col=1)
            r2 = 'undefined' if fit['r_squared'] is None else f'{fit["r_squared"]:.5f}'
            annotations.append(f'{mode}: {fit["slope"]*1e9:.3f} ns/trit + {fit["intercept"]*1e9:.3f} ns; R²={r2}')
    fig.add_trace(go.Scatter(x=[r['cell_count'] for r in rows],
        y=[r['static_power_worst_w']*1e3 for r in rows],mode='markers',
        name='DC power measured',marker={'color':'#23865c','size':9}),row=1,col=2)
    fit = fits['static_power']
    if fit:
        fig.add_trace(go.Scatter(x=fit['x'],y=[v*1e3 for v in fit['predicted']],
            mode='lines',name='DC power fit',line={'color':'#23865c','dash':'dash'}),row=1,col=2)
        r2 = 'undefined' if fit['r_squared'] is None else f'{fit["r_squared"]:.6f}'
        fig.add_annotation(x=.58,y=.99,xref='paper',yref='paper',showarrow=False,xanchor='left',yanchor='top',
            bgcolor='rgba(255,255,255,.85)',text=f'{fit["slope"]*1e3:.4f} mW/cell + {fit["intercept"]*1e3:.4f} mW<br>R²={r2}; fixed adder cell mix')
    if annotations:
        fig.add_annotation(x=.01,y=.99,xref='paper',yref='paper',showarrow=False,xanchor='left',yanchor='top',
                           bgcolor='rgba(255,255,255,.85)',text='<br>'.join(annotations))
    fig.add_annotation(x=0,y=-.26,xref='paper',yref='paper',xanchor='left',showarrow=False,align='left',
        text='Resistive-divider ternary cells draw DC current without switching; lower clock frequency alone does not remove it.'
             '<br>Nominal documented-state maxima; fit residuals are not PVT uncertainty. No extrapolation beyond measured widths.')
    fig.update_xaxes(title_text='Adder width (trits)',dtick=1,row=1,col=1)
    fig.update_xaxes(title_text='Mapped cells (fixed adder mix)',dtick=16,row=1,col=2)
    fig.update_yaxes(title_text='Settling (ns)',row=1,col=1)
    fig.update_yaxes(title_text='Static power (mW)',row=1,col=2)
    fig.update_layout(title=title,template='plotly_white',height=530,
                      legend={'orientation':'h','y':-.14},margin={'b':145})
    return fig
