"""Unmodified PDK drawing DRC, strict LVS, and extracted DC qualification."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import klayout.db as db
import klayout.rdb as rdb
from tritflow import CELLS_DIR, PDK_ROOT
from .circuits import circuits, truth_table

TECH = PDK_ROOT/'libs.tech/klayout/tech'
BINARY = Path(os.environ.get('KLAYOUT_BINARY') or os.environ.get('KLAYOUT_BIN') or Path.home()/'bin/klayout/klayout')


def run(cmd, folder, log):
    folder.mkdir(parents=True,exist_ok=True)
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    env.pop('KLAYOUT_PATH',None)
    with (folder/log).open('w') as f:
        p = subprocess.run(list(map(str,cmd)),cwd=folder,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
    return p.returncode,(folder/log).read_text()


def drc(gds, top, folder):
    report = folder/'drawing.lyrdb'
    report.unlink(missing_ok=True)
    code,log = run([BINARY,'-b','-r',TECH/'drc/run.drc','-rd',f'input={gds}',
                    '-rd',f'top_cell={top}','-rd',f'report={report}'],folder,'drawing.log')
    if code or not report.exists(): return {'passed':False,'error':log[-2000:]}
    r = rdb.ReportDatabase(); r.load(str(report))
    return {'passed':r.num_items()==0,'items':r.num_items(),
            'categories':{c.name():c.num_items() for c in r.each_category() if c.num_items()}}


def normalize_extracted(raw, target, circuit):
    """Reorder extracted public ports for the flow's signal/power contract.

    Empty pass-through rails are purged by KLayout. They are reintroduced as
    unused formal pins, never as devices or guessed connections.
    """
    text = raw.read_text()
    match = re.search(r'(?im)^\.subckt\s+'+circuit.name+r'\s*([^\n]*)',text)
    if not match:
        raise ValueError('No extracted circuit '+circuit.name)
    body = text[match.end():re.search(r'(?im)^\.ends',text).start()]
    temporary=target.with_suffix(target.suffix+'.next')
    temporary.write_text('* PDK extraction; public ports normalized, no parasitic RC\n.subckt '+
                         circuit.name+' '+' '.join(circuit.ports)+body+'\n.ends '+circuit.name+'\n')
    os.replace(temporary,target)


def lvs(gds, circuit, folder, normalize=True):
    """Use SIM's fixed strict-port check before restoring any public formal.

    An unused schematic pin is insufficient evidence: the public extractor now
    requires labelled, connected physical power metal across abutment edges.
    Preserve its raw device extraction and LVS database in our established paths.
    """
    from tritflow.extract import extract_layout
    from tritflow.extract.lvs import ExtractionError
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    report,raw=folder/'lvs.lvsdb',folder/'extracted.raw.spice'
    report.unlink(missing_ok=True);raw.unlink(missing_ok=True)
    (folder/'strict_lvs'/f'{circuit.name}.raw.ext.spice').unlink(missing_ok=True)
    try:
        check=extract_layout(gds,circuit.name,folder/'strict_lvs',
            reference=folder/f'{circuit.name}.lvs.spice',pdk=PDK_ROOT,
            executable=BINARY,timeout=240)
    except ExtractionError as exc:
        return {'passed':False,'strict_ports':True,'error':str(exc)}
    shutil.copyfile(check['report'],report)
    extracted=Path(check['extracted'])
    original=extracted.with_name(f'{circuit.name}.raw.ext.spice')
    shutil.copyfile(original if original.exists() else extracted,raw)
    (folder/'lvs.log').write_text(check['log'])
    result={'passed':check['matched'],'strict_ports':check['strict_ports'],
            'circuits':check['circuits'],'errors':check['errors'],
            'unused_power_formals_restored':check.get('unused_power_formals_restored',[]),
            'unused_power_physical_evidence':check.get('unused_power_physical_evidence',{}),
            'checker':'tritflow.extract.extract_layout; physical unloaded-rail proof required',
            'checker_sha256':hashlib.sha256((Path(__file__).parents[1]/'extract/lvs.py').read_bytes()).hexdigest()}
    if result['passed'] and normalize:
        try: normalize_extracted(raw,folder/f'{circuit.name}.ext.spice',circuit)
        except ValueError as e:
            result['normalization_error']=str(e)
            result['passed']=False
    return result


def fill_lvs(out, standalone):
    """Qualify a device-free filler by extraction and a strict rail-probe fixture.

    The PDK purges a device-free top before comparison, so standalone strict LVS
    reports mismatch even for an exact empty reference. Keep that result, then
    compare three real RR probes connected through the filler rails. Explicit
    geometry checks additionally prove that each rail and nwell spans its width.
    """
    from .layout import build_cell
    from .circuits import Circuit, spice
    folder=out/'FILL'; fixture=folder/'probe'; fixture.mkdir(exist_ok=True)
    template=json.loads((out/'template.json').read_text())
    ly=db.Layout(); ly.dbu=.001
    ly.read(str(folder/'FILL.gds'))
    f=ly.cell('FILL')
    a=json.loads((folder/'FILL.abstract.json').read_text())
    geometry=True
    for rail,(y0,y1) in template['rails'].items():
        actual=db.Region(f.begin_shapes_rec(ly.layer(13,0))).merged()
        wanted=db.Region(db.DBox(0,y0,a['width'],y1).to_itype(ly.dbu))
        geometry &= (wanted-actual).is_empty()
    wanted=db.Region(db.DBox(0,template['well_band'][0],a['width'],template['well_band'][1]).to_itype(ly.dbu))
    geometry &= (wanted-db.Region(f.begin_shapes_rec(ly.layer(140,0)))).is_empty()
    top=ly.create_cell('FILL_PROBE')
    top.insert(db.DCellInstArray(f.cell_index(),db.DTrans()))
    x=a['width']; entries=[]
    for name,pin in [('TIEP','YP'),('TIEZ','YZ'),('TIEN','YN')]:
        c=circuits()[name]
        abstract=build_cell(c,fixture,template)
        ly.read(str(fixture/name/f'{name}.gds'))
        trans=db.DTrans(db.DVector(x,0.))
        top.insert(db.DCellInstArray(ly.cell(name).cell_index(),trans))
        px,py=abstract['pins']['Y']['access'][0]
        top.shapes(ly.layer(48,0)).insert(db.DText(pin,db.DTrans(db.DVector(x+px,py))))
        entries.append(f'X{name} {pin} VDD VMID VSS {name}')
        x+=abstract['width']
    for rail,(y0,y1) in template['rails'].items():
        top.shapes(ly.layer(48,0)).insert(db.DText(rail,db.DTrans(db.DVector(3.,(y0+y1)/2))))
    gds=fixture/'FILL_PROBE.gds'; ly.write(str(gds))
    reference=''.join(spice(circuits()[n],False) for n in ['TIEP','TIEZ','TIEN'])
    reference+='\n.subckt FILL_PROBE YP YZ YN VDD VMID VSS\n'+'\n'.join(entries)+'\n.ends FILL_PROBE\n'
    (fixture/'FILL_PROBE.lvs.spice').write_text(reference)
    probe=lvs(gds,Circuit('FILL_PROBE',()),fixture,normalize=False)
    raw=(folder/'extracted.raw.spice').read_text()
    empty=not re.search(r'(?im)^\.subckt|^[MXR]',raw)
    result={'passed':empty and geometry and probe['passed'],'method':'empty-device extraction + strict three-rail RR probe fixture',
            'empty_device_extraction':empty,'rail_and_well_geometry':bool(geometry),
            'standalone_deck':standalone,'probe':probe,
            'explanation':'PDK purges device-free FILL; standalone comparison has no circuits. No device mismatch is waived.'}
    if result['passed']:
        (folder/'FILL.ext.spice').write_text('* Device-free PDK extraction; rail continuity qualified by FILL_PROBE\n.subckt FILL VDD VMID VSS\n.ends FILL\n')
    return result


def abutment(out, names):
    """All ordered neighbors and both legal orientations, including self pairs."""
    ly=db.Layout(); ly.dbu=.001
    for name in names: ly.read(str(out/name/f'{name}.gds'))
    top=ly.create_cell('ABUTMENT')
    h=json.loads((out/'template.json').read_text())['height']
    row=0
    for left in names:
        for right in names:
            for ml in (False,True):
                for mr in (False,True):
                    x=0
                    for name,mirror in ((left,ml),(right,mr)):
                        a=json.loads((out/name/f'{name}.abstract.json').read_text())
                        # KLayout mirror=True is MX, combined with R180 gives MY.
                        t=db.DTrans(2,True,x+a['width'],row*(h+24)) if mirror else db.DTrans(x,row*(h+24))
                        top.insert(db.DCellInstArray(ly.cell(name).cell_index(),t))
                        for pin,p in a['pins'].items():
                            px,py=p['access'][0]
                            point=t*db.DPoint(px,py)
                            label=f'row{row}_{name}_{x}_{pin}'
                            top.shapes(ly.layer(48,0)).insert(db.DText(label,db.DTrans(db.DVector(point.x,point.y))))
                        x+=a['width']
                    row+=1
    target=out/'abutment.gds'; ly.write(str(target))
    result=drc(target,'ABUTMENT',out)
    result['ordered_pair_orientation_cases']=row
    return result


def dc(circuit,folder):
    """Nine/three independent DC operating points on PDK-extracted devices."""
    ext=folder/f'{circuit.name}.ext.spice'
    if not ext.exists(): return {'passed':False,'error':'No extracted netlist'}
    cases=[]
    for i,row in enumerate(truth_table(circuit)):
        deck=['* TritFlow extracted DC sanity',f'.include "{PDK_ROOT}/libs.tech/spice/models/ip62_models"',
              f'.include "{ext}"','VDD VDD 0 5','VMID VMID 0 0','VSS VSS 0 -5']
        deck += [f'V{pin} {pin} 0 {value*5}' for pin,value in row['inputs'].items()]
        deck += ['XU '+' '.join(circuit.ports)+' '+circuit.name,'.temp 27',
                 '.options rshunt=1e12',f'.nodeset v(Y)={row["Y"]*5}','.control','op','print v(Y)','quit','.endc','.end']
        path=folder/f'dc_{i}.spice';path.write_text('\n'.join(deck)+'\n')
        from tritflow.sim.tools import ngspice_binary
        code,log=run([ngspice_binary(),'-n','-b',path],folder,f'dc_{i}.log')
        m=re.search(r'(?im)^v\(y\)\s*=\s*([-+\deE.]+)',log)
        value=float(m.group(1)) if m else None
        error=abs(value-row['Y']*5) if value is not None else None
        cases.append({**row,'output_V':value,'error_V':error,'passed':code==0 and error is not None and error<=.5})
    result={'passed':all(c['passed'] for c in cases),'cases':cases,'temperature_C':27,
            'scope':'DC sanity only; no wire/poly parasitics'}
    (folder/f'{circuit.name}.dc.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def verify(out=CELLS_DIR/'out',names=None):
    from tritflow.sim.provenance import pdk_provenance
    out=Path(out).resolve()
    selected={n:c for n,c in circuits().items() if not names or n in names}
    report={'cells':{},'pdk':str(PDK_ROOT),'pdk_provenance':pdk_provenance(),
            'deck_sha256':{str(p.relative_to(PDK_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                           for area in ['drc','lvs'] for p in sorted((TECH/area).rglob('*')) if p.is_file()},
            'scope':'nominal device/connectivity extraction, no interconnect RC'}
    for n,c in selected.items():
        folder=out/n;gds=folder/f'{n}.gds'
        result={'drc':drc(gds,n,folder),'lvs':lvs(gds,c,folder)}
        if c.name!='FILL':result['dc']=dc(c,folder)
        else: result['lvs']=fill_lvs(out,result['lvs'])
        report.setdefault('artifact_sha256',{})[n]={suffix:hashlib.sha256((folder/f'{n}.{suffix}').read_bytes()).hexdigest()
            for suffix in ['gds','spice','ext.spice','abstract.json','truth.json','png','pcells.json']
            if (folder/f'{n}.{suffix}').exists()}
        report['cells'][n]=result
        summary={k:v['passed'] for k,v in result.items()}
        print(n,json.dumps(summary),flush=True)
    report['abutment']=abutment(out,list(selected))
    report['passed']=all(v['passed'] for cell in report['cells'].values() for v in cell.values()) and report['abutment']['passed']
    temporary=out/'.verify_report.next.json'
    temporary.write_text(json.dumps(report,indent=2)+'\n')
    os.replace(temporary,out/'verify_report.json')
    return report
