"""python3 -m tritflow.pnr gate.json -o output/ --rows 4 --seed 7"""
import argparse
import json

from . import Library, place_and_route


def main():
    parser = argparse.ArgumentParser(description="TritFlow two-metal standard-cell placement and routing")
    parser.add_argument("netlist")
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("--rows", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--library", help="cells directory containing template.json and out/library.json")
    parser.add_argument("--skip-pdk-drc", action="store_true", help="explicitly skip only the external PDK check")
    args = parser.parse_args()
    result = place_and_route(args.netlist, Library.load(args.library) if args.library else None,
                             output_dir=args.output_dir, rows=args.rows, seed=args.seed,
                             run_pdk_drc=not args.skip_pdk_drc)
    print(json.dumps({"gds": str(result.gds_path), "json": str(result.json_path), **result.stats}, indent=2))


if __name__ == "__main__":
    main()
