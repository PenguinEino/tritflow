"""Replay the finest-bin settled-endpoint cout witness on the exact circuit."""
from pathlib import Path
import hashlib,json,re
import numpy as np
from tritflow import ROOT
from tritflow.netlist import GateNetlist
from tritflow.sta.diagnose import write
from tritflow.sim.runner import run_ngspice
from tritflow.sim.measure import settling_time
from tritflow.synth import evaluate_netlist
from tritflow.synth.writers import spice_names
if __name__=='__main__':
 source=ROOT/'build/adder_scaling/adder2/postlayout';target=ROOT/'results/sta/phase4/exact_witness'
 convergence=json.load(open(ROOT/'results/sta/phase4/bin_convergence.json'));pat=convergence['rows'][-1]['cout_witness']
 summary=json.load(open(source/'summary.json'));plan=json.load(open(source/'vectors.json'));net=GateNetlist.load(source/'inputs/adder2.json')
 vectors=[dict(zip(plan['input_order'],plan['vectors'][0])),pat['before'],pat['after']]
 hold=1e-6;step=1e-9;original=(source/'post/tb.spice').read_text();circuit=original.split('.control')[0]
 for col,pin in enumerate(plan['input_order']):
  match=re.search(rf'(?m)^Vin{col}\s+(\S+)\s+0\s+PWL\([^\n]*\)',circuit)
  points=[f'0 {5*vectors[0][pin]}']
  for k in range(1,len(vectors)):points.extend([f'{k*hold:.15g} {5*vectors[k-1][pin]}',f'{k*hold+1e-9:.15g} {5*vectors[k][pin]}'])
  circuit=circuit[:match.start()]+f'Vin{col} {match[1]} 0 PWL('+ ' '.join(points)+')'+circuit[match.end():]
 outputs=list(summary['settling']['post_max_settling_s']);safe=spice_names(plan['input_order']+outputs,('VDD','VMID','VSS','0'))
 probes={p:f'v({safe[p]})' for p in outputs}
 digest=hashlib.sha256((circuit+str(step)).encode()).hexdigest();cache=target/'measurements.json'
 if cache.exists() and json.load(open(cache)).get('sha256')==digest:result=json.load(open(cache))
 else:
  run=run_ngspice(circuit,f'tran {step:.15g} {len(vectors)*hold:.15g} 0 {step:.15g}',list(probes.values()),timeout=600,workdir=target)
  data=run['data'];ideal=evaluate_netlist(net,pat['after'])
  observed={p:settling_time(data['time'],data[q.lower()],5*int(ideal[p]),2*hold,3*hold) for p,q in probes.items()}
  result={'sha256':digest,'source_deck_sha256':hashlib.sha256(original.encode()).hexdigest(),
   'scope':'Exact published circuit and loads, 1 ns ramps; new window-model endpoint witness only. Separate from 838-case validation.',
   'step_s':step,'hold_s':hold,'pattern':pat,'settling_s':observed,
   'original_sim_max_s':summary['settling']['post_max_settling_s'],
   'ratio_vs_original_max':{p:observed[p]/t if observed[p] is not None else None for p,t in summary['settling']['post_max_settling_s'].items()}}
  write(cache,result);np.savez_compressed(target/'waveforms.npz',**data);(target/'waveform.txt').unlink(missing_ok=True)
 print(json.dumps(result,indent=2))
