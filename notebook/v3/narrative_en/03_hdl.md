## 3. HDL and Logic Synthesis

Chapter 2 confirmed that TritFlow's cell library is functionally complete and can cover any ternary logic. This chapter looks at TritVerilog, the dedicated HDL for ternary circuits, and at the logic synthesis engine that converts a description into a netlist of standard cells. TritVerilog extends the syntax of the industry-standard Verilog HDL naturally to ternary values, so ternary digital circuits can be designed with an intuitive grammar.

### 3.1 Values and Numbers

A signal value, or trit, is −1, 0 or +1, corresponding to −5 V, 0 V or +5 V. In conditions, these values mean false, unknown and true. Unknown is the valid trit 0 at a physical 0 V, unlike Verilog's undefined value X or high impedance Z.

A vector of trits (for example `trit [1:0] a;`) represents an integer in **balanced ternary**. Counting from the least significant digit, digit i has weight 3<sup>i</sup>. In numeric literals, the value −1 is written `T` (or lowercase `t`); for example, `2'tT1` represents −1·3 + 1 = −2. In general, n trits represent exactly the 3<sup>n</sup> integers from −(3<sup>n</sup> − 1)/2 to +(3<sup>n</sup> − 1)/2; two trits give the nine integers from −4 to +4.

<!-- tables: numbers -->

