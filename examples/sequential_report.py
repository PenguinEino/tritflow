"""Collect saved sequential trials, rechecking their waveforms and integer oracle.

Run after sequential_check completes, including separate frequency invocations:
    python3 -m examples.sequential_report --root build/seq_qualified
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from tritflow import flow
from tritflow.seq.library import EXTENSION
from tritflow.sim.runner import read_wrdata
from tritflow.sim.tools import simulator_identity
from tritflow.synth.writers import spice_names
from .sequential_check import sequence


def collect(root, names=('shift3','counter2','accumulator2')):
    root=Path(root);records=[]
    for name in names:
        out=root/name
        record=json.loads((out/'summary.json').read_text())
        net=flow.load(Path('examples')/(name+'.tv')).synthesize()
        if (out/(name+'.json')).read_text() != net.to_json():
            raise ValueError('saved gate netlist differs from current synthesis')
        vectors,initial,expected=sequence(name,net)
        encoded=spice_names([p.name for p in net.ports],('VDD','VMID','VSS','0'))
        trials=[]
        for path in (out/'spice').glob('*/measurements.json'):
            trial=json.loads(path.read_text())
            data=read_wrdata(path.parent/'waveform.txt')
            for check in trial['checks']:
                key=check['register_or_output']
                want=initial[key] if check['cycle']<0 else expected[check['cycle']][key]
                wave=data[f'v({encoded[key]})'.lower()]
                value=float(np.interp(check['sample_s'],data['time'],wave))
                if want != check['expected_trit'] or abs(value-check['actual_v']) > 1e-9:
                    raise ValueError('saved waveform/oracle differs from measurement')
                if (abs(value-5*want)<=.5) != check['passed']:
                    raise ValueError('saved band classification differs')
            if trial['passed'] != all(c['passed'] for c in trial['checks']):
                raise ValueError('inconsistent overall transient result')
            deck=path.parent/'tb.spice'
            trial.update(deck_sha256=sha256(deck.read_bytes()).hexdigest(),
                         waveform_sha256=sha256((path.parent/'waveform.txt').read_bytes()).hexdigest(),
                         simulator=simulator_identity())
            if 'runtime_s' not in trial:
                trial['runtime_s']=max(0.,(path.parent/'ngspice.log').stat().st_mtime-deck.stat().st_mtime)
                trial['runtime_origin']='approximate batch wall time from deck/log file timestamps'
            trials.append(trial)
        trials.sort(key=lambda t:t['period_s'],reverse=True)
        if not trials or not trials[0]['passed']:
            raise ValueError('missing passing baseline clock')
        caps=json.loads((out/'capacitance.json').read_text())
        record.update(synthesis=net.report(),
            clock_net={'name':net.clock,'fanout':net.report()['clock_fanout'],
                       'wire_capacitance_f':caps['nets'][net.clock]['capacitance_f'],
                       'scope':caps['scope'],'clock_tree_synthesis':False},
            frequency={'trials':trials,
                       'max_observed_passing_frequency_hz':max(t['frequency_hz'] for t in trials if t['passed']),
                       'scope':'listed sequence/load/nominal clocks only; no PVT or CTS guarantee'},
            passed=True,
            simulator=simulator_identity(),
            pdk_commit=json.loads((EXTENSION/'TDFF/provenance.json').read_text())['pdk_commit'],
            artifact_sha256={suffix:sha256((out/(name+suffix)).read_bytes()).hexdigest()
                             for suffix in ['.gds','.json','.pnr.json','.postlayout.spice']})
        pnr=json.loads((out/(name+'.pnr.json')).read_text())
        record['timings']['original_pnr_and_drc_s']=pnr['stats']['runtime_s']['total']
        record['timings']['all_spice_batch_s']=sum(t['runtime_s'] for t in trials)
        (out/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
        records.append(record)
        print(name,record['frequency']['max_observed_passing_frequency_hz'],record['clock_net'],flush=True)
    (root/'summary.json').write_text(json.dumps(records,indent=2)+'\n')
    return records


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',default='build/seq_qualified')
    p.add_argument('--names',nargs='+',default=['shift3','counter2','accumulator2'])
    args=p.parse_args();collect(args.root,args.names)
