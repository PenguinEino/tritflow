"""Notebook cell geometry, schematic-device correspondence, and row abutment.

Read published ``cells/out`` views only: GDS polygons, abstracts, PCell placement
records, SPICE and persisted LVS cross-references. No PDK registration, simulator,
reference checkout, ipywidgets or notebook imports are needed to make figures.
Legend clicks toggle layers; ordinary Plotly figures also work without widgets.
``device_mapping`` adds a portable, keyboard-accessible HTML table linked to its
Plotly view, and always exposes separate ``figure`` / ``table`` static fallbacks.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from html import escape
import json
from pathlib import Path
import re
from uuid import uuid4

import klayout.db as db
import plotly.graph_objects as go

from tritflow import CELLS_DIR

__all__ = ['cell_figure', 'device_locations', 'device_mapping', 'device_table',
           'row_abutment', 'DeviceMapping']

# Drawing-layer IDs, not recognition layers or guessed device rectangles.
LAYERS = {'WN': (140, 0), 'AP': (3, 1), 'AN': (3, 2), 'AR': (3, 3),
          'GC': (8, 1), 'CO': (11, 0), 'M1': (13, 0), 'V1': (19, 0), 'M2': (20, 0)}
LABELS = {'WN': 'n-well', 'AP': 'P active', 'AN': 'N active', 'AR': 'RR active',
          'GC': 'gate poly', 'CO': 'contact', 'M1': 'metal 1', 'V1': 'via', 'M2': 'metal 2'}
COLORS = {
    'light': dict(zip(LAYERS, ['#8064a2', '#cf4b35', '#168355', '#bb7800', '#a73c91',
                              '#343b46', '#2268b0', '#9b7100', '#007f91'])),
    'dark': dict(zip(LAYERS, ['#bea5e0', '#ff927b', '#63d59b', '#ffc861', '#ee9edd',
                             '#edf0f5', '#75b6ff', '#f5df73', '#5ce0e5']))}
RAIL_COLORS = {'VDD': '#d64d64', 'VMID': '#888888', 'VSS': '#397ed2'}
VOLTAGES = {'VDD': '+5 V', 'VMID': '0 V', 'VSS': '−5 V'}
MODEL_PCELL = {'PMOS': ('fet_p', 'AP'), 'NMOS': ('fet_n', 'AN'), 'F_RR': ('res_diff', 'AR')}


def _theme(theme):
    if theme not in COLORS:
        raise ValueError('theme must be light or dark')
    return {'template': 'plotly_white' if theme == 'light' else 'plotly_dark',
            'paper_bgcolor': '#ffffff' if theme == 'light' else '#151b26',
            'plot_bgcolor': '#ffffff' if theme == 'light' else '#151b26',
            'font': {'color': '#202938' if theme == 'light' else '#edf2fa'}}


def _rgba(color, alpha):
    return f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},{alpha})'


@contextmanager
def _snapshot(library):
    root = Path(library).expanduser().resolve()
    generation = root/'generation.json'
    before = generation.read_bytes() if generation.exists() else None
    yield root
    after = generation.read_bytes() if generation.exists() else None
    if before != after:
        raise RuntimeError('Cell library was published during figure creation; recreate the figure')


@dataclass
class _Cell:
    name: str
    root: Path
    abstract: dict
    layout: db.Layout
    top: db.Cell

    @property
    def width(self):
        return float(self.abstract['width'])

    @property
    def height(self):
        return float(self.abstract['height'])


def _load(cell, root):
    name = str(cell).upper()
    manifest = json.loads((root/'library.json').read_text())
    entry = next((e for e in manifest if e['name'] == name), None)
    if entry is None:
        raise ValueError(f'Unknown library cell: {cell}')
    abstract = json.loads((root/entry['abstract']).read_text())
    layout = db.Layout(); layout.read(str(root/entry['gds']))
    top = layout.cell(name)
    if top is None:
        raise ValueError(f'GDS has no top cell {name}')
    return _Cell(name, root, abstract, layout, top)


def _region(cell, pair):
    index = cell.layout.find_layer(*pair)
    return db.Region() if index is None else db.Region(cell.top.begin_shapes_rec(index)).merged()


def _xy(polygons, dbu=1., *, offset=0., width=0., orient='R0'):
    """Keep polygon holes empty by drawing a disjoint trapezoid decomposition."""
    xs, ys = [], []
    for polygon in polygons:
        points = list(polygon.each_point_hull())
        if not points:
            continue
        for p in points + points[:1]:
            x = p.x*dbu
            xs.append(offset + (width-x if orient == 'MY' else x))
            ys.append(p.y*dbu)
        xs.append(None); ys.append(None)
    return xs, ys


def _rect_xy(rects, **transform):
    return _xy([db.DPolygon(db.DBox(*rect)) for rect in rects], **transform)


def _polygon_trace(xs, ys, *, name, color, kind, fill=.18, dash='solid', **meta):
    return go.Scatter(x=xs, y=ys, mode='lines', fill='toself', fillcolor=_rgba(color, fill),
                      line={'color': color, 'width': 1., 'dash': dash}, name=name,
                      hoveron='fills+points', hovertemplate=name+'<br>x=%{x:g}, y=%{y:g} µm<extra></extra>',
                      meta={'kind': kind, **meta})


def _geometry(fig, cell, theme, *, offset=0., orient='R0', instance=None, seen=None):
    seen = set() if seen is None else seen
    transform = {'offset': offset, 'width': cell.width, 'orient': orient}
    for layer, pair in LAYERS.items():
        region = _region(cell, pair)
        if region.is_empty():
            continue
        xs, ys = _xy(region.decompose_trapezoids(), cell.layout.dbu, **transform)
        trace = _polygon_trace(xs, ys, name=f'{layer} · {LABELS[layer]} ({pair[0]}/{pair[1]})',
                               color=COLORS[theme][layer], kind='layer', fill=.12 if layer == 'WN' else .35,
                               layer=layer, cell=cell.name, instance=instance,
                               area_um2=region.area()*cell.layout.dbu**2)
        trace.legendgroup = layer; trace.showlegend = layer not in seen
        fig.add_trace(trace); seen.add(layer)
    xs, ys = _rect_xy([[0, 0, cell.width, cell.height]], **transform)
    trace = _polygon_trace(xs, ys, name='Cell boundary', color=_theme(theme)['font']['color'],
                           kind='boundary', fill=0, dash='dot', cell=cell.name, instance=instance)
    trace.legendgroup = 'boundary'; trace.showlegend = 'boundary' not in seen
    fig.add_trace(trace); seen.add('boundary')


def _obstructions(fig, cell, theme, *, offset=0., orient='R0', seen=None):
    seen = set() if seen is None else seen
    for layer in ('M2', 'V1'):
        rects = cell.abstract['obstructions'].get(layer, [])
        if not rects:
            continue
        xs, ys = _rect_xy(rects, offset=offset, width=cell.width, orient=orient)
        key = f'obstruction:{layer}'
        trace = _polygon_trace(xs, ys, name=f'{layer} router obstructions',
                               color=COLORS[theme][layer], kind='obstruction', fill=0, dash='dash',
                               layer=layer, cell=cell.name)
        trace.legendgroup = key; trace.showlegend = key not in seen
        trace.line.width = 2
        fig.add_trace(trace); seen.add(key)


def _pins(fig, cell, theme, *, offset=0., orient='R0', seen=None):
    seen = set() if seen is None else seen
    for name, pin in cell.abstract['pins'].items():
        if pin['dir'] == 'power':
            continue
        color = _theme(theme)['font']['color']
        xs, ys = _rect_xy(pin['rects'], offset=offset, width=cell.width, orient=orient)
        trace = _polygon_trace(xs, ys, name='Signal pins', color=color, kind='pin', fill=.12,
                               cell=cell.name, pin=name)
        trace.legendgroup = 'pins'; trace.showlegend = 'pins' not in seen
        trace.hovertemplate = f'{cell.name}.{name} · {pin["dir"]} on {pin["layer"]}<extra></extra>'
        fig.add_trace(trace); seen.add('pins')
        ax, ay = pin['access'][0]
        ax = offset + (cell.width-ax if orient == 'MY' else ax)
        fig.add_trace(go.Scatter(x=[ax], y=[ay], mode='markers+text', text=[name],
                      textposition='middle right' if ax-offset < cell.width/2 else 'middle left',
                      textfont={'color': color, 'size': 12}, marker={'color': color, 'size': 5, 'symbol': 'diamond'},
                      name=name, legendgroup='pins', showlegend=False, hoverinfo='skip',
                      meta={'kind': 'pin_label', 'pin': name, 'cell': cell.name}))


def _rails(fig, width, rails, theme, *, row=False):
    for rank,(name, rects) in enumerate(rails.items(),1):
        color = RAIL_COLORS[name]
        xs, ys = _rect_xy(rects)
        trace = _polygon_trace(xs, ys, name=f'{name} · {VOLTAGES[name]} (M1)', color=color,
                               kind='rail', fill=.28, net=name)
        trace.legendgroup = 'rail:'+name
        trace.legendrank = rank if row else 1000
        fig.add_trace(trace)
        y = sum(rects[0][1::2])/2
        label_y = y + (14 if name == 'VMID' else -12 if name == 'VSS' else 0) if row else y
        pad = min(12., width*.07)
        # Separate the closely spaced bottom rail labels in wide, true-scale rows.
        fig.add_trace(go.Scatter(x=[0, -pad/2, -pad], y=[y, y, label_y], mode='lines',
                      line={'color': color, 'width': 1}, showlegend=False, legendgroup='rail:'+name,
                      hoverinfo='skip', meta={'kind': 'rail_leader', 'net': name}))
        fig.add_trace(go.Scatter(x=[-pad], y=[label_y], text=[name], mode='text',
                      textposition='middle left', textfont={'color': _theme(theme)['font']['color'], 'size': 12},
                      showlegend=False, legendgroup='rail:'+name, hoverinfo='skip',
                      meta={'kind': 'rail_label', 'net': name}))


def _axes(fig, width, height, title, theme, *, row=False):
    fig.update_layout(**_theme(theme), title=title, height=460 if row else 700,
                      margin={'l': 25, 'r': 15, 't': 85, 'b': 40}, hovermode='closest',
                      legend={'groupclick': 'togglegroup', 'itemclick': 'toggle', 'itemdoubleclick': 'toggleothers',
                              'font': {'size': 11}},
                      xaxis={'title': 'x (µm)', 'range': [-max(25., width*.08), width+5], 'showgrid': False},
                      yaxis={'title': 'y (µm)', 'range': [-18 if row else -4, height+18 if row else height+4],
                             'showgrid': False, 'scaleanchor': 'x', 'scaleratio': 1})
    return fig


def _cell_figure(cell, theme):
    fig = go.Figure()
    _geometry(fig, cell, theme); _obstructions(fig, cell, theme); _pins(fig, cell, theme)
    rails = {n: cell.abstract['pins'][n]['rects'] for n in VOLTAGES}
    _rails(fig, cell.width, rails, theme)
    fig.update_layout(meta={'cell': cell.name, 'source': 'published GDS and abstract; coordinates in µm', 'theme': theme})
    return _axes(fig, cell.width, cell.height, f'{cell.name} · {cell.width:g} × {cell.height:g} µm', theme)


def cell_figure(cell, *, library=CELLS_DIR/'out', theme='light'):
    """Actual GDS, layer toggles, M2/V1 obstruction outlines, rails and pin access.

    Returns an ordinary Plotly Figure. Legend clicks toggle a layer/group;
    double-click isolates it. ``theme`` is light/dark; geometry uses equal axes.
    """
    _theme(theme)
    with _snapshot(library) as root:
        return _cell_figure(_load(cell, root), theme)


def _source_devices(cell):
    """Read canonical simulation names, terminal counts and W/L from SPICE."""
    devices = []
    text = re.sub(r'\n\s*\+\s*', ' ', (cell.root/cell.name/f'{cell.name}.spice').read_text())
    for line in text.splitlines():
        tokens = line.split()
        if not tokens or tokens[0][0].upper() not in 'XM':
            continue
        model_index = next((i for i,t in enumerate(tokens) if t in MODEL_PCELL), None)
        if model_index is None:
            continue
        dimensions = {}
        for field in tokens[model_index+1:]:
            match = re.fullmatch(r'([WL])=([0-9.eE+\-]+)([unmp]?)', field, re.I)
            if match:
                dimensions[match[1].upper()] = float(match[2])*{'': 1e6, 'u': 1., 'n': 1e-3, 'm': 1e3, 'p': 1e-6}[match[3].lower()]
        if set(dimensions) != {'W','L'}:
            raise ValueError(f'Missing source W/L for {tokens[0]}')
        devices.append({'name': tokens[0], 'reference_name': tokens[0][1:].upper(),
                        'model': tokens[model_index], 'w_um': dimensions['W'], 'l_um': dimensions['L']})
    return devices


def _matches(path, top):
    result = db.LayoutVsSchematic(); result.read(str(path))
    circuit = result.netlist().circuit_by_name(top)
    if circuit is None:
        return []
    pairs = []
    for pair in result.xref().each_device_pair(circuit):
        layout, reference = pair.first(), pair.second()
        if not layout or not reference or pair.status() != db.NetlistCrossReference.Match:
            raise ValueError(f'Unmatched schematic device in {path}')
        pairs.append({'reference_name': reference.name.upper(), 'model': layout.device_class().name,
                      'x_um': layout.trans.disp.x, 'y_um': layout.trans.disp.y,
                      'w_um': layout.parameter('W'), 'l_um': layout.parameter('L')})
    return pairs


def _location_key(row):
    return row['model'], round(row['x_um'], 6), round(row['y_um'], 6)


def _device_rows(cell):
    sources = _source_devices(cell)
    if not sources:  # FILL is intentionally purged by the PDK's LVS deck.
        return []
    folder = cell.root/cell.name
    matches = _matches(folder/'lvs.lvsdb', cell.name)
    aliases = {}
    for base in ('equivalence/parasitic/reference', 'equivalence/reference'):
        ref = cell.root/base/cell.name/('lvs.lvsdb' if cell.name == 'BUF' else 'compact_lvs/lvs.lvsdb')
        if ref.exists():
            aliases = {_location_key(m): m['reference_name'] for m in _matches(ref, cell.name)}
            break
    manifest = json.loads((folder/f'{cell.name}.pcells.json').read_text())
    rows = []
    for source in sources:
        candidates = [m for m in matches if m['reference_name'] == source['reference_name']]
        if len(candidates) != 1:
            raise ValueError(f'{source["name"]}: no unique matched LVS device')
        match = candidates[0]
        if match['model'] != source['model'] or any(abs(match[k]-source[k]) > 1e-6 for k in ('w_um','l_um')):
            raise ValueError(f'{source["name"]}: source/LVS dimensions differ')
        pcell, layer = MODEL_PCELL[source['model']]
        instances = [i for i in cell.top.each_inst() if i.cell.name.startswith(pcell+'__') or i.cell.name.startswith(pcell+'$')]
        instances = [i for i in instances if abs(i.dcplx_trans.disp.x-match['x_um']) < 1e-6
                     and abs(i.dcplx_trans.disp.y-match['y_um']) < 1e-6]
        if len(instances) != 1:
            raise ValueError(f'{source["name"]}: no unique physical PCell at LVS location')
        instance = instances[0]
        region = db.Region(instance.cell.begin_shapes_rec(cell.layout.layer(*LAYERS[layer])))
        box = region.bbox().to_dtype(cell.layout.dbu).transformed(instance.dcplx_trans)
        record = next((r for r in manifest if r['pcell'] == pcell
                       and abs(r['origin'][0]-match['x_um']) < 1e-6
                       and abs(r['origin'][1]-match['y_um']) < 1e-6), {})
        role=record.get('role')
        # Repeated INV PCell roles in BUF must not create duplicate table labels
        # when the optional independent schematic evidence is absent.
        fallback=role if role and sum(r.get('role')==role for r in manifest)==1 else source['name']
        alias = aliases.get(_location_key(match), fallback)
        rows.append({**source, 'schematic_name': alias, 'pcell_role': record.get('role'),
                     'x_um': match['x_um'], 'y_um': match['y_um'],
                     'bbox_um': [box.left, box.bottom, box.right, box.top],
                     'mapping': 'strict persisted LVS device pair + actual GDS active geometry'})
    if len(rows) != len(matches):
        raise ValueError('LVS/source device count differs')
    return rows


def device_locations(cell, *, library=CELLS_DIR/'out'):
    """JSON-ready schematic/SPICE name -> GDS location, active bbox and W/L (µm).

    ``name`` is the unique published SPICE instance ID. ``schematic_name`` also
    retains the original XM/R label when the published independent LVS evidence
    exists. BUF labels are stage-qualified; taps/vias are not schematic devices.
    """
    with _snapshot(library) as root:
        return _device_rows(_load(cell, root))


def _device_color(row, theme):
    return COLORS[theme][MODEL_PCELL[row['model']][1]]


def _device_label(row):
    return re.sub(r'STAGE(\d+)_MXM', r'\1.XM', row['schematic_name'])


def _outlines(fig, rows, theme):
    for row in rows:
        x0,y0,x1,y1 = row['bbox_um']
        # Outline active (including resistor end regions), not the oversized well.
        xs,ys = _rect_xy([[x0-.6,y0-.6,x1+.6,y1+.6]])
        trace = _polygon_trace(xs,ys,name=row['name'],color=_device_color(row,theme),kind='device',
                               fill=.025, device=row['name'], schematic_name=row['schematic_name'])
        trace.line.width=1.8; trace.showlegend=False
        trace.hovertemplate=(f'{escape(row["schematic_name"])} · {escape(row["name"])} · {row["model"]}<br>'
                             f'W/L = {row["w_um"]:g}/{row["l_um"]:g} µm<br>'
                             f'Origin ({row["x_um"]:g}, {row["y_um"]:g}) µm<extra></extra>')
        fig.add_trace(trace)
        fig.add_trace(go.Scatter(x=[x0-.6],y=[y1+1.4],mode='text',text=[_device_label(row)],
                      textposition='top right',textfont={'color':_theme(theme)['font']['color'],'size':11},
                      showlegend=False,hoverinfo='skip',
                      meta={'kind':'device_label','device':row['name']}))


def _selection_style(rows, selected, theme):
    return {'line.color': ['#f39b24' if r['name'] == selected else _device_color(r,theme) for r in rows],
            'line.width': [4 if r['name'] == selected else 1.8 for r in rows],
            'opacity': [1 if selected is None or r['name'] == selected else .55 for r in rows]}


def _table(rows, cell, theme):
    headers = ['Schematic label','Published SPICE','Model','W/L (µm)','GDS origin (µm)']
    values = [[r['schematic_name'] for r in rows], [r['name'] for r in rows],
              [r['model'] for r in rows], [f'{r["w_um"]:g} / {r["l_um"]:g}' for r in rows],
              [f'({r["x_um"]:g}, {r["y_um"]:g})' for r in rows]]
    if not rows:
        values = [['No schematic devices'],['—'],['—'],['—'],['—']]
    fig = go.Figure(go.Table(header={'values': headers, 'fill_color': '#345571', 'font': {'color': 'white'}, 'align': 'left'},
                            cells={'values': values, 'fill_color': _theme(theme)['paper_bgcolor'],
                                   'font': _theme(theme)['font'], 'align': 'left', 'height': 28},
                            columnwidth=[1.5,1.3,1,1,1.5]))
    fig.update_layout(**_theme(theme), title=f'{cell} · schematic → layout', height=max(180, 110+len(rows)*30),
                      margin={'l': 5, 'r': 5, 't': 55, 'b': 5})
    return fig


def device_table(cell, *, library=CELLS_DIR/'out', theme='light'):
    """Ordinary Plotly companion table; use device_mapping for row-click linking."""
    _theme(theme)
    return _table(device_locations(cell,library=library),str(cell).upper(),theme)


@dataclass
class DeviceMapping:
    """Linked notebook view with ordinary Plotly figure/table fallback attributes."""
    figure: go.Figure
    table: go.Figure
    rows: list[dict]
    theme: str
    selected: str | None = None

    def select(self, device=None):
        """Highlight a published ID or unique schematic alias; None clears it."""
        if device is not None:
            matches = [r for r in self.rows if device in (r['name'],r['schematic_name'])]
            if len(matches) != 1:
                raise ValueError(f'Unknown or ambiguous schematic device: {device}')
            device = matches[0]['name']
        self.selected = device
        style = _selection_style(self.rows, device, self.theme)
        outlines = [t for t in self.figure.data if (t.meta or {}).get('kind') == 'device']
        for i,trace in enumerate(outlines):
            trace.line.color=style['line.color'][i]; trace.line.width=style['line.width'][i]
            trace.opacity=style['opacity'][i]
        if self.rows:
            fills = ['#754b08' if r['name'] == device else _theme(self.theme)['paper_bgcolor'] for r in self.rows]
            fonts = ['#ffffff' if r['name'] == device else _theme(self.theme)['font']['color'] for r in self.rows]
            self.table.data[0].cells.fill.color=[fills]*5
            self.table.data[0].cells.font.color=[fonts]*5
            self.figure.layout.updatemenus[0].active=0 if device is None else next(
                i+1 for i,row in enumerate(self.rows) if row['name']==device)
        return self

    def static_figures(self):
        """Return (layout, companion table), usable without HTML/widget support."""
        return self.figure,self.table

    def to_html(self, *, full_html=True, include_plotlyjs=True):
        """Self-contained linked HTML: table buttons work by click/Enter/Space.

        Plotly's native dropdown is also present in the ordinary Figure. No
        Python callback, FigureWidget, ipywidgets or anywidget is required.
        """
        token='tfcell-'+uuid4().hex; plot_id=token+'-plot'; table_id=token+'-table'
        indices=[i for i,t in enumerate(self.figure.data) if (t.meta or {}).get('kind')=='device']
        names=[r['name'] for r in self.rows]
        colors=[_device_color(r,self.theme) for r in self.rows]
        script="""
