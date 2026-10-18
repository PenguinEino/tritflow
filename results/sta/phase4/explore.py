"""Diagnostic candidate analyses. Validation data never sets timing terms."""
import json
from itertools import product
from pathlib import Path
from tritflow import ROOT
from tritflow.netlist import GateNetlist
from tritflow.synth.simulate import ordered_instances,CELL_INPUTS
from tritflow.sta.propagation import PropagationLibrary
from tritflow.sta.validate import statistics,case_coverage

MODELS=PropagationLibrary(['INV','NAND','NOR','NANY','BUF','TIEP','TIEZ','TIEN'])
PAIRS=[(a,b) for a,b in product((-1,0,1),repeat=2) if a!=b]

def candidate(net,loads,*,classes=True,recovery=False,tail=True,lower=True):
 # row = latest clock, min/max equivalent full ramp, path
 states={p.name:{k:(.5e-9,1e-9,1e-9,[]) for k in PAIRS} for p in net.ports if p.dir=='input'}
 answer={};domains=[];details={}
 for inst in ordered_instances(net):
  pins=CELL_INPUTS[inst.cell];y=inst.pins['Y'];m=MODELS[inst.cell]
  if not pins:continue
  load=loads[y]['total_f'];out={};terminal=[]
  for pin in pins:
   parents=states.get(inst.pins[pin],{})
   if not parents:continue
   for arc in m.arcs:
    if pin not in arc['changed_inputs']:continue
    pair=(arc['from_inputs'][pin],arc['to_inputs'][pin]);opair=(arc['output_from'],arc['output_to'])
    source=[parents[pair]] if classes and pair in parents else [] if classes else list(parents.values())
    for t,lo,hi,path in source:
     axis=m.data['axes']['input_transition_s']
     if hi>axis[-1] or lo<axis[0]:domains.append([inst.name,pin,lo,hi])
     lo=max(lo,axis[0]) if lower else axis[0];hi=min(hi,axis[-1])
     knots=sorted(set([lo,hi]+[r for r in axis if lo<r<hi]))
     for r in knots:
      changing=opair[0]!=opair[1]
      d=m.sample(arc,load,r,field='propagation_s' if changing else 'recovery_s',load_policy='linear')
      tr=m.sample(arc,load,r,field='tail_s',load_policy='linear') if changing and tail else 0.
      nt=t+d;step={'instance':inst.name,'arc':arc['id'],'pair':opair,'ramp_s':r,'delay_s':d,'tail_s':tr}
      terminal.append((nt+tr,path+[step]))
      if changing:
       width=m.sample(arc,load,r,field='output_slew_10_90_s',load_policy='linear')/.8
       updates=[(opair,width,width)]
      elif recovery:
       width=(d+r/2)/.8
       updates=[(p,axis[0],max(axis[0],width)) for p in PAIRS if opair[0] in p]
      else:updates=[]
      for key,wl,wh in updates:
       prior=out.get(key)
       if prior:
        out[key]=(max(nt,prior[0]),min(wl,prior[1]),max(wh,prior[2]),path+[step] if nt>prior[0] else prior[3])
       else:out[key]=(nt,wl,wh,path+[step])
  states[y]=out
  if terminal:answer[y],details[y]=max(terminal,key=lambda x:x[0])
 return answer,domains,details

if __name__=='__main__':
 v=json.loads((ROOT/'results/sta/phase3/validation.json').read_text());rows={};domains={};case_counts={};paths={}
 modes={'scalar_slew':dict(classes=False),'class_slew':{},'class_zero_tail':dict(tail=False),
   'class_zero_lower':dict(lower=False),'class_recovery':dict(recovery=True)}
 for d in v['designs']:
  print(d['group'],d['design'],flush=True)
  folder=ROOT/('build/adder_scaling' if d['group']=='scaling' else 'build')/d['design']/'postlayout'
  summary=json.loads((folder/'summary.json').read_text())
  net=GateNetlist.load(folder/'inputs'/f'{summary["top"]}.json')
  measured=json.loads((folder/'post/measurements.json').read_text())
  report=json.loads((ROOT/'results/sta/phase3'/d['all_pairs_report']).read_text());loads=report['loads']
  for mode,options in modes.items():
   result,dom,detail=candidate(net,loads,**options)
   domains.setdefault(mode,[]).append({'design':d['design'],'violations':len(dom),'maximum_full_ramp_s':max((r[3] for r in dom),default=0)})
   case_counts.setdefault(mode,[]).append(case_coverage(measured,{r['output']:result.get(r['output'],0.) for r in d['outputs']}))
   for r in d['outputs']:
    rows.setdefault(mode,[]).append({**r,'candidate_s':result.get(r['output'],0.)})
   paths.setdefault(mode,{})[d['group']+'/'+d['design']]=detail
 result={'statistics':{m:statistics(rr,'candidate_s') for m,rr in rows.items()},'rows':rows,'domains':domains,'coverage':case_counts,'paths':paths}
 (ROOT/'results/sta/phase4/explore.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result['statistics'],indent=2))
 print('case underpredictions',{m:sum(x['underprediction_count'] for x in rr) for m,rr in case_counts.items()})
