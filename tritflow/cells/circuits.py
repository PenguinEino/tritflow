"""Transistor connectivity of the RR30 taped-out balanced-ternary gates.

MOS tuples are (name, model, drain, gate, source, bulk, W in um); L=1 um.
RR tuples are (name, terminal A, terminal B, well); W/L=2.8/30 um.
The two resistor branches form the inverter's resistive midpoint. NANY adds
oppositely controlled complementary stacks between that midpoint and VMID.
"""
from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class Circuit:
    name: str
    inputs: tuple[str, ...]
    mos: tuple = ()
    resistors: tuple = ()

    @property
    def ports(self):
        return self.inputs + (() if self.name == 'FILL' else ('Y',)) + ('VDD', 'VMID', 'VSS')

    @property
    def nets(self):
        return sorted(set(self.ports) | {n for m in self.mos for n in m[2:6]} |
                      {n for r in self.resistors for n in r[1:]})


def circuits():
    """Return explicit circuits, including a flattened pair of INV for BUF."""
    inv = Circuit('INV', ('A',), (
        ('MP', 'PMOS', 'p', 'A', 'VDD', 'VDD', 13.5),
        ('MN', 'NMOS', 'n', 'A', 'VSS', 'VSS', 5)),
        (('RP', 'p', 'Y', 'VDD'), ('RN', 'Y', 'n', 'VDD')))
    nand = Circuit('NAND', ('A', 'B'), (
        ('P1', 'PMOS', 'p', 'A', 'VDD', 'VDD', 19),
        ('P2', 'PMOS', 'p', 'B', 'VDD', 'VDD', 19),
        ('N1', 'NMOS', 'n', 'A', 'nn', 'VSS', 13),
        ('N2', 'NMOS', 'nn', 'B', 'VSS', 'VSS', 13)),
        (('RP', 'p', 'Y', 'VDD'), ('RN', 'Y', 'n', 'VDD')))
    nor = Circuit('NOR', ('A', 'B'), (
        ('P1', 'PMOS', 'pp', 'A', 'VDD', 'VDD', 37),
        ('P2', 'PMOS', 'p', 'B', 'pp', 'VDD', 37),
        ('N1', 'NMOS', 'n', 'A', 'VSS', 'VSS', 6.5),
        ('N2', 'NMOS', 'n', 'B', 'VSS', 'VSS', 6.5)),
        (('RP', 'p', 'Y', 'VDD'), ('RN', 'Y', 'n', 'VDD')))
    nany = Circuit('NANY', ('A', 'B'), (
        ('P1', 'PMOS', 'pp', 'A', 'VDD', 'VDD', 34),
        ('P2', 'PMOS', 'p', 'B', 'pp', 'VDD', 34),
        ('N1', 'NMOS', 'n', 'A', 'nn', 'VSS', 11),
        ('N2', 'NMOS', 'nn', 'B', 'VSS', 'VSS', 11),
        ('CP1', 'PMOS', 'c1', 'A', 'Y', 'VDD', 14),
        ('CN1', 'NMOS', 'c1', 'B', 'VMID', 'VSS', 8),
        ('CP2', 'PMOS', 'c2', 'B', 'Y', 'VDD', 14),
        ('CN2', 'NMOS', 'c2', 'A', 'VMID', 'VSS', 8)),
        (('RP', 'p', 'Y', 'VDD'), ('RN', 'Y', 'n', 'VDD')))
    mos, rr = [], []
    for stage, remap in enumerate(({'A': 'A', 'Y': 'mid', 'p': 'p0', 'n': 'n0'},
                                   {'A': 'mid', 'Y': 'Y', 'p': 'p1', 'n': 'n1'})):
        for name, model, d, g, s, b, w in inv.mos:
            mos.append((name + str(stage), model, *(remap.get(n, n) for n in (d,g,s,b)), w))
        for name, a, b, sub in inv.resistors:
            rr.append((name + str(stage), *(remap.get(n, n) for n in (a,b,sub))))
    return {c.name: c for c in (inv, nand, nor, nany, Circuit('BUF', ('A',), tuple(mos), tuple(rr)),
            *(Circuit(name, (), resistors=(('RT', 'Y', rail, 'VDD'),)) for name, rail in
              [('TIEP','VDD'), ('TIEZ','VMID'), ('TIEN','VSS')]), Circuit('FILL', ()))}


def ideal(name, values):
    """Balanced-ternary output; FILL has no logical function."""
    if name == 'INV': return -values[0]
    if name == 'BUF': return values[0]
    if name == 'NAND': return -min(values)
    if name == 'NOR': return -max(values)
    if name == 'NANY': return -max(-1, min(1, sum(values)))
    return {'TIEP': 1, 'TIEZ': 0, 'TIEN': -1}[name]


def truth_table(circuit):
    return [{'inputs': dict(zip(circuit.inputs, v)), 'Y': ideal(circuit.name, v)}
            for v in product((-1,0,1), repeat=len(circuit.inputs))] if circuit.name != 'FILL' else []


def spice(circuit, simulation=True):
    """PDK model wrappers are X devices; LVS requires native M devices."""
    lines = ['* RR30 schematic connectivity; lengths in micrometres',
             '.subckt ' + circuit.name + ' ' + ' '.join(circuit.ports)]
    for name, model, d, g, s, b, w in circuit.mos:
        lines.append(f'{"X" if simulation else "M"}{name} {d} {g} {s} {b} {model} W={w}u L=1u')
    for name, a, b, sub in circuit.resistors:
        lines.append(f'X{name} {a} {b} {sub} F_RR W=2.8u L=30u')
    return '\n'.join(lines + ['.ends ' + circuit.name, ''])
