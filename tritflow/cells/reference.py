"""Fresh independent source netlisting and extraction of the taped-out macros."""
from pathlib import Path
import hashlib
import re
import klayout.db as db

from tritflow import PDK_ROOT
from tritflow.sim.spice import lvs_netlist
from .circuits import Circuit, circuits
from .verify import lvs, run

ORIGINALS={'INV':'inverter','NAND':'mul_nand','NOR':'mul_nor','NANY':'nany'}
PORT_ALIASES={'vin':'A','a':'A','b':'B','vout':'Y','V+':'VDD','V-':'VSS',r'V\x2d':'VSS'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(text, cell):
    """Rename public ports only; keep all extracted devices/parameters intact."""
    declaration=re.search(r'(?im)^\.subckt\s+\S+[^\n]*\n',text)
    end=re.search(r'(?im)^\.ends\b',text)
    if declaration is None or end is None:raise ValueError('Missing subcircuit')
    body=text[declaration.end():end.start()]
    body=re.sub(r'\S+',lambda m:PORT_ALIASES.get(m[0],m[0]),body)
    return '* Public ports renamed from independent taped-out reference\n.subckt '+cell+' '+\
           ' '.join(circuits()[cell].ports)+'\n'+body+'.ends '+cell+'\n'


def original_port_names(gds,source,folder):
    """Rename existing legacy signal/rail labels in a scratch reference copy.

    KLayout escapes the '-' in V- as V\\x2d in extracted SPICE. Public strict
    port checking compares spelling too. Use the same unambiguous A/B/Y and
    VDD/VSS aliases in the existing labels and fresh source, without adding any
    port, conductor, device or changing a dimension. Keep the original top name.
    """
    layout=db.Layout();layout.read(str(gds));changes=0
    for cell in layout.each_cell():
        for layer in ((48,0),(49,0),(48,1),(49,1)):
            for shape in cell.shapes(layout.layer(*layer)).each():
                if shape.is_text() and shape.text.string in PORT_ALIASES:
                    label=shape.text;label.string=PORT_ALIASES[label.string];shape.text=label;changes+=1
    target=folder/'public_labels.gds';layout.write(str(target))
    renamed=re.sub(r'\S+',lambda m:PORT_ALIASES.get(m[0],m[0]),source)
    return target,renamed,{'method':'Existing legacy labels and source nodes renamed together; no geometry or port added.',
                          'labels_renamed':changes,'aliases':PORT_ALIASES,'gds_sha256':sha(target)}


def prepare(reference, out, compact):
    """Strict LVS both the original and compact GDS against fresh Xschem."""
    reference=Path(reference).expanduser().resolve();out=Path(out)
    report={}
    for cell,old in ORIGINALS.items():
        folder=out/cell;folder.mkdir(parents=True,exist_ok=True)
        rc=folder/'xschemrc'
        rc.write_text(f'set XSCHEM_LIBRARY_PATH {{{reference}:/usr/local/share/xschem/xschem_library:{PDK_ROOT}/libs.tech/xschem:{PDK_ROOT}/libs.tech/xschem/TR-1umLIB}}\n'
                      'set lvs_netlist 1\nset top_is_subckt 1\nset spiceprefix 1\n')
        sch=reference/f'{old}.sch';gds=reference/f'{old}.gds'
        code,log=run(['xschem','-r','-x','--rcfile',rc,'-s','--command',
                      'set result [xschem netlist]; puts [xschem get infowindow_text]; exit $result',
                      '-o',folder,sch],folder,'netlist.log')
        if code or re.search(r'Error:|SKIPPING|IS MISSING',log):raise RuntimeError(log[-2000:])
        source=lvs_netlist((folder/f'{old}.spice').read_text())
        (folder/f'{old}.source.lvs.spice').write_text(source)
        named_gds,named_source,normalization=original_port_names(gds,source,folder)
        (folder/f'{old}.lvs.spice').write_text(named_source)
        original=lvs(named_gds,Circuit(old,()),folder,normalize=False)
        # Match the compact GDS against this independently generated schematic,
        # not the generator's Circuit tuples or its .lvs.spice output.
        check=folder/'compact_lvs';check.mkdir(exist_ok=True)
        (check/f'{cell}.lvs.spice').write_text(canonical(source,cell))
        updated=lvs(compact/cell/f'{cell}.gds',circuits()[cell],check)
        raw=folder/'extracted.raw.spice'
        (folder/'original.ext.spice').write_text(canonical(raw.read_text(),cell))
        report[cell]={'original_top':old,'original_gds_sha256':sha(gds),
                      'source_schematic_sha256':sha(sch),'fresh_source_sha256':sha(folder/f'{old}.spice'),
                      'original_extracted_sha256':sha(raw),'compact_gds_sha256':sha(compact/cell/f'{cell}.gds'),
                      'compact_extracted_sha256':sha(compact/cell/f'{cell}.ext.spice'),
                      'original_lvs':original,'compact_lvs':updated,
                      'original_label_normalization':normalization,
                      'passed':original['passed'] and updated['passed']}
        print(cell,'independent schematic LVS',report[cell]['passed'],flush=True)
    return report


def device_parameters(text):
    """Compare intrinsic device/junction parameters independent of instance IDs.

    Connectivity is proved by strict LVS; this additionally checks the intrinsic
    parasitics retained in the simulator's device network.
    """
    rows=[]
    for line in text.splitlines():
        t=line.split()
        if not t or t[0][0].upper() not in ('X','M'):continue
        model_index=next((i for i,x in enumerate(t) if x in ('PMOS','NMOS','F_RR')),None)
        if model_index is None:continue
        rows.append((t[model_index],tuple(sorted(x.upper() for x in t[model_index+1:]))))
    return sorted(rows)


def two_inverters(text, *, native=False):
    """Flatten two independent INV references into the BUF public interface."""
    # Simulation-form node names avoid SPICE's escaped-dollar ambiguity.
    from tritflow.sim.spice import simulation_netlist
    text=simulation_netlist(text)
    body=[]
    devices=[line.split() for line in text.splitlines() if line and line[0] in 'XM']
    for stage in (0,1):
        public={'A':'A' if stage==0 else 'mid','Y':'mid' if stage==0 else 'Y',
                'VDD':'VDD','VMID':'VMID','VSS':'VSS'}
        for device in devices:
            t=device.copy();model_index=next(i for i,x in enumerate(t) if x in ('PMOS','NMOS','F_RR'))
            t[0]=t[0][0]+f'stage{stage}_'+t[0][1:]
            for i in range(1,model_index):t[i]=public.get(t[i],f'stage{stage}_'+t[i])
            body.append(' '.join(t))
    result='.subckt BUF A Y VDD VMID VSS\n'+'\n'.join(body)+'\n.ends BUF\n'
    return lvs_netlist(result) if native else result


def prepare_buf(original_inv, out, compact):
    """Prove BUF against two fresh source INV circuits, not generated tuples."""
    folder=out/'BUF';folder.mkdir(parents=True,exist_ok=True)
    source=canonical((out/'INV'/'inverter.spice').read_text(),'INV')
    (folder/'BUF.lvs.spice').write_text(two_inverters(source,native=True))
    result=lvs(compact/'BUF'/'BUF.gds',circuits()['BUF'],folder)
    original=two_inverters(original_inv)
    (folder/'original.ext.spice').write_text(original)
    return original,{'passed':result['passed'],'compact_lvs':result,
                     'source':'Two flattened fresh independent inverter.sch circuits',
                     'compact_gds_sha256':sha(compact/'BUF'/'BUF.gds'),
                     'compact_extracted_sha256':sha(compact/'BUF'/'BUF.ext.spice')}
