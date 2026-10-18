## 9. Next: compare the model with silicon

The reference-cell chip is expected in {history.delivery_month}. Measurement
will connect the divider and timing predictions to real devices: first DC
output levels and static rail currents, then settling with known stimulus
edges and loads. The recorded supply voltages, temperature and probe loading
will define a matching SPICE experiment.

<!-- figure: ch9 -->

| Measurement | Record with the result | Compare with SPICE |
|---|---|---|
| Input DC sweep | Supply voltages, temperature and rail currents | Transfer curve and middle-level error |
| Trit-to-trit step | Input edge, skew and total output loading | Final entry into the target voltage band |
| Supply and temperature sweep | Actual operating point at each measurement | Level and current sensitivity |

The first comparison will sweep the input through the middle region and
measure the output and each rail current. Next, step between trit levels,
measure final entry into the same voltage bands, and repeat at several loads.
Record pad, package and instrument capacitance alongside the circuit load.
Supply and temperature sweeps can then show which discrepancies depend on
bias and which call for changes to the interconnect or device assumptions.

### From your HDL to a shuttle-ready top

A routed core still needs a frame, real terminals and mask preparation.
`PnrResult.to_chip()` places a compatible core inside a copy of the pinned
MPW TEG frame, preserves its seal ring and prohibited regions, and replaces
the copied pad bank with peripheral passive `OSS_PAD_TEG` pads. With the
canonical adder layout selected, the public calls are:

```python
chip = layout.result.to_chip()
checks = chip.signoff()
chip.gds_path
```

`to_chip()` builds and qualifies the full top; `ChipResult.signoff()` repeats
its checks or reuses unchanged verified reports. `layout.signoff()` alone
checks the core, so use the returned chip for full-top signoff. The output
includes the drawing GDS, circuit reference, pad map, prepared mask GDS and
native reports.

> **What this shows.** The recorded framed adder based on {paper_adder.run_id} occupies
> {chip.die_um} µm with {chip.pad_count} real pads: drawing DRC reports
> {chip.drawing_drc_items} items, strict drawing LVS is {chip.lvs_status},
> mask DRC after mask-data preparation reports {chip.mask_drc_items} items,
> and the MPW precheck is {chip.precheck_status}.

Physical checks pass; `submission_ready` remains `{chip.submission_ready}`.
Before submitting a real design:

1. Obtain the shuttle organizer's allocation approval for the full frame and
   its custom pad/probe map; this top does not fit the earlier shared slot.
2. Complete the bond/package diagram. Power every same-domain supply pad,
   supply VMID separately, and agree die attach and common substrate at VSS.
3. Obtain process and ESD approval for the {levels.negative_v}/
   {levels.zero_v}/{levels.positive_v} V supplies. These passive pads have no
   ESD network; check package/probe loading, supply impedance and pad/bond
   current capability.
4. Complete the shuttle's metadata, license, schematic and circuit-reference
   package. Run the organizer's CI on the frozen revision and review the final
   masks and electrical results with the shuttle owner.

The inspected shuttle flow checks strict LVS on the drawing before mask-data
preparation; it defines no post-mask LVS check. TritFlow prepares the artifacts
and reports; it does not request an allocation or submit them.
