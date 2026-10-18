"""Reproduce phase-3 diagnosis from independent cell tables and SIM snapshots.

No simulation result is used to set an envelope term. This audit checks full
local-class coverage, unchanged loading, preserved matched predictions, global
underpredictions and the old/new endpoint-tail sampling conditions.
"""
from __future__ import annotations

from itertools import product
import json
from pathlib import Path

from tritflow import ROOT
from tritflow.netlist import GateNetlist
from tritflow.synth import evaluate_netlist
from .diagnose import write
from .propagation import PropagationLibrary
from .validate import DESIGNS, _read, _sha, fingerprint


def audit():
    """Write a provenance-checked diagnostic; require current validation first."""
    folder=ROOT/'results/sta';current=_read(folder/'validation.json')
    old=_read(folder/'phase2/validation.json')
    if current['source_sha256']!=fingerprint():
        raise RuntimeError('Results changed after validation; validate before auditing')
    models=PropagationLibrary(('INV','NAND','NOR','NANY','BUF'))
    class_coverage={}
    for name,model in models.cells.items():
        pins=model.data['inputs'];states=list(product((-1,0,1),repeat=len(pins)))
        expected={(a,b) for a,b in product(states,repeat=2) if a!=b}
        present={(tuple(a['from_inputs'][p] for p in pins),tuple(a['to_inputs'][p] for p in pins)) for a in model.arcs}
        class_coverage[name]={'expected':len(expected),'present':len(present),
            'missing':[[list(a),list(b)] for a,b in sorted(expected-present)],
            'all_knots_passed':all(all(all(row) for row in a['passed']) for a in model.arcs)}
    previous={(d['group'],d['design']):d for d in old['designs']}
    records=[]
    for d in current['designs']:
        key=d['group'],d['design'];prior=previous[key]
        directory=next(path for g,n,path in DESIGNS if (g,n)==key)
        sim=directory/'postlayout';summary=_read(sim/'summary.json')
        net=GateNetlist.load(sim/'inputs'/f'{summary["top"]}.json')
        measured=_read(sim/'post/measurements.json');plan=_read(sim/'vectors.json')
        envelope=_read(folder/d['all_pairs_report'])
        graph=_read(folder/'phase2'/prior['all_pairs_report'])
        before_tested={r['output']:r['tested_predicted_s'] for r in prior['outputs']}
        for r in d['outputs']:
            pin=r['output'];index,row=max(enumerate(measured['rows']),key=lambda q:q[1]['outputs'][pin]['settling_s'])
            first=dict(zip(plan['input_order'],row['previous_trits'])) if row['previous_trits'] is not None else None
            last=dict(zip(plan['input_order'],row['input_trits']))
            endpoints=None if first is None else [int(evaluate_netlist(net,p)[pin]) for p in (first,last)]
            path=envelope['paths'][pin];tail=None
            if path:
                stage=path[-1];model=models[stage['cell']]
                arc=next(a for a in model.arcs if a['id']==stage['arc_id'])
                if arc['output_from']!=arc['output_to']:
                    tail={'class':arc['id'],'load_f':stage['load_f'],
                        'selected_ramp_s':stage['input_transition_s'],'envelope_tail_s':stage['settling_tail_s'],
                        'same_class_at_1ns_tail_s':model.sample(arc,stage['load_f'],1e-9,field='tail_s',load_policy='linear')}
            records.append({'design':r['design'],'output':pin,
                'fixed_endpoint_s':r['fixed_ramp_endpoint_s'],
                'fixed_class_envelope_s':r['fixed_ramp_class_envelope_s'],
                'ramp_envelope_without_recovery_s':r['ramp_envelope_without_recovery_s'],
                'conservative_envelope_s':r['predicted_s'],'simulated_s':r['simulated_s'],
                'pessimism_factor':r['predicted_s']/r['simulated_s'],
                'maximum_observation_row':index,'maximum_observation_pattern':{'before':first,'after':last},
                'output_settled_endpoints':endpoints,'endpoint_stable_maximum':bool(endpoints and endpoints[0]==endpoints[1]),
                'loading_identical_to_phase2':envelope['loads']==graph['loads'],
                'matched_prediction_identical_to_phase2':r['tested_predicted_s']==before_tested[pin],
                'endpoint_tail_sampling':tail})
    result={'scope':'Diagnosis and empirical coverage, not a fitted margin or universal analog bound.',
        'validation_sha256':_sha(folder/'validation.json'),'source_sha256':current['source_sha256'],
        'complete_local_class_coverage':class_coverage,
        'mechanisms':[
            'No directed local endpoint class is absent from characterization. The fixed-ramp symbolic graph excludes transient classes that cannot share settled primary-input endpoints.',
            'A sampled output slew was discarded by the old global graph; downstream stages and the final tail were all sampled at a full 1 ns ramp.',
            'Unchanged-output activity could terminate at its gate in the old graph. The envelope propagates its recovery clock as a downstream guard.',
            'The actual load model is unchanged. Maxima over independent classes and internal ramp knots, including false paths and incompatible slow conditions, explain envelope pessimism.'],
        'ablation_statistics':{k:current['statistics'][k] for k in
            ('fixed_ramp_endpoint','fixed_ramp_class_envelope','ramp_envelope_without_recovery','conservative_envelope')},
        'worst_case_validation':current['worst_case_validation'],
        'endpoint_stable_maximum_count':sum(r['endpoint_stable_maximum'] for r in records),
        'all_loads_unchanged':all(r['loading_identical_to_phase2'] for r in records),
        'all_matched_predictions_unchanged':all(r['matched_prediction_identical_to_phase2'] for r in records),
        'outputs':records}
    if current['source_sha256']!=fingerprint():raise RuntimeError('Publication changed during audit')
    write(folder/'diagnosis/phase3_audit.json',result)
    print(json.dumps({k:result[k] for k in ('endpoint_stable_maximum_count','all_loads_unchanged','all_matched_predictions_unchanged')},indent=2))
    return result


if __name__=='__main__':audit()
