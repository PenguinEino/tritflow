# Official requirements and submission checklist

Checked **2026-10-18**, official repository revision
`a502a6ba01260d3492df9137dddae0bb5fabeb3c`.
Primary sources: [current root rules](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/a502a6ba01260d3492df9137dddae0bb5fabeb3c/README.md),
[IEEE award page](https://sscs.ieee.org/membership/awards/ieee-sscs-code-a-chip-travel-grant-awards/),
[ISSCC27 folder](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/tree/a502a6ba01260d3492df9137dddae0bb5fabeb3c/ISSCC27).

| Requirement / rule | Evidence or submitter action | State |
|---|---|---|
| Open Jupyter project about circuit design or education | Executed `tritflow_tr1um.ipynb`, chapters 0–9; linked public source | Included |
| Explain ideas, decisions, method, evidence and reproduction | Chapters 0/1, 4–6, 7/8; first setup cell and README | Included |
| Use open tools; open PDK where applicable | Lark/NumPy, KLayout, ngspice, Plotly; OpenSUSI TR-1um; versions in build information | Included |
| Reproducible source release | Current local execution and source hashes in build-info.json; public source and pinned setup | Next real-Colab verification pending |
| Suitable open-source license | Apache-2.0 `LICENSE`, verbatim attribution `NOTICE` and author-authorized derived schematic assets; README license statement | Included |
| One project folder under the current event's submitted notebooks | This directory maps to `ISSCC27/submitted_notebooks/TritFlow/` | Prepared |
| Keep proposed changes within that project folder | Copy only these small payload files; builder/tests remain in TritFlow | Prepared |
| Fork and submit a GitHub PR | Submitter/integrator action; no PR opened here | Pending |
| Deadline: 2026-10-31 at 11:59 AM Pacific | Submitter schedules and files PR before that time | Pending |
| Monitor review questions | Submitter watches the eventual PR | Pending |
| Teams name one award/travel representative | README and top notebook fields use docs/author.md; sole author named representative | Included |
| Attend ISSCC 2027 and present a poster if selected | Author-confirmed in-person attendance/poster commitment from docs/author.md, reproduced in README | Commitment confirmed; selection pending |
| Follow travel policy; keep eligible-expense receipts | Representative's post-award responsibility; reimbursement is after attendance/document review | Pending selection |
| Membership is encouraged, not an eligibility restriction | No membership assertion or invented applicant category | Informational |
| Final layout is encouraged, optional | Saved real GDS raster, generated DRC/LVS evidence, chapters 0/3/6/7 | Included (optional) |
| Technical jury decides awards | No claim of acceptance or award; applicant category/amount not assumed | Informational |

Conservative presentation guidance retained from the older application guide:

| Guidance | Location | State |
|---|---|---|
| Identify team members at notebook top | Title-cell Author block + README use docs/author.md exactly | Included |
| Cite reused work/notebooks | Notebook references + README provenance; no prior submission cells reused | Included |
| State recommended/used tool versions | Bootstrap pins and generated notebook/build information | Included |

`howtoapply.md` at the checked revision still specifies **ISSCC26** and
**November 27, 2025**. Those event/deadline instructions are superseded here by
the current root README and IEEE page. ISSCC27's directory README delegates to
the root and the submitted-notebooks README requests a separate project folder.
The FAQ's Python-3.7 installation recipe is an example, not a current tool mandate.
Neither current source states a numerical file/size limit, mandates an abstract
or pitch, requires final GDS, or imposes our local ten-minute runtime target.
Saved static outputs and a small payload are additional reviewer conveniences.

Accepted structure examples inspected (not templates copied):

- [ISSCC26 current-mode logic](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/tree/a502a6ba01260d3492df9137dddae0bb5fabeb3c/ISSCC26/submitted_notebooks/current_mode_logic_optimization): notebook, README, license and a few images; listed in ISSCC26's accepted table.
- [ISSCC26 CircuitsDNA](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/tree/a502a6ba01260d3492df9137dddae0bb5fabeb3c/ISSCC26/submitted_notebooks/CircuitsDNA): notebook with supporting code; listed in the accepted table.
- [VLSI26 IMC side-channel](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/tree/a502a6ba01260d3492df9137dddae0bb5fabeb3c/VLSI26/accepted_notebooks/IMC_Side_Channel_Analysis): compact notebook/README folder; listed among VLSI26 winners.

Before filing: check travel/poster logistics, the release
tag and external links, inspect saved outputs, and re-check live official rules.
The current saved outputs have local execution evidence. A new successful
real-Colab pass is required before publishing an installation-inclusive runtime.
