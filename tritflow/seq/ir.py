"""Single-clock state boundaries around the existing combinational trit DAG."""
from dataclasses import dataclass

from tritflow.hdl.ir import Design, Node, normalize_inputs


@dataclass
class Register:
    """One stored trit; q.name is also its stable RTL register identity."""
    name: str
    q: Node
    d: Node
    clock: Node


@dataclass
class SequentialDesign(Design):
    """Present-state outputs and simultaneous next-state functions, without delay.

    There is no implicit hardware reset or power-up value. Every simulation
    requires an explicit state dictionary, independent of the HDL declarations.
    """
    registers: tuple[Register, ...] = ()
    clock: str = ""

    @property
    def state_names(self):
        return [r.name for r in self.registers]

    @property
    def data_inputs(self):
        return [name for name in self.inputs if name != self.clock]

    def combinational(self):
        """Expose Q as inputs and D as outputs for the existing mapper/checker."""
        outputs = {**self.outputs, **{d_name(r.name): r.d for r in self.registers}}
        inputs = {**self.inputs, **{r.name: r.q for r in self.registers}}
        # A Q may also be a public output; use an internal name only on the D
        # side. This DAG is used for evaluation; mapping uses a renamed Q view.
        return Design(self.top, self.ports, outputs, inputs, self.params)

    def evaluate(self, inputs, state=None):
        if state is None:
            raise ValueError("sequential evaluation requires explicit initial/present state")
        state = normalize_inputs(self.state_names, state)
        normalize_inputs(list(self.inputs), inputs)
        if (normalize_inputs([self.clock], {self.clock: inputs[self.clock]})[self.clock] == 0).any():
            raise ValueError("clock must be -1 or +1; zero is not a valid clock level")
        values = self.combinational().evaluate({**inputs, **state})
        return {name: values[name] for name in self.outputs}

    simulate = evaluate

    def transition(self, inputs, state):
        """Capture once on a -1→+1 clock edge; inputs omit the clock port."""
        if set(inputs) != set(self.data_inputs):
            raise ValueError(f"expected data inputs {self.data_inputs}")
        values = self.combinational().evaluate({**inputs, self.clock: 1,
                                               **normalize_inputs(self.state_names, state)})
        return {r.name: values[d_name(r.name)] for r in self.registers}

    def cycles(self, vectors, initial):
        """Return state/output after each rising edge, never sequentially update Qs."""
        state = normalize_inputs(self.state_names, initial)
        rows = []
        for vector in vectors:
            state = self.transition(vector, state)
            rows.append({'state': state.copy(),
                         'outputs': self.evaluate({**vector, self.clock: 1}, state)})
        return rows

    def truth_table(self, **kwargs):
        raise ValueError("use transition(inputs, state) or cycles(vectors, initial) for registers")


def d_name(name):
    """Reserved private D endpoint, chosen outside the source identifier syntax."""
    return '$seq.d:' + name
