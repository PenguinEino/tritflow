"""Controlled attribution of schematic/extracted delay and PNR current limits."""
from __future__ import annotations
import json
from pathlib import Path
import re
import numpy as np
from tritflow import ROOT,CELLS_DIR,PDK_ROOT
from tritflow.netlist import GateNetlist
from .postlayout import _save,_simulate_cached,file_hash,_device_fingerprint
from .scaling import adder_vectors,adder_oracle
from .provenance import pdk_provenance
from .spice import signal_waveform


def reverse_negative_resistors(text):
    """Reverse only canonical RN terminals, retaining the schematic device model."""
    def swap(match):
        fields=match[0].split();fields[1],fields[2]=fields[2],fields[1]
        return ' '.join(fields)
    return re.sub(r'(?im)^XRN\w*\s+.+\bF_RR\b[^\n]*$',swap,text)


def _junction_audit(cell):
    """Check extracted MOS junctions against the active wrapper's 2.8 um default."""
    source=(CELLS_DIR/f'out/{cell}/{cell}.ext.spice').read_text()
    rows=[]
    def number(token):
        factors={'u':1e-6,'p':1e-12,'n':1e-9,'':1}
        m=re.fullmatch(r'([+\-\d.eE]+)([a-z]*)',token,re.I)
        return float(m[1])*factors[m[2].lower()]
    for line in source.splitlines():
        if line.lstrip()[:1].upper() not in ('X','M'):continue
        if not re.search(r'\b[PN]MOS\b',line,re.I):continue
        params={k.upper():number(v) for k,v in re.findall(r'(\w+)=(\S+)',line)}
        w=params['W'];expected={'AD':w*2.8e-6,'AS':w*2.8e-6,'PD':2*(w+2.8e-6),'PS':2*(w+2.8e-6)}
        rows.append(dict(device=line.split()[0],extracted={k:params[k] for k in expected},
                         schematic_wrapper_defaults=expected,
                         equal=all(np.isclose(params[k],v,rtol=1e-12,atol=0) for k,v in expected.items())))
    return dict(cell=cell,mos=rows,all_junctions_equal=all(r['equal'] for r in rows))


def diagnose_delay(destination=ROOT/'results/delay_diagnosis.json'):
    """Change RN orientation only, then compare device-only and wire-C controls."""
    directory=ROOT/'build/adder_scaling/adder1';net=GateNetlist.load(directory/'adder1.json')
    source=directory/'postlayout/schematic.spice'
    schematic=source.read_text()
    device_only=(directory/'postlayout/lvs/adder1.ext.spice').read_text()
    wire=(directory/'postlayout/postlayout.spice').read_text()
    inputs=[p.name for p in net.ports if p.dir=='input'];outputs=[p.name for p in net.ports if p.dir=='output']
    vectors,labels=adder_vectors(1,inputs);vectors,labels=vectors[:7],labels[:7]
    expected=adder_oracle(1,inputs,outputs);out=ROOT/'build/delay_diagnosis/control'
    modes={'schematic':schematic,'schematic_RN_reversed':reverse_negative_resistors(schematic),
           'extracted_device_only':device_only,'extracted_plus_wire':wire}
    measurements={};waves={}
    for mode,text in modes.items():
        print('delay control:',mode,flush=True)
        run=_simulate_cached(out,mode,text,net.top,inputs,outputs,vectors,expected,
                             hold_s=1e-6,step_s=.5e-9,load_f=10e-15,timeout=600)
        measurements[mode]=run['measurements'];waves[mode]=run['waveforms']
    reference=waves['extracted_device_only'];corrected=waves['schematic_RN_reversed']
    differences={p:float(max(abs(np.interp(reference['time'],corrected['time'],signal_waveform(corrected,p))-signal_waveform(reference,p)))) for p in outputs}
    carry={mode:max(row['outputs'][pin]['settling_s'] for i,row in enumerate(value['rows'])
                   if i in (2,3,5,6) for pin in outputs) for mode,value in measurements.items()}
    result=dict(pdk_provenance=pdk_provenance(),schema_version=1,carry_max_settling_s=carry,vector_plan={'inputs':inputs,'vectors':vectors,'labels':labels},
        conditions={'hold_s':1e-6,'step_s':.5e-9,'load_f':10e-15,'temperature_c':27},
        measurements=measurements,corrected_schematic_vs_extracted_max_waveform_difference_v=differences,
        junctions=[_junction_audit(cell) for cell in ['INV','NANY']],
        resistor_model=dict(source='models_IP62_res_v5.lib F_RR W=2.8u',
            length_um=30,plus_to_substrate_capacitance_f=(5.96e-4*30+8.07e-3)*1e-12,
            minus_to_substrate_capacitance_f=0.,
            schematic_RN='PLUS=Y, MINUS=n',extracted_RN='PLUS=n, MINUS=Y'),
        source_sha256={str(source):file_hash(source),
            str(directory/'postlayout/lvs/adder1.ext.spice'):file_hash(directory/'postlayout/lvs/adder1.ext.spice'),
            str(PDK_ROOT/'libs.tech/spice/models/models_IP62_res_v5.lib'):file_hash(PDK_ROOT/'libs.tech/spice/models/models_IP62_res_v5.lib')},
        interpretation='PDK F_RR lumped C is attached to PLUS only. Swapping RN terminals preserves symmetric DC resistor topology but moves its intrinsic 25.95 fF from Y to the internal NMOS drain. MOS junction parameters equal the active schematic wrapper defaults. Use the exact same extracted devices with/without added wire C for an isolated wire-effect comparison.')
    _save(destination,result);return result


