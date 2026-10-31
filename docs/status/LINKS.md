# LINKS — URL and citation audit

Completed 2026-10-24 JST (network checks on 2026-10-23 UTC). Report only;
the only file written by LINKS is this file. No commit, push, package installation,
notebook execution, or Colab VM was used.

## Scope and result

Read `AGENTS.md`, `docs/concept.md`, `docs/interfaces.md`, and `briefs/LINKS.md`.
Audited all 23 requested files: both sets of seven narrative Markdown files,
`notebook/v3/make_notebook.py`, `README.md`, `docs/references.md`, the four
submission templates, and both built v3 notebooks.

- Collected **245 URL occurrences, 102 distinct literal URL strings, and 15 distinct DOIs**.
- The literal strings include two URL construction prefixes and five rules-template
  strings. After expanding the latter and the primary `COLAB_URL` placeholder,
  there are **101 actual link destinations**: 95 literal destinations, five rules
  destinations, and one submission Colab destination.
- **Working targets: 80.** This includes **12/12 pinned notebook image/table URLs**
  and **3/3 Colab entry targets**. Successful links are not inventoried below.
- **Bot-gated targets: 20**, described under access limits; **unavailable target: 1**
  (L1). A challenge or empty HTTP 202 response was not counted as a successful
  content fetch.
- **Confirmed dead HTTP 404 destinations: 0; wrong-target redirects: 0;
  wrong-paper DOIs: 0; pinned raw-asset 404s: 0; Colab backing-notebook 404s: 0.**
- Three findings require an editorial decision or correction: one availability
  issue, one minor author-spelling mismatch, and one source/claim disagreement.
  No additional title, venue, year, or pagination mismatch was established.

The built notebooks use asset/bootstrap commit
`cc9a49e97e1ad098743494db7d82adb34a379bbe`. The rules templates expand with
`a502a6ba01260d3492df9137dddae0bb5fabeb3c`. The existing submission build record
expands its primary Colab badge with `d14970667c65c279d8f47efeb391e89507c6939b`.
These are separate pins, not assumed interchangeable. The two literal badges use
the `notebook-v3` branch. Their backing files, and both notebook files at each
of the two immutable TritFlow pins above, were fetched independently of Colab's
HTTP 200 shell. Immutable backing files parse as nbformat 4 with 64 cells.
This establishes link availability, not runtime compatibility or Run-all success.

## Findings and exact fixes

### L1 — Knuth edition-listing endpoint unavailable during the audit

**Location:** `docs/references.md:400`.

`https://cs.stanford.edu/~knuth/taocp.html` repeatedly refused the direct HTTPS
connection; the independent web fetch also timed out. The faculty-host alias
also refused connections. A recent indexed copy still exists, so this is an
observed availability failure, not evidence that the page has permanently moved.

**Exact fix:** replace the complete Markdown link on line 400 with:

```markdown
[Publisher's edition listing](https://www.informit.com/store/art-of-computer-programming-volume-2-seminumerical-9780201896848);
```

