"""Compare symbolic timing/slew labels without adjusting to circuit measurements."""
import json
from tritflow import ROOT
from tritflow.netlist import GateNetlist
from tritflow.sta.propagation import PropagationLibrary
from tritflow.sta.window import analyze_windows
from tritflow.sta.validate import statistics,case_coverage
if __name__=='__main__':
 v=json.load(open(ROOT/'results/sta/phase3/validation.json'));rows={};reports={};coverage={};failures=[]
 models=PropagationLibrary(['INV','NAND','NOR','NANY','BUF','TIEP','TIEZ','TIEN'])
 for d in v['designs']:
  folder=ROOT/('build/adder_scaling' if d['group']=='scaling' else 'build')/d['design']/'postlayout';summary=json.load(open(folder/'summary.json'))
  net=GateNetlist.load(folder/'inputs'/f'{summary["top"]}.json');measured=json.load(open(folder/'post/measurements.json'))
  base=json.load(open(ROOT/'results/sta/phase3'/d['all_pairs_report']))
  for mode in ('endpoint','reachable','free'):
   print(d['group'],d['design'],mode,flush=True)
   try:r=analyze_windows(net,library=models,wire_caps={n:c['wire_f'] for n,c in base['loads'].items()},output_load_f=summary['output_load_f'],side_states=mode)
   except Exception as ex:failures.append({'design':d['design'],'mode':mode,'error':str(ex)});print(type(ex).__name__,str(ex),flush=True);continue
   reports.setdefault(mode,{})[d['group']+'/'+d['design']]=r.to_dict()
   coverage.setdefault(mode,[]).append(case_coverage(measured,r.arrival))
   for rr in d['outputs']:rows.setdefault(mode,[]).append({**rr,'candidate_s':r.arrival[rr['output']]})
 result={'statistics':{m:statistics(rr,'candidate_s') for m,rr in rows.items()},'rows':rows,'coverage':coverage,'failures':failures,'reports':reports}
 (ROOT/'results/sta/phase4/windows.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result['statistics'],indent=2));print('case underpredictions',{m:sum(x['underprediction_count'] for x in rr) for m,rr in coverage.items()})
