"""SPICE boundaries: explicit port order, PDK model includes and gate netlists."""
from __future__ import annotations

from pathlib import Path
import re
from tritflow import PDK_ROOT, RAILS

CELL_PINS = {'INV': ('A', 'Y'), 'BUF': ('A', 'Y'), 'NAND': ('A', 'B', 'Y'),
             'NOR': ('A', 'B', 'Y'), 'NANY': ('A', 'B', 'Y'),
             'TIEP': ('Y',), 'TIEZ': ('Y',), 'TIEN': ('Y',), 'FILL': ()}


def subcircuits(text: str) -> dict[str, dict]:
    """Read subcircuit declarations, preserving formal pin spelling and order."""
    result = {}
    pattern = r'^[ \t]*\.subckt[ \t]+(\S+)[ \t]*([^\n]*(?:\n[ \t]*\+[^\n]*)*)\n(.*?)^[ \t]*\.ends\b[^\n]*'
    for match in re.finditer(pattern, text, re.M | re.S | re.I):
        pins = []
        for token in re.sub(r'\n[ \t]*\+[ \t]*', ' ', match[2]).split():
            if '=' in token or token.lower() == 'params:':
                break
            pins.append(token)
        result[match[1].lower()] = {'name': match[1], 'pins': pins, 'body': match[3], 'text': match[0]}
    return result


def simulation_netlist(text: str) -> str:
    """Make KLayout escaped-dollar nodes safe and use PDK MOS wrapper subckts.

    LVS reads native M devices; the ngspice PDK supplies PMOS/NMOS as X wrappers.
    Only device prefixes change; W/L and extracted junction geometry are retained.
    """
    text = re.sub(r'\\\$(\w+)', r'n_ex_\1', text)
    text = re.sub(r'(?m)^([XMRCD]\w*)\$(\w+)', r'\1_ex_\2', text)
    return re.sub(r'(?im)^M(\S+)(\s+\S+\s+\S+\s+\S+\s+\S+\s+(?:NMOS|PMOS|NMOSE|PMOSE)\b)', r'XM\1\2', text)


def lvs_netlist(text: str) -> str:
    """Translate PDK MOS X wrappers into native M devices for the LVS reader."""
    return re.sub(r'(?im)^X(\S+)(\s+\S+\s+\S+\s+\S+\s+\S+\s+(?:NMOS|PMOS|NMOSE|PMOSE)\b)', r'M\1\2', text)


def model_includes(pdk: str | Path = PDK_ROOT) -> str:
    """Resolve ip62_models and its sibling includes without relying on Xschem LIB."""
    folder = Path(pdk).expanduser().resolve() / 'libs.tech/spice/models'
    model = folder / 'ip62_models'
    if not model.is_file():
        raise FileNotFoundError(f"PDK model index missing: {model}")
    return re.sub(r'(?im)^\.include\s+["\']?([^\s"\']+)["\']?\s*$',
                  lambda m: f'.include "{folder / m[1]}"', model.read_text())


def gate_spice(netlist, cell_subckts: str) -> str:
    """Use synthesis' reversible SPICE naming and validate the cell pin contract."""
    from tritflow.synth.writers import spice
    definitions = subcircuits(cell_subckts)
    for inst in netlist.instances:
        order = CELL_PINS[inst.cell]
        if inst.cell.lower() not in definitions:
            raise ValueError(f"Missing cell subcircuit: {inst.cell}")
        actual = definitions[inst.cell.lower()]['pins']
        if [p.upper() for p in actual] != list(order) + list(RAILS):
            raise ValueError(f"Cell {inst.cell} port order violates docs/interfaces.md: {actual}")
    return spice(netlist) + '\n' + cell_subckts


def logical_spice_names(text):
    """Recover the explicit encoded→logical net annotations written by synthesis."""
    return {m[1]: m[2] for m in re.finditer(r'^\* net (\S+) = (.+)$', text, re.M)}


def signal_waveform(data, pin):
    """Prefer a case-sensitive logical key; support legacy lowercase raw data."""
    key = f'v({pin})'
    return data[key] if key in data else data[key.lower()]


def rename_formal_nodes(definition, mapping):
    """Rename exact terminal tokens, preserving model/device/subcircuit names."""
    lines=[]
    for line in re.sub(r'\n\s*\+\s*',' ',definition['text']).splitlines():
        fields=line.split()
        if not fields or fields[0].startswith('*'):
            lines.append(line); continue
        first=fields[0].upper()
        if first=='.SUBCKT':
            indices=range(2,2+len(definition['pins']))
        elif first.startswith('X'):
            end=next((i for i,t in enumerate(fields) if '=' in t or t.lower()=='params:'),len(fields))
            indices=range(1,end-1)
        elif first[0] in 'MRCLDVIE':
            indices=range(1,min(len(fields),5 if first[0] in 'ME' else 3))
        else:
            lines.append(line);continue
        for i in indices: fields[i]=mapping.get(fields[i],fields[i])
        lines.append(' '.join(fields))
    return '\n'.join(lines)