def device_fingerprint(text):
    """Ignore only comments and added Ctfwire elements, not device parameters."""
    return _device_fingerprint(text)


def refine_longest_carry(n=6):
    """One paired carry with coarse and two finer steps, identical devices."""
    from .corners import _adder_guesses
    directory=ROOT/f'build/adder_scaling/adder{n}'
    net=GateNetlist.load(directory/f'adder{n}.json')
    inputs=[p.name for p in net.ports if p.dir=='input'];outputs=[p.name for p in net.ports if p.dir=='output']
    source=directory/'postlayout';lvs=json.loads((source/'lvs.json').read_text())
    paths=[directory/f'adder{n}.gds',directory/f'adder{n}.pnr.json',directory/f'adder{n}.json',
           Path(lvs['extracted']),source/'postlayout.spice']
    hashes={str(p):file_hash(p) for p in paths}
    device=Path(lvs['extracted']).read_text();wire=(source/'postlayout.spice').read_text()
    if device_fingerprint(device)!=device_fingerprint(wire):raise ValueError('Device mismatch in wire-C control')
    vectors,labels=adder_vectors(n,inputs);pair=vectors[4:6]
    expected=adder_oracle(n,inputs,outputs)
    guesses=_adder_guesses(net,lvs['report'],inputs,{'VDD':5.,'VMID':0.,'VSS':-5.})(pair[0])
    rows=[]
    for step in (2e-9,.25e-9,.1e-9):
        results={}
        for mode,text in [('device_only',device),('device_plus_wire',wire)]:
            print(f'refined N={n} {mode} step={step*1e9:g}ns',flush=True)
            run=_simulate_cached(ROOT/f'build/delay_diagnosis/refined/N{n}',f'{mode}_{step.hex()}',
                text,net.top,inputs,outputs,pair,expected,hold_s=500e-9,step_s=step,
                load_f=10e-15,timeout=900,nodeset=guesses)
            results[mode]=run['measurements']
        pin=f'sum[{n-1}]';before=results['device_only']['rows'][1]['outputs'][pin]['settling_s']
        after=results['device_plus_wire']['rows'][1]['outputs'][pin]['settling_s']
        rows.append(dict(step_s=step,device_only_s=before,device_plus_wire_s=after,delta_s=after-before,
                         measurements=results))
    result=dict(pdk_provenance=pdk_provenance(),n=n,labels=labels[4:6],vectors=pair,device_fingerprint=device_fingerprint(device),
        source_sha256=hashes,rows=rows,scope='One isolated full-length negative-carry assertion, coarse and two finer timesteps; identical extracted devices and ideal input/rail sources. Other comparisons use their documented sequence and maximum step; sampling is not an integration-error bound.')
    if any(file_hash(p)!=h for p,h in hashes.items()):raise RuntimeError('Source changed during refined carry control')
    _save(ROOT/'results/delay_refined.json',result);return result


