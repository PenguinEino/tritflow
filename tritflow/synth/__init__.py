"""Map a TritVerilog design to the TR-1um balanced-ternary cell library.

The mapping follows the actual cell functions, with a/b in {-1,0,+1}:

* ``~a`` -> INV (Y=-A).
* ``~(a & b)`` -> NAND (Y=-min(A,B)); ``a & b`` -> NAND then INV.
* ``~(a | b)`` -> NOR (Y=-max(A,B)); ``a | b`` -> NOR then INV.
* ``nany(a,b)`` -> NANY (Y=-clamp(A+B,-1,+1)).
* Constants +1/0/-1 -> TIEP/TIEZ/TIEN, physically tied to the three supplies.

Arithmetic lowers to ripple adders and arrays of one-trit products. General
selectors use the complete unary cell basis and ternary Shannon selection.
Procedural case/if joins select on crisp +/-1 predicates.

``synthesize(design)`` first simplifies only ternary-valid expressions, shares
common logic and removes unused gates. In particular ``a & ~a`` is not a
constant: its value at a=0 is 0. Authored primitive cells retain their identities,
including the reference FA's 11 NANY and 5 INV. BUF trees limit cell input-pin
fanout to four by default; distinct output aliases also use BUFs.

The returned GateNetlist-compatible object has ``report()`` for cell counts,
logic depth in cell stages and source hierarchy. Synthesis compares its ideal
cell simulation against the original source DAG before returning: exhaustive
through 12 input trits, then 100,000 reproducible random vectors. Use
``write_artifacts(net, directory)`` for shared JSON, gate TritVerilog, SPICE and
reports. SPICE signal pins are A[, B], Y, then VDD VMID VSS.
"""

from .mapping import SynthesizedNetlist, fanouts, synthesize
from .optimize import optimize
from .simulate import check_equivalence, evaluate_netlist
from .writers import report_text, spice, tritverilog, write_artifacts

__all__ = ["SynthesizedNetlist", "synthesize", "optimize", "fanouts", "check_equivalence",
           "evaluate_netlist", "tritverilog", "spice", "report_text", "write_artifacts"]
