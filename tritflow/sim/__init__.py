"""ngspice simulation using ±5 V ternary levels and ±0.5 V acceptance bands."""
from .runner import SimulationError, run_ngspice, read_wrdata, read_ascii_raw
from .spice import gate_spice, subcircuits, model_includes, simulation_netlist
from .bench import build_testbench, input_vectors, simulate, dc_transfer
from .measure import settling_time, measure_sequence
from .compare import compare_layout

__all__ = ['SimulationError', 'run_ngspice', 'read_wrdata', 'read_ascii_raw',
           'gate_spice', 'subcircuits', 'model_includes', 'simulation_netlist',
           'build_testbench', 'input_vectors', 'simulate', 'dc_transfer',
           'settling_time', 'measure_sequence', 'compare_layout']
