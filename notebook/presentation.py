"""Small HTML/Plotly display helpers; native measurements keep full precision."""

from html import escape
import json
import os

import numpy as np
from IPython.display import HTML, display

_translations = {}
_figure_translations = {}


def configure_language(language="en"):
    """Choose prose labels only; circuit names and native reports stay intact."""
    global _translations, _figure_translations
    from pathlib import Path
    _translations = (json.loads(Path(__file__).with_name("narrative_ja").joinpath("labels.json").read_text())["display"]
                     if language == "ja" else {})
    _figure_translations = (json.loads(Path(__file__).with_name("narrative_ja").joinpath("labels.json").read_text())["figure"]
                            if language == "ja" else {})


def paper_figure(png, *, width):
    """Display the paper's fresh curve with localized SVG labels in Japanese."""
    from pathlib import Path
    from IPython.display import Image
    if not _figure_translations:
        return Image(filename=str(png), width=width)
    import base64
    from localization import localize_svg
    svg = localize_svg(Path(png).with_suffix('.svg').read_text(), _figure_translations)
    data = base64.b64encode(svg.encode()).decode()
    return HTML(f'<img src="data:image/svg+xml;base64,{data}" '
                f'style="width:100%;max-width:{width}px;height:auto">')


def label(value):
    from localization import translate_text
    return translate_text(value, _translations) if isinstance(value, str) else value


def localized_display(*objects, **kwargs):
    """Translate visible HTML labels while retaining embedded circuit data."""
    from localization import localize_html
    display(*(HTML(localize_html(obj.data, _translations)) if isinstance(obj, HTML) else obj for obj in objects), **kwargs)


def title_controls(figure):
    """Reserve separate title, controls and subplot-label bands in notebook views.

    Keep native traces, frames, slider steps and button actions unchanged.
    This copy only changes paper-coordinate UI placement; PNR owns the figure
    functions themselves.
    """
    if not figure.layout.updatemenus:
        return figure
    import plotly.graph_objects as go
    result = go.Figure(figure)
    for menu in result.layout.updatemenus:
        menu.update(y=1.06,yanchor="bottom",pad={"t":0,"b":0})
    result.update_layout(title={"y":.99,"yanchor":"top"},
                         margin={"t":max(140,result.layout.margin.t or 0)})
    return result


def gds_download(path, *, url=None):
    """Offer a GDSII file as a one-click browser download.

    Generated layouts are embedded as a data link, so the button also works in a
    saved or exported notebook. ``url`` links to a published copy instead of
    embedding it (used for the 1.4 MB shuttle chip).
    """
    import base64, hashlib
    from pathlib import Path
    path = Path(path)
    data = path.read_bytes()
    href = escape(url, quote=True) if url else "data:application/octet-stream;base64,"+base64.b64encode(data).decode()
    display(HTML(
        f'<a download="{escape(path.name, quote=True)}" href="{href}" target="_blank" '
        'style="display:inline-block;margin:6px 0;padding:9px 18px;border-radius:6px;background:#1a5fb4;'
        'color:#fff;font:600 15px sans-serif;text-decoration:none">'
        f'{label("Download")} {escape(path.name)}</a>'
        f'<span style="margin-left:12px;color:#555;font:13px sans-serif">GDSII, {len(data)/1024:.0f} KB · '
        f'{label("open in KLayout")} · SHA-256 {hashlib.sha256(data).hexdigest()[:16]}…</span>'))


def show(figure):
    figure = title_controls(figure)
    if _translations:
        import plotly.graph_objects as go
        def translated(item, key=""):
            if isinstance(item, dict):
                return {k: translated(v,k) for k,v in item.items()}
            if isinstance(item, list):
                return [translated(v,key) for v in item]
            return label(item) if key in {"text","title","name","label","prefix","suffix","hovertemplate"} else item
        figure = go.Figure(translated(figure.to_plotly_json()))
    if os.environ.get("TRITFLOW_NOTEBOOK_HEADLESS") == "1":
        figure.to_json()
    else:
        display(figure)


def display_value(value):
    """Four significant digits for tables, never a change to recorded values."""
    if isinstance(value,(float,np.floating)):
        return f"{value:.4g}"
    if isinstance(value,dict):
        return "; ".join(f"{key}: {display_value(item)}" for key,item in value.items())
    if isinstance(value,(list,tuple)):
        return "["+", ".join(display_value(item) for item in value)+"]"
    return str(label(value))


def table(rows, *, details=None):
    content = "<div style='display:block;width:100%;min-width:0;max-width:100%;overflow-x:auto;contain:inline-size;box-sizing:border-box'><table width='100%' style='width:100%;min-width:0;max-width:100%;table-layout:fixed'>"+"".join("<tr>"+"".join(
        "<td style='padding:.3em .8em;white-space:normal;overflow-wrap:anywhere;vertical-align:top'>"+escape(display_value(v))+"</td>" for v in row)+"</tr>"
        for row in rows)+"</table></div>"
    if details:
        content = "<details style='min-width:0;max-width:100%;overflow-x:auto'><summary>"+escape(label(details))+"</summary>"+content+"</details>"
    display(HTML(content))


def evidence(title, value):
    text=value if isinstance(value,str) else json.dumps(value,indent=2,default=str)
    display(HTML("<details><summary>"+escape(label(title))+"</summary><pre style='white-space:pre-wrap;overflow-wrap:anywhere;max-width:100%'>"+escape(text)+"</pre></details>"))


def details_html(title, content):
    """Collapse an existing HTML report without discarding any of its rows."""
    from localization import localize_html
    display(HTML('<details><summary>'+escape(label(title))+'</summary>'+localize_html(content, _translations)+'</details>'))


def details_svg(title, svg):
    """Keep an optional native schematic available outside the main figure path."""
    details_html(title,svg)
