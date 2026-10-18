"""Publish phase-4 attribution, candidate failures and independent replay evidence."""
import hashlib,json
from pathlib import Path
import numpy as np
from tritflow import ROOT
from tritflow.sta.validate import fingerprint,_IMPORTED_CODE_SHA256
from tritflow.sta.characterize import FIELDS
from tritflow.sta.diagnose import write
from tritflow.sta.logic import function

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def network(deck):return '\n'.join(line for line in deck.split('.control')[0].strip().splitlines() if not line.startswith('Vin')).strip()

if __name__=='__main__':
 root=ROOT/'results/sta';out=root/'phase4';v=read(root/'validation.json');prior=read(root/'phase3/validation.json')
 assert v['source_sha256']==fingerprint(), 'Revalidate changed producer evidence'
 assert v['sta_code_sha256']==_IMPORTED_CODE_SHA256
 olddesign={(d['group'],d['design']):d for d in prior['designs']};rows=[];caps_same=[]
 for d in v['designs']:
  previous=olddesign[d['group'],d['design']];oldrows={r['output']:r for r in previous['outputs']}
  newreport=read(root/d['all_pairs_report']);oldreport=read(root/'phase3'/previous['all_pairs_report'])
  caps_same.append(newreport['loads']==oldreport['loads'])
  for r in d['outputs']:
   old=oldrows[r['output']];assert old['tested_predicted_s']==r['tested_predicted_s']
   path=newreport['paths'][r['output']]
   rows.append({'design':r['design'],'output':r['output'],'simulated_s':r['simulated_s'],
    'phase3_s':old['predicted_s'],'phase4_s':r['predicted_s'],
    'phase3_factor':old['predicted_s']/r['simulated_s'],'phase4_factor':r['predicted_s']/r['simulated_s'],
    'endpoint_only_s':r['settled_slew_window_s'],
    'endpoint_tail_s':path[-1]['settling_tail_s'] if path else 0.,
    'selected_recovery_stage_count':sum(s['metric']=='local_recovery' for s in path)})
 assert all(caps_same)
 table_checks={}
 for path in sorted((root/'propagation/tables').glob('*.json')):
  table=read(path);old=read(root/'phase3/propagation_tables'/path.name)
  same=True
  for a,b in zip(table['arcs']+table['simultaneous'],old['arcs']+old['simultaneous']):
   for field in FIELDS+('passed','midpoint_crossing_count'):same &= a[field][:len(old['axes']['input_transition_s'])]==b[field]
  assert same and table['passed']
  table_checks[table['cell']]={'prior_rows_unchanged':same,'table_sha256':sha(path),
   'ramp_axis_s':table['axes']['input_transition_s'],'measured_profiles':table['coverage']['measured_grid_points']}
 # Retained isolated-cell waves show why scalar recovery is not a full trit edge.
 recovery={}
 for cell in ('NAND','NOR','NANY'):
  p=root/f'propagation/runs/{cell}/r1e-09_c1e-13';meas=read(p/'measurements.json');hold=meas['provenance']['hold_s']
  with np.load(p/'waveforms.npz') as w:t=w['time'];voltage=w['v(Y)']
  observations=[]
  for k,r in enumerate(meas['rows'],1):
   old,new=function(cell,r['from']),function(cell,r['to'])
   if old!=new:continue
   peak=float(np.max(abs(voltage[(t>=k*hold)&(t<=(k+1)*hold)]-5*old)))
   observations.append({'from':r['from'],'to':r['to'],'output_level':old,'peak_deviation_v':peak,'recovery_s':r['recovery_s']})
  recovery[cell]={'scope':'100 fF, 1 ns only; no extrapolation to other slew/load or arbitrary analog hazards.',
   'waveforms_sha256':sha(p/'waveforms.npz'),'maximum_peak_deviation_v':max(r['peak_deviation_v'] for r in observations),
   'cross_half_level_count':sum(r['peak_deviation_v']>=2.5 for r in observations),'observations':observations}
 exact=read(out/'exact_witness/measurements.json')
 original=ROOT/'build/adder_scaling/adder2/postlayout/post/tb.spice'
 assert sha(original)==exact['source_deck_sha256']
 assert network(original.read_text())==network((out/'exact_witness/tb.spice').read_text())
 convergence=read(out/'bin_convergence.json');fine=convergence['rows'][-1]
 ceiling=1.5*exact['original_sim_max_s']['cout'];actual=exact['settling_s']['cout']
 result={'schema_version':1,'validation_sha256':sha(root/'validation.json'),
  'source_sha256':v['source_sha256'],'sta_code_sha256':v['sta_code_sha256'],
  'target_factor':1.5,'target_passed':v['bound_target_passed'],'outputs_within_target':v['bound_outputs_within_target'],
  'worst_case_validation':v['worst_case_validation'],'same_loads':all(caps_same),'matched_predictions_unchanged':True,
  'table_extension':table_checks,'characterization_summary':read(root/'propagation/summary.json'),
  'component_attribution':read(out/'attribution.json'),
  'candidate_statistics':read(out/'windows.json')['statistics'],
  'endpoint_only_violations':[{'design':r['design'],'output':r['output'],'predicted_s':r['endpoint_only_s'],'simulated_s':r['simulated_s']} for r in rows if r['endpoint_only_s']<r['simulated_s']],
  'representative_recovery_amplitude':recovery,
  'bin_convergence':convergence,
  'independent_witness':{'record':exact,'network_and_loads_unchanged':True,
   'fine_window_cout_s':fine['arrival_s']['cout'],'same_pattern_event_cout_s':fine['same_pattern_event_s']['cout'],
   'remaining_room_below_1_5x_s':ceiling-actual,
   'event_model_error_s':fine['same_pattern_event_s']['cout']-actual,
   'window_model_error_s':fine['arrival_s']['cout']-actual},
  'conclusion':'The 1.5x target is not achieved. Scalar equal-ramp cell data do not bound relative side-input timing, pulse amplitude or waveform-shape error. Narrow bins converge above the target, and removing transient classes causes measured misses. This does not prove a 1.5x physical bound impossible; it is not justified by this characterization.',
  'outputs':rows}
 assert v['source_sha256']==fingerprint()
 write(out/'audit.json',result)
 import plotly.graph_objects as go
 f=go.Figure()
 labels=[r['design']+'/'+r['output'] for r in rows]
 for field,title in [('phase3_factor','Phase 3: broad ramp/recovery envelope'),('phase4_factor','Phase 4: measured slew windows')]:
  f.add_bar(x=labels,y=[r[field] for r in rows],name=title)
 f.add_hline(y=1.5,line_dash='dash',annotation_text='Requested 1.5× target')
 f.update_layout(title='Tightening the bound; 838 nominal observations remain covered',
  yaxis_title='Bound / measured output maximum (×)',xaxis_title='Design / output',template='plotly_white',barmode='group')
 f.write_html(out/'tightening.html',include_plotlyjs='cdn')
 print(json.dumps({k:result[k] for k in ['target_passed','outputs_within_target','worst_case_validation','same_loads','matched_predictions_unchanged']},indent=2))
