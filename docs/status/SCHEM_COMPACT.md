# SCHEM_COMPACT status

Updated: 2026-10-21. **Done.** No blockers or interface requests. No work remains in progress.
No dependencies were installed; no network services, commits, pushes, or git-state operations were used.

## Delivered

- Hand-drafted, editable Xschem sources: `notebook/assets/schematics/src/inv.sch`, `nand.sch`,
  `nor.sch`, and `nany.sch`. They replace `inverter_compact.sch`, `mul_nand_compact.sch`,
  `mul_nor_compact.sch`, and `nany_compact.sch`.
- Regenerated `notebook/assets/schematics/{INV,NAND,NOR,NANY}.compact.svg`.
- Replaced `notebook/v2/compact_schematics.py` with an exporter of those fixed drawings.
  It never generates, rewrites, or compacts source geometry.
- Added `notebook/assets/schematics/verify_compact.py` for repeatable source and Xschem-netlist checks.
- Chapter 2's `src/inv_compact.sch` is byte-for-byte identical to HEAD. `notebook/cell_views.py`
  and the notebook authoring files needed no changes. All writes stayed within the brief's paths,
  this status file, and ignored `build/` artifacts in this worktree. Reference repositories were read only.

## Drafting decisions

The circuits use a 10-unit drafting grid, short orthogonal wires, inputs at the left, output at
right, and supplies above/below the main branch. NAND's parallel PMOS pair and NOR's parallel
NMOS pair remain explicit. NANY has its series main branch at left and its two VMID clamp
branches beside the midpoint output. Main NANY body ties use narrow wired lanes; the clamp
body ties retain separate VDD/VSS labels, including the PMOS bodies whose sources connect to vout.

All figures use an exact 640-unit-wide print box and 1.6 print scale, with independently cropped
heights. Thus equal-width grid cards show identical device and lettering scales. At 480 px wide,
MOS parameters are about 10.9 px, resistor parameters 10.1 px, device names 11.7 px, and net labels
12.9 px. Native pin captions are 8.6 px. No labels or pins were hidden or deleted.

Each schematic embeds the pinned PDK's original `TR-1umLIB/MP.sym`, `MN.sym`, and `RR.sym`
definition once per used symbol. **Only annotation positions and sizes change.** This lets the
editable Xschem schematic and its print agree while leaving the PDK untouched. Native symbol
geometry, ordered pins, model/netlisting templates, and every annotation string remain exact.
Names sit above-left of MOS devices, W/L/m below-right, and resistor properties in a separate
left column. RR's PLUS/MINUS/SUB captions and computed R annotation remain visible.

Export still uses Xschem batch printing with an exact box, `notebook/export_schematics._theme_svg`,
and the serif face. The exporter restores native text positions after applying the shared theme,
because that theme also moves annotations in the old unmodified RR drawing. SVG accessibility
IDs are unique per cell when the four images are inlined together.

The obsolete free-text sizing sidebars were omitted. Several disagree with the original device
properties: the actual RR instances in **all four** original drawings have W=2.8e-6, L=30e-6,
R=1, m=1, tc1=tc2=0. Those properties are preserved, along with all MOS properties, original
instance names, original external port names/directions/order, original label instances, and
wire-net label names. V+/V− naming in NAND/NOR is retained from the originals.

## Electrical equivalence evidence

`verify_compact.py` runs `xschem -n -s -q -x` on temporary copies of both original and redrawn
schematics, using `TR1UM_PDK=~/pdk/TR-1um-pinned` and the system Xschem library. The two SPICE
netlists are compared device by device, preserving each ordered MOS D/G/S/BG terminal and RR
PLUS/MINUS/SUB terminal. One bijection of nets must satisfy every terminal, with external port
names fixed; opens, shorts and pin swaps therefore fail even if wire lab attributes claim otherwise.
Models and every emitted parameter must match. A separate source check compares **all** instance
properties, including m and the as/ad/ps/pd fields that Xschem omits when they have default values.
It also checks the complete embedded PDK geometry/pin/netlisting records and the multiset of
annotation strings.

| Cell | MOS | RR | Devices | Ordered terminals | Nets | Result |
|---|---:|---:|---:|---:|---:|---|
| INV | 2 | 2 | 4 | 14 | 6 | PASS |
| NAND | 4 | 2 | 6 | 22 | 8 | PASS |
| NOR | 4 | 2 | 6 | 22 | 8 | PASS |
| NANY | 8 | 2 | 10 | 38 | 12 | PASS |
| Total | 18 | 8 | 26 | 96 | 34 | PASS |

Detailed evidence: [equivalence.json](../../build/schem-compact/verification/equivalence.json),
including every device's original/redrawn nodes, parameters, source attributes and source hashes.
The actual SPICE netlists and Xschem logs are under
`build/schem-compact/verification/{original,redrawn}/`.

The checker also passed nine controls: it accepted a complete internal-net renaming and rejected
eight introduced defects (MOS width change, MOS BG short, RR SUB open, D/S swap, source m change,
hidden original label, modified native terminal geometry, and missing BG annotation).
Evidence: [checker-negative-controls.json](../../build/schem-compact/verification/checker-negative-controls.json).

