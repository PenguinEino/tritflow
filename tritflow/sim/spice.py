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
    text = re.sub(r'\n\s*\+\s*', ' ', text)
    result = {}
    for match in re.finditer(r'^\s*\.subckt\s+(\S+)\s*([^\n]*)\n(.*?)^\s*\.ends\b[^\n]*', text, re.M | re.S | re.I):
        pins = []
        for token in match[2].split():
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
    """Build an LVS reference with bit-blasted port names and the contracted cells."""
    definitions = subcircuits(cell_subckts)
    lines = [f'.subckt {netlist.top} ' + ' '.join([p.name for p in netlist.ports] + list(RAILS))]
    for inst in netlist.instances:
        order = CELL_PINS[inst.cell]
        if inst.cell.lower() not in definitions:
            raise ValueError(f"Missing cell subcircuit: {inst.cell}")
        actual = definitions[inst.cell.lower()]['pins']
        if [p.upper() for p in actual] != list(order) + list(RAILS):
            raise ValueError(f"Cell {inst.cell} port order violates docs/interfaces.md: {actual}")
        lines.append(f'X{inst.name} ' + ' '.join([inst.pins[p] for p in order] + list(RAILS)) + f' {inst.cell}')
    lines.append(f'.ends {netlist.top}')
    return '\n'.join(lines) + '\n' + cell_subckts
