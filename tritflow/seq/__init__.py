"""Opt-in single-clock sequential TritVerilog; see docs/status/SEQ_FLOW.md."""
from .ir import SequentialDesign, Register
from .synthesis import SequentialNetlist, as_sequential, check_sequential

__all__ = ['SequentialDesign','SequentialNetlist','Register','as_sequential','check_sequential']
