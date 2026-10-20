"""Sequential gate source and SPICE, preserving the shared physical pin order."""
from tritflow.synth.simulate import CELL_INPUTS, ordered_instances
from tritflow.synth.writers import spice_names, tv_identifier
from .synthesis import as_sequential


def spice(net):
    """D CLK Q VDD VMID VSS for TDFF; combinational pin order is unchanged."""
    net = as_sequential(net)
    names = spice_names(net.nets(), ('VDD', 'VMID', 'VSS', '0'))
    instances = spice_names([i.name for i in net.instances])
    top = spice_names([net.top])[net.top]
    lines = ['* TritFlow clocked cell netlist.']
    lines += [f'* net {encoded} = {original}' for original, encoded in names.items() if original != encoded]
    lines += [f'.subckt {top} ' + ' '.join([*(names[p.name] for p in net.ports), 'VDD', 'VMID', 'VSS'])]
    for inst in net.instances:
        order = ('D', 'CLK', 'Q') if inst.cell == 'TDFF' else (*CELL_INPUTS[inst.cell], 'Y')
        lines.append(f'X{instances[inst.name]} ' + ' '.join(names[inst.pins[p]] for p in order)
                     + f' VDD VMID VSS {inst.cell}')
    return '\n'.join([*lines, f'.ends {top}', ''])


def tritverilog(net):
    """Emit existing primitives plus one explicit <= assignment per stored trit."""
    net = as_sequential(net)
    states = set(net.state_names)
    ident = tv_identifier
    ports = ', '.join(f'{p.dir} ' + ('reg ' if p.dir == 'output' and p.name in states else '')
                      + f'trit {ident(p.name)}' for p in net.ports)
    lines = ['// Generated clocked TritVerilog; no implicit reset or initial state.',
             f'module {ident(net.top)}({ports});']
    for name in sorted(net.nets() - {p.name for p in net.ports}):
        lines.append(f'  {"reg" if name in states else "wire"} trit {ident(name)};')
    for inst in ordered_instances(net.cut()):
        if inst.cell.startswith('TIE'):
            digit = {'TIEN': 'T', 'TIEZ': '0', 'TIEP': '1'}[inst.cell]
            lines.append(f'  assign {ident(inst.pins["Y"])} = 1\'t{digit};')
        else:
            pins = [inst.pins['Y'], *(inst.pins[p] for p in CELL_INPUTS[inst.cell])]
            lines.append(f'  {inst.cell.lower()} {ident(inst.name)}(' + ', '.join(map(ident, pins)) + ');')
    for inst in net.registers:
        lines.append(f'  always @(posedge {ident(net.clock)}) {ident(inst.pins["Q"])} <= {ident(inst.pins["D"])};')
    return '\n'.join([*lines, 'endmodule', ''])
