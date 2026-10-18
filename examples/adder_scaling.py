"""Produce cached real-PNR adder scaling and the full-add output-load boundary.

Run from any directory; --jobs 2 runs independent widths in separate processes.
Use --load-only to refresh the 500 ns load experiment without rebuilding adders.
"""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sizes',nargs='+',type=int,default=list(range(1,7)))
    parser.add_argument('--jobs',type=int,default=1)
    parser.add_argument('--load-only',action='store_true')
    parser.add_argument('--skip-load',action='store_true')
    args = parser.parse_args()
    from tritflow.sim.scaling import run_scaling, compare_phase3
    from tritflow.viz.scaling import scaling_figure, load_sweep_figure, scaling_fit_figure
    passed = True
    if not args.load_only:
        result = run_scaling(args.sizes,jobs=args.jobs)
        scaling_figure(result).write_html(ROOT/'results/adder_scaling.html',include_plotlyjs='cdn')
        scaling_fit_figure(result).write_html(ROOT/'results/adder_scaling_fit.html',include_plotlyjs='cdn')
        if (ROOT/'results/phase3_assumed/adder_scaling.json').is_file():
            compare_phase3(result)
        passed = result['passed']
    if not args.skip_load:
        from tritflow.sim.load_sweep import sweep_output_load
        # Other streams may atomically republish PNR/library files while this
        # long experiment runs. Retry stale evidence, never a physical failure.
        for attempt in range(3):
            try:
                result = sweep_output_load()
                break
            except RuntimeError as error:
                if 'changed during' not in str(error) or attempt == 2: raise
                print(f'Retrying load sweep after concurrent publication: {error}',flush=True)
        load_sweep_figure(result).write_html(ROOT/'results/full_add_load_sweep.html',include_plotlyjs='cdn')
        passed = passed and result['boundary_found']
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
