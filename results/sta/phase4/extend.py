"""Add an independently measured 200 ns ramp; preserve prior table rows exactly."""
from concurrent.futures import ProcessPoolExecutor,as_completed
from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
from tritflow import ROOT
from tritflow.sta.characterize import profile,LOADS,FIELDS,sha
from tritflow.sta.diagnose import write

if __name__=='__main__':
 root=ROOT/'results/sta/propagation';archive=ROOT/'results/sta/phase3/propagation_tables';archive.mkdir(exist_ok=True)
 cells=('INV','NAND','NOR','NANY','BUF');ramp=200e-9;points={c:{} for c in cells}
 with ProcessPoolExecutor(max_workers=2) as pool:
  pending={pool.submit(profile,c,l,ramp,root):(c,l) for c in cells for l in LOADS}
  for f in as_completed(pending):
   c,l=pending[f];p=f.result();points[c][l]=p;print(c,l,p['passed'],flush=True)
 for c in cells:
  path=root/'tables'/f'{c}.propagation.json';original=json.loads(path.read_text())
  if not (archive/path.name).exists():shutil.copy2(path,archive/path.name)
  if ramp in original['axes']['input_transition_s']:continue
  data=deepcopy(original);data['axes']['input_transition_s'].append(ramp)
  pins=data['inputs'];lookup={l:{(tuple(row['from']),tuple(row['to'])):row for row in p['rows']} for l,p in points[c].items()}
  for arc in data['arcs']+data['simultaneous']:
   key=tuple(arc['from_inputs'][p] for p in pins),tuple(arc['to_inputs'][p] for p in pins)
   for field in FIELDS+('passed','midpoint_crossing_count'):
    arc[field].append([lookup[l][key][field] for l in data['axes']['load_f']])
  data['runs'] += [p['provenance'] for p in points[c].values()]
  data['conditions']['hold_s_by_ramp'].append(min(p['provenance']['hold_s'] for p in points[c].values()))
  data['conditions']['max_step_s_by_ramp'].append(max(p['provenance']['step_s'] for p in points[c].values()))
  data['coverage']['measured_grid_points']+=len(LOADS)
  data['max_settling_s']=max(data['max_settling_s'],max(row['settling_s'] or 0 for p in points[c].values() for row in p['rows']))
  data['passed']=data['passed'] and all(p['passed'] for p in points[c].values())
  data['created_utc']=datetime.now(timezone.utc).isoformat()
  data['phase4_extension']={'ramp_s':ramp,'profile_count':len(LOADS),'publisher_sha256':sha(__file__),'prior_table_sha256':sha(archive/path.name)}
  write(path,data)
 write(ROOT/'results/sta/phase4/extension.json',{'ramp_s':ramp,'new_profiles':len(cells)*len(LOADS),
  'passed':all(p['passed'] for ps in points.values() for p in ps.values()),
  'table_sha256':{c:sha(root/'tables'/f'{c}.propagation.json') for c in cells}})
