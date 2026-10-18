"""Small precomputed teaching controls; changing size never reruns SPICE."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from predictions import divider, zero_dc


def sizing_slider(grid, pdk):
    """Explore every measured INV size with the reference dimensions marked.

    One slider chooses complete simulated rows, never interpolated dimensions.
    The selected transfer, zero-input point, error/current point and independent
    divider prediction update together. Failed/unavailable rows retain status.
    """
    assert grid['cell'] == 'INV'
    rows, adopted_index = grid['rows'], grid['adopted_index']
    adopted = rows[adopted_index]
    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        'Transfer curve and zero-input operating point', 'Discrete-state error / maximum rail current'))
    data = adopted['transfer']['data']
    fig.add_trace(go.Scatter(x=data['v-sweep'],y=data['v(y)'],name='Taped-out size',
                            line={'color':'#555','dash':'dash'}),1,1)
    fig.add_trace(go.Scatter(name='Selected size',line={'color':'#2866b1'}),1,1)
    fig.add_trace(go.Scatter(name='Selected zero input',mode='markers',
                            marker={'color':'#d34a2f','size':10}),1,1)
    finite = [r for r in rows if r['max_error_v'] is not None and r['max_static_current_a'] is not None]
    fig.add_trace(go.Scatter(x=[r['max_static_current_a']*1e6 for r in finite],
                            y=[max(r['max_error_v']*1e3,1e-3) for r in finite],
                            mode='markers',name='All measured sizes',
                            marker={'color':['#a6b5c6' if r['passed'] else '#dc765e' for r in finite],
                                    'symbol':['circle' if r['passed'] else 'x' for r in finite]},
                            text=[str(r['dimensions']) for r in finite],
                            hovertemplate='%{text}<br>%{x:.4g} µA; %{y:.4g} mV<extra></extra>'),1,2)
    fig.add_trace(go.Scatter(x=[adopted['max_static_current_a']*1e6],
                            y=[adopted['max_error_v']*1e3],mode='markers',name='Taped-out dimensions',
                            marker={'symbol':'star','size':16,'color':'#222'}),1,2)
    fig.add_trace(go.Scatter(mode='markers',name='Selected error/current',
                            marker={'symbol':'circle-open','size':17,'color':'#d34a2f','line':{'width':3}}),1,2)
    fig.add_hline(y=grid['conditions']['band_v']*1e3,line_dash='dot',line_color='#a33',row=1,col=2)
    for target in grid['conditions']['supplies_v'].values():
        fig.add_hrect(y0=target-grid['conditions']['band_v'],y1=target+grid['conditions']['band_v'],
                      fillcolor='#e6ebf2',opacity=.35,line_width=0,row=1,col=1)
    base_annotations = list(fig.layout.annotations)
    steps = []
    for index,row in enumerate(rows):
        d = row['dimensions']
        label = (f"Wp {d['MP']['w_um']:g}, Wn {d['MN']['w_um']:g}, "
                 f"L {d['MP']['l_um']:g}, RR {d['RP']['l_um']:g} µm"
                 + (' ★ taped out' if index == adopted_index else ''))
        curve = row['transfer']['data'] if row['transfer'] else {'v-sweep':[],'v(y)':[]}
        prediction = divider(d,pdk)
        measured = zero_dc(row)['output_v']['Y'] if row['dc'] else None
        status = 'within band' if row['passed'] else (row['error'] or 'outside band')
        readout = (f'Candidate {index}: '+label+'<br>'+f"Predict first: Y(0)={prediction['output_v']:.4g} V, P={prediction['power_w']*1e3:.4g} mW"
                   + (f" → SPICE Y(0)={measured:.4g} V" if measured is not None else ' → SPICE unavailable')
                   + (f"<br>Worst error {row['max_error_v']*1e3:.4g} mV; max |rail I| "
                      f"{row['max_static_current_a']*1e6:.4g} µA; {status}"
                      if row['max_error_v'] is not None else f'<br>{status}'))
        x = [curve['v-sweep'], [0] if measured is not None else [],
             [row['max_static_current_a']*1e6] if row['max_static_current_a'] is not None else []]
        y = [curve['v(y)'], [measured] if measured is not None else [],
             [max(row['max_error_v']*1e3,1e-3)] if row['max_error_v'] is not None else []]
        annotations = [a.to_plotly_json() for a in base_annotations]+[
            {'text':readout,'xref':'paper','yref':'paper','x':0,'y':-.42,
             'showarrow':False,'xanchor':'left','yanchor':'top'}]
        steps.append({'label':'','value':str(index),'method':'update',
                      'args':[{'x':x,'y':y},{'annotations':annotations},[1,2,5]]})
    initial = steps[adopted_index]['args']
    for trace,x,y in zip((1,2,5),initial[0]['x'],initial[0]['y'],strict=True):
        fig.data[trace].update(x=x,y=y)
    fig.update_xaxes(title_text='Input A (V)',row=1,col=1)
    fig.update_yaxes(title_text='Output Y (V)',row=1,col=1)
    fig.update_xaxes(title_text='Maximum |rail current| (µA)',row=1,col=2)
    fig.update_yaxes(title_text='Worst level error (mV)',type='log',row=1,col=2)
    fig.update_layout(template='plotly_white',height=740,
                      title={'text':'Move the size; compare prediction with SPICE','y':.99,'yanchor':'top'},
                      margin={'t':150,'b':230},annotations=initial[1]['annotations'],
                      legend={'orientation':'h','y':1.2},
                      sliders=[{'active':adopted_index,'steps':steps,'y':-.18,
                                'currentvalue':{'prefix':'Drag to choose a measured size'},'ticklen':0}],
                      meta={'adopted_index':adopted_index,'candidate_count':len(rows),
                            'scope':grid.get('scope'),'dimensions':[r['dimensions'] for r in rows]})
    return fig


def value_selector(net):
    """A small half-adder input selector recolors real mapped nets and hover."""
    from itertools import product
    from tritflow.viz.graph import color_nets
    pins = [p.name for p in net.ports if p.dir == 'input']
    choices = list(product((-1,0,1),repeat=len(pins)))
    figures = [color_nets(net,dict(zip(pins,v,strict=True))) for v in choices]
    figure = go.Figure(figures[0])
    figure.frames = [go.Frame(name=str(i),data=f.data) for i,f in enumerate(figures)]
    figure.update_layout(title='Mapped half adder: choose settled input trits',
                          updatemenus=[{'buttons':[{'label':str(dict(zip(pins,v))),
                              'method':'animate','args':[[str(i)],{'mode':'immediate',
                                  'frame':{'duration':0,'redraw':True},'transition':{'duration':0}}]}
                              for i,v in enumerate(choices)],'x':0,'y':1.08}])
    return figure
