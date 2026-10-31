## 3. HDL and Logic Synthesis

Chapter 2 showed that TritFlow's cell library is functionally complete, so it can implement any ternary logic. This chapter covers TritVerilog, the dedicated HDL for ternary circuits, and the logic synthesis engine that turns a TritVerilog description into a netlist of standard cells. TritVerilog extends the syntax of industry-standard Verilog naturally to ternary values, so ternary digital circuits can be written with a familiar, intuitive grammar.

### 3.1 Values and Numbers

A signal value, or trit, is −1, 0 or +1, corresponding to −5 V, 0 V or +5 V. Used as a condition, these values mean false, unknown and true. Unknown is the valid trit 0 at a physical 0 V; it is not Verilog's undefined value X or high impedance Z.

A vector of trits (for example `trit [1:0] a;`) represents an integer in **balanced ternary**. Counting from the least significant digit, digit i has weight 3<sup>i</sup>. In numeric literals, −1 is written `T` (or lowercase `t`); for example, `2'tT1` is −1·3 + 1 = −2. In general, n trits represent exactly the 3<sup>n</sup> integers from −(3<sup>n</sup> − 1)/2 to +(3<sup>n</sup> − 1)/2; two trits give the nine integers from −4 to +4.

<!-- tables: numbers -->

Balanced ternary has advantages that binary representations such as two's complement lack.

- **No sign bit**: because the digits are symmetric around 0, positive numbers, zero and negative numbers share one format, with no dedicated sign bit.
- **Negation is immediate**: negating a number (−a) only flips the sign of every digit (T ↔ 1). Unlike two's complement, which inverts every bit and then adds 1 to the least significant bit, it involves no carry propagation.
- **Truncation rounds to the nearest value**: because every digit is −1, 0 or +1, dropping lower digits leaves an error within half the weight of the dropped digits, symmetric about zero. TritVerilog's `a >> 1` (divide by 3 and round to the nearest integer) gets this rounding simply by dropping the least significant digit.

### 3.2 Syntax

The table below summarizes TritVerilog's main operators and constructs, and the cell netlists that logic synthesis maps them to.

<!-- tables: syntax -->

Width rules follow Verilog: operations take the width of the assignment target. Operands narrower than the target are padded with 0 in the upper digits, and upper digits that do not fit in the target are discarded.

### 3.3 Synthesis Stages

TritFlow's logic synthesis engine is a deterministic compiler written in Python. It produces a netlist in five stages.

1. **Parsing and elaboration**: the TritVerilog source is parsed into an abstract syntax tree (AST), and the module hierarchy, parameters (`parameter`) and generate statements (`generate`) are elaborated into a logic intermediate representation. Procedural assignments inside `always @*` blocks are normalized to static single assignment (SSA) form, which tracks each signal's value at every assignment, and conditional branches such as `if` and `case` become selectors.
2. **Technology mapping**: each operator is replaced with a dedicated cell structure. Addition and subtraction become carry chains of full and half adders with the same structure as the taped-out circuits; comparisons become circuits that saturate the per-digit differences and decide the sign from the most significant digit; equality (`==`) and `case` labels become per-digit equality detectors. Selectors are described in section 3.5.
3. **Logic optimization**: constants are folded, common subexpressions shared and unused gates removed. Expressions are then simplified with the following identities, which still hold in ternary logic even though it is not a Boolean algebra.
   - Double negation: −(−x) = x
   - Idempotence: min(x, x) = x, max(x, x) = x
   - min and max with constants: min(x, +1) = x, min(x, −1) = −1, max(x, +1) = +1, max(x, −1) = x
   - NANY with a 0 input: NANY(x, 0) = −x
   - De Morgan's laws: min(−a, −b) = −max(a, b), max(−a, −b) = −min(a, b)
4. **Fanout limit and buffer trees**: too much input capacitance downstream slows the rising and falling edges and lengthens settling time. SPICE simulation confirmed that one output can drive eight identical cells in parallel and still hold correct levels, but logic synthesis limits each cell's fanout to **4** to keep a design margin. Nets with a fanout above 4 automatically get a tree of buffer cells (BUF) to share the load.
5. **Equivalence checking**: the synthesized netlist is checked against the original HDL. Section 3.6 describes how.

### 3.4 Arithmetic: `+` and `*`

Adding two one-trit values gives a sum from (−1) + (−1) = −2 to (+1) + (+1) = +2, so a carry is needed. For example,

1 + 1 = 2 = 3·1 + (−1)

so the sum digit is −1 and the carry into the next digit is +1.

