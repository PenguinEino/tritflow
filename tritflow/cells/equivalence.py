"""Prove compact cells against freshly extracted taped-out layouts and schematics."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path

import numpy as np
from tritflow import CELLS_DIR,PDK_ROOT
from . import regression
from .reference import ORIGINALS,device_parameters,prepare,prepare_buf,sha


def _max_current_difference(left,right):
    return max(abs(a['rail_current_a'][rail]-b['rail_current_a'][rail])
               for a,b in zip(left['rows'],right['rows']) for rail in ('VDD','VMID','VSS'))


def _delay_difference(left,right):
    pairs=list(zip(left['rows'][1:],right['rows'][1:]))
    result=0.
    for a,b in pairs:
        for pin in a['outputs']:
            x,y=a['outputs'][pin]['settling_s'],b['outputs'][pin]['settling_s']
            if (x is None)!=(y is None):return None
            if x is not None:result=max(result,abs(x-y))
    return result


def compare_cell(cell, original, compact, proof, folder):
    """Compare one independent extracted cell, retaining every protocol result."""
    result={'intrinsic_parameters_identical':device_parameters(original)==device_parameters(compact)}
    grids={};samples={};ops={};trans={}
    for label,text in [('original',original),('compact',compact)]:
        ops[label]=regression.operating_points(text,cell)
        grids[label],samples[label]=regression.grid(text,cell,folder/label/'dc_grid')
        trans[label]={}
        for load in (10e-15,100e-15):
            key='10f' if load==10e-15 else '100f'
            trans[label][key]=regression.transitions(text,cell,folder/label/key,load_f=load)
        if cell=='NANY':
            for pin in ('A','B'):
                trans[label]['skew_'+pin]=regression.transitions(text,cell,folder/label/('skew_'+pin),skew_input=pin)
    delta=float(np.max(abs(samples['original']['v(y)']-samples['compact']['v(y)'])))
    current=_max_current_difference(ops['original'],ops['compact'])
    delays={key:_delay_difference(trans['original'][key],trans['compact'][key]) for key in trans['original']}
    result.update(dc_grid=grids,operating_points=ops,transient=trans,
                  comparison={'max_grid_difference_v':delta,'max_static_current_difference_a':current,
                              'max_settling_difference_s':delays})
    result['passed']=(proof['passed'] and result['intrinsic_parameters_identical']
                      and all(g['passed'] for g in grids.values()) and all(o['passed'] for o in ops.values())
                      and all(t['passed'] for suite in trans.values() for t in suite.values())
                      and delta<=1e-4 and current<=1e-9
                      and all(v is not None and v<=1e-9 for v in delays.values()))
    print(cell,'equivalence',result['passed'],'grid delta',delta,'delay differences',delays,flush=True)
    return result


def compare_chain(kind, original, compact, folder):
    """Compare one complete cascade protocol with all stages observed."""
    rows={};data={}
    for label,texts in [('original',original),('compact',compact)]:
        rows[label],data[label]=regression.chain(texts,kind,folder/label)
    outputs=list(rows['original']['stages'])
    delta=max(float(np.max(abs(data['original'][f'v({p})']-data['compact'][f'v({p})']))) for p in outputs)
    delays=_delay_difference(rows['original']['transient'],rows['compact']['transient'])
    passed=all(r['passed'] for r in rows.values()) and delta<=1e-3 and delays is not None and delays<=1e-9
    result={**rows,'max_dc_difference_v':delta,'max_settling_difference_s':delays,'passed':passed}
    print(kind,'chain equivalence',passed,'DC delta',delta,flush=True)
    return result


def equivalence(out=CELLS_DIR/'out',reference=Path.home()/'balanced-ternary-logic'):
    """Run Phase 2 on one published compact generation; publish report atomically."""
    out=Path(out).resolve();work=out/'equivalence';work.mkdir(parents=True,exist_ok=True)
    generation=json.loads((out/'generation.json').read_text()) if (out/'generation.json').exists() else None
    proof=prepare(reference,work/'reference',out)
    original={c:(work/'reference'/c/'original.ext.spice').read_text() for c in ORIGINALS}
    original['BUF'],proof['BUF']=prepare_buf(original['INV'],work/'reference',out)
    compact={c:(out/c/f'{c}.ext.spice').read_text() for c in original}
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'generation':generation,
            'reference_root':str(Path(reference).expanduser().resolve()),'schematic_equivalence':proof,
            'conditions':{'temperature_c':27,'rails_v':[5,0,-5],'dc_grid_step_v':.125,
                          'transition_hold_s':100e-9,'transition_edge_s':1e-9,'transition_max_step_s':.1e-9,
                          'loads_f':[10e-15,100e-15],'input_skew_s':2e-9},
            'comparison_tolerances':{'grid_voltage_v':1e-4,'static_current_a':1e-9,
                                     'settling_difference_s':1e-9,'chain_voltage_v':1e-3},
            'scope':'Fresh PDK device/junction extraction, no interconnect RC. Nominal 27 C only.',
            'cells':{},'chains':{}}
    for cell in original:
        report['cells'][cell]=compare_cell(cell,original[cell],compact[cell],proof[cell],work/cell)
    for kind in ('inverter_two','nor_six','nany_six','mixed_six'):
        report['chains'][kind]=compare_chain(kind,original,compact,work/'chains'/kind)
    report['model_sha256']={p.name:sha(p) for p in sorted((PDK_ROOT/'libs.tech/spice/models').iterdir()) if p.is_file()}
    report['passed']=all(c['passed'] for c in report['cells'].values()) and all(c['passed'] for c in report['chains'].values())
    report['interpretation']=('Identical device sizes/connectivity and intrinsic junction parameters; negligible numerical differences are expected. '
                              'No interconnect RC is present in either extraction, so these results do not measure routing-dependent silicon delay.')
    report['additional_cells']={'BUF':'Strict LVS against two fresh independent INV schematic copies and analog comparison against two original extracted INV copies. No taped-out BUF macro exists.',
                               'TIEP/TIEZ/TIEN/FILL':'New support cells; phase-1 qualification only, no taped-out counterpart.'}
    for cell in original:
        if sha(out/cell/f'{cell}.ext.spice')!=proof[cell]['compact_extracted_sha256']:
            raise RuntimeError('Live library changed during equivalence; do not publish mixed-generation results')
    temporary=out/'.equivalence_report.next.json'
    temporary.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    os.replace(temporary,out/'equivalence_report.json')
    return report