const plot=document.getElementById(PLOT_ID), table=document.getElementById(TABLE_ID);
const names=NAMES, indices=INDICES, colors=COLORS;
function selectDevice(name) {
  const chosen=name || null;
  if(indices.length) {
  Plotly.restyle(plot, {
    'line.color':names.map((n,i)=>n===chosen?'#f39b24':colors[i]),
    'line.width':names.map(n=>n===chosen?4:1.8),
    'opacity':names.map(n=>!chosen || n===chosen?1:0.55)
  }, indices);
  Plotly.relayout(plot, {'updatemenus[0].active':chosen?names.indexOf(chosen)+1:0});
  }
  table.querySelectorAll('tr[data-device]').forEach(row=>{
    const active=row.dataset.device===chosen;
    row.classList.toggle('selected',active);
    row.setAttribute('aria-selected',String(active));
    row.querySelector('button').setAttribute('aria-pressed',String(active));
  });
}
table.querySelectorAll('tr[data-device]').forEach(row=>{
  row.addEventListener('click',()=>selectDevice(row.dataset.device));
});
table.querySelector('button[data-device=""]').addEventListener('click',()=>selectDevice(null));
plot.on('plotly_click',event=>{
  const meta=event.points[0].data.meta;
  if(meta && meta.kind==='device') selectDevice(meta.device);
});
plot.on('plotly_buttonclicked',event=>{
  selectDevice(names.includes(event.button.label)?event.button.label:null);
});
"""
        for key,value in {'PLOT_ID':plot_id,'TABLE_ID':table_id,'NAMES':names,'INDICES':indices,'COLORS':colors}.items():
            script=script.replace(key,json.dumps(value).replace('<','\\u003c'))
        rows=[]
        for row in self.rows:
            name=escape(row['name'],quote=True); selected=row['name']==self.selected
            rows.append(f'<tr data-device="{name}" aria-selected="{str(selected).lower()}" class="{"selected" if selected else ""}">'
                        f'<td><button type="button" data-device="{name}" aria-pressed="{str(selected).lower()}">{escape(row["schematic_name"])}</button></td>'
                        f'<td>{escape(row["name"])}</td><td>{row["w_um"]:g}/{row["l_um"]:g}</td>'
                        f'<td>({row["x_um"]:g}, {row["y_um"]:g})</td></tr>')
        if not rows:
            rows=['<tr><td colspan="4">No schematic devices (FILL).</td></tr>']
        background=_theme(self.theme)['paper_bgcolor']; foreground=_theme(self.theme)['font']['color']
        panel=(f'<section id="{table_id}" class="device-table"><h3>Schematic → layout (µm)</h3>'
               '<p>Click a device, or use Tab then Enter/Space.</p><button type="button" data-device="">All devices</button>'
               '<table><thead><tr><th>Schematic label</th><th>SPICE</th><th>W/L</th><th>Origin (x,y)</th></tr></thead>'
               '<tbody>'+''.join(rows)+'</tbody></table></section>')
        chart=self.figure.to_html(full_html=False,include_plotlyjs=include_plotlyjs,div_id=plot_id,post_script=script)
        html=(f'<style>#{token}{{display:flex;flex-wrap:wrap;background:{background};color:{foreground};font:14px system-ui}}'
              f'#{token} .plot{{order:1;flex:1 1 480px;min-width:0}}'
              f'#{token} .device-table{{order:2;flex:0 1 440px;padding:12px;overflow:auto}}'
              f'#{token} table{{border-collapse:collapse;width:100%}}'
              f'#{token} th,#{token} td{{padding:8px 6px;text-align:left;border-bottom:1px solid #858585}}'
              f'#{token} button{{font:inherit;color:inherit;background:transparent;border:1px solid #858585;border-radius:4px;padding:4px 7px;cursor:pointer}}'
              f'#{token} button:focus-visible{{outline:3px solid #f39b24}}'
              f'#{token} tr[data-device]{{cursor:pointer}}'
              f'#{token} tr.selected{{background:#754b08;color:white}}'
              '</style>'
              f'<div id="{token}">{panel}<div class="plot">{chart}</div></div>'
              '<noscript>The device table remains readable. Use the separate figure/table attributes for a static notebook view.</noscript>')
        return '<!doctype html><html><head><meta charset="utf-8"></head><body>'+html+'</body></html>' if full_html else html

    def write_html(self, path, *, include_plotlyjs=True):
        """Save the complete portable linked view; no CDN is used by default."""
        path=Path(path);path.write_text(self.to_html(include_plotlyjs=include_plotlyjs))
        return path

    def _repr_html_(self):
        # Isolate Plotly/CSS across repeated notebook outputs; Colab supports iframes.
        # Character references also survive a host page with an unspecified charset.
        document=escape(self.to_html(),quote=True).encode('ascii','xmlcharrefreplace').decode('ascii')
        return '<iframe title="Cell device mapping" style="border:0;width:100%;height:760px" srcdoc="'+document+'"></iframe>'


def device_mapping(cell, *, library=CELLS_DIR/'out', theme='light', selected=None):
    """Return a linked DeviceMapping; display it directly in a notebook.

    All devices are outlined/labelled, and hover shows source W/L and position.
    ``.figure`` and ``.table`` are ordinary Plotly Figures; ``.select(name)`` also
    supports static exports. Optional original labels come only from cells/out.
    """
    _theme(theme)
    with _snapshot(library) as root:
        data=_load(cell,root);rows=_device_rows(data);fig=_cell_figure(data,theme)
        _outlines(fig,rows,theme)
        indices=[i for i,t in enumerate(fig.data) if (t.meta or {}).get('kind')=='device']
        if rows:
            buttons=[{'label':'All devices' if name is None else name,'method':'restyle',
                      'args':[_selection_style(rows,name,theme),indices]} for name in [None]+[r['name'] for r in rows]]
            fig.update_layout(margin={'t':110},updatemenus=[{'buttons':buttons,'x':0,'y':1.01,
                                                           'xanchor':'left','yanchor':'bottom'}])
        return DeviceMapping(fig,_table(rows,data.name,theme),rows,theme).select(selected)


def row_abutment(cells=('INV','NAND','NOR','NANY','FILL'), *, orientations=None,
                 library=CELLS_DIR/'out', theme='light'):
    """Abut actual GDS cells, label continuous M1 rails and advertised free M2.

    Default orientations alternate R0/MY; pass an equal-length orientation list
    to choose them. Tracks use the published full-height width/clearance promise,
    not a fresh router search. All physical layers retain their legend toggles.
    """
    _theme(theme)
    if isinstance(cells,str) or not cells:
        raise ValueError('cells must be a nonempty sequence of cell names')
    cells=list(cells)
    orientations=list(orientations) if orientations is not None else ['R0' if i%2==0 else 'MY' for i in range(len(cells))]
    if len(orientations)!=len(cells) or any(o not in ('R0','MY') for o in orientations):
        raise ValueError('Provide one R0/MY orientation per cell')
    with _snapshot(library) as root:
        data=[_load(c,root) for c in cells]
        height=data[0].height
        reference={n:data[0].abstract['pins'][n]['rects'][0][1::2] for n in VOLTAGES}
        if any(c.height!=height or any(c.abstract['pins'][n]['rects'][0][1::2]!=reference[n] for n in VOLTAGES) for c in data):
            raise ValueError('Row cells must have equal height and aligned rails')
        for cell in data:
            metal=_region(cell,LAYERS['M1'])
            for name,(y0,y1) in reference.items():
                wanted=db.Region(db.DBox(0,y0,cell.width,y1).to_itype(cell.layout.dbu))
                if not (wanted-metal).is_empty():
                    raise ValueError(f'{cell.name}.{name} has a physical M1 rail gap')
        fig=go.Figure();offset=0.;seen=set();placements=[];rails={n:[] for n in VOLTAGES}
        for index,(cell,orient) in enumerate(zip(data,orientations)):
            instance=f'{cell.name}[{index}]'
            _geometry(fig,cell,theme,offset=offset,orient=orient,instance=instance,seen=seen)
            _obstructions(fig,cell,theme,offset=offset,orient=orient,seen=seen)
            _pins(fig,cell,theme,offset=offset,orient=orient,seen=seen)
            tracks=cell.abstract['free_M2_tracks']
            xs=[offset+(cell.width-x if orient=='MY' else x) for x in tracks['x']]
            tx=[];ty=[]
            for x in xs:tx.extend([x,x,None]);ty.extend([0,height,None])
            fig.add_trace(go.Scatter(x=tx,y=ty,mode='lines',line={'color':COLORS[theme]['M2'],'dash':'dot','width':1},
                          opacity=.65,name='Free full-height M2 tracks',legendgroup='free_tracks',legendrank=0,showlegend=index==0,
                          hovertemplate=f'{instance} · {len(xs)} free M2 tracks<br>Width {tracks["wire_width"]:g} µm, clearance {tracks["clearance"]:g} µm<extra></extra>',
                          meta={'kind':'free_tracks','cell':cell.name,'instance':instance,'orient':orient,'track_x_um':xs,
                                'count':len(xs),'wire_width_um':tracks['wire_width'],'clearance_um':tracks['clearance']}))
            fig.add_trace(go.Scatter(x=[offset+cell.width/2],y=[height+7],mode='text',
                          text=[f'{cell.name} · {orient} · {len(xs)} tracks'],textfont={'size':11},
                          showlegend=False,hoverinfo='skip',meta={'kind':'cell_label','instance':instance}))
            for n in VOLTAGES:
                for x0,y0,x1,y1 in cell.abstract['pins'][n]['rects']:
                    rails[n].append([offset+x0,y0,offset+x1,y1])
            placements.append({'cell':cell.name,'instance':instance,'x_um':offset,'width_um':cell.width,'orient':orient})
            offset+=cell.width
        _rails(fig,offset,rails,theme,row=True)
        fig.update_layout(meta={'placements':placements,'width_um':offset,'height_um':height,'theme':theme,
                                'track_scope':'Published full-height free M2 tracks; not a routing result'})
        return _axes(fig,offset,height,'Row abutment · continuous rails and free M2 tracks',theme,row=True)
