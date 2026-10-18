"""Publication gates, unchanged source, embedded figures and small-file scope."""

from base64 import b64encode
import importlib.util
import io
import json
import re
from pathlib import Path

import nbformat
from PIL import Image
import pytest


ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("submission_builder",ROOT/"submission/build_submission.py")
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def fixture_notebook(tmp_path):
    """Explicit unit fixture; real EDA execution is checked on the actual payload."""
    document=nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell("# Unit fixture",id="intro"),
        nbformat.v4.new_code_cell("print('unit fixture')",id="code")])
    source=tmp_path/"source.ipynb";nbformat.write(document,source)
    document.cells[1].execution_count=1
    stream=io.BytesIO();Image.new("RGB",(2,2),"white").save(stream,format="PNG")
    data={"image/png":b64encode(stream.getvalue()).decode(),"text/html":"<table><tr><td>fixture</td></tr></table>"}
    document.cells[1].outputs=[nbformat.v4.new_output("display_data",data=data) for _ in range(8)]
    return document,source


def test_rejects_unexecuted_changed_or_failed_evidence(tmp_path):
    document,source=fixture_notebook(tmp_path)
    assert builder.validate(document,source)["png_outputs"]==8
    document.cells[1].execution_count=None
    with pytest.raises(ValueError,match="executed"):builder.validate(document,source)
    document.cells[1].execution_count=1
    document.cells[1].source="print('changed')"
    with pytest.raises(ValueError,match="changed"):builder.validate(document,source)
    document.cells[1].source="print('unit fixture')"
    document.cells[1].outputs.append(nbformat.v4.new_output("error",ename="RuntimeError",evalue="failed",traceback=[]))
    with pytest.raises(ValueError,match="failed execution"):builder.portable_outputs(document,{})


def test_native_svg_gallery_is_embedded_without_local_assets():
    svg=(ROOT/"notebook/assets/schematics/INV.svg").read_bytes()
    data=b64encode(svg).decode()
    html=f'<img src="data:image/svg+xml;base64,{data}" alt="INV taped-out schematic">'
    output,=builder.gallery_outputs(html)
    assert output.data["image/svg+xml"].encode()==svg
    assert "image/png" in output.data and "INV" in output.data["text/plain"]
    with pytest.raises(ValueError,match="gallery markup"):builder.gallery_outputs("<img>")


def test_package_hashes_size_identity_and_allowlist(tmp_path):
    document,source=fixture_notebook(tmp_path)
    team={"team_name":"[TEAM]", "authors":[{"name":"[AUTHOR_NAME]","affiliation":"[AFFILIATION]","email":"[EMAIL]"}],
          "representative":"[REPRESENTATIVE]", "attendance_and_poster":"[CONFIRM]",
          "asset_rights_confirmation":"[CONFIRM]"}
    target=tmp_path/"payload"
    builder.package(document,source,target,team,{"tools":{"python":"unit-test"}})
    info=builder.check(target,source)
    assert info["file_count"]==8
    assert info["total_bytes"]==sum(p.stat().st_size for p in target.iterdir())
    assert "[AUTHOR_NAME]" in (target/"README.md").read_text()
    assert "[AFFILIATION]" in document.cells[0].source and "[EMAIL]" in document.cells[0].source
    assert (target/"LICENSE").read_bytes()==(ROOT/"LICENSE").read_bytes()
    assert (target/"NOTICE").read_bytes()==(ROOT/"NOTICE").read_bytes()
    (target/"README.md").write_text("changed")
    with pytest.raises(ValueError,match="hash mismatch"):builder.check(target,source)


def test_incomplete_or_stale_raw_capture_is_not_reused(tmp_path):
    document,source=fixture_notebook(tmp_path)
    raw=tmp_path/"raw.ipynb"
    document.metadata["tritflow_submission_capture"]={"completed":False,"source_sha256":builder.digest(source)}
    nbformat.write(document,raw)
    with pytest.raises(ValueError,match="incomplete"):builder.use_executed(raw,source)
    document.metadata.tritflow_submission_capture.completed=True
    document.metadata.tritflow_submission_capture.source_sha256="0"*64
    nbformat.write(document,raw)
    with pytest.raises(ValueError,match="different source"):builder.use_executed(raw,source)


def test_pitch_has_three_sentences_and_deadline_is_current():
    pitch=builder.read_template("PITCH.md").split("\n\n",1)[1]
    assert len([s for s in pitch.split(".") if s.strip()])==3
    checklist=builder.read_template("CHECKLIST.md")
    assert "2026-10-31 at 11:59 AM Pacific" in checklist
    assert "ISSCC27/submitted_notebooks/TritFlow/" in checklist
    assert "superseded" in checklist and "2025" in checklist


def test_capture_commit_uses_execution_output(tmp_path):
    document,_=fixture_notebook(tmp_path)
    assert builder.captured_commit(document) is None
    document.cells[1].outputs.append(nbformat.v4.new_output("stream",name="stdout",
        text="Source: /unit/test commit="+"a"*40+"\n"))
    assert builder.captured_commit(document)=="a"*40
    assert builder.has_placeholders({"authors":[{"name":"[AUTHOR_NAME]"}]})
    assert not builder.has_placeholders({"authors":[{"name":"Unit test author"}]})


def test_actual_payload_has_readable_embedded_evidence():
    info=builder.check(builder.DESTINATION,builder.SOURCE)
    assert info["file_count"]==8 and info["total_bytes"] < 8*1024*1024
    document=nbformat.read(builder.DESTINATION/"tritflow_tr1um.ipynb",as_version=4)
    for cell in document.cells:
        for output in cell.get("outputs",[]):
            data=output.get("data",{})
            assert not any(key.startswith("application/vnd.plotly") for key in data)
            assert "<script" not in data.get("text/html","").lower()
            if "image/png" in data:
                from base64 import b64decode
                with Image.open(io.BytesIO(b64decode(data["image/png"]))) as image:
                    assert image.width >= 500 and image.height >= 100
                    image.verify()


def test_author_identity_matches_integrator_record_and_asset_authorization():
    text = (ROOT/"docs/author.md").read_text()
    fields = {m[1].lower():" ".join(m[2].split()) for m in
              re.finditer(r"^- (Name|Affiliation|Status|Email|GitHub): (.*(?:\n  .*)*)",text,re.M)}
    team = json.loads((ROOT/"submission/team.json").read_text())
    assert team["authors"] == [fields]
    assert team["representative"] == fields["name"]
    readme = builder.render_readme(team)
    for value in fields.values(): assert value in readme
    assert "releases the derived assets" in readme and "Apache-2.0" in readme
    assert not {"phone", "telephone", "tel"} & team.keys()
    assert "confirm the rights field" not in readme
