"""Resolve EDITOR's exact tokens against checked, portable measurements.

LaTeX braces are left untouched. Experimental values never come from prose
status files; only historical context is parsed from the binding editorial plan.
"""

import json
from hashlib import sha256
from pathlib import Path
import re

from tritflow import flow, PDK_ROOT, TRIT_VOLTS, PASS_BAND
from tritflow.sim.scaling import load_scaling, fit_scaling
from tritflow.sim.sizing import load_grid
from tritflow.synth import evaluate_netlist
from predictions import divider, zero_dc, rail_power
from paper_evidence import load_paper
from routing_identity import archive_routing, routing_label

TOKEN = re.compile(r'\{([a-z][a-z_]*\.[a-z][a-z_0-9]*)\}')


def fmt(value):
    return f'{value:.4g}' if isinstance(value,float) else str(value)


def dimensions(values):
    return ' × '.join(map(fmt,values))


def context_identity(values):
    """Identify displayed quantities without requiring platform-identical BLAS.

    Input files retain exact SHA-256 checks. Derived floats are compared at
    the four significant digits actually printed in the narrative; a last-bit
    OLS or physical-constant difference is not a changed experimental claim.
    """
    displayed = {name:fmt(value) for name,value in values.items()}
    return sha256(json.dumps(displayed,sort_keys=True).encode()).hexdigest()


def render(text, values):
    """Substitute registered namespace.field tokens only; missing data rejects."""
    def replace(match):
        if match[1] not in values:
            raise ValueError(f'Unresolved narrative value: {match[0]}')
        return fmt(values[match[1]])
    return TOKEN.sub(replace,text)


