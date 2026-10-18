"""Reproduce the SCHEM visual review set from the committed HDL examples.

    python3 -m tritflow.schematic.gallery --output build/schematic-review

This is a developer review utility, not a dependency of drawing a GateNetlist.
It renders both views of every requested design, plus the symbol legend and
one explicitly synthetic wire-C overlay; it never launches physical tools.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

from . import draw, legend


def generate(root, output):
    from tritflow.flow import load
    from examples.curated import DESIGNS
    output.mkdir(parents=True,exist_ok=True)
    cases = [('half_add','half_add',None),('full_add','full_add',None),
             ('adder2','adder',2),('adder4','adder',4),('mul1','mul1',None),('mac1','mac1',None)]
    cases += [(name,item.top,None) for name,item in DESIGNS.items()]
    manifest=[]
    for stem,top,n in cases:
        net=load(root/f'examples/{top}.tv',top,{'N':n} if n else {}).synthesize()
        for mode,expand in [('hierarchical',None),('flat','*')]:
            name=f'{stem}-{mode}'
            sch=draw(net,expand=expand,title=f'{stem} · {mode}')
            for ext in ('svg','png','pdf'):
                sch.save(output/f'{name}.{ext}')
            manifest.append({'name':name,'cells':len(net.instances),'symbols':len(sch.scene.symbols),
                             'segments':len(sch.scene.segments),'size':[sch.scene.width,sch.scene.height],
                             'notes':list(sch.scene.notes)})
    net=load(root/'examples/half_add.tv','half_add').synthesize()
    # These deliberately fabricated values test the overlay's visual range.
    # They are labelled as such and never presented as a PNR measurement.
    caps={s:(i+1)*10e-15 for i,s in enumerate(sorted(net.nets()))}
    overlay=draw(net,inputs={'a':-1,'b':1},parasitics=caps,net_names=True,
                 title='half_add · settled values / synthetic C legend')
    for ext in ('svg','png','pdf'):
        overlay.save(output/f'half_add-overlay.{ext}')
        legend().save(output/f'legend.{ext}')
    manifest.append({'name':'half_add-overlay','size':[overlay.scene.width,overlay.scene.height]})
    manifest.append({'name':'legend','size':[1088,624]})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    cards=[]
    for entry in manifest:
        name=entry['name']
        cards.append(f'<section><h2>{escape(name)}</h2><p><a href="{name}.svg">SVG</a> · '
                     f'<a href="{name}.pdf">PDF</a> · <a href="{name}.png">PNG at native resolution</a></p>'
                     f'<div><img src="{name}.svg" alt="{escape(name)}"/></div></section>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>TritFlow schematic review</title>'
        '<style>body{font:15px sans-serif;margin:32px;color:#0b0b0b}section{margin:40px 0}section div{overflow:auto;'
        'border:1px solid #e1e0d9;padding:16px}img{max-height:1000px}a{color:#2a78d6}</style>'
        '<h1>TritFlow schematic review</h1><p>Pan horizontally for the full-resolution flat views. '
        'The overlay preview uses explicitly synthetic capacitances.</p>'+''.join(cards))
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output',type=Path,default=Path('build/schematic-review'))
    args=parser.parse_args()
    manifest=generate(args.root,args.output)
    print(f'Rendered {len(manifest)} figures in {args.output}; open index.html for SVG/PDF/PNG.')


if __name__=='__main__':
    main()
