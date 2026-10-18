"""Reproduce the gallery and notebook views through the browser SVG renderer.

python3 -m tritflow.schematic.review --output build/schematic-review/round4/after
CairoSVG is only a review dependency; the public SVG/PDF API does not use it.
"""
import argparse
import json
from pathlib import Path
import cairosvg

from .gallery import generate


def notebook_views(root,output):
    """Use the same public schematic/annotation calls as the notebook."""
    from tritflow.flow import load
    from tritflow.pnr import Library,place_and_route
    output.mkdir(parents=True,exist_ok=True)
    half=load(root/'examples/half_add.tv','half_add').synthesize().schematic(inputs={'a':1,'b':1},net_names=True,title='half')
    minmax=load(root/'examples/minmax.tv','minmax').synthesize().schematic(net_names=True,title='minmax')
    net=load(root/'examples/adder.tv','adder',{'N':2}).synthesize()
    adder=net.schematic(inputs={'a[0]':1,'a[1]':0,'b[0]':1,'b[1]':0,'cin':0},net_names=True,title='adder2')
    physical=place_and_route(net,Library.load(root/'cells'),output_dir=output/'physical',run_pdk_drc=False,anneal_steps=0)
    annotated=adder.annotate(parasitics=physical,title='annotated')
    views={'half':half,'minmax':minmax,'adder2':adder,'annotated':annotated}
    for name,sch in views.items():
        if any(sch.metrics['clearance_violations'].values()) or sch.metrics['short_jogs']:
            raise ValueError(f'Notebook view {name} violates schematic drawing rules')
        sch.save(output/(name+'.svg'));sch.save(output/(name+'.pdf'))
    (output/'metrics.json').write_text(json.dumps({name:s.metrics for name,s in views.items()},indent=2)+'\n')
    assert annotated.scene is adder.scene


def rasterize(folder):
    for p in sorted(folder.glob('*.svg')):
        cairosvg.svg2png(bytestring=p.read_bytes(),write_to=str(p.with_suffix('.png')),scale=1.25)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('build/schematic-review/round4/after'))
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    manifest=generate(root,args.output/'gallery')
    for item in manifest:
        if any(item['metrics']['clearance_violations'].values()) or item['metrics']['short_jogs']:
            raise ValueError(f'{item["name"]} violates schematic drawing rules')
    notebook_views(root,args.output/'notebook')
    for folder in ('gallery','notebook'):rasterize(args.output/folder)
    print(f'Rendered 22 gallery and 4 notebook PNGs through CairoSVG in {args.output}.')


if __name__=='__main__':main()