## Visual review and notebook validation

Inspected all four 480 px PNGs after each of four drafting passes and after the final export.
Each pass also built the actual v2 notebook, executed all ten code cells with nbclient, extracted
cell `# 3-2`'s HTML, opened its details element, and rendered/reviewed it in headless Chrome at
1100 px wide. Iteration 1 exposed RR/MOS text crowding, clipped vout, and NANY collisions.
Iterations 2–3 fixed spacing and supply-pin/rail intersections. Iteration 4 moved MOS parameters
to the right and removed NANY's temporary substrate-wire detour. The final pass added unique
SVG IDs without changing the visible geometry.

Final screenshots, all opened and inspected:

- [INV-480.png](../../build/schem-compact/final/INV-480.png) — 480 × 442.
- [NAND-480.png](../../build/schem-compact/final/NAND-480.png) — 480 × 555.
- [NOR-480.png](../../build/schem-compact/final/NOR-480.png) — 480 × 600.
- [NANY-480.png](../../build/schem-compact/final/NANY-480.png) — 480 × 622.
- [chapter3-1100.png](../../build/schem-compact/final/chapter3-1100.png) — actual notebook output,
  1100 × 1630, including truth tables and both full rows of schematics.

The final notebook execution ran all **10 code cells successfully in 5.0 s** locally with
`TRITFLOW_ROOT=~/code-a-chip-schem` and the pinned PDK. This is local notebook execution and figure
qualification. Artifacts: [executed.ipynb](../../build/schem-compact/final/executed.ipynb),
[chapter3.html](../../build/schem-compact/final/chapter3.html), and
[notebook.log](../../build/schem-compact/final/notebook.log).

An additional Chrome DOM measurement checked all **277 text elements** against one another,
SVG boundaries, and the actual schematic wire segments: **zero overlaps, zero clipped labels,
zero wire/text intersections** in all four figures at the actual grid width (512 px per card).
This supplements the visual inspection; native symbol outlines/pin stubs were reviewed by eye.
[Text-clearance evidence](../../build/schem-compact/final/text-clearances.json).

`python3 -m pytest tests/schematic -q`: **178 passed in 40.71 s**.
[pytest.log](../../build/schem-compact/pytest.log).
`git diff --check` passed. Re-exporting produced byte-identical SVGs and left every .sch unchanged.
[Final source/SVG hashes](../../build/schem-compact/final/source-hashes.json).
Earlier reviewed passes remain in `build/schem-compact/iteration-{1,2,3,4}/` and the baseline in
`build/schem-compact/baseline/`.

## Reproduce

From this worktree, using the existing Python/Xschem/Chrome installation:

```bash
export TR1UM_PDK="$HOME/pdk/TR-1um-pinned"
export TRITFLOW_ROOT="$PWD"
python3 notebook/v2/compact_schematics.py
python3 notebook/assets/schematics/verify_compact.py
python3 -m pytest tests/schematic -q
mkdir -p build/v2
python3 notebook/v2/make_notebook.py --out build/v2/local.ipynb
python3 build/schem-compact/run_notebook.py final
```

The last command uses the build-only review driver retained with the screenshots. For a clean
build without that helper, the equivalent notebook execution and HTML extraction are:

```python
from pathlib import Path
import nbformat
from nbclient import NotebookClient
root = Path.cwd()
out = root / "build/schem-compact/final"
out.mkdir(parents=True, exist_ok=True)
nb = nbformat.read("build/v2/local.ipynb", as_version=4)
NotebookClient(nb, timeout=600, kernel_name="python3",
               resources={"metadata": {"path": str(root)}}).execute()
nbformat.write(nb, out / "executed.ipynb")
cell = next(c for c in nb.cells if c.cell_type == "code" and c.source.startswith("# 3-2"))
html = "".join(o.get("data", {}).get("text/html", "") for o in cell.outputs)
(out / "chapter3.html").write_text(
    '<!doctype html><meta charset="utf-8"><style>body{margin:20px;background:white}</style>'
    + html.replace("<details>", "<details open>"))
```

Then render with:

```bash
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --window-size=1100,1630 --force-device-scale-factor=1 \
  --screenshot="$PWD/build/schem-compact/final/chapter3-1100.png" \
  "file://$PWD/build/schem-compact/final/chapter3.html"
```

The four SVG previews are generated with `cairosvg.svg2png(url=..., output_width=480, write_to=...)`.
The retained build-only `audit.py` and `check_checker.py` reproduce the supplemental checks.

## Remaining aesthetic tradeoffs

NANY has more blank space above its clamp branches than the other cells. Its main chain and
both clamps remain visibly distinct, and reducing that area further would require a different
circuit arrangement. Native pin captions are necessarily smaller than device/net labels at
480 px; the vector exports remain zoomable. No unresolved overlaps, clipped text, electrical
mismatches, or notebook-integration issues remain.
