"""Nominal extracted-device TDFF timing and static current, in seconds/amperes."""
from itertools import permutations, product
import json
from pathlib import Path

import numpy as np

from tritflow import PDK_ROOT
from tritflow.sim.runner import run_ngspice
from tritflow.sim.tools import simulator_identity
from tritflow.sim.spice import model_includes, simulation_netlist
from .library import EXTENSION, digest


def pwl(points):
    return 'PWL(' + ' '.join(f'{t:.12g} {v:.12g}' for t,v in points) + ')'


def base(extension=EXTENSION, pdk=PDK_ROOT):
    return ('TDFF extracted-device qualification\n' + model_includes(pdk) + '\n'
            + simulation_netlist((Path(extension)/'TDFF/TDFF.ext.spice').read_text())
            + '\n.temp 27\n.options method=gear maxord=2 reltol=1e-5 abstol=1e-13\n')


def timing(load, *, setup=300e-9, hold=None, slew=1e-9, extension=EXTENSION,
           workdir=None, pdk=PDK_ROOT):
    """Six directed transitions; setup/hold measured to CLK's 0-V crossing."""
    pairs = list(permutations((-1,0,1), 2))
    first, second, stop = 100e-9, 1000e-9, 1500e-9
    s = base(extension, pdk) + 'VP VDD 0 5\nVN VSS 0 -5\nVM VMID 0 0\n'
    s += 'VC CLK 0 ' + pwl([(0,-5),(first-slew/2,-5),(first+slew/2,5),
        (500e-9-slew/2,5),(500e-9+slew/2,-5),(second-slew/2,-5),(second+slew/2,5)])+'\n'
    for i,(old,new) in enumerate(pairs):
        change = second - setup if hold is None else 700e-9
        points = [(0,5*old),(change-.5e-9,5*old),(change+.5e-9,5*new)]
        if hold is not None:
            change = second+hold
            points += [(change-.5e-9,5*new),(change+.5e-9,5*old)]
        s += f'X{i} d{i} CLK q{i} VDD VMID VSS TDFF\nC{i} q{i} 0 {load:.12g}\nVD{i} d{i} 0 {pwl(points)}\n'
    result = run_ngspice(s, f'tran 0.5n {stop:.12g} 0 0.5n',
                         [f'v(q{i})' for i in range(len(pairs))],
                         workdir=workdir, timeout=300)
    t = result['data']['time']
    rows = []
    for i,(old,new) in enumerate(pairs):
        y = result['data'][f'v(q{i})']
        window = (t >= second) & (t <= stop)
        outside = np.flatnonzero(np.abs(y[window] - 5*new) > .5)
        samples = t[window]
        settle = None if len(outside) and outside[-1] == len(samples)-1 else (
            float(samples[outside[-1]+1]-second) if len(outside) else 0.)
        rows.append({'old':old, 'new':new, 'final_v':float(y[-1]),
                     'passed':bool(abs(y[-1]-5*new) <= .5), 'clock_to_q_settle_s':settle})
    return rows


