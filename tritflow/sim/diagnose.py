"""Controlled attribution of schematic/extracted delay and PNR current limits."""
from __future__ import annotations
import json
from pathlib import Path
import re
import numpy as np
from tritflow import ROOT,CELLS_DIR,PDK_ROOT
from tritflow.netlist import GateNetlist
from .postlayout import _save,_simulate_cached,file_hash
from .scaling import adder_vectors,adder_oracle


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
    source=ROOT/'build/delay_diagnosis/phase4/adder1/prelayout.spice'
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
    differences={p:float(max(abs(np.interp(reference['time'],corrected['time'],corrected[f'v({p})'])-reference[f'v({p})']))) for p in outputs}
    result=dict(schema_version=1,vector_plan={'inputs':inputs,'vectors':vectors,'labels':labels},
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


if __name__=='__main__':diagnose_delay()
