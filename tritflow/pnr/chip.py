"""Optional 2.5 mm OpenSUSI TEG wrapper with real passive probe terminals.

The pinned PDK's seal ring is copied unchanged. Its 16-pad TEG bank is replaced
in the *copy* by peripheral instances of the same OSS_PAD_TEG primitive: the
adder needs 17 independent terminals. This is a custom probe/bond map, not the
stock 16-pin package, and does not claim ESD qualification for a 10 V rail span.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time

import klayout.db as db
import numpy as np

from tritflow import PDK_ROOT, RAILS
from tritflow.netlist import GateNetlist
from .chip_router import ChipRouter
from .gds import DBU, box, wire_box
from .library import Library
from .power import dc_current_check
from .signoff import _drc, _hash, _layout_audit, _metal_preservation, _run, _write
from .verify import PhysicalVerificationError, connectivity


@dataclass
class ChipResult:
    """Separate full-chip artifacts; the original macro and SIM JSON stay intact."""
    gds_path: Path
    json_path: Path
    data: dict
    report: dict

    @property
    def stats(self):
        return self.data['stats']

    def signoff(self, **options):
        """Revalidate the full-chip drawing, LVS, MDP, mask and MPW checks."""
        return chip_signoff(self, **options)


def _shift_wire(wire, dx, dy):
    return {**wire, 'points': [[x+dx,y+dy] for x,y in wire['points']]}


def _shift_pin(pin, dx, dy):
    x0,y0,x1,y1 = pin['rect']
    return {**pin, 'rect':[x0+dx,y0+dy,x1+dx,y1+dy]}


def _via_array(vias, net, x, y, width, height):
    """Real 1.4 um TC cuts at 3 um pitch, with at least 1 um enclosure."""
    nx, ny = max(1,math.floor((width-3.4)/3)+1), max(1,math.floor((height-3.4)/3)+1)
    for i in range(nx):
        for j in range(ny):
            vias.append({'net':net,'x':round(x+(i-(nx-1)/2)*3,3),
                         'y':round(y+(j-(ny-1)/2)*3,3)})


def _power_header(data, macro_pins, core, margin):
    """Three M2 distribution bars, M1 bank fingers, and parallel M1 pad feeds.

    Long common links use M2. M1 pad feeders split the total rail current into
    enough <=44 um strips for the conservative stepped-M1 rating and reserve.
    No new via is placed in a pad opening; the imported PDK cut array is used.
    """
    x0,y0,x1,y1 = core
    totals = {r:sum(v[r] for v in data['power']['rail_currents_a'].values()) for r in RAILS}
    widths = {r:max(6.4,math.ceil(totals[r]/((3.7e-3/3)*(1-margin))*10)/10) for r in RAILS}
    if any(w > 44. for w in widths.values()):
        raise ValueError('Chip supply needs parallel M2 bars; reduce the macro size or split the allocation')
    bars, cursor = {}, y1+8.
    for rail in RAILS:
        w = widths[rail]; bars[rail] = cursor+w/2; cursor += w+8.
    collector_y = max(cursor+8., 1032.)
    if collector_y+16 > 1050.:
        raise ValueError('Macro leaves insufficient top power-channel space; use fewer rows or more placement effort')
    power = data['power']; fingers = []
    for pin in macro_pins:
        rail = pin['name']; a,b,c,d = pin['rect']; x = (a+c)/2; w = c-a
        # The flat lower end avoids M1 already routed in the last macro channel.
        low, high = y1-4.7, bars[rail]+widths[rail]/2
        power['rails'].append({'net':rail,'layer':'M1','width':w,
                              'points':[[x,y1-3],[x,bars[rail]]],
                              'rect':[a,low,c,high]})
        power['straps'].append({'net':rail,'layer':'M2','width':w,
                               'points':[[x,y1-3],[x,y1+3]],
                               'rect':[a,y1-6,c,y1+7]})
        _via_array(power['vias'],rail,x,y1+1,w,9.4)
        _via_array(power['vias'],rail,x,bars[rail],w,widths[rail])
        fingers.append((a,c))
    # Find three genuinely empty M1 corridors, also disjoint from each other.
    used, pads = list(fingers), []
    for rail, preferred in zip(RAILS,(-650.,0.,650.)):
        required = totals[rail]/(.00025*(1-margin))
        count = max(1,math.ceil(required/44.))
        leg_width = max(6.4,math.ceil(required/count*10)/10)
        pitch = leg_width+4.
        span = count*leg_width+(count-1)*4.
        candidates = sorted(np.arange(-900.,901.,2.),key=lambda x:(abs(x-preferred),x))
        cx = next((float(x) for x in candidates
                   if all(x+span/2+3 <= a or x-span/2-3 >= b for a,b in used)),None)
        if cx is None:
            raise ValueError(f'No M1 supply corridor for {rail}; use a narrower macro or more rows')
        used.append((cx-span/2,cx+span/2))
        pads.append((rail,cx,1100.))
        for i in range(count):
            x = cx+(i-(count-1)/2)*pitch
            power['rails'].append({'net':rail,'layer':'M1','width':leg_width,
                'points':[[x,bars[rail]],[x,collector_y]]})
            _via_array(power['vias'],rail,x,bars[rail],leg_width,widths[rail])
            # A shallow cut array stays well away from the PRO opening.
            _via_array(power['vias'],rail,x,collector_y,leg_width,6.4)
        power['straps'] += [
            {'net':rail,'layer':'M2','width':widths[rail],
             'points':[[min(min(p['rect'][0] for p in macro_pins),cx-span/2),bars[rail]],
                       [max(max(p['rect'][2] for p in macro_pins),cx+span/2),bars[rail]]]},
            {'net':rail,'layer':'M2','width':widths[rail],
             'points':[[cx-(count-1)/2*pitch,collector_y],[cx+(count-1)/2*pitch,collector_y]]},
            {'net':rail,'layer':'M2','width':widths[rail],
             'points':[[cx,collector_y],[cx,1100.]]}]
    return pads, {'rail_current_envelope_a':totals,'M2_width_um':widths,
                  'reserve':margin,'collector_y_um':collector_y,
                  'M1_step_limit_a_per_um':.00025,'M2_field_limit_a_per_um':3.7e-3/3}


def chip(result, *, output_dir=None, top=None, library=None, pdk_root=PDK_ROOT,
         klayout_binary=None, mpw_template=None, current_margin=.2, timeout=180):
    """Wrap a verified macro in a custom, passive OpenSUSI TEG allocation.

    Every signal and each of VDD/VMID/VSS gets an independent real PDK pad.
    The 2500 x 2500 um centered frame uses the pinned PDK seal ring and pad
    primitive. The peripheral probe/bond map needs organizer/package approval;
    this API performs physical signoff, not submission or ESD qualification.
    A failed connectivity/DRC/LVS/mask check never publishes a canonical GDS.
    """
    started = time.perf_counter()
    if not 0 <= current_margin < 1:
        raise ValueError('current_margin must be in [0, 1)')
    if result.data.get('library',{}).get('mock'):
        raise ValueError('Full-chip signoff requires real device cells')
    netlist = getattr(result,'netlist',None)
    if netlist is None:
        netlist = GateNetlist.load(Path(result.gds_path).with_suffix('.json'))
    library = library or Library.load(result.data['library']['source'])
    if isinstance(library,(str,Path)):
        library = Library.load(library)
    pdk = Path(pdk_root).expanduser().resolve()
    frame_path = pdk/'libs.tech/klayout/libraries/TR-1um_frame_25x25.gds'
    top = top or f'tr_1um_{netlist.top}'
    if not top or any(c in top for c in '/\\') or top == netlist.top:
        raise ValueError('Chip top must be a safe name distinct from the macro')
    w,h = result.data['die']
    if w > 2050 or h > 1810:
        raise ValueError(f'Macro {w:g} x {h:g} um does not fit the TEG power/pad channels; try fewer rows, another seed or more annealing')
    dx,dy = -w/2,-h/2
    core = [dx,dy,dx+w,dy+h]
    out = Path(output_dir or Path(result.gds_path).parent/'chip').resolve();out.mkdir(parents=True,exist_ok=True)
    data = copy.deepcopy(result.data)
    data.update(top=top,schema='tritflow.chip.v1',die=[2500.,2500.],die_origin=[-1250.,-1250.])
    data['placements'] = [{**p,'x':p['x']+dx,'y':p['y']+dy} for p in data['placements']]
    data['wires'] = [_shift_wire(v,dx,dy) for v in data['wires']]
    data['vias'] = [{**v,'x':v['x']+dx,'y':v['y']+dy} for v in data['vias']]
    macro_pins = [_shift_pin(v,dx,dy) for v in data['power']['pins']]
    for key in ('rails','straps'):
        data['power'][key] = [_shift_wire(v,dx,dy) for v in data['power'][key]]
    data['power']['vias'] = [{**v,'x':v['x']+dx,'y':v['y']+dy} for v in data['power']['vias']]
    data['power']['assumptions']['reserved_current_margin'] = current_margin
    pads, power_header = _power_header(data,macro_pins,core,current_margin)
    layout = db.Layout();layout.dbu=DBU
    parent = layout.create_cell(top)
    source = db.Layout();source.read(str(result.gds_path))
    macro = layout.create_cell(netlist.top);macro.copy_tree(source.cell(netlist.top))
    parent.insert(db.CellInstArray(macro.cell_index(),db.Trans(round(dx/DBU),round(dy/DBU))))
    ref = db.Layout();ref.read(str(frame_path))
    frame = layout.create_cell('OSS_FRAME_TEG');frame.copy_tree(ref.cell('OSS_FRAME_TEG'))
    # Only the copied pad bank changes; the pinned seal-ring tree is preserved.
    for inst in list(frame.each_inst()):
        if layout.cell(inst.cell_index).name.startswith('OSS_PAD16'):
            inst.delete()
    pad = layout.create_cell('TRITFLOW_PROBE_PAD');pad.copy_tree(ref.cell('OSS_PAD_TEG'))
    parent.insert(db.CellInstArray(frame.cell_index(),db.Trans()))
    route_cell = layout.create_cell(top+'__chip_wiring')
    parent.insert(db.CellInstArray(route_cell.cell_index(),db.Trans()))
    shapes, terminals = [], {}
    macro_signal = {p['name']:_shift_pin(p,dx,dy) for p in result.data['pins']}
    wrapper_wires, wrapper_vias = [], []
    for direction,px in (('input',-1100.),('output',1100.)):
        ports = [p for p in netlist.ports if p.dir == direction]
        if len(ports)>13:
            raise ValueError('TEG side supports at most 13 ports; use a multi-side pad assignment')
        # Align each pad's vertical order with its macro access to avoid crossings.
        ports.sort(key=lambda p:sum(macro_signal[p.name]['rect'][1::2])/2)
        ys = np.linspace(-900.,900.,len(ports)) if len(ports)>1 else [0.]
        for port,py in zip(ports,ys):
            py=round(float(py),3);pads.append((port.name,px,py))
            p=macro_signal[port.name];a,b,c,d=p['rect']
            x=dx+3 if direction=='input' else dx+w-3;y=(b+d)/2
            ex=dx-12 if direction=='input' else dx+w+12
            wrapper_wires.append({'net':port.name,'layer':'M1','width':3.4,'points':[[x,y],[ex,y]]})
            wrapper_vias.append({'net':port.name,'x':x,'y':y})
            terminals[port.name]=[(0,ex,y),(0,px+(45 if px<0 else -45),py)]
    for name,x,y in pads:
        frame.insert(db.CellInstArray(pad.cell_index(),db.Trans(round(x/DBU),round(y/DBU))))
        for layer in (0,1):
            shapes.append((layer,name,[x-50,y-50,x+50,y+50]))
    data['pins']=[{'name':n,'layer':'M2','rect':[x-50,y-50,x+50,y+50]} for n,x,y in pads if n not in RAILS]
    data['power']['pins']=[{'name':n,'layer':'M2','rect':[x-50,y-50,x+50,y+50]} for n,x,y in pads if n in RAILS]
    for wire in wrapper_wires+data['power']['rails']+data['power']['straps']:
        rect=wire.get('rect',wire_box(wire))
        if rect[0]<core[0] or rect[2]>core[2] or rect[1]<core[1] or rect[3]>core[3]:
            shapes.append((0 if wire['layer']=='M1' else 1,wire['net'],rect))
    router = ChipRouter(shapes,terminals,core,pads,{n:3.4 for n in terminals})
    for name in sorted(terminals,key=lambda n:abs(terminals[n][0][2]-terminals[n][1][2]),reverse=True):
        wires,vias=router.route(name);wrapper_wires+=wires;wrapper_vias+=vias
    data['wires']+=wrapper_wires;data['vias']+=wrapper_vias
    for wire in wrapper_wires+data['power']['rails'][len(result.data['power']['rails']):]+data['power']['straps'][len(result.data['power']['straps']):]:
        route_cell.shapes(layout.layer(13 if wire['layer']=='M1' else 20,0)).insert(box(wire.get('rect',wire_box(wire))))
    # Power cuts were appended after the translated original macro cuts.
    new_power_vias=data['power']['vias'][len(result.data['power']['vias']):]
    for via in wrapper_vias+new_power_vias:
        x,y=via['x'],via['y']
        route_cell.shapes(layout.layer(19,0)).insert(box([x-.7,y-.7,x+.7,y+.7]))
        for layer in (13,20):
            route_cell.shapes(layout.layer(layer,0)).insert(box([x-1.7,y-1.7,x+1.7,y+1.7]))
    for n,x,y in pads:
        parent.shapes(layout.layer(49,0)).insert(db.Text(n,db.Trans(round(x/DBU),round(y/DBU))))
    for unused in [c.cell_index() for c in layout.top_cells() if c.cell_index()!=parent.cell_index()]:
        if layout.is_valid_cell_index(unused):
            layout.prune_cell(unused,-1)
    candidate=out/(top+'.candidate.gds');options=db.SaveLayoutOptions();options.gds2_write_timestamps=False
    layout.write(str(candidate),options)
    data['macro']={'top':netlist.top,'gds_path':str(Path(result.gds_path).resolve()),
        'gds_sha256':_hash(result.gds_path),'pnr_json':str(Path(result.json_path).resolve()),
        'origin_um':[dx,dy],'bbox_um':core}
    data['frame']={'source':str(frame_path),'sha256':_hash(frame_path),'cell':'OSS_FRAME_TEG',
        'modification':'Peripheral OSS_PAD_TEG instances replace the copied OSS_PAD16 bank; unchanged pinned seal ring',
        'pad_master':'OSS_PAD_TEG','pad_count':len(pads),'ESD':False,'stock_16_pin_package':False}
    data['pad_map']=[{'net':n,'center_um':[x,y],'type':'power' if n in RAILS else 'signal',
                      'opening_um':[x-40,y-40,x+40,y+40]} for n,x,y in pads]
    data['power_header']=power_header
    data['checks']={'connectivity':connectivity(candidate,data,netlist,library)}
    data['power']['dc_current_check']=dc_current_check(data,library)
    data['stats']={'die_size_um':[2500.,2500.],'macro_size_um':[w,h],
                   'pad_count':len(pads),'build_runtime_s':time.perf_counter()-started}
    json_path=out/(top+'.chip.json');_write(json_path,data)
    _reference(netlist,library,out/(top+'.cir'),top)
    wrapped=ChipResult(candidate,json_path,data,{})
    try:
        report=chip_signoff(wrapped,pdk_root=pdk,klayout_binary=klayout_binary,
                            mpw_template=mpw_template,timeout=timeout)
        wrapped.report=report
        if not report['clean']:
            raise PhysicalVerificationError(f'Chip qualification failed; inspect {report["summary_path"]}')
    except Exception:
        failed=out/(top+'.failed.gds');candidate.replace(failed)
        raise
    published=out/(top+'.gds');candidate.replace(published);wrapped.gds_path=published
    report['gds_path']=str(published);_write(Path(report['summary_path']),report)
    return wrapped


def _reference(netlist,library,path,top):
    from tritflow.sim.spice import gate_spice
    from tritflow.synth.writers import spice_names
    # Preserve synthesis's reversible encoding annotations on all wrapper ports.
    ports=[p.name for p in netlist.ports]+list(RAILS)
    mapping=spice_names(netlist.nets(), (*RAILS,'0'))
    encoded=[mapping[p.name] for p in netlist.ports]+list(RAILS)
    reference=gate_spice(netlist,(Path(library.source)/'out/all.spice').read_text())
    reference+='\n.subckt '+top+' '+' '.join(encoded)+'\nXmacro '+' '.join(encoded)+' '+netlist.top+'\n.ends '+top+'\n'
    path.write_text(reference)


def chip_signoff(result, *, pdk_root=PDK_ROOT, klayout_binary=None, mpw_template=None, timeout=180):
    """Unmodified pinned drawing/LVS, MDP and mask decks, all items counted."""
    from tritflow.extract import extract_layout
    started=time.perf_counter();source=Path(result.gds_path).resolve();top=result.data['top']
    out=source.parent/'signoff';out.mkdir(exist_ok=True)
    pdk=Path(pdk_root).expanduser().resolve()
    binary=Path(klayout_binary or shutil.which('klayout') or Path.home()/'bin/klayout/klayout').resolve()
    for group in ('drc','lvs'):
        shutil.copytree(pdk/'libs.tech/klayout/tech'/group,out/'pdk/libs.tech/klayout/tech'/group,dirs_exist_ok=True)
    drawing=out/(top+'.drawing.gds');shutil.copy2(source,drawing)
    deck=out/'pdk/libs.tech/klayout/tech/drc'
    drc=_drc(binary,deck/'run.drc',drawing,top,out,'drawing_drc',timeout)
    lvs=extract_layout(drawing,top,out/'lvs',reference=source.parent/(top+'.cir'),
                       pdk=out/'pdk',executable=binary,timeout=timeout);lvs.pop('log',None)
    mask=out/(top+'.ip62.gds');mask.unlink(missing_ok=True)
    mdp=_run([binary,'-b','-r',deck/'run_mdp.drc','-rd',f'input={drawing}',
              '-rd',f'cellname={top}','-rd',f'output={mask}'],out,'mdp',timeout)
    if mdp['exit_code'] or not mask.exists():
        raise RuntimeError(f'MDP failed; inspect {mdp["log_path"]}')
    mdp.update(output_path=str(mask),metal_preservation=_metal_preservation(drawing,mask,top))
    mask_drc=_drc(binary,deck/'run_IP62.drc',mask,top,out,'mask_drc',timeout)
    audit=_layout_audit(drawing,top)
    precheck={'clean':audit['bbox_um']==[-1250.,-1250.,1250.,1250.] and audit['top_cells']==[top]
                       and audit['dbu_um']==.001 and bool(audit['frame_cells']),
              'method':'MPW fixed 2.5 mm centered die, DBU and frame checks'}
    if mpw_template:
        copied=out/'pre_check.py';shutil.copy2(Path(mpw_template)/'scripts/pre_check.py',copied)
        precheck=_run([sys.executable,copied,'--top',top,drawing],out,'mpw_precheck',timeout)
        precheck['clean']=precheck['exit_code']==0
    clean=(drc['clean'] and lvs['matched'] and mask_drc['clean'] and precheck['clean']
           and result.data['checks']['connectivity']['clean'] and not audit['waiver_polygon_count']
           and mdp['metal_preservation']['clean'])
    report={'schema':'tritflow.chip.signoff.v1','clean':bool(clean),'physical_checks_passed':bool(clean),
        'submission_ready':False,'reason':'Custom TEG pad/bond allocation and ESD/power/package approval still required',
        'top':top,'gds_path':str(source),'drawing_drc':drc,'drawing_lvs':lvs,'mdp':mdp,'mask_drc':mask_drc,
        'drawing_audit':audit,'mpw_precheck':precheck,'self_checks':result.data['checks'],
        'dc_current_check':result.data['power']['dc_current_check'],
        'mask_lvs':{'defined':False,'matched':None,'reason':'Inspected MPW workflow defines drawing LVS before MDP; no post-MDP LVS stage'},
        'provenance':{'pdk_root':str(pdk),'frame':result.data['frame'],
            'rule_sha256':{str(p.relative_to(out/'pdk')):_hash(p) for p in (out/'pdk').rglob('*') if p.is_file()},
            'binary_sha256':_hash(binary),'source_sha256':_hash(source)},
        'runtime_s':time.perf_counter()-started,'summary_path':str(out/'signoff.summary.json')}
    _write(out/'signoff.summary.json',report)
    return report
