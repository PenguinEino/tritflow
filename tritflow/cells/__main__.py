"""Build and qualify the balanced-ternary standard-cell library."""
import argparse
from pathlib import Path
from tritflow import CELLS_DIR
from .circuits import circuits

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('command', choices=['build','verify','equivalence','parasitic'])
p.add_argument('--out',type=Path,default=CELLS_DIR/'out')
p.add_argument('--cells',nargs='+',choices=list(circuits()))
a = p.parse_args()
if a.command == 'build':
    from .layout import build
    if a.out.resolve()==(CELLS_DIR/'out').resolve():
        from .publish import qualified_build
        qualified_build(a.out,a.cells)
    else: build(a.out,a.cells)
elif a.command=='parasitic':
    from .parasitic import compare, publish_comparison
    if a.out.resolve()==(CELLS_DIR/'out').resolve():
        result,_=publish_comparison()
    else:result=compare(a.out)
    raise SystemExit(0 if result['passed'] else 1)
elif a.command=='equivalence':
    from .equivalence import equivalence
    raise SystemExit(0 if equivalence(a.out)['passed'] else 1)
else:
    from .verify import verify
    raise SystemExit(0 if verify(a.out,a.cells)['passed'] else 1)