def characterize(extension=EXTENSION, *, output_dir='build/seq_flow/characterize', pdk=PDK_ROOT):
    """Sweep six transitions at 10/100 fF and search 0.5-ns setup/hold brackets.

    Setup requires correct capture and settled-band clock-to-Q no worse than
    nominal + max(10%, 0.5 ns). Hold requires retaining the captured value after
    a post-edge D reversal. Bounds are nominal empirical observations, not PVT.
    """
    extension, output_dir = Path(extension), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timing_rows = []
    for load in (10e-15,100e-15):
        tag = f'{load*1e15:g}f'
        nominal = timing(load, extension=extension, pdk=pdk, workdir=output_dir/tag/'nominal')
        if not all(r['passed'] and r['clock_to_q_settle_s'] is not None for r in nominal):
            raise ValueError('TDFF nominal capture failed')
        cache = []
        def good(mode, offset):
            rows = timing(load, extension=extension, pdk=pdk,
                          workdir=output_dir/tag/f'{mode}_{offset*1e9:.4f}n',
                          **{mode: offset})
            passed = all(r['passed'] for r in rows)
            if mode == 'setup':
                passed &= all(r['clock_to_q_settle_s'] is not None and
                    r['clock_to_q_settle_s'] <= n['clock_to_q_settle_s'] + max(.1*n['clock_to_q_settle_s'], .5e-9)
                    for r,n in zip(rows,nominal))
            cache.append({'mode':mode,'offset_s':offset,'passed':bool(passed),'arcs':rows})
            return passed
        row = {'load_f':load, 'clock_slew_s':1e-9, 'data_slew_s':1e-9, 'nominal_arcs':nominal,
               'clock_to_q_settle_s':max(r['clock_to_q_settle_s'] for r in nominal)}
        for mode in ('setup','hold'):
            low, high = -100e-9, 200e-9
            if good(mode,low) or not good(mode,high):
                raise ValueError(f'TDFF {mode} boundary not bracketed')
            while high-low > .5e-9:
                mid = (low+high)/2
                if good(mode, mid): high=mid
                else: low=mid
            bound = max(0., float(np.ceil(high/.5e-9)*.5e-9))
            if not good(mode,bound):
                raise ValueError('rounded timing bound did not pass')
            row[mode+'_s'] = bound
            row[mode+'_bracket_s'] = [low,high]
        row['trials'] = cache
        timing_rows.append(row)
        (output_dir/f'timing_{tag}.json').write_text(json.dumps(row,indent=2)+'\n')
    # Stored state and D are independent while CLK is high. While CLK is low
    # the master follows D; include both phases and every D/Q combination.
    s = base(extension,pdk)
    cases = list(product((-1,0,1), (-1,0,1), (-1,1)))
    vectors = []
    for i,(q,d,clk) in enumerate(cases):
        points = [(0,-5),(100e-9,-5),(101e-9,5)]
        if clk == -1: points += [(500e-9,5),(501e-9,-5)]
        s += (f'VP{i} p{i} 0 5\nVN{i} n{i} 0 -5\nVM{i} m{i} 0 0\n'
              f'X{i} d{i} c{i} q{i} p{i} m{i} n{i} TDFF\nC{i} q{i} 0 10f\n'
              f'VC{i} c{i} 0 {pwl(points)}\nVD{i} d{i} 0 {pwl([(0,5*q),(300e-9,5*q),(301e-9,5*d)])}\n')
        vectors += [f'v(q{i})', f'i(VP{i})', f'i(VM{i})', f'i(VN{i})']
    result = run_ngspice(s, 'tran 1n 1u 0 1n', vectors, workdir=output_dir/'static', timeout=300)
    data = result['data']; mask = data['time'] >= 900e-9
    dc = []
    for i,(q,d,clk) in enumerate(cases):
        currents = {rail: float(np.mean(data[f'i(v{v}{i})'][mask])) for rail,v in [('VDD','p'),('VMID','m'),('VSS','n')]}
        out = float(np.mean(data[f'v(q{i})'][mask]))
        dc.append({'state_trit':q,'input_trits':[d,clk],'output_v':{'Q':out},
                   'rail_current_a':currents,'passed':abs(out-5*q)<=.5})
    if not all(r['passed'] for r in dc):
        raise ValueError('TDFF static hold failed')
    report = {'schema_version':1,'simulator':simulator_identity(),'cell':'TDFF','conditions':{'temperature_c':27,'band_v':.5},
              'source_sha256':digest(extension/'TDFF/TDFF.ext.spice'), 'timing':timing_rows,
              'dc':dc,'max_static_current_a':max(abs(i) for r in dc for i in r['rail_current_a'].values()),
              'scope':'nominal extracted MOS/RR incl junctions; no interconnect C or PVT',
              'passed':True}
    (extension/'TDFF/TDFF.char.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps({k:v for k,v in characterize().items() if k not in {'dc','timing'}},indent=2))
