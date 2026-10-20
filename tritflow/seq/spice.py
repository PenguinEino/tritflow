"""Clocked transient decks, state initialization guesses and cycle-band checks.

This module calls the existing ngspice runner and extraction APIs. No behavioral
storage or ideal data sources replace the TDFF device network. Explicit initial
state is a Newton .nodeset guess only: it is not a reset, .ic, or UIC constraint.
Every initial Q and every sampled register are checked against the logic model.
"""
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
import time as clock_time

from tritflow import PDK_ROOT
from tritflow.sim.runner import run_ngspice
from tritflow.sim.tools import simulator_identity
from tritflow.sim.spice import model_includes, simulation_netlist, subcircuits, logical_spice_names
from tritflow.synth.writers import spice_names
from .characterize import pwl
from .synthesis import as_sequential


def _node(name):
    return simulation_netlist('\\'+name if name.startswith('$') else name)


def initial_guesses(net, text, initial, inputs, lvs_report):
    """Use the LVS name map for Q, mapped gate nets, and actual TDFF latch nodes."""
    from tritflow.extract import reference_net_map
    values = net.values(inputs, initial)
    mapping = (reference_net_map(lvs_report, net.top) if lvs_report else
               spice_names(net.nets(), ('VDD','VMID','VSS','0')))
    top = subcircuits(text)[net.top.lower()]
    ports = spice_names([p.name for p in net.ports], ('VDD','VMID','VSS','0'))
    guesses = {(ports[name] if name in ports else 'xdut.'+_node(mapping[name])):5*int(value)
               for name,value in values.items() if name in mapping and name != net.clock}
    memory = (reference_net_map(lvs_report, 'TDFF') if lvs_report else
              {name: {'S.U':'xs.u','M.U':'xm.u'}.get(name,name)
               for name in ['SQ','SQB','S.U','M','MQB','M.U','B','DI','DB','ML','MB','SL','SB']})
    definitions = subcircuits(text)
    pins = definitions['tdff']['pins']
    qi = [p.upper() for p in pins].index('Q')
    physical = []
    for line in top['body'].splitlines():
        fields = line.split()
        if fields and fields[0].upper().startswith('X') and fields[-1].upper() == 'TDFF':
            physical.append(fields)
    for reg in net.registers:
        q, d = int(initial[reg.pins['Q']]), int(values[reg.pins['D']])
        expected = _node(mapping[reg.pins['Q']]).lower()
        matches = [row for row in physical if _node(row[1+qi]).lower() == expected]
        if len(matches) != 1:
            raise ValueError('Cannot map exactly one physical TDFF to '+reg.pins['Q'])
        inst = _node(matches[0][0])
        seeds = {'SQ':q,'SQB':-q,'S.U':q,'M':d,'MQB':-d,'M.U':d,
                 'B':d,'DI':d,'DB':-d,'ML':1,'MB':-1,'SL':-1,'SB':1}
        # RR models admit off-rail algebraic roots. Seed each inverter's
        # PMOS/NMOS drain side of the divider as well as its output, without
        # constraining any voltage during transient integration.
        inv_inputs = {'M.1':d,'M.2':-d,'B':-d,'DA':d,'DB':-d,
                      'S.1':q,'S.2':-q,'Q':-q}
        for inv, value in inv_inputs.items():
            for terminal, guess in [('NET1',1 if value <= 0 else -1),
                                    ('NET2',-1 if value >= 0 else 1)]:
                logical = inv+'.'+terminal
                if logical in memory:
                    seeds[logical] = guess
        for logical, value in seeds.items():
            if logical not in memory:
                raise ValueError('TDFF memory-node contract missing '+logical)
            guesses['xdut.'+inst+'.'+_node(memory[logical])] = 5*value
    if lvs_report:
        from .initial import gate_nodes
        cell_maps = {name:reference_net_map(lvs_report,name)
                     for name in {i.cell for i in net.instances if i.cell != 'TDFF'}}
        for gate in (i for i in net.instances if i.cell != 'TDFF'):
            cell = definitions[gate.cell.lower()]
            yi = [p.upper() for p in cell['pins']].index('Y')
            target = _node(mapping[gate.pins['Y']]).lower()
            physical_gate = []
            for line in top['body'].splitlines():
                fields = line.split()
                if (fields and fields[0].upper().startswith('X') and
                    fields[-1].upper() == gate.cell and _node(fields[1+yi]).lower() == target):
                    physical_gate.append(fields)
            if len(physical_gate) != 1:
                raise ValueError('Cannot map gate for Newton guesses '+gate.name)
            instance = _node(physical_gate[0][0])
            internal = cell_maps[gate.cell]
            logical = {pin:int(values[net_name]) for pin,net_name in gate.pins.items()}
            for name,value in gate_nodes(gate.cell,logical).items():
                actual = internal.get(name,internal.get(name.upper()))
                if actual is None:
                    raise ValueError('Missing published gate internal node '+gate.cell+'.'+name)
                guesses['xdut.'+instance+'.'+_node(actual)] = 5*value
    return guesses, mapping


