"""Direct synthesis and the notebook facade share the public SCHEM hook."""

import pytest

from tritflow import flow, hdl, synth


@pytest.mark.parametrize("factory",[
    lambda:synth.synthesize(hdl.load("examples/half_add.tv",top="half_add")),
    lambda:flow.load("examples/half_add.tv","half_add").synthesize(),
])
def test_schematic_delegates_options_and_preserves_mapped_netlist(factory,monkeypatch):
    import tritflow.schematic
    net=factory()
    before=net.to_json()
    sentinel=object()
    options={"expand":"*","inputs":{"a":1,"b":1},"net_names":True}
    def draw(actual,**kwargs):
        assert actual is net and kwargs == options
        return sentinel
    monkeypatch.setattr(tritflow.schematic,"draw",draw)
    assert net.schematic(**options) is sentinel
    assert net.to_json() == before


def test_public_half_adder_drawing_has_independent_arithmetic_values():
    net=flow.load("examples/half_add.tv","half_add").synthesize()
    diagram=net.schematic(expand="*",inputs={"a":1,"b":1})
    assert diagram.values["sum"] + 3*diagram.values["carry"] == 2
    assert diagram.values["sum"] == -1 and diagram.values["carry"] == 1
    assert diagram._repr_svg_().startswith("<svg")
