"""Read-only diagnostic: separate fixed-ramp and endpoint-correlation effects."""
import json
from pathlib import Path
from tritflow import ROOT
from tritflow.netlist import GateNetlist
from tritflow.synth.simulate import ordered_instances,CELL_INPUTS
from tritflow.sta.propagation import PropagationLibrary
p=ROOT/'results/sta'
v=json.loads((p/'phase2/validation.json').read_text())
models=PropagationLibrary(['INV','NAND','NOR','NANY','BUF','TIEP','TIEZ','TIEN'])
rows=[]
for d in v['designs']:
 folder=ROOT/('build/adder_scaling' if d['group']=='scaling' else 'build')/d['design']
 summary=json.loads((folder/'postlayout/summary.json').read_text())
 net=GateNetlist.load(folder/'postlayout/inputs'/f'{summary["top"]}.json')
 report=json.loads((p/'phase2'/d['all_pairs_report']).read_text())
 variants={}
 for mode in ['fixed_relaxed','ramp_relaxed','ramp_recovery','slew_relaxed','slew_recovery']:
  clocks={x.name:.5e-9 for x in net.ports if x.dir=='input'};settled={};slews={n:.8e-9 for n in clocks}
  for inst in ordered_instances(net):
   pins=CELL_INPUTS[inst.cell];y=inst.pins['Y'];m=models[inst.cell]
   if not pins:clocks[y]=settled[y]=slews[y]=0.;continue
   load=report['loads'][y]['total_f']
   ramps=[1e-9] if mode=='fixed_relaxed' else m.data['axes']['input_transition_s']
   mid=[];rec=[];ends=[];ss=[]
   for a in m.arcs:
    t=max(clocks[inst.pins[pin]] for pin in a['changed_inputs'])
    for pin in a['changed_inputs']:
     if mode.startswith('slew'):
      requested=slews[inst.pins[pin]]/.8
      if requested>ramps[-1]: requested=ramps[-1]
      samples=sorted(set([r for r in ramps if r<=requested]+[max(ramps[0],requested)]))
     else:samples=ramps
     t=clocks[inst.pins[pin]]
     for r in samples:
      if a['output_from']!=a['output_to']:
       q=t+m.sample(a,load,r,field='propagation_s',load_policy='linear')
       ss.append(m.sample(a,load,r,field='output_slew_10_90_s',load_policy='linear'));mid.append(q);ends.append(q+m.sample(a,load,r,field='tail_s',load_policy='linear'))
      else:
       q=t+m.sample(a,load,r,field='recovery_s',load_policy='linear');rec.append(q);ends.append(q)
   clocks[y]=max(mid+(rec if mode in ['ramp_recovery','slew_recovery'] else []));settled[y]=max(ends);slews[y]=max(ss)
  variants[mode]={r['output']:settled[r['output']] for r in d['outputs']}
 for r in d['outputs']:
  rows.append({**r,**{mode:rr[r['output']] for mode,rr in variants.items()}})
from tritflow.sta.validate import statistics
result={'rows':rows,'statistics':{f:statistics(rows,f) for f in ['predicted_s','fixed_relaxed','ramp_relaxed','ramp_recovery','slew_relaxed','slew_recovery']}}
(p/'diagnosis/phase3_prototype.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['statistics'],indent=2))
