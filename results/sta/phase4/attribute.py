"""Order-independent attribution of phase-3 ramp/recovery/tail relaxation."""
from copy import deepcopy
from itertools import product
import json,math
from tritflow import ROOT
from tritflow.netlist import GateNetlist
from tritflow.sta.propagation import PropagationLibrary
from tritflow.sta.envelope import analyze_envelope
from tritflow.sta.validate import statistics

if __name__=='__main__':
 folder=ROOT/'results/sta';v=json.load(open(folder/'phase3/validation.json'));rows=[]
 models=PropagationLibrary(['INV','NAND','NOR','NANY','BUF','TIEP','TIEZ','TIEN'],root=folder/'phase3/propagation_tables')
 zero=deepcopy(models)
 for model in zero.cells.values():
  for arc in model.arcs:arc['tail_s']=[[0. for x in row] for row in arc['tail_s']]
 for d in v['designs']:
  print(d['group'],d['design'],flush=True)
  directory=ROOT/('build/adder_scaling' if d['group']=='scaling' else 'build')/d['design']/'postlayout'
  summary=json.load(open(directory/'summary.json'));net=GateNetlist.load(directory/'inputs'/f'{summary["top"]}.json')
  base=json.load(open(folder/'phase3'/d['all_pairs_report']))
  terms={}
  for mask in range(8):
   r=analyze_envelope(net,library=models if mask&4 else zero,wire_caps={n:c['wire_f'] for n,c in base['loads'].items()},
       output_load_f=summary['output_load_f'],fixed_ramp=not bool(mask&1),include_recovery=bool(mask&2))
   terms[mask]=r.arrival
  for row in d['outputs']:
   pin=row['output'];ff={mask:rr[pin] for mask,rr in terms.items()};phi={}
   for bit,name in ((1,'internal_ramp_relaxation'),(2,'recovery_activity'),(4,'endpoint_tail')):
    phi[name]=sum(math.factorial(mask.bit_count())*math.factorial(2-mask.bit_count())/6*(ff[mask|bit]-ff[mask]) for mask in range(8) if not mask&bit)
   assert abs(ff[7]-row['predicted_s'])<1e-18
   assert abs(sum(phi.values())-(ff[7]-ff[0]))<1e-18
   path=base['paths'][pin]
   rows.append({'design':row['design'],'output':pin,'simulated_s':row['simulated_s'],'factorial_s':{str(k):x for k,x in ff.items()},
       'shapley_s':phi,'fixed_1ns_no_guard_no_tail_s':ff[0],'phase3_s':ff[7],
       'phase3_path_terms_s':{'midpoint_propagation':sum(s['delay_s'] for s in path if s['metric']=='midpoint_envelope'),
        'recovery_guard':sum(s['delay_s'] for s in path if s['metric']=='recovery_guard'),'endpoint_tail':path[-1]['settling_tail_s'] if path else 0.}})
 names=list(rows[0]['shapley_s']);means={n:sum(r['shapley_s'][n] for r in rows)/len(rows) for n in names};total=sum(means.values())
 result={'scope':'Phase-3 tables and identical loads. Factorial masks: 1=all internal ramps, 2=recovery clocks, 4=endpoint tail. Shapley averages marginal effects over every application order.',
  'mean_attribution_s':means,'fraction_of_relaxation_increase':{n:x/total for n,x in means.items()},
  'rows':rows,'without_recovery_or_tail_statistics':statistics([{'candidate_s':r['factorial_s']['1'],'simulated_s':r['simulated_s']} for r in rows],'candidate_s')}
 (folder/'phase4/attribution.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
