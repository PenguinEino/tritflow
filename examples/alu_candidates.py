"""Reproduce the Round 3 instruction/area experiments with the real library.

Run python3 -m examples.alu_candidates. Each candidate keeps two-trit a,b and
three result trits. Sources and native reports are saved beside the measurements;
the final ALU's SPICE evidence is produced by examples.rtl_check --names alu.
"""

import argparse
import json
from pathlib import Path
from time import perf_counter

from tritflow import flow
from tritflow.synth import write_artifacts


BODIES = {
    'case_add_sub_right': "case(op) 1'tT:r=a-b; 1't0:r=a>>1; 1't1:r=a+b; endcase",
    'case_signed_add': "case(op) 1'tT,1't1:r=a+op*b; 1't0:r=a>>1; endcase",
    'case_signed_add_neg': "case(op) 1'tT,1't1:r=a+op*b; 1't0:r=-a; endcase",
    'case_signed_add_pass': "case(op) 1'tT,1't0,1't1:r=a+op*b; endcase",
}
DEFAULT_NAMES = tuple(BODIES)
BODIES.update({
    'case_add_sub_neg': "case(op) 1'tT:r=a-b; 1't0:r=-a; 1't1:r=a+b; endcase",
    'case_add_sub_left': "case(op) 1'tT:r=a-b; 1't0:r=a<<1; 1't1:r=a+b; endcase",
})


def source(name):
    return (f'module {name}(input trit [1:0] a,b,input trit op,'
            f'output reg trit [2:0] r);always @* {BODIES[name]} endmodule\n')


def check_reference(name, design, net):
    """Independent integer prediction for all 243 candidate input states."""
    from .alu_reference import decode
    from tritflow.synth import evaluate_netlist

    table = design.truth_table()
    actual = evaluate_netlist(net,{key:table[key] for key in design.inputs})
    for row in range(243):
        a = decode([table['a[1]'][row],table['a[0]'][row]])
        b = decode([table['b[1]'][row],table['b[0]'][row]])
        op = int(table['op'][row])
        middle = (-a if name in {'case_signed_add_neg','case_add_sub_neg'} else
                  3*a if name == 'case_add_sub_left' else
                  a if name == 'case_signed_add_pass' else (a+1)//3)
        expected = a-b if op == -1 else a+b if op == 1 else middle
        for result in (table,actual):
            assert decode([result[f'r[{i}]'][row] for i in (2,1,0)]) == expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--names',nargs='+',choices=BODIES,default=DEFAULT_NAMES)
    parser.add_argument('--synthesis-only',action='store_true',help='Screen cells without physical tools')
    parser.add_argument('--output-root',type=Path,default=Path('build/hdl_verilog_round3/candidates'))
    parser.add_argument('--mpw-template',type=Path,default=Path.home()/'TR-1um_MPW_Sanken')
    args = parser.parse_args()
    args.output_root.mkdir(parents=True,exist_ok=True)
    summary = {}
    for name in args.names:
        path = args.output_root/(name+'.tv')
        path.write_text(source(name))
        started = perf_counter()
        circuit = flow.load(path)
        net = circuit.synthesize()
        check_reference(name,circuit.design,net)
        times = {'synthesis':perf_counter()-started}
        item = {'cells':len(net.instances),'synthesis':net.report(),'wall_s':times}
        summary[name] = item
        folder = args.output_root/name
        write_artifacts(net,folder)
        if args.synthesis_only:
            item['physical'] = 'not run'
            print(name,json.dumps(item),flush=True)
            (args.output_root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
            continue
        started = perf_counter()
        layout = net.place_and_route(output_dir=folder,seed=0,anneal_steps=600,run_pdk_drc=False)
        times['pnr'] = perf_counter()-started
        item.update(die_um=layout.data['die'],stats=layout.stats)
        started = perf_counter()
        drc = layout.drc()
        times['drc'] = perf_counter()-started
        assert drc['clean'],drc
        started = perf_counter()
        lvs = layout.lvs()
        times['lvs'] = perf_counter()-started
        assert lvs['matched'],lvs
        item.update(drc_clean=True,lvs_matched=True)
        started = perf_counter()
        try:
            chip = layout.result.to_chip(pdk_root=net.settings.pdk,
                klayout_binary=net.settings.klayout,
                mpw_template=args.mpw_template if args.mpw_template.is_dir() else None)
            report = chip.signoff()
            assert report['clean'],report
            item['chip'] = {'clean':True,'gds':str(chip.gds_path),'pad_count':len(chip.data['pad_map'])}
        except ValueError as error:
            # Oversize is an expected experiment result. Native verification
            # failures are deliberately not caught or converted to passes.
            if 'does not fit the TEG' not in str(error):
                raise
            item['chip'] = {'clean':False,'error':str(error)}
        times['chip_and_signoff'] = perf_counter()-started
        print(name,json.dumps(item),flush=True)
        (args.output_root/'summary.json').write_text(json.dumps(summary,indent=2,default=str)+'\n')


if __name__ == '__main__':
    main()
