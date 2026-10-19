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
            {'text':readout,'xref':'paper','yref':'paper','x':0,'y':-.16,
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
    # The slider sits above the plots in the accent colour, so it is the first thing a reader sees.
    fig.update_layout(template='plotly_white',height=800,
                      title={'text':'Move the size; compare prediction with SPICE','y':.99,'yanchor':'top'},
                      margin={'t':200,'b':150},annotations=initial[1]['annotations'],
                      legend={'orientation':'h','y':1.08,'yanchor':'bottom'},
                      sliders=[{'active':adopted_index,'steps':steps,'x':0,'len':1,'y':1.17,'yanchor':'bottom',
                                'pad':{'t':0,'b':0},'bgcolor':'#fde68a','activebgcolor':'#d97706',
                                'bordercolor':'#d97706','borderwidth':2,'ticklen':0,'font':{'size':12},
                                'currentvalue':{'prefix':'◀ ▶ DRAG THIS SLIDER to try another simulated size — ',
                                                'font':{'size':16,'color':'#b45309'},'xanchor':'left'}}],
                      meta={'adopted_index':adopted_index,'candidate_count':len(rows),
                            'scope':grid.get('scope'),'dimensions':[r['dimensions'] for r in rows]})
    return fig


def value_selector(net, *, title='Mapped half adder: choose the input trits'):
    """Choose input trits; the routed schematic shows every settled net value.

    All 3^n views are rendered once from the same routed scene, so buttons only
    swap images: no kernel callback, and nothing moves between selections.
    """
    import base64, html, uuid
    from itertools import product
    from IPython.display import HTML
    from tritflow.synth import evaluate_netlist
    pins = [p.name for p in net.ports if p.dir == 'input']
    outs = [p.name for p in net.ports if p.dir == 'output']
    base = net.schematic(expand='*', net_names=True, title=title)
    trit = {-1: '−1', 0: '0', 1: '+1'}
    uid = 'tv' + uuid.uuid4().hex[:8]
    views = []
    for combo in product((-1, 0, 1), repeat=len(pins)):
        state = dict(zip(pins, combo, strict=True))
        result = evaluate_netlist(net, state)
        svg = base.annotate(inputs=state).svg
        reading = ' · '.join(f'{name} = {trit[int(result[name])]}' for name in outs)
        key = '_'.join(str(v) for v in combo)
        views.append(f'<div data-key="{key}" style="display:{"block" if all(v == 1 for v in combo) else "none"}">'
                     f'<div style="font:15px serif;margin:4px 0">outputs: {html.escape(reading)}</div>'
                     f'<img style="max-width:100%;height:auto" src="data:image/svg+xml;base64,'
                     f'{base64.b64encode(svg.encode()).decode()}"></div>')
    buttons = []
    for i, pin in enumerate(pins):
        group = ''.join(f'<button type="button" data-pin="{i}" data-v="{v}" onclick="{uid}(this)" '
                        f'style="font:14px serif;padding:3px 10px;margin:0 2px;border:1px solid #888;'
                        f'background:{"#333" if v == 1 else "#fff"};color:{"#fff" if v == 1 else "#000"}">'
                        f'{trit[v]}</button>' for v in (-1, 0, 1))
        buttons.append(f'<span style="margin-right:18px;font:15px serif">{html.escape(pin)}: {group}</span>')
    script = (f'<script>function {uid}(b){{var r=document.getElementById("{uid}");'
              f'r.querySelectorAll("button[data-pin=\'"+b.dataset.pin+"\']").forEach(function(x){{'
              f'x.style.background="#fff";x.style.color="#000";x.dataset.on=""}});'
              f'b.style.background="#333";b.style.color="#fff";b.dataset.on="1";'
              f'var k=[];for(var i=0;i<{len(pins)};i++){{var on=r.querySelector("button[data-pin=\'"+i+"\'][data-on=\'1\']");'
              f'k.push(on?on.dataset.v:"1")}}'
              f'r.querySelectorAll("div[data-key]").forEach(function(d){{d.style.display=d.dataset.key==k.join("_")?"block":"none"}})}}</script>')
    return HTML(f'<div id="{uid}" data-trit-selector="1"><div style="margin:6px 0">{"".join(buttons)}</div>{"".join(views)}</div>{script}')


def highlight_devices(mapping, devices, *, title):
    """Outline the named schematic devices on the cell layout; returns the figure.

    These are LVS-matched device outlines, not a simulated current-density map.
    """
    assert set(devices) <= {r['name'] for r in mapping.rows}
    for trace in mapping.figure.data:
        meta = trace.meta or {}
        if meta.get('kind') == 'device' and meta.get('device') in devices:
            trace.update(line={'color':'#d13c28','width':4},opacity=1)
    mapping.figure.update_layout(title=title)
    return mapping.figure


# What each primitive does electrically, read from the taped-out netlists (cells/out/*/*.spice).
CELL_NOTES = {
    "INV": ("Y = −A",
            "One PMOS (W 13.5 µm) pulls toward VDD and one NMOS (W 5 µm) toward VSS, each through a "
            "30 µm poly resistor into Y. At A = ±1 only one branch conducts and Y reaches a rail. At A = 0 "
            "both conduct, and the two resistive branches divide Y to the middle level, drawing a static current."),
    "NAND": ("Y = −min(A, B)",
             "Two parallel PMOS (W 19 µm) pull up when either input is low; two series NMOS (W 13 µm) pull "
             "down only when both inputs are high. The same resistor pair sets the middle level when the "
             "smaller input is 0."),
    "NOR": ("Y = −max(A, B)",
            "Two series PMOS (W 37 µm) pull up only when both inputs are low; two parallel NMOS "
            "(W 6.5 µm) pull down when either input is high. The resistor pair sets the middle level when "
            "the larger input is 0."),
    "NANY": ("Y = −sat(A + B)",
             "Series PMOS (W 34 µm) pull Y up when both inputs are low; series NMOS (W 11 µm) pull it down "
             "when both are high; the resistor pair divides 0 + 0 to the middle. Two clamp branches "
             "(PMOS W 14 µm + NMOS W 8 µm to VMID) hold Y at 0 V when the inputs have opposite signs, so "
             "(−1) + (+1) gives 0. This is the only logic cell that uses VMID."),
}
TRIT_HTML = {-1: ("−1", "#2a78d6"), 0: ("0", "#6f6e69"), 1: ("+1", "#e34948")}


def _trit_table(values, two_inputs):
    """A 3×3 (or 1×3) ternary table with each output coloured by its trit."""
    cell = lambda v: (f'<td style="background:{TRIT_HTML[v][1]};color:#fff;font-weight:600;'
                      f'text-align:center;width:46px;height:30px">{TRIT_HTML[v][0]}</td>')
    head = 'style="padding:4px 8px;color:#555;font-weight:600;text-align:center;white-space:nowrap"'
    if not two_inputs:
        return (f'<table style="border-collapse:separate;border-spacing:3px"><tr><th {head}>A</th>'
                + ''.join(f'<th {head}>{TRIT_HTML[a][0]}</th>' for a in (-1, 0, 1))
                + f'</tr><tr><th {head}>Y</th>' + ''.join(cell(values[(a,)]) for a in (-1, 0, 1)) + '</tr></table>')
    rows = ''.join(f'<tr><th {head}>A = {TRIT_HTML[a][0]}</th>' + ''.join(cell(values[(a, b)]) for b in (-1, 0, 1))
                   + '</tr>' for a in (-1, 0, 1))
    return (f'<table style="border-collapse:separate;border-spacing:3px"><tr><th {head}></th>'
            + ''.join(f'<th {head}>B = {TRIT_HTML[b][0]}</th>' for b in (-1, 0, 1)) + '</tr>' + rows + '</table>')


def cell_cards(truth, cells_dir, schematics_dir):
    """The primitive library at a glance: function, truth table, taped-out schematic, operation.

    ``truth`` is ``gates.truth_table()`` of examples/gates.tv; schematics are the batch Xschem
    exports of the taped-out sources; sizes and device counts come from the cell library.
    """
    import base64, json
    from pathlib import Path
    from IPython.display import HTML
    cells_dir, schematics_dir = Path(cells_dir), Path(schematics_dir)
    columns = {"INV": "inva", "NAND": "nandab", "NOR": "norab", "NANY": "nanyab"}
    cards = []
    for name, column in columns.items():
        two = name != "INV"
        values = {((int(a), int(b)) if two else (int(a),)): int(y)
                  for a, b, y in zip(truth["a"], truth["b"], truth[column])}
        abstract = json.loads((cells_dir/name/f"{name}.abstract.json").read_text())
        devices = sum(1 for line in (cells_dir/name/f"{name}.spice").read_text().splitlines()
                      if line.strip().upper().startswith("X"))
        svg = base64.b64encode((schematics_dir/f"{name}.svg").read_bytes()).decode()
        function, note = CELL_NOTES[name]
        cards.append(
            '<div style="display:flex;gap:18px;align-items:flex-start;border:1px solid #d0d7de;border-radius:8px;'
            'padding:14px 16px;margin:10px 0;background:#fff;color:#1f2328;font-family:sans-serif">'
            f'<div style="flex:0 0 360px"><div style="font-size:20px;font-weight:700">{name}'
            f'<span style="font-weight:400;font-size:17px;margin-left:12px">{function}</span></div>'
            f'<div style="margin:10px 0">{_trit_table(values, two)}</div>'
            f'<div style="font-size:14px;line-height:1.45">{note}</div>'
            f'<div style="font-size:12.5px;color:#57606a;margin-top:8px">{devices} devices · cell '
            f'{abstract["width"]:g} × {abstract["height"]:g} µm · schematic: taped-out Xschem source '
            '(click it to enlarge)</div></div>'
            f'<img alt="{name} cell schematic" title="Click to enlarge" src="data:image/svg+xml;base64,{svg}" '
            'onclick="this.style.maxHeight=this.style.maxHeight===\'none\'?\'430px\':\'none\';'
            'this.style.maxWidth=this.style.maxHeight===\'none\'?\'100%\':\'560px\'" '
            'style="flex:1 1 auto;max-width:560px;max-height:430px;width:auto;height:auto;object-fit:contain;'
            'margin-left:auto;background:#fff;cursor:zoom-in"></div>')
    others = ('<div style="border:1px solid #d0d7de;border-radius:8px;padding:12px 16px;margin:10px 0;'
              'font:14px/1.5 sans-serif;color:#1f2328;background:#f6f8fa">'
              '<b>Support cells.</b> <b>BUF</b> is two INV stages (8 devices): it restores levels and drives '
              'large fanout. <b>TIEP / TIEZ / TIEN</b> are a single 30 µm resistor from Y to VDD / VMID / VSS, '
              'supplying a constant +1 / 0 / −1 through finite resistance. <b>FILL</b> carries the rails and '
              'wells across gaps in a row.</div>')
    return HTML('<div data-cell-cards="1">' + ''.join(cards) + others + '</div>')
