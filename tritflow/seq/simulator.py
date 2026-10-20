"""Explicit clock-level driver around simultaneous cycle transition functions."""
from tritflow.hdl.ir import normalize_inputs
from .ir import SequentialDesign


class Simulator:
    """Stateful logic simulator with no implicit hardware initialization.

    drive() accepts the full input dictionary, including CLK=-1 or +1. Repeated
    low/high levels and falling edges only reevaluate outputs; -1→+1 captures
    all register D functions together. Zero and skipped/ambiguous edges fail.
    """
    def __init__(self, circuit, *, initial, clock=-1):
        if clock not in (-1,1):
            raise ValueError('clock must be -1 or +1')
        self.circuit = circuit
        self.state = normalize_inputs(circuit.state_names, initial)
        self.clock = clock
        self.edges = 0

    def drive(self, inputs):
        names = [*self.circuit.data_inputs, self.circuit.clock]
        values = normalize_inputs(names, inputs)
        if any(v.ndim for v in values.values()):
            raise ValueError('stateful clock simulation accepts scalar trits')
        clock = int(values.pop(self.circuit.clock))
        if clock == 0:
            raise ValueError('zero is not a valid settled clock level')
        if self.clock == -1 and clock == 1:
            self.state = self.circuit.transition(values,self.state)
            self.edges += 1
        self.clock = clock
        if isinstance(self.circuit, SequentialDesign):
            return self.circuit.evaluate({**values,self.circuit.clock:clock},self.state)
        return self.circuit.evaluate(values,self.state)