def build_testbench(net, text, vectors, *, initial, period_s=1e-6, edge_s=1e-9,
                    load=10e-15, pdk=PDK_ROOT, lvs_report=None, solver_options=None):
    """One rising capture per data row; change data in the preceding low phase."""
    net = as_sequential(net)
    if not vectors or not np.isfinite(period_s) or period_s <= 4*edge_s or edge_s <= 0:
        raise ValueError('finite positive clock period > four edge times and nonempty vectors required')
    if not np.isfinite(load) or load < 0:
        raise ValueError('output load must be finite and nonnegative')
    # Validate initial state and every input before starting a tool.
    net.values(vectors[0], initial)
    rows = net.cycles(vectors, initial)
    top_name = spice_names([net.top])[net.top]
    definition = subcircuits(text).get(top_name.lower())
    if definition is None:
        raise ValueError('missing DUT subcircuit')
    decoded = logical_spice_names(text)
    ports = {p.name for p in net.ports}
    names = spice_names(ports, ('VDD','VMID','VSS','0'))
    connections = []
    for pin in definition['pins']:
        logical = decoded.get(pin, pin)
        if logical.upper() in ('VDD','VMID','VSS'):
            connections.append(logical.upper())
        elif logical in ports:
            connections.append(names[logical])
        else:
            raise ValueError('unexpected physical DUT formal '+pin)
    guesses, mapping = initial_guesses(net, text, initial, vectors[0], lvs_report)
    s = 'TritFlow clocked extracted device + estimated wire C\n' + model_includes(pdk) + '\n'
    options = solver_options or '.options method=gear maxord=2 reltol=1e-5 abstol=1e-13'
    if not options.startswith('.options ') or '\n' in options:
        raise ValueError('solver_options must be one .options line')
    s += simulation_netlist(text) + '\n.temp 27\n' + options + '\n'
    s += 'VP VDD 0 5\nVM VMID 0 0\nVN VSS 0 -5\n'
    s += 'Xdut ' + ' '.join(connections) + ' ' + top_name + '\n'
    edges = [(i+2)*period_s for i in range(len(vectors))]
    clock = [(0,-5)]
    for t in edges:
        clock += [(t-edge_s/2,-5),(t+edge_s/2,5),
                  (t+.5*period_s-edge_s/2,5),(t+.5*period_s+edge_s/2,-5)]
    s += f'VC {names[net.clock]} 0 {pwl(clock)}\n'
    for index, name in enumerate(net.data_inputs):
        points = [(0,5*int(vectors[0][name]))]
        for i,vector in enumerate(vectors[1:],1):
            t = edges[i]-.4*period_s
            points += [(t-edge_s/2,points[-1][1]), (t+edge_s/2,5*int(vector[name]))]
        s += f'VI{index} {names[name]} 0 {pwl(points)}\n'
    for index, port in enumerate(p for p in net.ports if p.dir == 'output'):
        if load:
            s += f'CL{index} {names[port.name]} 0 {load:.12g}\n'
    for node, value in guesses.items():
        s += f'.nodeset v({node})={value:.12g}\n'
    observed = {name:'v(xdut.'+_node(mapping[name])+')' for name in net.state_names}
    observed.update({p.name:f'v({names[p.name]})' for p in net.ports if p.dir == 'output'})
    return s, {'edges':edges, 'samples':[t+.9*period_s for t in edges],
               'stop_s':edges[-1]+.95*period_s, 'observed':observed, 'logic_rows':rows,
               'initial_sample_s':period_s, 'initial':initial, 'period_s':period_s,
               'edge_s':edge_s, 'load_f':load, 'solver_options':options}


