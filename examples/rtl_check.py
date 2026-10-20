"""Reproduce synthesis and real-PDK DRC/LVS evidence for the RTL examples.

Run from the repository root: python3 -m examples.rtl_check
Artifacts and a JSON summary are written under build/hdl_verilog. A failed
physical check raises instead of being recorded as a successful qualification.
"""

import json
from pathlib import Path

from tritflow import flow
from tritflow.synth import write_artifacts


NAMES = ('full_add_rtl', 'adder4_rtl', 'alu_rtl', 'case_table', 'comparator_rtl', 'mux_rtl')


def main():
    out = Path('build/hdl_verilog')
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name in NAMES:
        print(f'{name}: synthesize', flush=True)
        circuit = flow.load(Path(__file__).with_name(name+'.tv'))
        net = circuit.synthesize()
        write_artifacts(net, out/name)
        print(f'{name}: {len(net.instances)} cells; place and route', flush=True)
        layout = net.place_and_route(output_dir=out/name, seed=0, anneal_steps=600)
        drc, lvs = layout.drc(), layout.lvs()
        summary[name] = {'synthesis':net.report(), 'drc':drc, 'lvs':lvs,
                         'gds':str(layout.gds_path), 'stats':layout.stats}
        (out/'summary.json').write_text(json.dumps(summary, indent=2, default=str)+'\n')
        assert drc['clean'], drc
        assert lvs['matched'], lvs
        print(f'{name}: DRC clean, LVS matched', flush=True)


if __name__ == '__main__':
    main()
