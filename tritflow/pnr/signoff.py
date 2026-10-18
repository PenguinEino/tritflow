"""Unwaived drawing/LVS → MDP → IP62 checks, matching the local MPW flow.

This is an optional macro qualification, separate from placement/routing. A
macro with naked input gates can pass drawing checks and still fail mask DRC.
No label, warning filter, fake bond-pad marker or waiver turns that into a pass.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import klayout.db as db
import klayout.rdb as rdb

from tritflow import PDK_ROOT
from tritflow.netlist import GateNetlist
from .library import Library
from .lvs import strict_lvs
from .placement import pin_location
from .verify import Index, connectivity, routing_drc


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path, value):
    temporary = path.with_name(path.name+".new")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")
    temporary.replace(path)


def _run(command, directory, label, timeout):
    started = time.perf_counter()
    log = directory/f"{label}.log"
    try:
        result = subprocess.run([str(p) for p in command], cwd=directory,
                                capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        log.write_text(str(error.stdout or "")+str(error.stderr or ""))
        raise RuntimeError(f"Sign-off {label} timed out; inspect {log}") from error
    log.write_text(result.stdout+result.stderr)
    return {"command": [str(p) for p in command], "exit_code": result.returncode,
            "runtime_s": time.perf_counter()-started, "log_path": str(log)}


def _drc(binary, deck, drawing, top, directory, label, timeout):
    report = directory/f"{label}.lyrdb"
    report.unlink(missing_ok=True)
    result = _run([binary, "-b", "-r", deck, "-rd", f"input={drawing}",
        "-rd", f"top_cell={top}", "-rd", f"report={report}"], directory, label, timeout)
    if result["exit_code"] or not report.exists():
        raise RuntimeError(f"Sign-off {label} did not create a valid report; inspect {result['log_path']}")
    root = ET.parse(report).getroot()
    if root.tag != "report-database" or root.find("items") is None:
        raise RuntimeError(f"Not a KLayout DRC report: {report}")
    counts = Counter(item.findtext("category", "unknown").strip("'")
                     for item in root.findall("./items/item"))
    return {**result, "clean": not counts, "violations": sum(counts.values()),
            "categories": dict(counts), "report_path": str(report),
            "policy": "all report items, including warnings and visited items, count as failures"}


def _layout_audit(path, top):
    layout = db.Layout(); layout.read(str(path))
    cell = layout.cell(top)
    if cell is None:
        raise ValueError(f"Sign-off input has no top cell {top}")
    b = cell.dbbox()
    waiver = db.Region(cell.begin_shapes_rec(layout.layer(63, 0)))
    return {"dbu_um": layout.dbu, "top_cells": [c.name for c in layout.top_cells()],
        "bbox_um": [b.left, b.bottom, b.right, b.top],
        "waiver_polygon_count": waiver.size(), "waiver_area_um2": waiver.area()*layout.dbu**2,
        "frame_cells": [c.name for c in layout.each_cell() if c.name in ("OSS_FRAME", "OSS_FRAME_TEG")]}


def _metal_preservation(drawing, mask, top):
    """MDP must preserve contacts and routed conductors as exact regions."""
    before, after = db.Layout(), db.Layout()
    before.read(str(drawing)); after.read(str(mask))
    if before.dbu != after.dbu:
        return {"clean": False, "error": "MDP changed the database unit"}
    differences = {}
    for name, layer in (("CO", 11), ("M1", 13), ("V1", 19), ("M2", 20)):
        a = db.Region(before.cell(top).begin_shapes_rec(before.layer(layer, 0)))
        b = db.Region(after.cell(top).begin_shapes_rec(after.layer(layer, 0)))
        differences[name] = (a ^ b).area()*before.dbu**2
    return {"clean": all(area == 0 for area in differences.values()),
            "xor_area_um2": differences, "method": "independent flattened Region XOR"}


def _floating_gates(mask, report_path, data, netlist, library):
    """Trace WAR06 SG islands through real contacts/M1/V1/M2 to named nets.

    Device channels and resistors are not shorted by this graph. Its purpose is
    to identify the signal attached to each warned gate, not to replace LVS.
    """
    report = rdb.ReportDatabase(); report.load(str(report_path))
    markers = [item for item in report.each_item()
               if report.category_by_id(item.category_id()).name() == "WAR06: Floating SG Detected"]
    if not markers:
        return {"counts": {}, "markers": []}
    layout = db.Layout(); layout.read(str(mask)); top = layout.cell(data["top"])
    layers = {"SG": (8, 0), "CO": (11, 0), "M1": (13, 0), "V1": (19, 0), "M2": (20, 0)}
    polygons = {name: list(db.Region(top.begin_shapes_rec(layout.layer(*pair))).merged().each())
                for name, pair in layers.items()}
    indices = {name: Index(shapes, round(48/layout.dbu)) for name, shapes in polygons.items()}
    offset, size = {}, 0
    for name, shapes in polygons.items():
        offset[name] = size; size += len(shapes)
    parent = list(range(size))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for via, metals in (("CO", ("SG", "M1")), ("V1", ("M1", "M2"))):
        for i, polygon in enumerate(polygons[via]):
            for metal in metals:
                for j in indices[metal].query(polygon.bbox()):
                    if not (db.Region(polygon) & db.Region(polygons[metal][j])).is_empty():
                        parent[find(offset[via]+i)] = find(offset[metal]+j)
    tags = defaultdict(set)
    def tag(layer, x, y, name):
        ix, iy = round(x/layout.dbu), round(y/layout.dbu)
        for hit in indices[layer].query(db.Box(ix-1, iy-1, ix+1, iy+1)):
            tags[find(offset[layer]+hit)].add(name)
    for pin in data["pins"]:
        x0, y0, x1, y1 = pin["rect"]
        tag("M2", (x0+x1)/2, (y0+y1)/2, pin["name"])
    instances = {inst.name: inst for inst in netlist.instances}
    for pl in data["placements"]:
        for pin, name in instances[pl["inst"]].pins.items():
            tag("M1", *pin_location(library.cells[pl["cell"]], pin, pl), name)
    inputs = {p.name for p in netlist.ports if p.dir == "input"}
    details = []
    for marker in markers:
        nets, boxes = set(), []
        for value in marker.each_value():
            if not value.is_polygon():
                continue
            poly = db.Polygon.from_dpoly(value.polygon()*(1/layout.dbu))
            b = value.polygon().bbox(); boxes.append([b.left, b.bottom, b.right, b.top])
            for hit in indices["SG"].query(poly.bbox()):
                if not (db.Region(poly) & db.Region(polygons["SG"][hit])).is_empty():
                    nets.update(tags.get(find(offset["SG"]+hit), ()))
        category = "external_input_gate" if nets and nets <= inputs else "internal_or_unmapped_gate"
        details.append({"classification": category, "nets": sorted(nets), "boxes_um": boxes})
    return {"counts": dict(Counter(d["classification"] for d in details)), "markers": details,
            "method": "flattened mask SG/CO/M1/V1/M2 islands; actual contact overlap; named signal terminals"}


def signoff(result, netlist=None, library=None, *, output_dir=None, pdk_root=PDK_ROOT,
            klayout_binary=None, mpw_template=None, force=False, timeout=180):
    """Run and cache the unmodified local MPW checks on a PnrResult.

    ``clean`` means the macro's drawing/connectivity/LVS and mask checks all
    passed, with zero waiver polygons. ``submission_ready`` additionally needs
    the MPW template precheck (fixed die/frame). Naked external-gate warnings
    remain failures. The inspected MPW flow has no mask-level LVS step, reported
    explicitly as not defined rather than as a successful skipped check.
    """
    started = time.perf_counter()
    source = Path(result.gds_path).resolve()
    top, data = result.data["top"], result.data
    if data.get("library", {}).get("mock"):
        raise ValueError("Manufacturing sign-off requires real device cells, not a mock library")
    if netlist is None:
        netlist = getattr(result, "netlist", None)
    if netlist is None:
        reference_path = source.with_name(f"{top}.json")
        if not reference_path.exists():
            raise ValueError("Sign-off needs the gate reference: pass netlist=... or retain <top>.json beside the GDS")
        netlist = GateNetlist.load(reference_path)
    if isinstance(netlist, (str, Path)):
        netlist = GateNetlist.load(netlist)
    if netlist.top != top:
        raise ValueError("Sign-off reference top differs from the GDS top")
    if library is None:
        library = Library.load(data["library"]["source"])
    elif isinstance(library, (str, Path)):
        library = Library.load(library)
    pdk = Path(pdk_root).expanduser().resolve()
    binary = Path(klayout_binary or shutil.which("klayout") or Path.home()/"bin/klayout/klayout").resolve()
    if not binary.is_file() or timeout <= 0:
        raise ValueError("Sign-off needs an existing KLayout binary and positive timeout")
    tech = pdk/"libs.tech/klayout/tech"
    subckts = Path(library.source)/"out/all.spice"
    files = [source, binary, subckts, Path(library.source)/"template.json", Path(library.source)/"out/library.json"]
    files += [p for group in ("drc", "lvs") for p in (tech/group).rglob("*") if p.is_file()]
    files += [cell.gds for cell in library.cells.values() if cell.gds]
    files += list((Path(library.source)/"out").glob("*/*.abstract.json"))
    files += [Path(__file__), Path(__file__).with_name("lvs.py"), Path(__file__).with_name("verify.py")]
    template = Path(mpw_template).expanduser().resolve() if mpw_template else None
    if template:
        files += [template/"scripts/pre_check.py", template/".github/workflows/check.yml", template/"info.yaml"]
    inputs = {str(p): _hash(p) for p in sorted(set(files))}
    state = {"files": inputs, "top": top, "netlist": json.loads(netlist.to_json()),
             "pnr_data_sha256": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}
    fingerprint = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    out = Path(output_dir or source.parent/"signoff").resolve(); out.mkdir(parents=True, exist_ok=True)
    summary_path = out/"signoff.summary.json"
    if not force and summary_path.exists():
        try:
            previous = json.loads(summary_path.read_text())
        except (json.JSONDecodeError, OSError):
            previous = {}
        if previous.get("fingerprint") == fingerprint and previous.get("artifacts"):
            try:
                if all(_hash(path) == digest for path, digest in previous["artifacts"].items()):
                    return {**previous, "cache_hit": True}
            except FileNotFoundError:
                pass
    run_dir = out/"runs"/fingerprint[:16]; run_dir.mkdir(parents=True, exist_ok=True)
    # All decks execute on copies, with all their relative includes intact.
    snapshot = run_dir/"pdk/libs.tech/klayout/tech"
    for group in ("drc", "lvs"):
        shutil.copytree(tech/group, snapshot/group, dirs_exist_ok=True)
    drawing = run_dir/f"{top}.drawing.gds"; shutil.copy2(source, drawing)
    mask = run_dir/f"{top}.ip62.gds"
    drawing_check = _drc(binary, snapshot/"drc/run.drc", drawing, top, run_dir, "drawing_drc", timeout)
    own = {"connectivity": connectivity(drawing, data, netlist, library),
           "routing_drc": routing_drc(drawing, data, library)}
    lvs_started = time.perf_counter()
    drawing_lvs = strict_lvs(drawing, data, netlist, library, run_dir/"drawing_lvs", subckts.read_text(),
                            pdk=run_dir/"pdk", executable=binary, timeout=timeout)
    drawing_lvs.pop("log", None)
    drawing_lvs["runtime_s"] = time.perf_counter()-lvs_started
    _write(run_dir/"drawing_lvs.summary.json", drawing_lvs)
    mask.unlink(missing_ok=True)
    mdp = _run([binary, "-b", "-r", snapshot/"drc/run_mdp.drc", "-rd", f"input={drawing}",
        "-rd", f"cellname={top}", "-rd", f"output={mask}"], run_dir, "mdp", timeout)
    if mdp["exit_code"] or not mask.exists():
        raise RuntimeError(f"MDP failed to generate mask GDS; inspect {mdp['log_path']}")
    mdp.update(completed=True, output_path=str(mask), output_sha256=_hash(mask),
               metal_preservation=_metal_preservation(drawing, mask, top))
    mask_check = _drc(binary, snapshot/"drc/run_IP62.drc", mask, top, run_dir, "mask_drc", timeout)
    audit = _layout_audit(drawing, top)
    mask_audit = _layout_audit(mask, top)
    attribution = _floating_gates(mask, mask_check["report_path"], data, netlist, library)
    precheck = {"defined": bool(template), "clean": None, "reason": "No MPW template supplied; full-chip frame precheck not run"}
    if template:
        script = run_dir/"pre_check.py"; shutil.copy2(template/"scripts/pre_check.py", script)
        precheck = _run([sys.executable, script, "--top", top, drawing], run_dir, "mpw_precheck", timeout)
        precheck.update(defined=True, clean=precheck["exit_code"] == 0,
                        template_path=str(template), expected_bbox_um=[-1250., -1250., 1250., 1250.],
                        frame_present=bool(audit["frame_cells"]))
    clean = (drawing_check["clean"] and drawing_lvs["matched"] and mask_check["clean"]
             and mdp["metal_preservation"]["clean"]
             and all(c["clean"] for c in own.values()) and audit["waiver_polygon_count"] == 0
             and mask_audit["waiver_polygon_count"] == 0)
    stable = all(_hash(path) == digest for path, digest in inputs.items())
    if not stable:
        raise RuntimeError("Sign-off inputs changed during the run; rerun after the publication settles")
    report = {"schema": "tritflow.signoff.v1", "top": top, "scope": "unwaived macro drawing/LVS, MDP and IP62 mask DRC",
        "clean": bool(clean), "submission_ready": bool(clean and precheck["clean"]), "cache_hit": False,
        "fingerprint": fingerprint, "inputs": state, "drawing_audit": audit, "mask_audit": mask_audit,
        "drawing_drc": drawing_check, "drawing_lvs": drawing_lvs, "self_checks": own,
        "mdp": mdp, "mask_drc": mask_check, "floating_gate_attribution": attribution,
        "mask_lvs": {"defined": False, "matched": None,
            "reason": "The inspected MPW workflow and prior submission qualify drawing LVS, then MDP and mask DRC; no mask LVS step is defined"},
        "mpw_precheck": precheck, "runtime_s": time.perf_counter()-started,
        "summary_path": str(summary_path)}
    outputs = [p for p in run_dir.rglob("*") if p.is_file()]
    report["artifacts"] = {str(path): _hash(path) for path in outputs}
    _write(summary_path, report)
    return report
