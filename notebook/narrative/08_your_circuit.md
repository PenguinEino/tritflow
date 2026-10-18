## 8. Change the circuit and close the loop

Choose a sign detector, signed comparator, multiplier or min/max sorter.
Read its mathematical specification, then edit the HDL below and run the
design cell. The truth table first compares both source and mapped logic
with an independent integer reference. Placement, routing, drawing DRC, LVS
and extracted simulation then follow the same path as the opening adder.

<!-- figure: ch8 -->

*Set the circuit choice in the code cell, inspect its HDL, then change an
expression. The generated layout and waveform belong to that edited source.*

Keep the arithmetic reference while making an equivalent implementation.
If you change the intended function, edit that specification as well.
For a deliberate first experiment, try replacing a minimum with a maximum
in the sorter: the truth-table check identifies the disagreement before routing.

> **What this shows.** {custom.name} passes the integer reference for
> {custom.logic_states} input states. Its {custom.cells} mapped cells occupy
> {custom.die_um} µm; drawing DRC has {custom.drc_items} markers, LVS is
> {custom.lvs_status}, and the extracted sequence visits
> {custom.analog_states} input states with output checks {custom.analog_status}.

Use the generated HDL, SPICE, GDS and result files as the starting point for
another ternary design on OpenSUSI TR-1um.
