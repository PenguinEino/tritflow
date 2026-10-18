# Synthesized ternary schematics

`tritflow.schematic.draw()` turns a public `GateNetlist` into a deterministic
SVG drawing. Symbols follow signal flow from left to right. The same routed
scene can later show ideal trit values and estimated wire capacitance.

```python
from tritflow import flow
from tritflow.schematic import draw, legend

net = flow.load('examples/full_add.tv', 'full_add').synthesize()
sch = draw(net)                       # ha1 / ha2 blocks, plus top-level gates
sch.show()                           # or display(sch) in Colab
sch.save('build/full_add.svg')
sch.save('build/full_add.pdf')
svg_text, pdf_bytes = sch.svg, sch.pdf

flat = draw(net, expand='*')          # every actual synthesized cell
ha1 = draw(net, expand=['ha1'])       # ha1 cells; ha2 stays a block
coloured = flat.annotate(inputs={'a': -1, 'b': 1, 'cin': 0}, net_names=True)
coloured.show()
legend().show()
```

The requested `net.schematic(**options)` convenience method is a one-line
FRONTEND delegate to `draw`; SCHEM does not alter the shared netlist classes.
The callable hook works now with `flow.Netlist`, `SynthesizedNetlist`, and a
netlist loaded from JSON.

## Symbol legend

![Ternary symbol legend](assets/legend.svg)

The triangle and inversion bubble preserve the familiar INV/BUF convention.
NAND uses the AND outline with `min` inside; NOR uses the OR outline with
`max` inside. The bubble means **arithmetic sign reversal**, which also leaves
zero unchanged. It does not mean a Boolean complement. NANY uses a clipped
summing body with a Σ and an output bubble: sum the inputs, saturate to
−1…+1, then reverse the sign. Clipped corners distinguish this operation from
AND, OR, XOR and the ordinary amplifier triangle. TIE symbols resemble supply
sources and explicitly print +1, 0 or −1. Input and output flags point along
the signal flow; ascending numerical bit order keeps vectors together.

The three signal colours exactly match `figures/style.py`: −1 blue
`#2a78d6`, 0 grey `#6f6e69`, +1 red `#e34948`. The installed drawing package
copies those constants so it does not depend on the repository's figure
scripts; a regression check prevents palette drift.

## Hierarchy and wiring

The default view closes module-instance scopes recorded in `Instance.hier`.
Unary generate containers are compressed: the adder shows `digit[0].fa`,
`digit[1].fa`, and so on. `expand` accepts a path, a sequence of paths, or
`'*'` / `'all'`. Selecting a scope exposes all its descendant cells; selecting
a deeper scope opens its ancestors while sibling scopes remain closed.
Unknown paths raise `ValueError`.

Mapped netlists retain hierarchy paths but do not retain original module
port aliases or module types. A block therefore prints its instance path,
cell count and actual boundary **net names**. It never invents an `a`/`b`/`sum`
alias. When shared optimized logic crosses a scope more than once, closing
that scope could imply false feedback. The affected scope is opened and
`sch.scene.notes` explains why.

Longest-path columns, dummy lanes for long nets, and repeated barycenter
sweeps reduce crossings. Each inter-column channel assigns one distinct
vertical track to each net. Pin rows, wire bends and lanes follow an 8-pixel
grid. Symbol keep-outs include their labels; routing cannot enter them.
Collinear same-net segments merge so shared trunks are drawn once. Same-net
T joins get dots. Different-net perpendicular crossings get a gap in the
vertical wire and no dot. Dots are never used to imply a crossing connection.

Flat views preserve every synthesized cell, including fanout buffers and
TIE drivers. Large ripple adders make wide flat schematics; the default
hierarchical view is intended for an overview, with flat SVGs available at
native scale for following individual pins. No cells or long connections
are omitted to fit a page.

## Reuse after placement and routing

```python
# lay is the public flow.Layout returned by net.place_and_route(...).
post = sch.annotate(parasitics=lay.result)
# Equivalently:
post = sch.annotate(parasitics=lay.result.net_parasitics())
post.show()
# Geometry stays identical, including when values and C appear together.
assert post.scene is sch.scene
```

The adapter calls `PnrResult.net_parasitics()` and reads each net's
`wire_capacitance_f`. It also accepts `{net: farads}` and extraction-style
`{'nets': {net: {'capacitance_f': farads}}}` reports. Matching uses exact,
case-sensitive logical names. Unknown supply/report nets are ignored.
Nonfinite or negative capacitance raises `ValueError`. Receiving-pin C and
`total_load_f` are never relabelled as wire C.

Wire width and darkness grow monotonically with the square root of C,
normalised to the maximum C in that report. With values enabled, hue retains
the trit encoding and larger C darkens it. A source-side label prints C in fF.
Name, value and C labels occupy reserved space, so annotations neither move a
gate nor reroute a net. `annotate(inputs=None, parasitics=None)` removes those
overlays. These are settled ideal logic values and PNR's estimated lumped
wire C, not transient voltages or signoff PEX.

## Files and verification

`sch.svg` is UTF-8 text. `sch.pdf` contains vector paths and embedded fonts.
`save()` accepts `.svg`, `.pdf`, or `.png`; `png(scale=2)` returns a larger
raster preview. SVG creation uses only the Python standard library. PDF/PNG
exports lazily use the project's existing Matplotlib dependency. No Graphviz,
Cairo, Xschem, browser, TeX, extra pip package or system package is needed.
PDF timestamps are disabled so repeated exports are byte-identical.

SVG metadata includes one record per original cell terminal and external
port, with exact net name and owning symbol. A closed block records every
contained cell, including its internal terminals and nets. Visible boundary
terminals resolve to exact pin anchors; hidden terminals have `pin: null`.
This ledger documents electrical completeness without pretending a closed
block exposes its internal wiring.

```bash
python3 -m pytest tests/schematic -q
python3 -m tritflow.schematic.gallery --output build/schematic-review
```

The gallery produces native SVG, PDF and PNG for hierarchical and flat
`half_add`, `full_add`, adder N=2 and N=4, `mul1`, `mac1`, and all four
chapter-8 catalog choices (`sign`, `compare2`, `mul2`, `minmax`). It also
includes the legend and an explicitly **synthetic** C/value overlay.
`index.html` links all artifacts; `manifest.json` records the scene dimensions.
The gallery is a development utility run from this repository, not a runtime
dependency of the schematic stage.
