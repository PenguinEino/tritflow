## 3. HDL and Logic Synthesis

Chapter 2 established that TritFlow's cell basis can implement arbitrary ternary logic. This chapter introduces TritVerilog, the HDL used to describe circuits, and logic synthesis, which maps it to cell netlists. TritVerilog extends Verilog's combinational constructs to ternary values. Each construct is introduced with its synthesis mapping.

### 3.1 Values and Numbers

A signal value, or trit, is −1, 0 or +1, corresponding to −5 V, 0 V or +5 V. In conditions, these denote false, unknown and true. Unknown is the valid trit 0 at a physical 0 V, distinct from Verilog's undefined X and high-impedance Z. Vectors such as `trit [1:0] a` represent balanced-ternary integers, with digit $i$ weighted by $3^i$. Literals use T for −1: `2'tT1`, for example, represents −1·3 + 1 = −2. Two trits represent −4 through +4 without a sign bit. Negation simply negates every digit.

<!-- tables: numbers -->

### 3.2 Syntax

The table lists TritVerilog's combinational constructs and their synthesis mappings.

<!-- tables: syntax -->

As in Verilog, the assignment destination determines the expression width. Shorter operands are zero-extended; excess high digits are discarded.

### 3.3 Synthesis Stages

Logic synthesis proceeds through the following stages.

1. Elaboration: parse the HDL and elaborate module hierarchy, parameters and `generate` constructs into an expression intermediate representation. Procedures in `always @*` are converted to static single assignment, updating each signal's current value on every assignment. Branches in `if` and `case` become value selections.
2. Mapping: replace each operation with a fixed circuit structure. Addition and subtraction use carry chains of half adders and full adders verified in the taped-out circuits. Comparisons saturate per-digit differences and determine the sign from the most significant digit. Equality tests and `case` labels use per-digit equality detectors. Selection is described in section 3.5.
3. Optimization: fold constants, share common subexpressions, remove unused logic, and simplify using identities valid in ternary logic, such as $-(-x) = x$, $\min(x, x) = x$, $\min(x, +1) = x$, $\max(x, +1) = +1$, $\mathrm{NANY}(x, 0) = -x$, $\min(-a, -b) = -\max(a, b)$.
4. Fanout control: SPICE simulation confirmed correct levels with eight identical cells on one output. With margin, each cell output drives at most four inputs by default, and additional loads are distributed through BUF trees.
5. Equivalence checking: verify that the synthesized netlist implements the same function as the HDL (section 3.6).

### 3.4 Arithmetic: `+` and `*`

The sum of two one-trit values ranges from −2 to +2 and requires a carry. For example, 1 + 1 = 2 = 3·1 + (−1), giving a sum digit of −1 and a carry of +1. A full adder satisfies $a + b + c_{in} = s + 3\,c_{out}$. TritFlow maps HDL `+` to the full-adder structure verified in the taped-out circuits (11 NANY and 5 INV cells), connecting carry chains for multiple digits.

<!-- code: fa_source -->

<!-- code: fa_synth -->

The product of two one-trit values is −1, 0 or +1 and produces no carry. It is x for w = +1, −x for w = −1, and 0 for w = 0. TritFlow maps HDL `*` to the taped-out multiplier structure (2 NAND, 1 NOR and 1 INV).

<!-- code: mul_source -->

<!-- code: mul_synth -->

### 3.5 Selection: Mapping Conditional Logic

Conditional constructs (`if`, `case` and `?:`) map to selectors that pass one candidate value to the output. Binary conditions are 0 or 1, so AND and OR can implement a selector. A ternary condition can itself be −1, 0 or +1, requiring a defined output for condition 0. Synthesis chooses between two selector structures according to whether the condition can be 0.

The following two descriptions select output r from one-trit inputs a, b and op: a for op = +1 and b for op = −1.

<!-- code: sel_source -->

The first uses the comparison `op == 1't1` as its condition. Its result s is either true (+1) or false (−1), never 0. At op = 0, the comparison is false and selects b. When the condition cannot be 0, r can use the same structure as a binary AND/OR selector:

$$r = \max\bigl(\min(s,\ a),\ \min(-s,\ b)\bigr)$$

For s = +1, min(s, a) is a and min(−s, b) is −1, so max selects a. For s = −1, the same argument selects b. NAND, NOR and INV implement min, max and negation. A `case` statement uses the same structure with label equality as its condition.

The second description uses op directly, so op = 0 remains possible. TritVerilog defines this case to return the common value if a and b agree, and 0 otherwise. Multiple-trit values are compared digit by digit. This behavior uses a ternary selector (MUX3) with one input for each of the three condition values.

<!-- code: sel_synth -->

The second circuit is larger because it requires MUX3. Synthesis uses the first structure only after proving in the intermediate representation that the condition cannot be 0.

### 3.6 Equivalence Checking

Every synthesis run checks that the synthesized netlist implements the same function as the HDL. The HDL is evaluated using integer and truth-table semantics; the netlist is independently evaluated using cell truth tables. Their outputs are compared for all combinations with up to 12 input trits, or for 100,000 random combinations beyond that. The synthesis summaries reporting equivalence over all input vectors refer to this check.

### 3.7 Dot Product with Ternary Weights

The matrix products in [BitNet b1.58](https://doi.org/10.48550/arXiv.2402.17764), introduced at the start, consist of repeated dot products of ternary weights $w_i$ and inputs $x_i$, $y = \sum_i w_i x_i$. BitNet b1.58 uses 8-bit inputs; here, the inputs are restricted to one trit. The taped-out one-trit multiply-accumulate circuit underlying TritFlow's cells ($X + A \times B + C_{in} = S + 3\,C_{out}$) corresponds to one term of this dot product. Here, the `*` and `+` operations from section 3.4 describe a four-term dot product, dot4. Each product ranges from −1 to +1, and the four-term sum ranges from −4 to +4, so two trits suffice for output y.

<!-- code: dot4_source -->

<!-- code: dot4_synth -->

Each of the four products maps to 2 NAND, 1 NOR and 1 INV. The remaining NANY and INV cells form one full adder and two half adders for the sum. Chapters 4 and 5 place and route dot4, verify it, and run post-layout simulation. Chapter 6 evaluates area, delay and static power against dot-product size, then demonstrates HDL changes and integration into a shuttle top-level layout.
