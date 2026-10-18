"""Internal-M2/V1 barriers, certified free tracks, and off-grid pin rows."""
import json

import klayout.db as db
import pytest

from tritflow.pnr import Library, mock_library, place_and_route
from tritflow.pnr.constraints import m2_obstacles, reflected_rect
from tritflow.pnr.gds import DBU, box, wire_box
from tritflow.pnr.placement import pin_location
from tests.pnr.circuits import chain


def obstructed_library(tmp_path):
    library = mock_library()
    cell = library.cells["INV"]
    # Actual floating metal and a via island inside the mock cell: the router
    # must avoid them even when they lie between its original y coordinates.
    m2 = [13.3, 103.3, 16.7, 121.7]
    cut = [14.3, 111.3, 15.7, 112.7]
    cell.obstructions["M2"] = [m2]
    cell.obstructions["V1"] = [cut]
    cell.free_tracks = {"M2": {"x": [9., 27.], "wire_width": 3.4, "clearance": 2.}}
    layout = db.Layout(); layout.dbu = DBU
    top = layout.create_cell("INV")
    for pin in cell.pins.values():
        for rect in pin["rects"]:
            top.shapes(layout.layer(13, 0)).insert(box(rect))
    top.shapes(layout.layer(20, 0)).insert(box(m2))
    top.shapes(layout.layer(19, 0)).insert(box(cut))
    top.shapes(layout.layer(13, 0)).insert(box([13.3, 110.3, 16.7, 113.7]))
    top.shapes(layout.layer(235, 0)).insert(box([0, 0, cell.width, cell.height]))
    cell.gds = tmp_path/"INV.gds"
    layout.write(str(cell.gds))
    library.validate()
    return library


def test_obstructed_mock_has_clean_drawn_geometry_and_free_transit(tmp_path):
    library = obstructed_library(tmp_path)
    result = place_and_route(chain(5), library, output_dir=tmp_path/"route", rows=3,
                             seed=5, anneal_steps=90)
    assert all(c["clean"] for c in result.data["checks"].values())
    for pl in result.data["placements"]:
        cell = library.cells[pl["cell"]]
        free = [pl["x"]+(cell.width-x if pl["orient"] == "MY" else x) for x in (9., 27.)]
        for wire in result.data["wires"]:
            if wire["layer"] != "M2":
                continue
            x, y0 = wire["points"][0]; _, y1 = wire["points"][-1]
            if pl["x"] < x < pl["x"]+cell.width and max(y0, y1) > pl["y"] and min(y0, y1) < pl["y"]+cell.height:
                assert x in free
            for obstacle in m2_obstacles(cell, pl, library.template):
                if obstacle[0] == obstacle[2]:
                    continue
                assert (db.Region(box(wire_box(wire))).sized(1999) & db.Region(box(obstacle))).is_empty()


def test_via_only_metadata_blocks_its_enclosed_metal(tmp_path):
    library = mock_library()
    cell = library.cells["INV"]
    cell.obstructions["V1"] = [[14.3, 111.3, 15.7, 112.7]]
    obstacles = list(m2_obstacles(cell, {"x": 60., "y": 200., "orient": "MY"}, library.template))
    assert obstacles == [[79.3, 310.3, 82.7, 313.7]]
    assert reflected_rect(cell, {"x": 60., "y": 200., "orient": "MY"}, [13.3, 110.3, 16.7, 113.7]) == obstacles[0]


def test_selects_legal_alternative_access_and_rejects_blocked_pin():
    library = mock_library()
    cell = library.cells["INV"]
    cell.obstructions["M2"] = [[7.3, 58.3, 10.7, 61.7]]
    cell.pins["A"]["access"] = [[9., 60.], [3., 60.]]
    library.validate()
    assert pin_location(cell, "A", {"x": 0., "y": 0., "orient": "R0"}) == (3., 60.)
    assert pin_location(cell, "A", {"x": 0., "y": 0., "orient": "MY"}) == (33., 60.)
    cell.pins["A"]["access"] = [[9., 60.]]
    with pytest.raises(ValueError, match="no access clears"):
        library.validate()


def test_loads_compact_cell_free_m2_metadata(tmp_path):
    source = mock_library()
    (tmp_path/"out/INV").mkdir(parents=True)
    (tmp_path/"template.json").write_text(json.dumps(source.template))
    (tmp_path/"out/library.json").write_text('[{"name":"INV"}]')
    cell = source.cells["INV"]
    (tmp_path/"out/INV/INV.abstract.json").write_text(json.dumps({"name":"INV", "width":cell.width,
        "height":cell.height, "pins":cell.pins, "obstructions":cell.obstructions,
        "free_M2_tracks":{"x":[9.,27.],"wire_width":3.4,"clearance":2.}}))
    loaded = Library.load(tmp_path).cells["INV"]
    assert loaded.free_tracks["M2"]["x"] == [9.,27.]


def test_every_saved_placement_respects_row_current_capacity(tmp_path):
    library = mock_library()
    library.cells["INV"].characterization = {"max_static_current_a": .0008}
    result = place_and_route(chain(20), library, output_dir=tmp_path,
                             anneal_steps=100, history_every=10, seed=19, run_pdk_drc=False)
    limit = 2*.00025*min(y1-y0 for y0, y1 in library.template["rails"].values())
    currents = result.data["power"]["currents_a"]
    assert result.stats["row_count"] == 4
    for snapshot in result.data["history"]:
        for row in {p["row"] for p in snapshot["placements"]}:
            load = sum(currents[p["inst"]] for p in snapshot["placements"] if p["row"] == row)
            assert load <= limit+1e-12