def simulate(net, text, vectors, *, initial, period_s=1e-6, edge_s=1e-9,
             step_s=1e-9, load=10e-15, pdk=PDK_ROOT, lvs_report=None,
             workdir=None, timeout=600, solver_options=None):
    """Check every Q before every next edge, plus actual public output functions."""
    net = as_sequential(net)
    if not np.isfinite(step_s) or step_s <= 0:
        raise ValueError('maximum timestep must be positive and finite')
    circuit, plan = build_testbench(net,text,vectors,initial=initial,period_s=period_s,
                                   edge_s=edge_s,load=load,pdk=pdk,lvs_report=lvs_report,solver_options=solver_options)
    started = clock_time.perf_counter()
    result = run_ngspice(circuit, f'tran {step_s:.12g} {plan["stop_s"]:.12g} 0 {step_s:.12g}',
                         list(dict.fromkeys(plan['observed'].values())),
                         workdir=workdir,timeout=timeout)
    data, checks = result['data'], []
    time = data['time']
    if time[-1] < plan['stop_s']*(1-1e-7):
        raise ValueError('incomplete transient')
    def check(cycle, when, expected, phase):
        for name,value in expected.items():
            actual = float(np.interp(when,time,data[plan['observed'][name].lower()]))
            error = actual-5*int(value)
            checks.append({'cycle':cycle,'phase':phase,'register_or_output':name,
                           'sample_s':when,'expected_trit':int(value),'actual_v':actual,
                           'error_v':error,'passed':bool(abs(error)<=.5)})
    check(-1,plan['initial_sample_s'],initial,'initial state guess verified')
    for i,row in enumerate(plan['logic_rows']):
        check(i,plan['samples'][i],row['state'],'before next edge')
        current_inputs = vectors[min(i+1,len(vectors)-1)]
        outputs = net.evaluate(current_inputs,row['state'])
        check(i,plan['samples'][i],outputs,'public output')
    report = {'passed':all(c['passed'] for c in checks),'cycles':len(vectors),
              'runtime_s':clock_time.perf_counter()-started,
              'simulator':simulator_identity(), 'solver_options':plan['solver_options'],
              'netlist_sha256':sha256(net.to_json().encode()).hexdigest(),
              'spice_sha256':sha256(text.encode()).hexdigest(),
              'deck_sha256':sha256(result['deck'].encode()).hexdigest(),
              'period_s':period_s,'frequency_hz':1/period_s,'clock_edge_s':edge_s,
              'max_timestep_s':step_s,'load_f':load,'checks':checks,
              'max_abs_error_v':max(abs(c['error_v']) for c in checks),
              'initialization':'explicit state via verified Newton nodeset guesses; no reset/IC/UIC',
              'scope':'27 C nominal extracted devices + estimated top-net lumped wire C; no signal R or coupling'}
    if workdir:
        Path(workdir,'measurements.json').write_text(json.dumps(report,indent=2)+'\n')
    return {**result, 'measurements':report}


def frequency_sweep(net, text, vectors, *, initial, periods_s, workdir, **kwargs):
    """Maximum observed passing frequency on this sequence, not a PVT fmax claim."""
    periods = list(periods_s)
    if not periods or len(set(periods)) != len(periods):
        raise ValueError('use distinct nonempty test periods')
    trials = []
    for period in sorted(periods,reverse=True):
        result = simulate(net,text,vectors,initial=initial,period_s=period,
                          workdir=Path(workdir)/f'{period*1e9:g}ns',**kwargs)
        trials.append(result['measurements'])
    passing = [r['frequency_hz'] for r in trials if r['passed']]
    report = {'trials':trials,'max_observed_passing_frequency_hz':max(passing,default=None),
              'scope':'maximum among listed tested clocks/sequence/load, nominal only; no CTS/skew/PVT guarantee'}
    Path(workdir,'frequency.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
