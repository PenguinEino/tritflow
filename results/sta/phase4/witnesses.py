"""Search actual all-pair counterexamples to a 1.5x finite-sequence ceiling.

Patterns are selected by the unchanged event model; transistor replay uses the
exact published circuit/loads and new input stimuli only. These diagnostic
observations are kept separate from the 838 validation observations.
"""
from itertools import product
from pathlib import Path
import json,re,hashlib,random
import numpy as np
from tritflow import ROOT
from tritflow.netlist import GateNetlist
from tritflow.sta.propagation import PropagationLibrary
from tritflow.sta.events import analyze_events
from tritflow.sta.diagnose import write
from tritflow.sim.runner import run_ngspice
from tritflow.sim.measure import settling_time
from tritflow.synth import evaluate_netlist
from tritflow.synth.writers import spice_names

if __name__=='__main__':
 records=[];rng=random.Random(4104)
 for n in (2,6):
  name=f'adder{n}';directory=ROOT/'build/adder_scaling'/name/'postlayout'
  summary=json.loads((directory/'summary.json').read_text());plan=json.loads((directory/'vectors.json').read_text())
  net=GateNetlist.load(directory/'inputs'/f'{summary["top"]}.json')
  base=json.loads((ROOT/'results/sta/phase3'/f'scaling_{name}.timing.json').read_text())
  models=PropagationLibrary([i.cell for i in net.instances]);pairs=[]
  for sign in (-1,1):
   for orient in product((0,1),repeat=n):
    for first,last in product((-1,0,1),repeat=2):
     if first==last:continue
     before={'cin':first};after={'cin':last}
     for i,swap in enumerate(orient):
      before[f'a[{i}]']=after[f'a[{i}]']=sign if swap else 0
      before[f'b[{i}]']=after[f'b[{i}]']=0 if swap else sign
     pairs.append((before,after))
  for _ in range(512):pairs.append(tuple({p:rng.choice((-1,0,1)) for p in plan['input_order']} for _ in range(2)))
  # Keep several distinct model-selected worst patterns, not a circuit-data fit.
  scores=[]
  for k in range(0,len(pairs),32):
   report=analyze_events(net,pairs[k:k+32],library=models,
       wire_caps={x:v['wire_f'] for x,v in base['loads'].items()},output_load_f=summary['output_load_f'])
   for pin,t in report.arrival.items():
    scores.append((t,report.patterns[pin],pin))
  candidates=[]
  for t,pat,pin in sorted(scores,key=lambda row:row[0],reverse=True):
   if pat.get('before') is not None and pat not in candidates:candidates.append(pat)
   if len(candidates)==3:break
  old=json.loads((ROOT/'results/sta/phase2'/f'scaling_{name}.timing.json').read_text())
  for pat in [old['patterns']['cout']]:
   if pat.get('before') is not None and pat not in candidates:candidates.append(pat)
  hold=1e-6;step=1e-9 if n==2 else 2e-9
  vectors=[dict(zip(plan['input_order'],plan['vectors'][0]))]
  for pat in candidates:vectors.extend([pat['before'],pat['after']])
  deck=(directory/'post/tb.spice').read_text();circuit=deck.split('.control')[0]
  for col,pin in enumerate(plan['input_order']):
   match=re.search(rf'(?m)^Vin{col}\s+(\S+)\s+0\s+PWL\([^\n]*\)',circuit)
   if not match:raise ValueError(f'Missing stimulus {pin}')
   points=[f'0 {5*vectors[0][pin]}']
   for k in range(1,len(vectors)):points += [f'{k*hold:.15g} {5*vectors[k-1][pin]}',f'{k*hold+1e-9:.15g} {5*vectors[k][pin]}']
   circuit=circuit[:match.start()]+f'Vin{col} {match[1]} 0 PWL('+ ' '.join(points)+')'+circuit[match.end():]
  outputs=list(summary['settling']['post_max_settling_s'])
  safe=spice_names(plan['input_order']+outputs,('VDD','VMID','VSS','0'))
  probes={p:f'v({safe[p]})' for p in outputs}
  folder=ROOT/'results/sta/phase4/witnesses'/name
  digest=hashlib.sha256((circuit+str(step)).encode()).hexdigest();cache=folder/'measurements.json'
  if cache.exists() and json.loads(cache.read_text()).get('sha256')==digest:record=json.loads(cache.read_text())
  else:
   print('SPICE',name,len(candidates),flush=True)
   run=run_ngspice(circuit,f'tran {step:.15g} {len(vectors)*hold:.15g} 0 {step:.15g}',list(probes.values()),timeout=600,workdir=folder)
   data=run['data'];rows=[]
   for index,pat in enumerate(candidates):
    k=2+2*index;ideal=evaluate_netlist(net,pat['after']);before=evaluate_netlist(net,pat['before'])
    times={p:settling_time(data['time'],data[probe.lower()],5*int(ideal[p]),k*hold,(k+1)*hold) for p,probe in probes.items()}
    rows.append({'pattern':pat,'settling_s':times,'output_before':{p:int(before[p]) for p in probes},'output_after':{p:int(ideal[p]) for p in probes}})
   record={'design':name,'sha256':digest,'source_deck_sha256':hashlib.sha256(deck.encode()).hexdigest(),
       'scope':'Exact published circuit, device/wire/output C and 1 ns input ramps; only pattern sequence, hold and sample step changed.',
       'step_s':step,'hold_s':hold,'rows':rows,'original_sim_max_s':summary['settling']['post_max_settling_s']}
   write(cache,record);np.savez_compressed(folder/'waveforms.npz',**data);(folder/'waveform.txt').unlink(missing_ok=True)
  records.append(record)
  print(name,{p:max(r['settling_s'][p] or 0 for r in record['rows'])/t for p,t in record['original_sim_max_s'].items()},flush=True)
 write(ROOT/'results/sta/phase4/witnesses.json',{'designs':records,'selection':'Unmodified matched-event timing on carry orientations and seeded random endpoint pairs; top candidates plus historical exact endpoint witnesses.'})
