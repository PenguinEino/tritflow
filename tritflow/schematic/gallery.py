"""Render the review set and before/after geometry report from committed HDL.

    python3 -m tritflow.schematic.gallery --output build/schematic-review

The overlay routes the real half-adder cell library and calls the public PNR
net_parasitics() method. The geometry comparison uses the frozen phase-2
gallery; the original baseline remains in the JSON manifest.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

from . import draw, legend
from .metrics import measure
from .model import Scene


def _summary(name,before,after):
    return (f'| {name} | {before["wire_length_px"]} → {after["wire_length_px"]} | '
            f'{before["bends_total"]} → {after["bends_total"]} | '
            f'{before["bends_per_net_mean"]:.2f} → {after["bends_per_net_mean"]:.2f} | '
            f'{before["bends_per_net_max"]} → {after["bends_per_net_max"]} | '
            f'{before["crossings"]} → {after["crossings"]} | '
            f'{before["aspect_ratio"]:.2f} → {after["aspect_ratio"]:.2f} |')


def generate(root,output):
    from tritflow.flow import load
    from tritflow.pnr import Library, place_and_route
    from examples.curated import DESIGNS
    output.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((Path(__file__).parent/'assets/baseline_metrics.json').read_text())['items']
    previous={item['name']:item['metrics'] for item in json.loads(
        (Path(__file__).parent/'assets/phase2_metrics.json').read_text())}
    cases=[('half_add','half_add',None),('full_add','full_add',None),('adder2','adder',2),
           ('adder4','adder',4),('mul1','mul1',None),('mac1','mac1',None)]
    cases += [(name,item.top,None) for name,item in DESIGNS.items()]
    manifest=[]
    for stem,top,n in cases:
        net=load(root/f'examples/{top}.tv',top,{'N':n} if n else {}).synthesize()
        for mode,expand in [('hierarchical',None),('flat','*')]:
            name=f'{stem}-{mode}'
            sch=draw(net,expand=expand,title=f'{stem} · {mode}')
            for ext in ('svg','png','pdf'):sch.save(output/f'{name}.{ext}')
            manifest.append({'name':name,'cells':len(net.instances),'symbols':len(sch.scene.symbols),
                             'metrics':measure(sch.scene),'before':baseline[name],
                             'notes':list(sch.scene.notes)})
    net=load(root/'examples/half_add.tv','half_add').synthesize()
    result=place_and_route(net,Library.load(root/'cells'),output_dir=output/'physical',
                           run_pdk_drc=False,anneal_steps=0)
    report=result.net_parasitics()
    overlay=draw(net,inputs={'a':-1,'b':1},parasitics=result,net_names=True,
                 title='half_add · settled trits and routed wire capacitance')
    metrics=overlay.metrics
    for ext in ('svg','png','pdf'):
        overlay.save(output/f'half_add-overlay.{ext}')
        legend().save(output/f'legend.{ext}')
    manifest.append({'name':'half_add-overlay','metrics':metrics,'before':baseline['half_add-overlay'],
                     'parasitics':{'schema':report['schema'],'source':'physical/half_add.net_parasitics.json',
                                    'library_mock':result.data['library']['mock'],
                                    'wire_capacitance_f':sum(overlay.capacitance_f.values())}})
    empty=measure(Scene('legend',(),(),{},(),{},1088,624))
    manifest.append({'name':'legend','metrics':empty,'before':baseline['legend']})
    for item in manifest:item['previous']=previous[item['name']]
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows=['# Schematic geometry: phase 2 → phase 3','',
          'Wire length is in drawing pixels, not chip micrometres. A bend is a unique same-net '
          'degree-two orthogonal corner; T joins are excluded. Crossings count distinct '
          'different-net perpendicular intersections. Aspect is full canvas width / height; '
          'the real-C overlay includes its annotation table.','',
          '| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect |',
          '|---|---:|---:|---:|---:|---:|---:|']
    rows += [_summary(item['name'],item['previous'],item['metrics']) for item in manifest]
    rows += ['', 'A short jog is a leg shorter than one gate input pitch (32 px) between two '
             'degree-two corners. Terminal stubs and T joins are excluded; pin access uses the '
             'finer 8 px raster. Edge runs count positive overlap along any symbol/label '
             'keep-out boundary; perpendicular pin contact is allowed.', '',
             '| Figure | Short jogs | Rotated gates | Symbol-edge runs |',
             '|---|---:|---:|---:|']
    for item in manifest:
        old,new=item['previous'],item['metrics']
        rows.append(f'| {item["name"]} | {old["short_jogs"]} → {new["short_jogs"]} | '
                    f'{old["rotated_gates"]} → {new["rotated_gates"]} | '
                    f'{old["symbol_edge_runs"]} → {new["symbol_edge_runs"]} |')
    (output/'metrics.md').write_text('\n'.join(rows)+'\n')
    cards=[]
    for entry in manifest:
        name=entry['name'];m=entry['metrics'];old=entry['previous']
        detail=(f'Wire {old["wire_length_px"]:,} → {m["wire_length_px"]:,} px; '
                f'bends {old["bends_total"]} → {m["bends_total"]}; '
                f'crossings {old["crossings"]} → {m["crossings"]}; '
                f'aspect {old["aspect_ratio"]:.2f} → {m["aspect_ratio"]:.2f}. '
                f'Short jogs {old["short_jogs"]} → {m["short_jogs"]}; '
                f'rotated gates {old["rotated_gates"]} → {m["rotated_gates"]}; '
                f'symbol-edge runs {m["symbol_edge_runs"]}.')
        cards.append(f'<section><h2>{escape(name)}</h2><p>{detail}</p><p><a href="{name}.svg">SVG</a> · '
                     f'<a href="{name}.pdf">PDF</a> · <a href="{name}.png">PNG</a></p>'
                     f'<img src="{name}.svg" alt="{escape(name)}"/></section>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>TritFlow schematic review</title>'
        '<style>body{font:16px Georgia,serif;margin:40px auto;max-width:1400px;padding:0 32px;color:#0b0b0b}'
        'section{margin:56px 0}img{width:100%;height:auto;border:1px solid #e1e0d9}a{color:#2a78d6}</style>'
        '<h1>TritFlow schematic review</h1><p><a href="metrics.md">Before / after metrics for every figure</a>. '
        'The overlay uses real routed cell-library geometry and PnrResult.net_parasitics(). '
        'Capacitance is an uncalibrated wire-C estimate; this gallery does not rerun DRC/LVS.</p>'+''.join(cards))
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output',type=Path,default=Path('build/schematic-review'))
    args=parser.parse_args()
    manifest=generate(args.root,args.output)
    print(f'Rendered {len(manifest)} figures with before/after metrics in {args.output}.')


if __name__=='__main__':main()
