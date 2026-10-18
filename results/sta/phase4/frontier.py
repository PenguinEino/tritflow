"""Diagnostic timing/slew correlation with narrow measured-surface labels."""
import importlib.util
from pathlib import Path
import math,json
from tritflow import ROOT
from tritflow.netlist import GateNetlist
from tritflow.synth.simulate import ordered_instances,CELL_INPUTS
from tritflow.sta.validate import statistics,case_coverage
spec=importlib.util.spec_from_file_location('explore',Path(__file__).with_name('explore.py'));e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)


def candidate(net,loads,*,bin_s=5e-9,classes=True):
 states={p.name:{(a,b,0):(.5e-9,1e-9,1e-9,[]) for a,b in e.PAIRS} for p in net.ports if p.dir=='input'}
 answer={};domains=[];details={};nc=0
 for inst in ordered_instances(net):
  pins=CELL_INPUTS[inst.cell];y=inst.pins['Y'];m=e.MODELS[inst.cell]
  if not pins:continue
  load=loads[y]['total_f'];out={};terminal=[];axis=m.data['axes']['input_transition_s']
  for pin in pins:
   parents=states.get(inst.pins[pin],{})
   for arc in m.arcs:
    if pin not in arc['changed_inputs']:continue
    pair=(arc['from_inputs'][pin],arc['to_inputs'][pin]);opair=(arc['output_from'],arc['output_to']);changing=opair[0]!=opair[1]
    for pk,(t,lo,hi,path) in parents.items():
     if classes and pk[:2]!=pair:continue
     if hi>axis[-1] or lo<axis[0]:domains.append([inst.name,pin,lo,hi])
     lo=max(lo,axis[0]);hi=min(hi,axis[-1])
     knots=sorted(set([lo,hi]+[r for r in axis if lo<r<hi]))
     samples=[]
     for r in knots:
      d=m.sample(arc,load,r,field='propagation_s' if changing else 'recovery_s',load_policy='linear')
      tail=m.sample(arc,load,r,field='tail_s',load_policy='linear') if changing else 0
      width=m.sample(arc,load,r,field='output_slew_10_90_s',load_policy='linear')/.8 if changing else None
      samples.append((r,d,tail,width))
     if changing:
      extra=[]
      for a,b in zip(samples,samples[1:]):
       if a[3]==b[3]:continue
       for k in range(math.floor(min(a[3],b[3])/bin_s)+1,math.ceil(max(a[3],b[3])/bin_s)):
        width=k*bin_s;f=(width-a[3])/(b[3]-a[3]);extra.append(tuple(a[i]+f*(b[i]-a[i]) for i in range(4)))
      samples=sorted(samples+extra)
     for r,d,tail,width in samples:
      nt=t+d;step={'instance':inst.name,'arc':arc['id'],'pair':opair,'ramp_s':r,'delay_s':d,'tail_s':tail}
      terminal.append((nt+tail,path+[step]))
     if not changing:continue
     segments=list(zip(samples,samples[1:])) or [(samples[0],samples[0])]
     for a,b in segments:
      wl,wh=sorted([a[3],b[3]]);nt=t+max(a[1],b[1]);selected=max([a,b],key=lambda x:x[1]);r,d,tail,_=selected
      step={'instance':inst.name,'arc':arc['id'],'pair':opair,'ramp_s':r,'delay_s':d,'tail_s':tail}
      key=(*opair,math.floor((wl+wh)/2/bin_s));prior=out.get(key);nc+=1
      if prior:out[key]=(max(nt,prior[0]),min(wl,prior[1]),max(wh,prior[2]),path+[step] if nt>prior[0] else prior[3])
      else:out[key]=(nt,wl,wh,path+[step])
  states[y]=out
  if terminal:answer[y],details[y]=max(terminal,key=lambda x:x[0])
 return answer,domains,details,nc

if __name__=='__main__':
 v=json.loads((ROOT/'results/sta/phase3/validation.json').read_text());rows=[];domains=[];coverage=[];paths={}
 for d in v['designs']:
  print(d['group'],d['design'],flush=True)
  folder=ROOT/('build/adder_scaling' if d['group']=='scaling' else 'build')/d['design']/'postlayout'
  summary=json.loads((folder/'summary.json').read_text());net=GateNetlist.load(folder/'inputs'/f'{summary["top"]}.json')
  measured=json.loads((folder/'post/measurements.json').read_text());report=json.loads((ROOT/'results/sta/phase3'/d['all_pairs_report']).read_text())
  result,dom,detail,nc=candidate(net,report['loads'])
  domains.append({'design':d['design'],'violations':len(dom),'maximum_full_ramp_s':max((r[3] for r in dom),default=0),'candidates':nc})
  coverage.append(case_coverage(measured,{r['output']:result.get(r['output'],0.) for r in d['outputs']}))
  for r in d['outputs']:rows.append({**r,'candidate_s':result.get(r['output'],0.)})
  paths[d['group']+'/'+d['design']]=detail
 result={'statistics':statistics(rows,'candidate_s'),'rows':rows,'domains':domains,'coverage':coverage,'paths':paths}
 (ROOT/'results/sta/phase4/frontier.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result['statistics'],indent=2));print('case underpredictions',sum(x['underprediction_count'] for x in coverage))
