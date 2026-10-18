"""Build the reading path from EDITOR's prose and the committed paper figures.

The executable stages are independent of editorial Markdown. Static captions
are resolved from a portable, checked measurement snapshot; live results keep
runtime assertions. This script never regenerates the integrator's figures.
"""

import base64
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import textwrap

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from colab_evidence import run_note
from editorial import context, context_identity, render
from markdown_support import colab_markdown, responsive_image
import stages

ROOT = Path(__file__).resolve().parents[1]
NARRATIVE = ROOT/'notebook/narrative'


def build():
    values = context(ROOT)
    context_sha = context_identity(values)
    cells, code_ids = [], {}
    chapter_title = 'Setup'
    def cell(kind,source,key=None,requires=(),hidden=False):
        item = {'cell_type':kind,'id':key or f'tritflow-{len(cells):02d}',
                'metadata':{},'source':textwrap.dedent(source).strip()+'\n'}
        if kind == 'code':
            if key not in ('setup','imports'):
                dependency_ids = [code_ids[k] for k in requires]
                item['source'] = ('if "_tf_cells" not in globals():\n'
                    '    raise RuntimeError("Run setup and imports successfully before this chapter; rerun them after any requested runtime restart.")\n'
                    f'with _tf_cells.running({key!r}, {chapter_title!r}, requires={dependency_ids!r}):\n'
                    +textwrap.indent(item['source'],'    '))
                item['metadata']['tritflow'] = {'title':chapter_title,'requires':dependency_ids}
            item.update(execution_count=None,outputs=[])
            if hidden: item['metadata']['jupyter'] = {'source_hidden':True}
            code_ids[key] = item['id']
        cells.append(item)
        return item
    def md(source): return cell('markdown',colab_markdown(source))
    def code(key,requires=(),hidden=True):
        return cell('code',getattr(stages,key.upper()),key,requires,hidden)
    captions = (NARRATIVE/'captions.md').read_text()
    def caption(name):
        return render(captions.split(f'## fig_{name}\n\n',1)[1].split('\n## ',1)[0].strip(),values)
    def image(name,alt,include_caption=True):
        data = base64.b64encode((ROOT/f'figures/out/fig_{name}.png').read_bytes()).decode()
        return responsive_image(data,alt)+('\n\n'+caption(name) if include_caption else '')
    def prose(name):
        text = (NARRATIVE/name).read_text()
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
    def chapter(filename,hero=None):
        nonlocal chapter_title
        text = prose(filename)
        chapter_title = text.splitlines()[0].removeprefix('## ')
        # Keep the prediction before the measured hero and its success box.
        if hero:
            before,after = text.split('> **What this shows.**',1)
            if filename.startswith('01_'):
                before += (f"\nAt A=VMID the possible conducting path is VDD → MP → RP → Y → RN → MN → VSS. "
                    f"The nominal dimensions give \\(R_u\\) = {values['divider.upper_kohm']:.4g} kΩ and "
                    f"\\(R_d\\) = {values['divider.lower_kohm']:.4g} kΩ. "
                    f"**Hand estimate, before SPICE:** I = {values['divider.current_ma']:.4g} mA; "
                    f"Y = {values['divider.output_v']:.4g} V; "
                    f"P = {values['divider.power_mw']:.4g} mW.\n\n")
            md(render(before,values)+'\n\n'+image(hero,chapter_title)+'\n\n'+render('> **What this shows.**'+after,values))
        else:
            md(render(text,values))

    intro,chapter0 = prose('00_intro.md').split('## 0.',1)
    # REVIEW 1: contribution and its electrical cost precede setup and identity.
    intro = intro.replace('cells, routed GDS, DRC/LVS results and transistor-level waveforms.',
        'cells, DRC-clean and LVS-matched GDS, and transistor-level waveforms.')
    author = (ROOT/'docs/author.md').read_text()
    author_block = author[author.index('- Name:'):].split('\n\n',1)[0]
    power = (f"The middle level has a standing cost: {values['scaling.power_per_cell_mw']:.3g} mW "
             f"per mapped cell for this adder mix, reaching {values['scaling.max_power_mw']/1e3:.3g} W "
             f"at {values['scaling.selected_n']} trits. Sizing trades current against voltage accuracy.")
    badge = '[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb)'
    # One generated result sentence replaces the caption/teaser/result repeats.
    headline = (f"**The illustrated {values['paper_adder.width']}-trit adder:** "
                f"{values['paper_adder.hdl_lines']} top-level HDL lines plus shared modules → "
                f"{values['paper_adder.cells']} cells, a {values['paper_adder.die_um']} µm GDS, "
                f"{values['paper_adder.drc_items']} drawing-DRC markers and LVS {values['paper_adder.lvs_status']}.")
    md(render(intro,values)+'\n\n'+image('flow','HDL → cells → checked GDS → extracted SPICE, four-trit paper example',False)+
       '\n\n'+headline+'\n\n'+power+'\n\n'+badge+('\n\n'+run_note() if run_note() else '')+
       '\n\n<details><summary>Author and license</summary>\n\n'+author_block+
       '\n\nApache-2.0, including historical schematic assets released by their author.\n\n</details>')
    cell('code',stages.SETUP,'setup')
    imports = cell('code',f'NARRATIVE_CONTEXT_SHA256 = {context_sha!r}\n'+stages.IMPORTS,'imports')
    chapter_title = 'Chapter 0: From HDL to a checked adder layout'
    md(render('## 0.'+chapter0,values)+'\n\n'+'''```python
    d = flow.load("examples/adder.tv", "adder", {"N": 2})
    net = d.synthesize()
    lay = net.place_and_route()
    assert lay.drc()["clean"] and lay.lvs()["matched"]
    post = lay.extract().simulate(vectors, load=LOAD_F)
    ```'''.replace('    ',''))
    code('opening',hidden=False)
    chapter('01_gates.md','gates'); code('gates')
    chapter('02_sizing.md','sizing'); code('sizing')
    chapter('03_cells.md','cell'); code('cells')
    chapter('04_hdl.md','synth'); code('arithmetic')
    chapter('05_synthesis.md'); code('synthesis'); code('schematic')
    chapter('06_pnr.md','pnr'); code('pnr',requires=('opening',))
    # The two result panels are distinct questions, not duplicate schematics.
    text = prose('07_results.md')
    before,after = text.split('> **What this shows.**',1)
    chapter_title = 'Chapter 7: Does the layout still work?'
    md(render(before,values)+'\n\n'+image('postlayout','Identical extracted devices without and with wire C; observed load failure'))
    code('pre',requires=('opening','schematic'))
    md(power+'\n\n'+image('scaling','Ripple width, carry/MSB settling, tested-state static power and die area')+
       '\n\n'+render('> **What this shows.**'+after,values))
    code('published')
    text = prose('08_your_circuit.md').split('> **What this shows.**',1)[0]
    chapter_title = 'Chapter 8: Change the circuit and close the loop'
    md(text+'\n\n**Successful first edit:** the visible sorter below implements its minimum as '
       '`~((~a) | (~b))`. Run it to obtain a new mapped schematic and GDS while keeping the independent sorting reference.')
    code('edit',hidden=False)
    code('custom',requires=('edit',),hidden=False)
    md('A deliberately unsupported expression produces a located, readable error before synthesis:')
    code('broken')
    chapter('09_next.md')
    chapter('A_limits.md')
    chapter_title = 'Appendix B: Verification evidence and how to rerun'
    appendix = prose('B_evidence.md')
    # The detailed generated tables supersede the placeholder summary table.
    appendix = re.sub(r'\| Check \| Result from the selected evidence \|.*?\n\n','',appendix,flags=re.S)
    appendix = appendix.replace('{evidence.session_seconds}', 'printed in the closing cell')
    appendix = appendix.replace('The measured runtime for this session is\nprinted in the closing cell s including setup.',
                                'The closing cell prints the measured runtime for this session, including setup.')
    appendix = appendix.replace(' The clean-Colab result above\nstates whether an installation-inclusive Run all has completed successfully.','')
    md(appendix+('\n\n'+run_note() if run_note() else '')+'\n\n'+textwrap.dedent('''
    <details><summary>Setup, recovery and source selection</summary>

    Colab shallow-clones `colab-v0` into `/content/tritflow`; `TRITFLOW_REF` selects another release.
    Use the source revision matching this notebook. Setup preserves Colab's NumPy/SciPy/Matplotlib/Plotly,
    checks minimum versions, and prints KLayout/ngspice versions. If mixed versions are detected,
    restart once and rerun setup/imports. After a failed chapter, rerun its named prerequisite.
    Missing or changed scientific inputs stop execution; changed illustrations only warn.
    The closing table distinguishes calculations from recorded experiments.

    </details>
    '''))
    code('characterization')
    code('four')
    code('final',requires=tuple(code_ids)[2:])
    titles = {item['id']:item['metadata'].get('tritflow',{}).get('title',item['id'])
              for item in cells if item['cell_type'] == 'code'}
    imports['source'] += '\n_tf_cells = CellState('+repr(titles)+')\n'
    document = {'nbformat':4,'nbformat_minor':5,'metadata':{
        'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':'3.12'},
        'colab':{'name':'tritflow_tr1um.ipynb','provenance':[]},
        'tritflow_editorial':{'context_sha256':context_sha,'narrative_sha256':{
            str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sorted(NARRATIVE.glob('*.md'))}}},'cells':cells}
    return document


if __name__ == '__main__':
    Path(__file__).with_name('tritflow_tr1um.ipynb').write_text(json.dumps(build(),indent=1)+'\n')
