"""Reproduce synthesis and real-PDK DRC/LVS evidence for the RTL examples.

Run from the repository root: python3 -m examples.rtl_check
Artifacts and a JSON summary are written under build/hdl_verilog_round2. A failed
physical check raises instead of being recorded as a successful qualification.
"""

import argparse
import json
from pathlib import Path
from time import perf_counter

from tritflow import flow
from tritflow.synth import write_artifacts


NAMES = ('full_add_rtl', 'adder4_rtl', 'alu', 'case_table', 'comparator_rtl', 'mux_rtl')
# The 423-cell showcase needs more feeds than the default near-square plan.
# Keep the 20% current reserve and reduce the assumed density to spread loads.
ALU_PNR = {'rows': 32, 'current_density_a_per_um': 0.000135,
           'channel_tracks': 24, 'ripup_passes': 2}


def alu_spice(layout, folder, *, step_s=2e-9):
    """Post-layout devices plus estimated GDS wire C, with integer-oracle levels."""
    from .alu_reference import expected, representative_vectors
    from tritflow.sim.postlayout import logical_nodeset

    extracted = layout.extract(wire_c=True)
    (folder/'alu.postlayout.spice').write_text(extracted.spice)
    (folder/'alu.capacitance.json').write_text(json.dumps(extracted.capacitance, indent=2)+'\n')
    vectors = representative_vectors()
    inputs = [p.name for p in layout.netlist.ports if p.dir == 'input']
    guesses = logical_nodeset(layout.netlist, extracted.report['report'], inputs, vectors[0])
    started = perf_counter()
    result = extracted.simulate(vectors, expected=expected, load=10e-15,
                                hold_s=1e-6, step_s=step_s, edge_s=1e-9,
                                nodeset=guesses, workdir=folder/'spice', timeout=900)
    elapsed = perf_counter()-started
    measurements = result['measurements']
    (folder/'alu.measurements.json').write_text(json.dumps(measurements, indent=2)+'\n')
    assert measurements['passed'], measurements
    observed = {key: sorted({row['outputs'][key]['ideal_trit'] for row in measurements['rows']})
                for key in expected(vectors[0])}
    assert all(levels == [-1, 0, 1] for levels in observed.values())
    return {'measurements': measurements, 'vectors': vectors, 'output_levels': observed,
            'load_f': 10e-15, 'hold_s': 1e-6, 'step_s': step_s}, elapsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--names', nargs='+', choices=NAMES, default=NAMES)
    parser.add_argument('--output-root', type=Path, default=Path('build/hdl_verilog_round2'))
    args = parser.parse_args()
    out = args.output_root
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name in args.names:
        print(f'{name}: synthesize', flush=True)
        started = perf_counter()
        circuit = flow.load(Path(__file__).with_name(name+'.tv'))
        net = circuit.synthesize()
        timings = {'synthesis': perf_counter()-started}
        if name == 'alu':
            from .alu_reference import check_truth_table
            check_truth_table(circuit.design, net)
        write_artifacts(net, out/name)
        print(f'{name}: {len(net.instances)} cells; place and route', flush=True)
        started = perf_counter()
        # Separate official DRC from P&R so their wall times are not double counted.
        pnr_options = ALU_PNR if name == 'alu' else {}
        layout = net.place_and_route(output_dir=out/name, seed=0, anneal_steps=600,
                                    run_pdk_drc=False, **pnr_options)
        timings['pnr'] = perf_counter()-started
        print(f'{name}: P&R {timings["pnr"]:.2f} s; DRC', flush=True)
        started = perf_counter()
        drc = layout.drc()
        timings['drc'] = perf_counter()-started
        assert drc['clean'], drc
        print(f'{name}: DRC clean; LVS', flush=True)
        started = perf_counter()
        lvs = layout.lvs()
        timings['lvs'] = perf_counter()-started
        assert lvs['matched'], lvs
        summary[name] = {'synthesis':net.report(), 'drc':drc, 'lvs':lvs,
                         'gds':str(layout.gds_path), 'stats':layout.stats,
                         'die_um':layout.data['die'], 'wall_s':timings,
                         'pnr_options':pnr_options}
        (out/'summary.json').write_text(json.dumps(summary, indent=2, default=str)+'\n')
        print(f'{name}: DRC clean, LVS matched', flush=True)
        if name == 'alu':
            print('alu: extracted-device SPICE with estimated wire capacitance', flush=True)
            started = perf_counter()
            spice, elapsed = alu_spice(layout, out/name)
            timings['extraction_and_setup'] = perf_counter()-started-elapsed
            timings['spice'] = elapsed
            summary[name]['postlayout'] = spice
            (out/'summary.json').write_text(json.dumps(summary, indent=2, default=str)+'\n')
            print(f'alu: SPICE passed, {len(spice["vectors"])} vectors; {timings}', flush=True)


if __name__ == '__main__':
    main()
