"""Run the installed TR-1um KLayout deck with strict top-level port checking."""
from __future__ import annotations
from pathlib import Path
import re
import subprocess
from tritflow import PDK_ROOT
from tritflow.sim.spice import gate_spice, lvs_netlist, subcircuits


class ExtractionError(RuntimeError):
    """KLayout execution or extraction failed (distinct from an LVS mismatch)."""


def _unused_pin(definitions, top, pin, active=()):
    """Prove a formal is unused recursively; unknown device models count as use."""
    key=(top.lower(),pin.lower())
    if key in active: return False
    definition=definitions.get(top.lower())
    if definition is None: return False
    for line in re.sub(r'\n\s*\+\s*',' ',definition['body']).splitlines():
        tokens=line.split()
        if not tokens or tokens[0].startswith(('*','.')): continue
        end=next((i for i,t in enumerate(tokens) if '=' in t or t.lower()=='params:'),len(tokens))
        if tokens[0][0].upper()=='X':
            model=tokens[end-1].lower();nodes=tokens[1:end-1]
            for index,node in enumerate(nodes):
                if node.lower()!=pin.lower(): continue
                child=definitions.get(model)
                if child is None or index>=len(child['pins']): return False
                if not _unused_pin(definitions,model,child['pins'][index],active+(key,)): return False
        else:
            count=4 if tokens[0][0].upper()=='M' else 2
            if any(n.lower()==pin.lower() for n in tokens[1:count+1]): return False
    return True


def extract_layout(gds: str | Path, top: str, outdir: str | Path, *,
                   reference: str | Path | None = None, gate_netlist=None,
                   cell_subckts: str | None = None, pdk: str | Path = PDK_ROOT,
                   executable: str | Path = Path.home() / 'bin/klayout/klayout',
                   timeout: float = 180) -> dict:
    """Extract devices and optionally compare to reference SPICE or GateNetlist.

    Returns paths, match status, per-circuit comparison statuses and deck errors.
    A completed mismatch is returned as matched=False, never hidden by exit code 0.
    Input files are read only; all outputs are inside outdir.
    """
    import klayout.db as db
    out = Path(outdir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    gds = Path(gds).expanduser().resolve()
    if not gds.is_file():
        raise FileNotFoundError(gds)
    deck = Path(pdk).expanduser().resolve() / 'libs.tech/klayout/tech/lvs/run.lvs'
    if not deck.is_file():
        raise FileNotFoundError(deck)
    if reference is not None and gate_netlist is not None:
        raise ValueError('Choose a reference file or a GateNetlist')
    if gate_netlist is not None:
        if cell_subckts is None:
            raise ValueError('GateNetlist comparison requires cell subcircuits')
        text = gate_spice(gate_netlist, cell_subckts)
    elif reference is not None:
        text = Path(reference).read_text()
    else:
        text = None
    ref = out / 'reference.spice'
    if text is not None:
        ref.write_text(lvs_netlist(text))
    extracted, report = out / f'{top}.ext.spice', out / f'{top}.lvsdb'
    for path in (extracted, report):
        path.unlink(missing_ok=True)
    command = [str(executable), '-b', '-r', str(deck)]
    options = dict(input=gds, top_cell=top, report=report, extracted=extracted)
    options.update(circuit=ref) if text is not None else options.update(netlist_only='true')
    for name, value in options.items():
        command.extend(['-rd', f'{name}={value}'])
    try:
        process = subprocess.run(command, cwd=out, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ExtractionError(f'KLayout timeout after {timeout:g} s') from exc
    except OSError as exc:
        raise ExtractionError(f'Cannot execute KLayout: {exc}') from exc
    log = process.stdout + process.stderr
    (out / 'klayout.log').write_text(log)
    if process.returncode or not extracted.is_file() or (text is not None and not report.is_file()):
        raise ExtractionError(f'KLayout failed (exit {process.returncode}):\n{log[-6000:]}')
    if text is None:
        # The PDK does not emit an LVS database when no comparison is run.
        return dict(matched=None, extracted=str(extracted), report=None, circuits=[],
                    errors=[], log=log, strict_ports=True,
                    scope='PDK device extraction only; no comparison or connectivity database')
    result = db.LayoutVsSchematic()
    result.read(str(report))
    errors = [error.message for error in result.each_error()]
    pairs = list(result.xref().each_circuit_pair()) if result.xref() is not None else []
    circuits = [{'layout': pair.first().name if pair.first() is not None else None,
                 'reference': pair.second().name if pair.second() is not None else None,
                 'status': str(pair.status())} for pair in pairs]
    layout_top = subcircuits(extracted.read_text()).get(top.lower())
    reference_top = subcircuits(text).get(top.lower())
    layout_pins = {p.lower() for p in layout_top['pins']} if layout_top else set()
    reference_pins = {p.lower() for p in reference_top['pins']} if reference_top else set()
    restored=[]
    # The PDK purges physically present pass-through rails with no device loads.
    # Restore only reference power formals proven unused through the hierarchy.
    for pin in sorted(reference_pins-layout_pins):
        if pin in {'vdd','vmid','vss'} and layout_top and _unused_pin(subcircuits(text),top,pin):
            restored.append(pin.upper())
    if restored:
        raw=extracted.read_text()
        (out/f'{top}.raw.ext.spice').write_text(raw)
        signature=re.compile(r'(?im)^(\s*\.subckt\s+'+re.escape(top)+r'\b[^\n]*)')
        extracted.write_text(signature.sub(lambda m:m[1]+' '+' '.join(restored),raw,count=1))
        layout_pins.update(p.lower() for p in restored)
    if layout_top is None or reference_top is None or layout_pins != reference_pins:
        errors.append(f'Top port mismatch for {top}: layout-only={sorted(layout_pins-reference_pins)}, '
                      f'reference-only={sorted(reference_pins-layout_pins)}')
    matched = (bool(pairs) and not errors
                    and all(p.status() == db.NetlistCrossReference.Match for p in pairs)
                    and 'Congratulations! Netlists match.' in log)
    return dict(matched=matched, extracted=str(extracted), report=str(report),
                circuits=circuits, errors=errors, log=log, strict_ports=True,
                unused_power_formals_restored=restored,
                scope='PDK device extraction; intrinsic device parasitics; no signal-wire resistance')