A ternary full adder takes two inputs a and b and a carry c<sub>in</sub> from the digit below, and satisfies a + b + c<sub>in</sub> = s + 3c<sub>out</sub>. TritFlow's logic synthesizer expands the HDL `+` operator into a full adder with the same structure as the author's taped-out circuit: **11 NANY and 5 INV** (a half adder uses 5 NANY and 2 INV). Multi-digit adders chain these through their carries.

<!-- code: fa_source -->

<!-- code: fa_synth -->

Multiplying two one-trit values (`*`) is much simpler. The product is always −1, 0 or +1, so **no carry is produced**. The product of a weight w and an input x is x itself for w = +1, its negation −x for w = −1, and 0 for w = 0. The synthesizer expands this multiplication into the same netlist as the taped-out circuit: **2 NAND, 1 NOR and 1 INV**.

<!-- code: mul_source -->

<!-- code: mul_synth -->

### 3.5 Selection: Mapping Conditional Logic

Conditional constructs such as `if-else`, `case` and the ternary operator `?:` are synthesized into selectors (multiplexers) that pass one of several candidates to the output according to a condition signal.

In binary logic the condition is either 0 or 1, so a simple AND-OR circuit makes a selector. In ternary logic, however, **the condition itself can be 0 (unknown)**, so the output for a 0 condition has to be defined and built into the circuit. TritFlow's logic synthesizer chooses between two kinds of selector depending on the condition.

The code cell below compares two ways of writing the same function: select a when op = +1 and b when op = −1.

<!-- code: sel_source -->

**A comparison as the condition: `op == 1't1`**　Let s be the result of the comparison. s is only ever true (+1) or false (−1), never 0; for op = 0 the comparison is false and b is selected. When the condition is guaranteed never to be 0, output r can take the same form as a binary AND-OR selector:

$$r = \max\bigl(\min(s,\ a),\ \min(-s,\ b)\bigr)$$

For s = +1, min(+1, a) = a and min(−1, b) = −1, so their max is a. For s = −1, the output is b by the same reasoning. min, max and negation are built from NAND, NOR and INV, respectively.

**The value itself as the condition: `op`**　When the signal `op` is used directly as the condition, op can be 0. The TritVerilog language specification defines the output for a 0 condition as the common value if a and b are equal, and 0 if they differ (multi-trit values are compared digit by digit). This behavior needs a ternary selector with one input for each of the three condition values (−1, 0, +1): MUX3.

<!-- code: sel_synth -->

The second description, which needs MUX3, uses more cells than the first. Whenever TritFlow's logic synthesizer can confirm on the intermediate representation that a condition never takes 0, it uses the first structure.

### 3.6 Equivalence Checking

To make logic synthesis trustworthy, TritFlow automatically checks after every synthesis run that the synthesized gate netlist means the same as the original HDL. It evaluates the HDL behavior (integer and truth-value evaluation) and the gate netlist (logic simulation from each cell's truth table) along two independent paths and compares every output.

Inputs of up to 12 trits are checked exhaustively (at most 3<sup>12</sup> = 531,441 combinations). Circuits with more than 12 input trits are checked with 100,000 pseudorandom test vectors from a fixed seed. The "equivalent over all … inputs" in the synthesis results so far comes from this check.

### 3.7 Application: Dot Product with Ternary Weights

The core operation of ternary-weight neural networks such as [BitNet b1.58](https://doi.org/10.48550/arXiv.2402.17764), mentioned at the start, is the dot product y = Σ<sub>i</sub> w<sub>i</sub>x<sub>i</sub> of ternary weights w<sub>i</sub> ∈ {−1, 0, +1} and inputs x<sub>i</sub>. BitNet b1.58 uses 8-bit inputs; here, the inputs are also restricted to one trit. The circuit the author taped out on OpenSUSI-TR10 is itself a one-trit multiply-accumulate circuit (X + A × B + C<sub>in</sub> = S + 3C<sub>out</sub>), one term of this dot product.

Here, the multiplier and adder from section 3.4 are combined into a four-term dot-product circuit (module name dot4), written in TritVerilog and synthesized. Each product w<sub>i</sub>x<sub>i</sub> lies between −1 and +1 and the four-term sum between −4 and +4, so output y fits in two trits (weights 3<sup>1</sup> and 3<sup>0</sup>).

<!-- code: dot4_source -->

<!-- code: dot4_synth -->

In the synthesized netlist, each of the four multipliers is built from 2 NAND, 1 NOR and 1 INV (16 cells in total), and the adder that sums them from one full adder and two half adders (21 NANY and 9 INV).
