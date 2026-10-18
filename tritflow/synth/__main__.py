"""Command-line TritVerilog synthesis with parameter overrides."""

import argparse
import sys

from tritflow.hdl import load
from . import report_text, synthesize, write_artifacts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="+", help="TritVerilog source file(s)")
    parser.add_argument("--top", required=True)
    parser.add_argument("-P", "--parameter", action="append", default=[], metavar="NAME=INTEGER")
    parser.add_argument("-o", "--output", default="build")
    parser.add_argument("--name", help="output top/artifact name (default top plus explicit N)")
    parser.add_argument("--fanout-limit", type=int, default=4)
    args = parser.parse_args(argv)
    try:
        params = {}
        for override in args.parameter:
            name, value = override.split("=", 1)
            if name in params:
                raise ValueError(f"duplicate parameter override {name!r}")
            params[name] = int(value)
        design = load(args.source, top=args.top, params=params)
        net = synthesize(design, fanout_limit=args.fanout_limit)
        net.top = args.name or args.top + (str(params["N"]) if "N" in params else "")
        write_artifacts(net, args.output)
        print(report_text(net.report()), end="")
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