The [publisher replacement](https://www.informit.com/store/art-of-computer-programming-volume-2-seminumerical-9780201896848)
returned HTTP 200 and identifies Donald E. Knuth, volume 2, third edition, the
matching ISBN, and publication on 4 November 1997. Keep the citation year 1997
and the separate section-excerpt link on line 401.

### L2 — WANG2021 uses manuscript spellings in a journal-version citation

**Locations:** `docs/references.md:81`,
`notebook/v3/narrative/06_results.md:62`,
`notebook/v3/narrative_en/06_results.md:62`,
`notebook/v3/tritflow_ja.ipynb:462`, and
`notebook/v3/tritflow_en.ipynb:462` (reference 4 in each built notebook).

The journal citation uses `Xiaoyuan Wang` and, in the full author list,
`Pengfei Zhou`. [IEEE-deposited Crossref metadata](https://api.crossref.org/works/10.1109%2FTCSI.2020.3027693)
uses **Xiao-Yuan Wang** and **Peng-Fei Zhou**. Title, DOI, journal, 68(1),
264–274, and January 2021 all agree. This is a minor spelling/version mismatch,
not a different author or paper: the linked author manuscript actually uses
the unhyphenated spellings.

**Exact fix:** in `docs/references.md:81`, replace
`Xiaoyuan Wang, Pengfei Zhou,` with `Xiao-Yuan Wang, Peng-Fei Zhou,`.
In both narrative references, replace `Xiaoyuan Wang et al.,` with
`Xiao-Yuan Wang et al.,`. Regenerate both notebooks so their reference 4 uses
the same journal spelling. Retain the DOI and all other citation fields.

### L3 — January arrival and assured ISSCC measurements disagree with the cited announcement

**Locations:** `notebook/v3/narrative/00_opening.md:10`,
`notebook/v3/narrative_en/00_opening.md:14`,
`notebook/v3/tritflow_ja.ipynb:22`, and
`notebook/v3/tritflow_en.ipynb:22` (opening cell in each built notebook).

The opening promises January 2027 delivery and measurements at ISSCC. The
[OpenSUSI announcement dated 16 October 2026](https://prtimes.jp/main/html/rd/p/000000014.000182004.html),
already cited as bibliography item 16, estimates delivery **around February 2027**.
It does not establish that measurements will be ready before the conference.
The announcement's own citation details are correct. No newer project-specific
delivery confirmation was found in the read project records.

**Exact Japanese fix:** replace the two sentences beginning
`チップは2027年1月に届く。採択されれば、` with:

```markdown
OpenSUSIの2026年10月16日の[発表](https://prtimes.jp/main/html/rd/p/000000014.000182004.html)では、チップの到着は2027年2月頃の予定とされている。採択された場合は2月のISSCCでTritFlowを発表し、チップの到着と測定が間に合えば、元になったセルの最初の実測結果も報告する。
```

**Exact English fix:** replace the two sentences beginning
`The chips will arrive in January 2027. If selected,` with:

```markdown
OpenSUSI's [16 October 2026 announcement](https://prtimes.jp/main/html/rd/p/000000014.000182004.html) estimates delivery around February 2027. If selected, the author will present TritFlow at ISSCC in February and include the first measurements of its underlying cells if delivery and testing are completed in time, then fabricate a circuit designed with TritFlow on the next OpenSUSI shuttle.
```

Regenerate both built notebooks after the narrative changes. The decision for
this audit is to use the dated public estimate and make measurement availability
conditional; no unsupported replacement delivery date is proposed.

## Access limits and false-positive handling

The following are access restrictions, not established broken links. Retain the
references; no DOI replacement is warranted. Locations below identify the
canonical entries in `docs/references.md`; duplicated notebook citations inherit
the same endpoint behavior.

| Targets | Canonical locations | Observation and verification limit |
|---|---|---|
| IEEE Xplore: 9 | `docs/references.md:60`, `:61`, `:85`, `:125`, `:139`, `:140`, `:167`, `:441`, `:442` | DOI redirects reach the expected article identifiers, but direct GETs return empty HTTP 202 responses; the web view identifies JavaScript/bot verification. IEEE-deposited Crossref records verify paper identity and bibliography. Direct publisher-page/full-text inspection remains restricted. |
| Springer: 8 | `docs/references.md:72`, `:73`, `:230`, `:231`, `:270`, `:271`, `:414`, `:415` | Direct DOI/article GETs return HTTP 200 `Client Challenge`. Publisher pages were readable through the independent web fetch and agree with the citations. These endpoints remain in the bot-gated count for direct HTTP access. |
| IET: 2 | `docs/references.md:97`, `:98` | HTTP 403 Cloudflare challenge. Publisher-deposited metadata confirms Wu/Prosser, title, journal, 137(1), 1990, and starting page 21. The ending page 27 could not be independently rechecked against the live publisher page in this audit; no contrary pagination was found. |
| CiNii: 1 | `docs/references.md:260` | Empty HTTP 202 / JavaScript verification. The indexed primary library record matches Kleene, title, both publishers, 1952, and Bibliotheca Mathematica volume 1. Direct access remains gated. |

Transient asset/download 403 responses were retried and recovered. The ngspice
download landing page and the actual version-42 PDF were both checked; its title
page confirms the three named authors, version 42, and 27 December 2023.

The bare `RAW` and `CDN` constants at `notebook/v3/make_notebook.py:27` and `:29`
return 404 and 400 when fetched alone. They are construction prefixes, not reader
links; their 12 concrete image/table expansions were checked. Likewise, the five
literal `{{RULES_COMMIT}}` paths in `submission/templates/CHECKLIST.md:4` through
`:8` return 404 before substitution and resolve after the actual rules pin is
inserted. `submission/templates/README.md:62` is intentionally a `COLAB_URL`
placeholder, checked against the existing rendered package value. None of these
template/prefix responses warrants a source edit.

## Method, validation, and handoff

- Used network **GET**, followed redirects, and inspected response types/titles,
  DOI destinations, publisher records, and PDF title pages. HTTP status alone was
  insufficient for Colab, challenge pages, or download landing pages.
- Checked all 15 DOI identities with publisher-deposited Crossref metadata or
  arXiv/DataCite records, with a successful retry after one Crossref rate limit.
  Read accessible publisher/library records and original PDF pages for citations
  without a DOI. Checked software snapshot dates against GitHub commit pages and
  release dates against release pages; merge-commit patch headers were not used
  as the merge date.
- Confirmed the Słupecki fragment opens the intended original article at PDF
  page 110 / printed page 102. The 1972 translation's DOI is kept separate from
  the 1939 original. Issue/proceedings years were distinguished from early access,
  conference dates, and the year embedded in a DOI.
- Notebook file/line references are physical JSON lines. Source edits belong in
  the narratives; the generated notebook lines identify where the fixes appear.
- No applicable `tests/LINKS` suite exists and no executable code was changed.
  Validation consists of the complete URL scan, network/metadata checks above,
  a final source-hash comparison, and `git diff --check -- docs/status/LINKS.md`.
  No files outside this report were written by LINKS.

To repeat an individual HTTP check without creating an artifact:

```sh
curl --location --max-time 30 --user-agent 'Mozilla/5.0 (compatible; TritFlowLinksAudit/1.0)' --dump-header - --output /dev/null 'URL_FROM_SOURCE'
```

Inspect the body/title separately when the result is 200/202 but may be a
challenge, and check Colab's corresponding raw GitHub notebook as well.

**Done:** full requested link/citation audit and exact-fix report.
**In progress:** none.
**Blockers:** none to completing the report; the publisher access limits above
remain explicit limits on direct content verification.
**Interface requests:** none. Narrative owners can apply L2/L3, the reference
document owner can apply L1/L2, and FRONTEND can regenerate the notebooks.
LINKS has not changed their files.
