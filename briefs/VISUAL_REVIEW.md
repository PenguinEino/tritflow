# Brief: VISUAL_REVIEW — look at every chapter of the v2 notebook and fix what looks wrong

Work in the git worktree `~/code-a-chip-look` (branch `visual-review`). Never touch other worktrees or
`~/balanced-ternary-logic`. No git commit or push: the integrator reviews and commits.

## Context

The v2 Japanese notebook is built by `notebook/v2/make_notebook.py` from `notebook/v2/narrative/*.md` and the
code cells in that file; its views are `notebook/views.py`, `notebook/inverter_views.py`,
`notebook/cell_views.py`, `notebook/style.py`, `notebook/live.py` (progress lines, live P&R picture), the
SVG tables from `notebook/v2/make_tables.py`, and Plotly figures. The author wants a single academic,
paper-like look (see `notebook/style.py` and docs/notebook-v2/STORYBOARD.md "横断する決まり"), and has
repeatedly found layout faults only after opening the notebook in Colab: things too small, cramped or
misaligned, overlapping text, inconsistent styles between figures, legends for things the picture already
shows, broken layout when <details> are opened. Your job is to find and fix these before the author sees them.

## How to look

1. Build and execute: `python3 notebook/v2/make_notebook.py --out build/v2/local.ipynb`, then execute it with
   nbclient (`TR1UM_PDK=~/pdk/TR-1um-pinned TRITFLOW_ROOT=~/code-a-chip-look`, kernel python3, cwd build/v2).
2. Render each chapter as a page close to what Colab shows: Markdown cells via markdown-it (html enabled,
   tables), code cells' source in a grey box, and their outputs (text/html, image/svg+xml, streams, errors) in
   order. Open every <details>. Images referenced by URL (jsDelivr / raw.githubusercontent) must be replaced
   by the local files under `notebook/assets/` or `figures/out/` so the page renders offline.
3. Screenshot with headless Chrome at 1100 px and at 700 px wide (`google-chrome --headless=new --no-sandbox
   --virtual-time-budget=8000 --screenshot=... --window-size=W,H file://...`), split tall pages into pieces,
   and look at every image yourself. Also click-through interactive parts by injecting a small script into
   the page that changes radio buttons / sliders and screenshot again (buttons must change what they claim).
4. Critique like a picky reviewer of a paper figure and fix: sizes and balance, alignment, overlaps, font and
   colour consistency, table style (booktabs), spacing, unreadable labels at 700 px, anything that looks
   app-like rather than paper-like. Re-render and look again after every fix.

Known open issue: cells "3-5" and "3-7" fail to draw their schematic (another stream, SCHEM_ROUTE, fixes the
schematic router in `tritflow/schematic/`); do not edit `tritflow/schematic/`, just note it.

## Rules

- Edit only presentation: `notebook/style.py`, `notebook/views.py`, `notebook/inverter_views.py`,
  `notebook/cell_views.py`, `notebook/live.py` (only its drawing parts), `notebook/v2/make_tables.py` and the
  SVGs it writes, and the code-cell display calls in `notebook/v2/make_notebook.py`. Do not change the
  narrative text (report wording problems instead), computed numbers, `tritflow/` (except none), or recorded
  results.
- TR1UM_PDK=~/pdk/TR-1um-pinned. No new dependencies, no network services, no publishing, no sign-in.
- Keep `python3 -m pytest tests/viz -q` passing.
- Write `docs/status/VISUAL_REVIEW.md`: per chapter, what you saw (with the screenshot paths under
  `build/visual-review/`), what you changed, and wording issues for the author.
