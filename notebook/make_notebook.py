"""Build the reading path from EDITOR's prose and the committed paper figures.

The executable stages are independent of editorial Markdown. Static captions
are resolved from a portable, checked measurement snapshot; live results keep
runtime assertions. This script never regenerates the integrator's figures.
"""

import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import subprocess
import textwrap

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from colab_evidence import run_note
from editorial import context, context_identity, render
from markdown_support import colab_markdown, responsive_image
import methods
import stages

ROOT = Path(__file__).resolve().parents[1]


def build(language="en"):
    if language not in ("en", "ja"):
        raise ValueError(f"Unsupported narrative language: {language}")
    narrative = ROOT/("notebook/narrative_ja" if language == "ja" else "notebook/narrative")
    labels = json.loads((narrative/"labels.json").read_text()) if language == "ja" else {}
    def ui(key, fallback):
        return labels["ui"][key] if language == "ja" else fallback
    result_marker = ui("result_marker", "> **What this shows.**")
    sta_heading = ui("sta_heading", "### Predict with static timing, confirm with SPICE")
    shuttle_heading = ui("shuttle_heading", "### From your HDL to a shuttle-ready top")
    # A submission notebook is generated after the implementation commit exists.
    revision = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    setup_source = re.sub(r'(?m)^SOURCE_REF = .*',
        f'SOURCE_REF = os.environ.get("TRITFLOW_REF", "{revision}")', stages.SETUP)
    values = context(ROOT)
    context_sha = context_identity(values)
    cells, code_ids = [], {}
    chapter_title = ui('setup_heading', 'Setup')
    def cell(kind,source,key=None,requires=(),hidden=False,title=None):
        display_chapter = labels.get('code', {}).get(chapter_title, chapter_title)
        if kind == 'code' and language == 'ja':
            from localization import localize_source
            source = localize_source(source, labels.get('code', {}))
        if title and language == 'ja':
            title = labels['titles'][title]
        item = {'cell_type':kind,'id':key or f'tritflow-{len(cells):02d}',
                'metadata':{},'source':textwrap.dedent(source).strip()+'\n'}
        if kind == 'code':
            tracked = key not in ('setup','imports') and not key.startswith('method-')
            if tracked:
                dependency_ids = [code_ids[k] for k in requires]
                item['source'] = ('if "_tf_cells" not in globals():\n'
                    '    raise RuntimeError("Run setup and imports successfully before this chapter; rerun them after any requested runtime restart.")\n'
                    f'with _tf_cells.running({key!r}, {display_chapter!r}, requires={dependency_ids!r}):\n'
                    +textwrap.indent(item['source'],'    '))
                item['metadata']['tritflow'] = {'title':display_chapter,'requires':dependency_ids}
            item.update(execution_count=None,outputs=[])
            if title:
                # Colab shows only the title of a form cell; its code stays one click away.
                item['source'] = f'#@title {title} {{ display-mode: "form" }}\n'+item['source']
                item['metadata']['cellView'] = 'form'
                hidden = True
            if hidden: item['metadata']['jupyter'] = {'source_hidden':True}
            if not key.startswith('method-'):
                code_ids[key] = item['id']
        cells.append(item)
        return item
    def md(source): return cell('markdown',colab_markdown(source))
    def code(key,title,requires=()):
        return cell('code',getattr(stages,key.upper()),key,requires,title=title)
    def method(key):
        # Visible, untracked: the public API calls this chapter teaches.
        return cell('code',getattr(methods,key.upper()),f'method-{key}')
    captions = (narrative/'captions.md').read_text()
    def caption(name):
        return render(captions.split(f'## fig_{name}\n\n',1)[1].split('\n## ',1)[0].strip(),values)
    def image(name,alt,include_caption=True):
        alt = labels.get('alt', {}).get(name, alt)
        if language == 'ja':
            from html import escape
            from localization import localize_svg
            svg = localize_svg((ROOT/f'figures/out/fig_{name}.svg').read_text(), labels['figure'])
            data = base64.b64encode(svg.encode()).decode()
            return (f'<img src="data:image/svg+xml;base64,{data}" alt="{escape(alt, quote=True)}" '
                    'style="display:block;width:100%;max-width:100%;height:auto">'
                    + ('\n\n'+caption(name) if include_caption else ''))
        data = base64.b64encode((ROOT/f'figures/out/fig_{name}.png').read_bytes()).decode()
        width = 520 if name == 'sta' else None   # single-column figure
        return responsive_image(data,alt,width)+('\n\n'+caption(name) if include_caption else '')
    def verilog(*names):
        # Show the exact HDL files the method cells load, as highlighted definitions.
        return '\n\n'.join(f"`examples/{n}`\n\n```verilog\n{(ROOT/'examples'/n).read_text().strip()}\n```" for n in names)
    def prose(name):
        text = (narrative/name).read_text()
        # Images are inserted once at the editorial anchors below.
        text = re.sub(r'!\[[^\]]*\]\([^\n]*\)\n*','',text)
        text = re.sub(r'<!--[^>]*-->\n*','',text)
        text = text.replace('[mapped half adder](../../figures/out/fig_synth.png)',
                            '[mapped half adder](#4.-Describe-signed-arithmetic-in-TritVerilog)')
        if name == '01_gates.md':
            # Two short rows fit Colab's text column after math is typeset.
            text = re.sub(r'\\\[[\s\S]*?\\\]',lambda _:r'''$$
\begin{aligned}
\mathrm{INV}(a)&=-a, & \mathrm{NAND}(a,b)&=-\min(a,b),\\
\mathrm{NOR}(a,b)&=-\max(a,b), & \mathrm{NANY}(a,b)&=-\mathrm{clamp}(a+b,-1,1).
\end{aligned}
$$''',text,count=1)
        return text
    def chapter(filename,hero=None,generated=None):
        """generated=(lead, cells): the hero is drawn by method cells, not embedded."""
        nonlocal chapter_title
        text = prose(filename)
        chapter_title = text.splitlines()[0].removeprefix('## ')
        # Keep the prediction before the measured hero and its success box.
        if hero:
            before,after = text.split(result_marker,1)
            if filename.startswith('01_') and language == 'en':
                before += (f"\nAt A=VMID the possible conducting path is VDD → MP → RP → Y → RN → MN → VSS. "
                    f"The nominal dimensions give \\(R_u\\) = {values['divider.upper_kohm']:.4g} kΩ and "
                    f"\\(R_d\\) = {values['divider.lower_kohm']:.4g} kΩ. "
                    f"**Hand estimate, before SPICE:** I = {values['divider.current_ma']:.4g} mA; "
                    f"Y = {values['divider.output_v']:.4g} V; "
                    f"P = {values['divider.power_mw']:.4g} mW.\n\n")
            if generated:
                lead,cells = generated
                md(render(before,values)+'\n\n'+lead); cells()
                md(caption(hero)+'\n\n'+render(result_marker+after,values))
            else:
                md(render(before,values)+'\n\n'+image(hero,chapter_title)+'\n\n'+render(result_marker+after,values))
        else:
            md(render(text,values))

    intro,chapter0 = prose('00_intro.md').split('## 0.',1)
    # The first screen shows the contribution and checked physical output.
    intro = intro.replace('cells, routed GDS, DRC/LVS results and transistor-level waveforms.',
        'cells, DRC-clean and LVS-matched GDS, and transistor-level waveforms.')
    author = (ROOT/'docs/author.md').read_text()
    author_block = author[author.index('- Name:'):].split('\n\n',1)[0]
    attendance = ' '.join(re.search(r'^- Representative: (.*(?:\n  .*)*)',author,re.M)[1].split())
    power = (f"The middle level has a standing cost: {values['scaling.power_per_cell_mw']:.3g} mW "
             f"per mapped cell for this adder mix, reaching {values['scaling.max_power_mw']/1e3:.3g} W "
             f"at {values['scaling.selected_n']} trits. Sizing trades current against voltage accuracy.")
    badge = '[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb)'
    # One generated result sentence replaces the caption/teaser/result repeats.
    headline = (f"**The illustrated {values['paper_adder.width']}-trit adder:** "
                f"{values['paper_adder.hdl_lines']} top-level HDL lines plus shared modules → "
                f"{values['paper_adder.cells']} cells, a {values['paper_adder.die_um']} µm GDS, "
                f"{values['paper_adder.drc_items']} drawing-DRC markers and LVS {values['paper_adder.lvs_status']}.")
    if language == 'ja':
        headline = render(ui('headline', ''), values)
        badge = ui('badge', '')
    md(render(intro,values)+'\n\n'+image('flow','HDL → cells → checked GDS → extracted SPICE, four-trit paper example',False)+
       '\n\n'+headline+'\n\n'+badge+('\n\n'+run_note(language) if run_note(language) else '')+
       '\n\n<details><summary>'+ui('author', 'Author and license')+'</summary>\n\n'+author_block+
       '\n\n'+attendance+'\n\n'+ui('license', 'Apache-2.0, including historical schematic assets released by their author.')+'\n\n</details>')
    cell('code',setup_source,'setup',title='Setup: clone TritFlow at the release tag, install KLayout and ngspice, fetch the pinned TR-1um PDK')
    imports = cell('code',f'NARRATIVE_CONTEXT_SHA256 = {context_sha!r}\nNOTEBOOK_LANGUAGE = {language!r}\n'+stages.IMPORTS,'imports',
                   title='Imports and run bookkeeping')
    chapter_title = 'Chapter 0: From HDL to a checked adder layout'
    md(render('## 0.'+chapter0,values)+'\n\n'+verilog('adder.tv'))
    code('opening_inputs','Chapter 0 inputs: test conditions and an independent integer oracle')
    method('opening')
    code('opening','Chapter 0 checks')
    method('gds')
    # Fig. 2 is regenerated from ten live DC sweeps by the paper's own figure script.
    chapter('01_gates.md','gates',generated=(verilog('gates.tv'),lambda: method('gates')))
    code('gates','Chapter 1 checks and the taped-out INV schematic')
    method('completeness')
    code('completeness','Chapter 1 checks: unary closure and Słupecki criterion')
    chapter('02_sizing.md','sizing')
    if language == 'en': md(power)
    method('sizing')
    code('sizing','Chapter 2 details: resistor-length candidates at the taped-out MOS sizes')
    chapter('03_cells.md','cell'); method('cells')
    code('cells','Chapter 3 checks: template, clamp devices and cell qualification')
    chapter('04_hdl.md','synth'); md(verilog('half_add.tv','full_add.tv')); method('arithmetic')
    code('arithmetic','Chapter 4 checks: cell counts against the taped-out schematics')
    chapter('05_synthesis.md'); method('synthesis')
    code('synthesis','Chapter 5 checks: mapping rules and gate-level TritVerilog')
    method('schematic')
    chapter('06_pnr.md','pnr'); method('pnr')
    code('pnr','Chapter 6 details and an optional floorplan experiment',requires=('opening',))
    # Chapter 7: post-layout comparison, recorded campaigns, then the static-timing prediction.
    text = prose('07_results.md')
    text,sta_text = text.split(sta_heading,1)
    before,after = text.split(result_marker,1)
    chapter_title = 'Chapter 7: Does the layout still work?'
    md(render(before,values)+'\n\n'+image('postlayout','Identical extracted devices without and with wire C; observed load failure'))
    method('pre')
    code('pre','Chapter 7 checks: identical devices with and without wire C',requires=('opening',))
    md(image('scaling','Ripple width, carry/MSB settling, tested-state static power and die area')+
       '\n\n'+render(result_marker+after,values))
    code('published','Chapter 7 recorded width and load campaigns')
    # The live cell below replaces the narrative's illustrative snippet.
    sta_text = re.sub(r'```python[\s\S]*?```\n\n','',sta_text)
    sta_text = re.sub(r'Here `vectors`[^\n]*\n[^\n]*\n\n','',sta_text)
    sta_before,sta_after = sta_text.split(result_marker,1)
    md(render(sta_heading+sta_before,values)+
       '\n\n'+ui('sta_live', 'The cell below runs STA on the live adder with its routed wire capacitances and compares it with the SPICE run above.'))
    method('sta')
    code('sta','Chapter 7 STA comparison table and critical path',requires=('opening',))
    md(image('sta','Ternary static timing versus post-layout SPICE for matched input-transition sets')+
       '\n\n'+render(result_marker+sta_after,values))
    text = prose('08_your_circuit.md').split(result_marker,1)[0]
    chapter_title = 'Chapter 8: Change the circuit and close the loop'
    md(text+('\n\n**Successful first edit:** the visible sorter below implements its minimum as '
       '`~((~a) | (~b))`. Run it to obtain a new mapped schematic and GDS while keeping the independent sorting reference.' if language == 'en' else ''))
    method('edit')
    method('pick')
    method('custom')
    code('custom_check','Chapter 8 check: every input state against the independent arithmetic reference',requires=())
    method('custom_layout')
    code('custom','Chapter 8: extracted SPICE of your layout and its waveform',requires=('custom_check',))
    md(ui('broken', 'A deliberately unsupported expression produces a located, readable error before synthesis:'))
    method('broken')
    # Chapter 9: outlook, then the recorded shuttle-ready top.
    text = prose('09_next.md')
    outlook,shuttle = text.split(shuttle_heading,1)
    chapter_title = text.splitlines()[0].removeprefix('## ')
    md(render(outlook,values))
    shuttle_before,shuttle_after = shuttle.split(result_marker,1)
    md(render(shuttle_heading+shuttle_before,values))
    method('shuttle')
    code('shuttle','Chapter 9 checks: recorded signoff snapshot and pad map')
    md(render(result_marker+shuttle_after,values))
    chapter('A_limits.md')
    chapter_title = 'Appendix B: Verification evidence and how to rerun'
    appendix = prose('B_evidence.md')
    # The detailed generated tables supersede the placeholder summary table.
    appendix = re.sub(r'\| Check \| Result from the selected evidence \|.*?\n\n','',appendix,flags=re.S)
    appendix = appendix.replace('{evidence.session_seconds}', 'printed in the closing cell')
    appendix = appendix.replace('The measured runtime for this session is\nprinted in the closing cell s including setup.',
                                'The closing cell prints the measured runtime for this session, including setup.')
    appendix = appendix.replace(' The clean-Colab result above\nstates whether an installation-inclusive Run all has completed successfully.','')
    if language == 'ja':
        md(render(appendix,values)+'\n\n'+run_note(language))
    else:
        md(render(appendix,values)+('\n\n'+run_note(language) if run_note(language) else '')+'\n\n'+textwrap.dedent('''
        <details><summary>Setup, recovery and source selection</summary>

        Colab clones the source revision named in the setup cell into `/content/tritflow` (`TRITFLOW_REF`
        selects another release). Setup downloads
        checksum-verified KLayout 0.30.6 and Ubuntu ngspice 42+ds-3build1 with exact snapshot dependencies;
        hash-locked Python packages that Colab has not yet imported, and the pinned circuit-label fonts, install
        privately, while Colab's already imported scientific modules are preserved and version-checked. Tested
        minimum and current stacks and a weekly pinned run cover the review period; `notebook/Dockerfile` is a
        digest-pinned independent reproduction route. After a failed chapter, rerun its named prerequisite.
        Missing or changed scientific inputs stop execution; changed illustrations only warn.
        The closing table distinguishes calculations from recorded experiments.

        </details>
        '''))
    code('characterization','Appendix B: cell characterization and fanout evidence')
    code('four','Appendix B: four-design physical and timing campaign')
    code('final','Appendix B: evidence tables, provenance and run time',requires=tuple(code_ids)[2:])
    chapter('C_reuse.md')
    titles = {item['id']:item['metadata'].get('tritflow',{}).get('title',item['id'])
              for item in cells if item['cell_type'] == 'code'}
    imports['source'] += '\n_tf_cells = CellState('+repr(titles)+')\n'
    document = {'nbformat':4,'nbformat_minor':5,'metadata':{
        'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':'3.12'},
        'colab':{'name':('tritflow_tr1um_ja.ipynb' if language == 'ja' else 'tritflow_tr1um.ipynb'),'provenance':[]},
        'tritflow_editorial':{'language':language,'context_sha256':context_sha,'narrative_sha256':{
            str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sorted(narrative.glob('*')) if p.is_file()}}},'cells':cells}
    return document


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=('en', 'ja'), default='en')
    args = parser.parse_args()
    filename = 'tritflow_tr1um_ja.ipynb' if args.language == 'ja' else 'tritflow_tr1um.ipynb'
    Path(__file__).with_name(filename).write_text(json.dumps(build(args.language),indent=1,ensure_ascii=args.language != 'ja')+'\n')
