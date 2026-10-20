"""Reproduce sequential synthesis, real P&R/LVS and clocked post-layout SPICE.

    TR1UM_PDK=~/pdk/TR-1um-pinned python3 -m examples.sequential_check

No automatic reference-tree import: the checked-in cells/out_seq snapshot is the
reproducible publication barrier. Use --physical-only to prepare GDS and LVS,
then --resume to reuse that geometry (strict LVS is still rerun). Frequency
results are observed on these finite sequences with 10-fF public output loads.
"""
import argparse
import json
from pathlib import Path
import time

from tritflow import flow, synth
from tritflow.seq.spice import frequency_sweep


def digits(x, width=2):
    out=[]
    for _ in range(width):
        digit=(x+1)%3-1
        out.append(digit);x=(x-digit)//3
    return list(reversed(out))


def sequence(name, net):
    """Independent shift/radix arithmetic oracle; no source DAG or mapped gates."""
    initial = {n:0 for n in net.state_names}
    if name == 'shift3':
        values = [-1,0,1,1,-1,0,0,1,-1,1,0,-1]
        vectors = [{'d':v} for v in values]
        state = [0,0,0]; expected=[]
        for v in values:
            state = [v,*state[:2]]
            expected.append({f'q[{i}]':d for i,d in enumerate(state)})
    elif name == 'counter2':
        vectors = [{} for _ in range(12)]
        expected = [dict(zip(['n[1]','n[0]'],digits(i+1))) for i in range(len(vectors))]
    elif name == 'accumulator2':
        cases=[(1,0),(-1,1),(0,4),(0,-2),(0,-4),(0,3),(0,1),(1,-4),(0,-1),(0,2),(0,4),(0,3)]
        vectors=[dict(zip(['rst','a[1]','a[0]'],[rst,*digits(a)])) for rst,a in cases]
        value=0;expected=[]
        for rst,a in cases:
            value=0 if rst==1 else value+a
            ds=digits(value);value=3*ds[0]+ds[1]
            expected.append(dict(zip(['q[1]','q[0]'],ds)))
    else:
        raise ValueError(name)
    rows = net.cycles(vectors,initial)
    assert all({k:int(v) for k,v in row['state'].items()} == want for row,want in zip(rows,expected))
    return vectors,initial,expected


def run(name, root, *, physical_only=False, resume=False, periods=(1e-6,500e-9,250e-9,125e-9,62.5e-9,31.25e-9)):
    out=Path(root)/name;out.mkdir(parents=True,exist_ok=True)
    timings={};start=time.perf_counter()
    n=flow.load(Path('examples')/(name+'.tv')).synthesize()
    vectors,initial,expected=sequence(name,n)
    synth.write_artifacts(n,out)
    timings['synthesis_and_equivalence_s']=time.perf_counter()-start
    start=time.perf_counter()
    if resume:
        layout=flow.load_layout(n,out)
        # Revalidate the actual saved drawing even when its routing is reused.
        assert layout.drc()['clean']
    else:
        layout=n.place_and_route(output_dir=out,channel_tracks=12,
                                 sequential_rails=18 if name == 'accumulator2' else True)
    timings['pnr_drc_s']=time.perf_counter()-start
    start=time.perf_counter();report=layout.lvs()
    assert report['matched'] and report['strict_ports']
    timings['lvs_s']=time.perf_counter()-start
    record={'example':name,'synthesis':n.report(),'die_um':layout.data['die'],
            'power_dc':layout.data['power']['dc_current_check'],
            'drc_clean':True,'lvs_matched':report['matched'],'timings':timings,
            'initial_state':initial,'vectors':vectors,'independent_expected':expected}
    (out/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
    if not physical_only:
        start=time.perf_counter();extracted=layout.extract()
        (out/(name+'.postlayout.spice')).write_text(extracted.spice)
        (out/'capacitance.json').write_text(json.dumps(extracted.capacitance,indent=2)+'\n')
        timings['extract_wire_c_s']=time.perf_counter()-start
        from tritflow.extract import reference_net_map
        mapped=reference_net_map(extracted.report['report'],name)
        clk=mapped[n.clock]
        record['clock_net']={'name':n.clock,'fanout':n.report()['clock_fanout'],
            'wire_capacitance_f':extracted.capacitance['nets'][clk]['capacitance_f'],
            'scope':extracted.capacitance['scope'],'clock_tree_synthesis':False}
        start=time.perf_counter()
        freq=frequency_sweep(n,extracted.spice,vectors,initial=initial,periods_s=periods,
            lvs_report=extracted.report['report'],pdk=n.settings.pdk,workdir=out/'spice',step_s=2e-9,
            **({'solver_options':'.options rshunt=1e12'} if name == 'accumulator2' else {}))
        timings['spice_s']=time.perf_counter()-start
        record['frequency']=freq
        record['passed']=freq['max_observed_passing_frequency_hz'] is not None
        if max(periods) >= 1e-6:
            assert freq['trials'][0]['passed'], 'baseline clocked SPICE failed'
    (out/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--names',nargs='+',default=['shift3','counter2','accumulator2'])
    parser.add_argument('--output-root',default='build/seq_flow')
    parser.add_argument('--physical-only',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--period-ns',nargs='+',type=float,default=[1000,500,250,125,62.5,31.25])
    args=parser.parse_args()
    results=[]
    for name in args.names:
        result=run(name,args.output_root,physical_only=args.physical_only,resume=args.resume,
                   periods=[ns*1e-9 for ns in args.period_ns])
        results.append(result)
        print(name, result['synthesis']['cells'],result['die_um'],result.get('passed'),flush=True)
    Path(args.output_root,'summary.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__ == '__main__':main()