def audit_rail_currents(destination=ROOT/'results/rail_current_audit.json'):
    """Check saved sizing decisions and solved branch currents, including T/V.

    PVT uses independently worst measured cell currents at each condition on
    the fixed geometry and resistance model. This is an envelope sensitivity,
    not a claim that all cells attain their individual maxima in one vector.
    """
    from tritflow.extract import estimate_ir_drop
    template=json.loads((CELLS_DIR/'template.json').read_text())
    paths=sorted((ROOT/'build').glob('*/*.pnr.json'))+sorted((ROOT/'build/adder_scaling').glob('*/*.pnr.json'))
    corners_path=ROOT/'results/corners/summary.json'
    corners=json.loads(corners_path.read_text()) if corners_path.is_file() else None
    rows=[]
    for path in paths:
        data=json.loads(path.read_text());power=data['power'];assumptions=power.get('assumptions',{})
        used={p['cell'] for p in data['placements']}
        chars={name:json.loads((CELLS_DIR/f'out/{name}/{name}.char.json').read_text()) for name in used}
        abstracts={name:json.loads((CELLS_DIR/f'out/{name}/{name}.abstract.json').read_text()) for name in used}
        groups={}
        for pl in data['placements']:
            key=(pl['row'],pl.get('span',0));groups[key]=groups.get(key,0.)+power['currents_a'][pl['inst']]
        rate=assumptions.get('allowed_current_a_per_um')
        group_worst=max((load/(2*.00025*(band[1]-band[0])) for load in groups.values() for band in template['rails'].values()),default=0.)
        nominal=estimate_ir_drop(data,template,abstracts,chars)['em_check']
        row=dict(design=path.stem.removesuffix('.pnr'),pnr=str(path.relative_to(ROOT)),pnr_sha256=file_hash(path),
            sizing_assumptions=assumptions,uses_published_M1_step_limit=rate is not None and rate<=.00025,
            current_sources=sorted(set(power.get('current_sources',{}).values())),
            worst_row_span_centered_feed_utilization=group_worst,
            feed_banks=[dict(**bank,published_limit_a=bank['width']*bank['count']*.00025,
                 utilization=bank['current_a']/(bank['width']*bank['count']*.00025)) for bank in power.get('feed_banks',[])],
            nominal_solved_em_check=nominal,pvt=[])
        if corners and all(name in {'INV','NANY','NAND','NOR','BUF'} for name in used):
            for t in corners['temperatures_c']:
                for scale in corners['supply_scales']:
                    selected={r['dut']:r for r in corners['rows'] if r['dut'] in used and r['conditions']['temperature_c']==t and r['conditions']['supply_scale']==scale and r['state']=='complete'}
                    if set(selected)!=used: continue
                    pvchars={name:{'dc':case['dc']['rows']} for name,case in selected.items()}
                    em=estimate_ir_drop(data,template,abstracts,pvchars)['em_check']
                    row['pvt'].append(dict(temperature_c=t,supply_scale=scale,em_check=em))
        rows.append(row)
    result=dict(pdk_provenance=pdk_provenance(),rows=rows,
        source_sha256={str(CELLS_DIR/f'out/{c}/{c}.char.json'):file_hash(CELLS_DIR/f'out/{c}/{c}.char.json') for c in sorted({p['cell'] for path in paths for p in json.loads(path.read_text())['placements']})},
        corner_summary_sha256=file_hash(corners_path) if corners else None,
        scope='Drawn PNR rail network, published width-scaled DC limits. Nominal sizing and fixed-geometry T/V current sensitivity; unchanged assumed metal/via R, no temperature/lifetime derating or signal/internal-cell EM sign-off.')
    _save(destination,result);return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refine',action='store_true');parser.add_argument('--rail-audit',action='store_true')
    args=parser.parse_args()
    if args.rail_audit:audit_rail_currents()
    elif args.refine:refine_longest_carry()
    else:diagnose_delay()
