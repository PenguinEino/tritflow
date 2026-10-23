# LINKS stream brief: every link and citation resolves and says what we claim

Report only: write `docs/status/LINKS.md`. Do not edit any other file. Do not commit.

Collect every URL and DOI in `notebook/v3/narrative/*.md`, `notebook/v3/narrative_en/*.md`,
`notebook/v3/make_notebook.py`, `README.md`, `docs/references.md`, `submission/templates/*.md`,
and the image/asset URLs the built notebooks load (`notebook/v3/tritflow_{ja,en}.ipynb`).
Fetch each one (use the network; follow redirects). Report: dead or redirected-to-wrong links, DOIs
that resolve to a different paper than the citation text, Colab badges and raw.githubusercontent
asset URLs that 404 at the pinned commit, and citation details (authors, title, venue, year, pages)
that disagree with the publisher page. For each problem give file:line and the exact fix.
List working links only as a count.
