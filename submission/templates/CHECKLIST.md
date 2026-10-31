# Official requirements and submission checklist

Rechecked **{{RULES_DATE}}**, official default-branch head
`{{RULES_COMMIT}}`. Sources: [root README](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/{{RULES_COMMIT}}/README.md),
[FAQ](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/{{RULES_COMMIT}}/FAQ.md),
[How to Apply](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/{{RULES_COMMIT}}/howtoapply.md),
[ISSCC27 instructions](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/{{RULES_COMMIT}}/ISSCC27/README.md),
[submission-folder instructions](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/{{RULES_COMMIT}}/ISSCC27/submitted_notebooks/README.md),
and the independently checked [IEEE award page](https://sscs.ieee.org/membership/awards/ieee-sscs-code-a-chip-travel-grant-awards/).
The builder repository retains the fetched Markdown and content hashes in
`submission/official_snapshot.json` and `submission/official_sources.json`.

{{PACKAGE_STATUS}}

| Requirement or guidance | Evidence / remaining submitter action |
|---|---|
| Openly licensed circuit-design or educational Jupyter project | Executed v3 notebooks, public source, Apache-2.0 LICENSE and verbatim NOTICE |
| Explain concept, decisions, method, results and reproducibility | Notebook chapters, executed outputs and README |
| Open tools and, where applicable, an open PDK | KLayout, ngspice, Python libraries and OpenSUSI TR-1um |
| Spell out all team members at notebook top | First cell of every packaged notebook and README use docs/author.md |
| Add references, including reused notebooks | Notebook bibliography and submission references; README provenance; no previous submission code/cells reused |
| Add recommended tool versions | Generated notebook front matter, bootstrap pins and build-info.json; observed execution/export versions are separate |
| Designate one attending representative | Confirmed representative named in README and each notebook |
| Attend ISSCC 2027 and present a poster if selected | Author-confirmed commitment reproduced in README; selection pending |
| Project folder: ISSCC27/submitted_notebooks/TritFlow/ | Copy only this payload folder into the official fork |
| Keep official-repository changes inside the project folder | Exclude TritFlow builder, tests, source checkout and raw captures |
| Submit through a GitHub pull request | Submitter/integrator action; no PR opened by this task |
| Deadline: 2026-10-31 at 11:59 AM Pacific | File the final PR before the current root-README deadline |
| Monitor organizer questions and revisions | Submitter follows the eventual PR |
| Follow IEEE travel policy and retain receipts | Representative's responsibility if selected; reimbursement follows attendance and document approval |
| Final circuit layout is encouraged, not required | Saved real routed-core GDS views and PDK drawing-DRC/LVS evidence are included |
| Membership is encouraged, not required | No membership or applicant grant-category assumption |

The checked `howtoapply.md` states no deadline and still names the **ISSCC26**
folder. That folder instruction is superseded by the current root README and
IEEE page. Its author, reference and tool-version guidance remains
applicable. The FAQ's Python-3.7 installation example is historical, not a tool
version mandate. The rules do not impose a numerical payload-size limit,
require an abstract or pitch, require final GDS, or set a ten-minute runtime
limit; our static outputs and 16 MiB budget are reviewer conveniences.

Before filing, rebuild the completed English primary and Japanese companion,
inspect their saved figures, run the builder's `--check --require-final`, and
re-check the live rules. Build-info.json distinguishes a development preview
from a final package and records the exact source pins. Historical v1 Colab
runs do not verify v3, and local saved execution is labelled accordingly.
