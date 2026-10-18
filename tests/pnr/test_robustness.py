"""Reader-authored corner cases, strict unloaded ports and failure publication."""
import json

import klayout.db as db
import pytest

from tritflow import CELLS_DIR
from tritflow.hdl import loads
from tritflow.synth import synthesize
from tritflow.pnr import (Library, PhysicalVerificationError, RoutingFailure,
                         mock_library, place_and_route)
from tritflow.pnr.lvs import strict_lvs
from .circuits import chain


def test_real_blocked_access_names_net_region_and_remedy(tmp_path):
    library = mock_library()
    cell = library.cells["INV"]
    # Both legal pin landings lie inside an M2 pocket with no channel escape.
    cell.obstructions["M2"] = [[0., 40., cell.width, 44.], [0., 90., cell.width, 94.]]
    with pytest.raises(RoutingFailure) as caught:
        place_and_route(chain(1), library, output_dir=tmp_path,
                        max_expansions=0, ripup_passes=1, run_pdk_drc=False)
    error = caught.value
    assert error.net in str(error) and error.region_um and "Congested" in str(error)
    assert "rows=" in str(error) and "channel_tracks=" in str(error)
    failure = json.loads(next(tmp_path.glob("*.pnr.failure.json")).read_text())
    assert failure["failed_nets"] and failure["region_um"] == error.region_um
    assert not list(tmp_path.glob("*.gds"))


@pytest.mark.parametrize("failure_stage", ["own", "pdk"])
def test_bad_gds_is_quarantined_and_previous_success_preserved(tmp_path, monkeypatch, failure_stage):
    from tritflow.pnr import flow
    library = mock_library()
    good = place_and_route(chain(2), library, output_dir=tmp_path, run_pdk_drc=False)
    before = good.gds_path.read_bytes(), good.json_path.read_bytes()
    original = flow.write_gds
    def faulty(data, library, path):
        layout = original(data, library, path)
        route = layout.cell(f"{data['top']}__routing")
        x = data["die"][0]/2
        if failure_stage == "own":
            # An unenclosed cut is rejected before handing to the PDK deck.
            route.shapes(layout.layer(19, 0)).insert(db.DBox(x, .5, x+1.4, 1.9))
        else:
            # A tiny N-well is invisible to the metal check and must be caught
            # by the actual unmodified PDK device DRC, rather than a mock report.
            route.shapes(layout.layer(140, 0)).insert(db.DBox(x, .5, x+.1, .6))
        layout.write(str(path))
    monkeypatch.setattr(flow, "write_gds", faulty)
    with pytest.raises(PhysicalVerificationError, match="canonical GDS was not published"):
        place_and_route(chain(2), library, output_dir=tmp_path, run_pdk_drc=failure_stage == "pdk")
    assert (good.gds_path.read_bytes(), good.json_path.read_bytes()) == before
    assert list(tmp_path.glob("*.failed.gds"))
    assert not list(tmp_path.glob("*.candidate.gds"))


def test_unused_inputs_need_actual_isolated_labeled_pads(tmp_path):
    if not (CELLS_DIR/"out/library.json").exists():
        pytest.skip("Real library not published")
    # This also regresses the strict comparator's unused-port/supply ambiguity
    # when a TIEZ feeds NOR and one output drives several aliased output BUFs.
    net = synthesize(loads("""module unused_pads(input trit [9:0] a, output trit [4:0] z);
        wire trit w; assign w = a[8] | 1't0;
        assign z[0]=w; assign z[1]=w; assign z[2]=w; assign z[3]=w; assign z[4]=w;
        endmodule"""))
    library = Library.load()
    result = place_and_route(net, library, output_dir=tmp_path)
    subckts = (CELLS_DIR/"out/all.spice").read_text()
    report = strict_lvs(result.gds_path, result.data, net, library, tmp_path/"lvs", subckts)
    assert report["matched"] and report["strict_ports"]
    assert set(report["unused_input_formals_restored"]) == {f"a[{i}]" for i in range(10) if i != 8}
    # JSON still claims this pad exists, but its actual GDS label is missing.
    layout = db.Layout(); layout.read(str(result.gds_path))
    for shape in list(layout.cell(net.top).shapes(layout.layer(49, 0)).each()):
        if shape.is_text() and shape.text.string == "a[0]":
            shape.delete()
    broken = tmp_path/"missing_pad_label.gds"; layout.write(str(broken))
    assert not strict_lvs(broken, result.data, net, library, tmp_path/"bad_lvs", subckts)["matched"]


def test_fuzzer_sources_are_reproducible_and_multiplier_is_arithmetic():
    from examples.fuzz_pnr import random_source, scale_sources
    import numpy as np
    for seed in (0, 10, 49, 74, 99):
        assert random_source(seed) == random_source(seed)
        source, parameters = random_source(seed)
        assert 2 <= parameters["inputs"] <= 12
        assert loads(source).top == f"fuzz_{seed:05d}"
    design = loads(scale_sources()["mul2"], top="mul2")
    vectors = np.array([(a0,a1,b0,b1) for a0 in (-1,0,1) for a1 in (-1,0,1)
                        for b0 in (-1,0,1) for b1 in (-1,0,1)])
    values = design.evaluate({name: vectors[:,i] for i,name in enumerate(("a[0]","a[1]","b[0]","b[1]"))})
    output = sum(values[f"p[{i}]"]*3**i for i in range(4))
    assert np.array_equal(output, (vectors[:,0]+3*vectors[:,1])*(vectors[:,2]+3*vectors[:,3]))
