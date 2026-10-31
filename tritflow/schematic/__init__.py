"""Synthesized ternary schematics: ``draw(net).svg``, ``.pdf`` and ``.show()``.

Only the public GateNetlist, evaluator and PnrResult.net_parasitics() interfaces
are consumed. The drawing never invokes synthesis, physical tools or ngspice.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import math
from pathlib import Path

from .layout import layout
from .model import Scene
from .render import get_language, metadata, render, set_language

_UNSET = object()


def _values(net, inputs):
    if inputs is None:
        return None
    from tritflow.synth.simulate import evaluate_netlist
    result = evaluate_netlist(net, dict(inputs), return_all=True)
    if any(v.shape != () for v in result.values()):
        raise ValueError('schematic inputs must describe one scalar input vector')
    return {name:int(value) for name,value in result.items()}


def _caps(parasitics, nets):
    """Accept the public PNR method, {net: farads}, or an extraction report.

    PNR records use wire_capacitance_f; extraction records use capacitance_f.
    Pin capacitance and total_load_f are never substituted for wire C.
    Logical net names are matched exactly and case-sensitively. The drawing
    never guesses an extracted-name alias or derives capacitance from wirelength.
    """
    if parasitics is None:
        return {}
    method = getattr(parasitics,'net_parasitics',None)
    if callable(method):
        parasitics = method()
    if not isinstance(parasitics,Mapping):
        raise TypeError('parasitics must be a farad map/report or expose net_parasitics()')
    raw = parasitics.get('nets',parasitics)
    if not isinstance(raw,Mapping):
        raise TypeError('parasitics["nets"] must map logical nets to capacitance records')
    result = {}
    for signal,record in raw.items():
        if signal not in nets:
            continue  # reports can include global rails; never draw invented nets
        if isinstance(record,Mapping):
            field = 'wire_capacitance_f' if 'wire_capacitance_f' in record else 'capacitance_f'
            if field not in record:
                raise ValueError(f'wire_capacitance_f / capacitance_f is missing for net {signal!r}')
            record = record[field]
        try:
            value = float(record)
        except (TypeError,ValueError) as exc:
            raise ValueError(f'invalid capacitance for net {signal!r}') from exc
        if not math.isfinite(value) or value < 0:
            raise ValueError(f'capacitance must be finite and nonnegative for {signal!r}')
        result[signal] = value
    return result


@dataclass(frozen=True)
class Schematic:
    """A reusable routed scene and its settled-value / wire-capacitance overlays.

    ``svg`` is text and ``pdf`` is bytes; ``save(path)`` selects by suffix.
    ``annotate(...)`` returns a new view sharing the same ``scene`` object.
    In a notebook, ``display(sch)`` or ``sch.show()`` renders native SVG.
    """
    netlist: object
    scene: Scene
    values: dict | None = None
    capacitance_f: dict | None = None
    net_names: bool = False
    title: str | None = None
    legend: bool = True

    def _vector(self):
        return render(self.scene,self.values,self.capacitance_f,self.net_names,self.title,self.legend)

    @property
    def svg(self):
        return self._vector().svg(self.title or self.scene.top,
                                  metadata(self.scene,self.values,self.capacitance_f or {}))

    @property
    def pdf(self):
        return self._vector().export('pdf')

    @property
    def metrics(self):
        """Drawing length/bends/crossings, canvas aspect and clearance audits."""
        from .metrics import measure
        result=measure(self.scene)
        vector=self._vector()
        minimum=min(i['size'] for i in vector.items if i['kind']=='text')*.75
        result.update(width_px=vector.width,height_px=vector.height,
                      rendered_width_px=vector.display_size[0],rendered_height_px=vector.display_size[1],
                      aspect_ratio=vector.width/vector.height,
                      min_font_pt_at_1000px=minimum*1000/vector.width,
                      min_font_pt_native=minimum*vector.display_size[0]/vector.width)
        return result

    def png(self, *, scale=1):
        """Raster preview for review; the default publication artifact is SVG."""
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError('PNG scale must be positive and finite')
        return self._vector().export('png',scale=scale)

    def save(self, path, *, scale=1):
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix not in {'.svg','.pdf','.png'}:
            raise ValueError('schematic output must be .svg, .pdf or .png')
        path.parent.mkdir(parents=True,exist_ok=True)
        if suffix == '.svg':
            path.write_text(self.svg,encoding='utf-8')
        else:
            path.write_bytes(self.pdf if suffix == '.pdf' else self.png(scale=scale))
        return path

    def annotate(self, *, inputs=_UNSET, parasitics=_UNSET, net_names=None, title=_UNSET):
        """Apply/remove overlays without moving a symbol or rerouting any net.

        Omitted arguments preserve the existing view; explicit None removes
        values or capacitance. ``parasitics=pnr_result`` calls its public method.
        """
        return replace(self,values=self.values if inputs is _UNSET else _values(self.netlist,inputs),
                       capacitance_f=self.capacitance_f if parasitics is _UNSET else _caps(parasitics,self.netlist.nets()),
                       net_names=self.net_names if net_names is None else bool(net_names),
                       title=self.title if title is _UNSET else title)

    def _repr_svg_(self):
        return self.svg

    def show(self):
        from IPython.display import SVG, display
        display(SVG(self.svg))
        return self


def draw(netlist, *, expand=None, inputs=None, net_names=False, parasitics=None, title=None, hierarchy=None,
         legend=True):
    """Draw a mapped GateNetlist with default collapsed module-instance blocks.

    ``expand='*'`` gives the full cell view. A path or sequence such as
    ``expand=['digit[0].fa']`` exposes those scopes and all their descendant
    gates, leaving other blocks closed. Unknown scopes are errors.
    ``hierarchy={scope: {"module": name, "ports": {formal: net}}}`` supplies
    authoritative port aliases for modules outside the verified arithmetic set.
    Supply bit-blasted scalar trits via ``inputs={'a[0]': -1, ...}``.
    ``parasitics`` accepts a PnrResult, its report, or ``{net: farads}``.
    ``legend=False`` drops the cell count and the keys under the drawing.
    """
    scene = layout(netlist,expand,hierarchy)
    return Schematic(netlist,scene,_values(netlist,inputs),_caps(parasitics,netlist.nets()),bool(net_names),title,
                     bool(legend))


def legend():
    """Return the symbol legend as an SVG/PDF-capable vector figure."""
    from .legend import SymbolLegend
    return SymbolLegend()


__all__ = ['draw','legend','Schematic','set_language','get_language']
