"""Small HTML/Plotly display helpers; native measurements keep full precision."""

from html import escape
import json
import os

import numpy as np
from IPython.display import HTML, display


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


def show(figure):
    figure = title_controls(figure)
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
    return str(value)


def table(rows, *, details=None):
    content = "<div style='overflow-x:auto'><table>"+"".join("<tr>"+"".join(
        "<td style='padding:.3em .8em'>"+escape(display_value(v))+"</td>" for v in row)+"</tr>"
        for row in rows)+"</table></div>"
    if details:
        content = "<details><summary>"+escape(details)+"</summary>"+content+"</details>"
    display(HTML(content))


def evidence(title, value):
    text=value if isinstance(value,str) else json.dumps(value,indent=2,default=str)
    display(HTML("<details><summary>"+escape(title)+"</summary><pre>"+escape(text)+"</pre></details>"))


def details_html(title, content):
    """Collapse an existing HTML report without discarding any of its rows."""
    display(HTML('<details><summary>'+escape(title)+'</summary>'+content+'</details>'))


def details_svg(title, svg):
    """Keep an optional native schematic available outside the main figure path."""
    details_html(title,svg)