def context(root):
    """The static reading context, coupled to the committed paper illustrations."""
    root = Path(root)
    paper = load_paper(root)
    values = {}
    def put(namespace, **fields):
        values.update({f'{namespace}.{k}':v for k,v in fields.items()})
    history = (root/'docs/editorial.md').read_text().split('## Context that belongs in the intro')[1].split('## Limits')[0]
    put('history',node_um=re.search(r'NDA-free (\d+) µm',history)[1],
        pdk_opened_year=re.search(r'opened (\d+)',history)[1],
        tapeout_year=re.search(r'shuttle in\s+(\d+)',history)[1],
        delivery_month=re.search(r'expected in ([A-Z][a-z]+ \d+)',history)[1])
    put('levels',negative_v=TRIT_VOLTS[-1],zero_v=TRIT_VOLTS[0],
        positive_v=f'{TRIT_VOLTS[1]:+g}',band_v=PASS_BAND)
    report,physical = paper['paper_report'],paper['paper_pnr']
    put('paper_adder',width=sum(p['name'].startswith('a[') for p in paper['paper_net']['ports']),
        hdl_lines=len((root/'examples/adder.tv').read_text().splitlines()),
        cells=report['total_cells'],nany=report['cells']['NANY'],inv=report['cells']['INV'],
        equivalence_mode=report['equivalence']['mode'],die_um=dimensions(physical['die']),
        drc_items=physical['checks']['pdk_drc']['violations'],lvs_status='Match',
        run_id=routing_label(physical['routing']))
    for name,route in archive_routing(root/'notebook/assets/four_designs.zip').items():
        put('archive',**{('adder' if name == 'adder4' else name)+'_run_id':routing_label(route)})
    put('adder',width=2)
    initial,final = [physical['history'][i]['hpwl'] for i in (0,-1)]
    put('paper_pnr',initial_hpwl_mm=initial/1e3,final_hpwl_mm=final/1e3,
        hpwl_reduction_pct=100*(1-final/initial))
    gi,gn = load_grid('INV'),load_grid('NANY')
    a = gi['rows'][gi['adopted_index']]
    variants = [r for r in gi['rows'] if all(r['dimensions'][k] == a['dimensions'][k] for k in ('MP','MN'))
                and r['transfer'] and r['dc']]
    selected = max(variants,key=lambda r:r['dimensions']['RP']['l_um'])
    hand,changed = [divider(r['dimensions'],PDK_ROOT) for r in (a,selected)]
    put('divider',output_v=hand['output_v'],power_mw=hand['power_w']*1e3,
        upper_kohm=hand['upper']['total_ohm']/1e3,lower_kohm=hand['lower']['total_ohm']/1e3,
        current_ma=hand['current_a']*1e3,
        spice_output_v=zero_dc(a)['output_v']['Y'],
        spice_power_mw=rail_power(zero_dc(a),gi['conditions']['supplies_v'])*1e3)
    put('sizing',adopted_error_mv=a['max_error_v']*1e3,adopted_current_ua=a['max_static_current_a']*1e6,
        adopted_rr_um=a['dimensions']['RP']['l_um'],selected_rr_um=selected['dimensions']['RP']['l_um'],
        selected_current_ua=selected['max_static_current_a']*1e6,selected_error_mv=selected['max_error_v']*1e3,
        predicted_shift_mv=(changed['output_v']-hand['output_v'])*1e3,
        spice_shift_mv=(zero_dc(selected)['output_v']['Y']-zero_dc(a)['output_v']['Y'])*1e3)
    def finite_count(g):
        return sum(r['max_error_v'] is not None and r['max_static_current_a'] is not None for r in g['rows'])
    nany = gn['rows'][gn['adopted_index']]
    put('paper_sizing',resistor_lengths_um=', '.join(fmt(v) for v in sorted({r['dimensions']['RP']['l_um'] for r in variants})),
        inv_count=finite_count(gi),nany_count=finite_count(gn),nany_error_mv=nany['max_error_v']*1e3,
        nany_current_ua=nany['max_static_current_a']*1e6,error_floor_mv=paper['display_settings']['sizing_floor_mv'])
    char = json.loads((root/'cells/out/INV/INV.char.json').read_text())
    point = paper['inv_dc']
    put('paper_gates',temperature_c=char['conditions']['temperature_c'],inv_zero_v=point['output_v'],
        inv_current_ma=point['current_a']*1e3,inv_power_mw=point['power_w']*1e3)
    ref = json.loads((root/'notebook/narrative/reference_geometry.json').read_text())['cells']['NANY']
    eq = json.loads((root/'cells/out/equivalence_report.json').read_text())
    assert ref['source_sha256'] == eq['schematic_equivalence']['NANY']['original_gds_sha256']
    assert eq['parasitic_aware']['passed']
    abstract = json.loads((root/'cells/out/NANY/NANY.abstract.json').read_text())
    box = ref['bbox_um']
    put('paper_cell',original_die_um=dimensions([box[2]-box[0],box[3]-box[1]]),
        row_count=len(paper['display_settings']['row_cells']))
    put('cell',width_um=abstract['width'],height_um=abstract['height'],
        area_ratio=abstract['width']*abstract['height']/ref['area_um2'])
    arithmetic = {}
    for name,key in [('half_add','ha'),('full_add','fa')]:
        design = flow.load(root/f'examples/{name}.tv',name)
        table = design.truth_table(); mapped = design.synthesize()
        expected = table['a']+table['b']+(table['cin'] if key == 'fa' else 0)
        output = 'cout' if key == 'fa' else 'carry'
        assert (expected == table['sum']+3*table[output]).all()
        final = evaluate_netlist(mapped,{p.name:table[p.name] for p in mapped.ports if p.dir == 'input'})
        assert all((table[p] == final[p]).all() for p in ('sum',output))
        arithmetic.update({f'{key}_{cell.lower()}':count for cell,count in mapped.report()['cells'].items()})
        if key == 'ha': put('paper_synth',ha_cells=mapped.report()['total_cells'])
    put('arithmetic',**arithmetic)
    scale = load_scaling(root/'results/adder_scaling.json'); fits = fit_scaling(scale)
    assert all(r['state'] == 'complete' and r['passed'] for r in scale['rows'])
    widest = max(scale['rows'],key=lambda r:r['n']); one = next(r for r in scale['rows'] if r['n'] == 1)
    put('paper_scaling',width_min=min(r['n'] for r in scale['rows']),width_max=widest['n'],
        load_ff=widest['conditions']['load_f']*1e15,
        run_id=('width-sweep · seed '+str(scale['rows'][0]['seed'])
                if len({r['seed'] for r in scale['rows']}) == 1 else
                'width-sweep · '+', '.join(f"N={r['n']} seed {r['seed']}" for r in scale['rows'])))
    mapped = flow.load(root/'examples/adder.tv','adder',{'N':widest['n']}).synthesize()
    zeros = {p.name:0 for p in mapped.ports if p.dir == 'input'}
    assert all(int(v) == 0 for v in evaluate_netlist(mapped,zeros,return_all=True).values())
    predicted_power = 0
    for name,count in mapped.report()['cells'].items():
        char = json.loads((root/f'cells/out/{name}/{name}.char.json').read_text())
        dc = next(r for r in char['dc'] if not any(r['input_trits']))
        predicted_power += count*rail_power(dc,char['conditions']['supplies_v'])
    put('scaling',selected_n=widest['n'],device_slope_ns=fits['carry']['pre']['slope']*1e9,
        wired_slope_ns=fits['carry']['post']['slope']*1e9,power_per_cell_mw=fits['static_power']['slope']*1e3,
        max_power_mw=widest['static_power_worst_w']*1e3,
        predicted_ns=(one['carry']['pre']['max_settling_s']+(widest['n']-1)*one['carry']['pre']['endpoint_max_settling_s']['cout'])*1e9,
        device_ns=widest['carry']['pre']['max_settling_s']*1e9,
        predicted_power_mw=predicted_power*1e3,
        zero_power_mw=paper['zero_dc'][str(widest['n'])]['dc']['static_power_w']*1e3,
        current_utilization_pct=widest['em_check']['max_utilization']*100)
    sweep = json.loads((root/'results/full_add_load_sweep.json').read_text())
    assert sweep['boundary_found']
    put('load',hold_ns=sweep['conditions']['hold_s']*1e9,
        last_pass_pf=sweep['boundary']['last_pass_f']*1e12,first_fail_pf=sweep['boundary']['first_fail_f']*1e12)
    p = paper['paper_post']
    put('paper_post',states=p['states'],hold_ns=p['hold_s']*1e9,load_ff=p['load_f']*1e15,
        pre_sum_ns=p['pre_sum_s']*1e9,post_sum_ns=p['post_sum_s']*1e9,
        run_id=routing_label(p['routing']))
    # Static timing: recorded validation against post-layout SPICE (matched transitions).
    sta = json.loads((root/'results/sta/validation.json').read_text())
    matched = sta['statistics']['sim_endpoint_pairs']
    outliers = sta['outside_accuracy_target']
    assert len(outliers) == 1, 'the narrative names a single STA exception'
    groups = {}
    for design in sta['designs']:
        groups.setdefault(design['group'],[]).append(design['design'])
    put('sta',within_target=sta['outputs_within_target'],output_count=matched['count'],
        target_pct=sta['accuracy_target_percent'],mape_pct=matched['mean_absolute_percent_error'],
        outlier_endpoint=f"{outliers[0]['design']}/{outliers[0]['output']}",
        outlier_error_pct=outliers[0]['error_percent'],
        bound_mean_factor=sta['worst_case_validation']['pessimism_vs_output_maxima']['mean_factor'],
        run_ids='; '.join(f"STA {group}: {', '.join(names)}" for group,names in groups.items()))
    # Shuttle-ready top: committed snapshot of the recorded to_chip()/signoff() run.
    chip = json.loads((root/'notebook/assets/chip/adder4/signoff.json').read_text())
    assert chip['drawing_drc']['clean'] and chip['mask_drc']['clean']
    assert chip['drawing_lvs']['matched'] and chip['drawing_lvs']['strict_ports']
    put('chip',die_um=dimensions(chip['die_um']),pad_count=chip['pad_count'],
        drawing_drc_items=chip['drawing_drc']['violations'],lvs_status='Match',
        mask_drc_items=chip['mask_drc']['violations'],
        precheck_status='Pass' if chip['mpw_precheck']['clean'] and chip['mpw_precheck']['exit_code'] == 0 else 'Fail',
        submission_ready=str(chip['submission_ready']).lower())
    # The public release tag serves both the Colab launch and pip installs.
    put('reuse',source_ref='colab-v0')
    put('release',colab_url='https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb')
    return values