Balanced ternary has advantages that binary representations (such as two's complement) lack.

- **No sign bit**: because −1 is included symmetrically, positive numbers, zero and negative numbers share one symmetric format without a dedicated sign bit.
- **Negation completes at once**: negating a number (−a) only flips the sign of every digit (T ↔ 1). There is no carry propagation, unlike two's complement, which inverts every bit and then adds 1 to the least significant bit.
- **Truncation rounds to the nearest value**: because every digit is −1, 0 or +1, dropping lower digits leaves an error within half the weight of the dropped digits, symmetric between positive and negative. TritVerilog's `a >> 1` (divide by 3 and round to the nearest integer) achieves this rounding by simply dropping the least significant digit.

### 3.2 Syntax

The table below summarizes TritVerilog's main operators and constructs and the cell netlist each is replaced by in logic synthesis.

<!-- tables: syntax -->

Widths follow Verilog: operations use the digit width of the assignment destination. Operands shorter than the destination are padded with zeros in the upper digits, and upper digits that do not fit are discarded.

### 3.3 Synthesis Stages

TritFlow's logic synthesis is implemented in Python and builds the netlist in five stages.

1. **Elaboration**: parse the TritVerilog source and elaborate module hierarchy, parameters (`parameter`) and `generate` into an expression intermediate representation. Procedural assignments in `always @*` become static single assignment (SSA), which updates each signal's current value at every assignment, and `if` and `case` branches become value selections.
2. **Mapping**: replace each operation with a fixed cell structure. Addition and subtraction become carry chains of full and half adders with the same structure as the taped-out circuits, comparisons saturate per-digit differences and decide the sign from the most significant digit, and equality (`==`) and `case` labels use per-digit equality detectors. Selection is described in section 3.5.
3. **Optimization**: fold constants, share common subexpressions, remove unused logic, and simplify with the following identities that hold in ternary logic.
   - Double negation: −(−x) = x
   - Idempotence: min(x, x) = x, max(x, x) = x
   - min and max with constants: min(x, +1) = x, min(x, −1) = −1, max(x, +1) = +1, max(x, −1) = x
   - NANY with a 0 input: NANY(x, 0) = −x
   - De Morgan's laws: min(−a, −b) = −max(a, b), max(−a, −b) = −min(a, b)
4. **Fanout control**: too many inputs on one output slow its transitions and lengthen settling time. SPICE simulation confirmed correct levels with eight identical cells on one output. With margin, each cell output drives at most four inputs by default, and additional loads are distributed through BUF trees.
5. **Equivalence checking**: verify that the synthesized netlist implements the same function as the HDL, as described in section 3.6.

### 3.4 Arithmetic: `+` and `*`

The sum of two one-trit values ranges from (−1) + (−1) = −2 to (+1) + (+1) = +2, so a carry is needed. For example, 1 + 1 = 2 = 3·1 + (−1), so the digit's sum is −1 and the carry into the next digit is +1.

A ternary full adder takes inputs a and b and the carry c<sub>in</sub> from the lower digit and satisfies a + b + c<sub>in</sub> = s + 3c<sub>out</sub>. TritFlow's logic synthesis expands HDL `+` into a full adder with the same structure as the taped-out circuit (11 NANY and 5 INV). A half adder is 5 NANY and 2 INV. Multi-digit addition chains them through the carries.

<!-- code: fa_source -->

<!-- code: fa_synth -->

The product of two one-trit values is −1, 0 or +1 and produces no carry. The product of a weight w and an input x is x for w = +1, −x for w = −1 and 0 for w = 0. Logic synthesis expands HDL `*` into the same structure as the taped-out multiplier (2 NAND, 1 NOR and 1 INV).

<!-- code: mul_source -->

<!-- code: mul_synth -->

### 3.5 Selection: Mapping Conditional Logic

Conditional constructs (`if`, `case` and `?:`) become selectors (multiplexers) that pass one candidate to the output according to a condition. Binary conditions are 0 or 1, so AND and OR can implement a selector. A ternary condition can itself be 0 (unknown), so the output for a 0 condition must also be defined. Logic synthesis chooses between two kinds of selector depending on whether the condition can be 0.

The following two descriptions select output r from one-trit inputs a, b and op: a for op = +1 and b for op = −1.

<!-- code: sel_source -->

**A comparison as the condition (`op == 1't1`)**　Let s be the comparison result. s is true (+1) or false (−1), never 0. For op = 0 the comparison is false, so b is selected. When the condition cannot be 0, output r can be built with the same form as binary AND-OR selection:

$$r = \max\bigl(\min(s,\ a),\ \min(-s,\ b)\bigr)$$

For s = +1, min(s, a) is a and min(−s, b) is −1, so max leaves a. For s = −1, b remains in the same way. NAND, NOR and INV build min, max and negation. A `case` statement takes the same form when label matches are used as conditions.

**The value itself as the condition (`op`)**　The case op = 0 remains. TritVerilog defines the output for this case as the shared value if a and b are equal, and 0 otherwise; multi-trit values are compared digit by digit. This behavior uses a ternary selector with one input for each of the condition's three values (MUX3).

<!-- code: sel_synth -->

The second description needs MUX3 and is therefore larger than the first. Logic synthesis uses the first form after confirming on the intermediate representation that the condition cannot be 0.

### 3.6 Equivalence Checking

Every synthesis run automatically checks that the synthesized netlist implements the same function as the HDL. The HDL semantics (integer and truth-table rules) and the netlist (each cell's truth table) are evaluated separately, and every output is compared. Inputs of up to 12 trits are checked exhaustively (at most 3<sup>12</sup> = 531,441 combinations); larger inputs use 100,000 random combinations from a fixed seed. The "equivalent over all … inputs" results shown so far come from this check.

### 3.7 Dot Product with Ternary Weights

The matrix products in [BitNet b1.58](https://doi.org/10.48550/arXiv.2402.17764), introduced at the start, consist of repeated dot products of ternary weights w<sub>i</sub> and inputs x<sub>i</sub>, y = Σ<sub>i</sub> w<sub>i</sub>x<sub>i</sub>. BitNet b1.58 uses 8-bit inputs; here, the inputs are restricted to one trit. The taped-out one-trit multiply-accumulate circuit underlying TritFlow's cells (X + A × B + C<sub>in</sub> = S + 3C<sub>out</sub>) corresponds to one term of this dot product. Here, the `*` and `+` operations from section 3.4 describe a four-term dot-product circuit (module name dot4). Each product ranges from −1 to +1, and the four-term sum ranges from −4 to +4, so two trits suffice for output y.

<!-- code: dot4_source -->

<!-- code: dot4_synth -->

Each of the four products maps to 2 NAND, 1 NOR and 1 INV (16 cells in total), and the sum is one full adder and two half adders (21 NANY and 9 INV).
