"""Execute the current notebook and build a small, readable Code-a-Chip payload.

Only ISSCC27/submitted_notebooks/TritFlow is intended for the eventual PR.
Saved plots are real Plotly PNG renders; SVG gallery outputs get native SVG/PNG
fallbacks. No numerical results are invented or copied into Markdown templates.
The local source notebook and Colab bootstrap are never rewritten. Git use is
read-only; this program does not submit, commit, clone or push anything.
"""

from __future__ import annotations


import argparse
from base64 import b64decode, b64encode
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
from capture import CAPTURE_CODE, SETUP_CODE
sys.path.insert(0,str(ROOT))
SOURCE = ROOT/"notebook/v3/tritflow_en.ipynb"
JAPANESE = ROOT/"notebook/v3/tritflow_ja.ipynb"
DESTINATION = HERE/"ISSCC27/submitted_notebooks/TritFlow"
COMMON_FILES = {"README.md", "LICENSE", "NOTICE", "ABSTRACT.md", "PITCH.md", "CHECKLIST.md", "build-info.json"}
NOTEBOOK_FILES = {"tritflow_en.ipynb", "tritflow_ja.ipynb"}
FILES = COMMON_FILES | NOTEBOOK_FILES
LIMIT_BYTES = 12*1024*1024  # own packaging budget for two languages, not an official limit


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_template(name):
    return (HERE/"templates"/name).read_text()


def authors_table(team):
    def safe(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "| Author | Affiliation | Email |\n|---|---|---|\n"+"\n".join(
        "| "+" | ".join(safe(author[k]) for k in ("name", "affiliation", "email"))+" |"
        for author in team["authors"])


def has_placeholders(value):
    if isinstance(value,dict): return any(has_placeholders(v) for v in value.values())
    if isinstance(value,list): return any(has_placeholders(v) for v in value)
    return isinstance(value,str) and bool(re.search(r"\[[A-Z][A-Z_ ]*\]",value))


def author_details(team):
    return "\n\n".join("\n".join(str(author[k]) if k == "status" else
        f'GitHub: [{author[k]}](https://github.com/{author[k]}).'
        for k in ("status", "github") if author.get(k)) for author in team["authors"])


def render_readme(team, values=None):
    text = read_template("README.md")
    for key, value in {"TEAM_NAME":team["team_name"], "AUTHORS_TABLE":authors_table(team),
                       "REPRESENTATIVE":team["representative"], "ATTENDANCE":team["attendance_and_poster"],
                       "ASSET_RIGHTS":team["asset_rights_confirmation"],
                       "AUTHOR_DETAILS":author_details(team),
                       "COLAB_RUN_NOTE":"Saved outputs were executed locally; this v3 package has no claimed real-Colab Run-all verification."}.items():
        text = text.replace("{{"+key+"}}",str(value))
    return render(text, values or preview_values())


def render(text, values):
    for key, value in values.items():
        text = text.replace("{{"+key+"}}", str(value))
    if re.search(r"\{\{[^}]+\}\}", text):
        raise ValueError("unresolved submission template placeholder")
    return text


def preview_values():
    """Honest defaults for template previews, never numerical result stand-ins."""
    return {"RESULTS":"No executed result record was supplied for this preview.",
            "RESULTS_SENTENCE":"Numerical results are generated only from an executed notebook.",
            "CHAPTER6_LINKS":"links available when packaged",
            "PACKAGE_STATUS":"Development preview; inspect build-info.json before filing.",
            "NOTEBOOKS":"Notebook links are generated when the package is built.",
            "COLAB_URL":"https://colab.research.google.com/", "RUNTIME":"Recommended runtime pins are in notebook/setup_pins.json.",
            "RULES_DATE": "2026-10-29", "RULES_COMMIT":"611b9d712ced9dd67b8aa0855ede44717579adbf"}


def tool_version(command):
    result = subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
    return (result.stdout+result.stderr).strip()


def release_status(source):
    """Read local release objects without fetching or changing git state."""
    document=json.loads(Path(source).read_text())
    setup=next(("".join(c["source"]) for c in document["cells"] if "SOURCE_REF = " in "".join(c.get("source", ""))), "")
    match=re.search(r'SOURCE_REF = os.environ.get\("TRITFLOW_REF", "([0-9a-f]{40})"\)',setup)
    if not match: raise ValueError("Submission SOURCE_REF must be a full immutable Git commit")
    ref=match[1]
    result=subprocess.run(["git","-C",str(ROOT),"rev-parse","--verify",ref+"^{commit}"],
                          capture_output=True,text=True)
    info={"default_ref":ref,"commit":result.stdout.strip() if not result.returncode else None,
          "matches_source_notebook":False,"missing_required_helpers":[]}
    if info["commit"]:
        source_path = Path(source).relative_to(ROOT).as_posix()
        notebook=subprocess.run(["git","-C",str(ROOT),"show",ref+":"+source_path],capture_output=True)
        def identity(raw):
            # Stamping the containing implementation commit must not require
            # a notebook to contain its own Git hash (an impossible fixed point).
            # The stamp also appears in pinned asset URLs, so every occurrence
            # of the notebook's own SOURCE_REF is normalized.
            document=json.loads(raw)
            for cell in document["cells"]:
                cell["source"] = "".join(cell["source"])
            stamp=re.search(r'SOURCE_REF = os.environ.get\("TRITFLOW_REF", "([0-9a-f]{40})"\)',
                            "".join(cell["source"] for cell in document["cells"]))
            for cell in document["cells"]:
                if stamp:
                    cell["source"]=cell["source"].replace(stamp[1], "<implementation commit>")
            return document
        info["matches_source_notebook"]=(not notebook.returncode and identity(notebook.stdout)==identity(Path(source).read_bytes()))
        for name in ("notebook/runtime_support.py", "notebook/views.py", "tritflow/flow.py", "notebook/setup_pins.json"):
            test=subprocess.run(["git","-C",str(ROOT),"cat-file","-e",ref+":"+name],capture_output=True)
            if test.returncode: info["missing_required_helpers"].append(name)
    info["compatible"] = bool(info["matches_source_notebook"] and not info["missing_required_helpers"])
    return info


def release_notice(info):
    if info.get("compatible"):
        return f'Immutable source commit `{info["commit"]}` matches the packaged notebook, allowing its commit-stamp line (local git-object check).'
    return (f"The local source-ref check found `{info.get('default_ref','unavailable')}` at "
            f"`{info.get('commit') or 'unavailable'}`. The local notebook differs from that pinned release. "
            "Build-info.json records the checked source-ref details. "
            "Before filing, the integrator must publish a source pin compatible with the final notebooks.")


def captured_commit(document):
    """Use the notebook's actual bootstrap print, not a later integrator commit."""
    evidence = captured_evidence(document)
    if evidence:
        return evidence.get("runtime_commit")
    for cell in document.cells:
        for output in cell.get("outputs",[]):
            if output.get("output_type") == "stream":
                match=re.search(r"Source: .*?commit=([0-9a-f]{40})\b",output.text)
                if match: return match[1]
    return None


def captured_evidence(document):
    for cell in document.cells:
        if cell.id == "submission-evidence":
            for output in cell.get("outputs", []):
                evidence = output.get("data", {}).get("application/json")
                if evidence is not None:
                    return evidence
    return {}


def execute(source, workdir, timeout):
    """Use an ordinary Jupyter kernel; stop on failures and retain raw evidence."""
    import nbformat
    from nbclient import NotebookClient

    document = nbformat.read(source,as_version=4)
    nbformat.validate(document)
    if any(c.get("outputs") for c in document.cells):
        # Existing outputs never substitute for an actual execution here.
        for cell in document.cells:
            if cell.cell_type == "code":
                cell.outputs, cell.execution_count = [], None
    setup = nbformat.v4.new_code_cell(SETUP_CODE, id="submission-render-setup")
    document.cells.insert(0,setup)
    document.cells.append(nbformat.v4.new_code_cell(CAPTURE_CODE, id="submission-evidence"))
    environment = os.environ.copy()
    environment.update(TRITFLOW_ROOT=str(ROOT),TRITFLOW_NOTEBOOK_BUILD=str(workdir/"flow"),
                       TRITFLOW_SUBMISSION_WORKDIR=str(workdir),
                       PYTHONDONTWRITEBYTECODE="1",QT_QPA_PLATFORM="offscreen")
    environment.pop("TRITFLOW_NOTEBOOK_HEADLESS",None)
    client = NotebookClient(document,timeout=timeout,kernel_name="python3",allow_errors=False,
                            resources={"metadata":{"path":str(ROOT)}},store_widget_state=False)
    client.on_cell_start = lambda cell,cell_index: print(f"Executing {cell_index}: {cell.id}",flush=True)
    started = time.monotonic()
    started_utc = datetime.now(timezone.utc).isoformat()
    raw = workdir/"executed.raw.ipynb"
    succeeded = False
    try:
        client.execute(env=environment)
        succeeded = True
    finally:
        # A failed notebook stays outside the PR payload and is never a pass.
        document.metadata["tritflow_submission_capture"] = {
            "source_sha256":digest(source),"elapsed_s":time.monotonic()-started,
            "renderer":"png", "completed":succeeded,
            "source_path":str(source.relative_to(ROOT)),
            "started_utc":started_utc, "completed_utc":datetime.now(timezone.utc).isoformat()
        }
        nbformat.write(document,raw)
    document.cells.pop(0)
    if document.metadata.tritflow_submission_capture.source_sha256 != digest(source):
        raise RuntimeError("source notebook changed during execution; regenerate")
    return document, raw


def use_executed(path, source):
    import nbformat
    document = nbformat.read(path,as_version=4)
    capture = document.metadata.get("tritflow_submission_capture",{})
    if not capture.get("completed") or capture.get("source_sha256") != digest(source):
        raise ValueError("raw execution is incomplete or belongs to a different source notebook")
    if document.cells and document.cells[0].id == "submission-render-setup":
        document.cells.pop(0)
    validate(document, source, require_evidence=True, require_static=False)
    return document


def gallery_outputs(html):
    """Replace repeated light/dark data-URL markup with readable native images."""
    import cairosvg
    import nbformat
    images = []
    selected = re.search(r'data-schematic-selected="([^"]+)"',html)
    pattern = r'<img src="data:image/svg\+xml;base64,([^"]+)" alt="([^"]+)"'
    for data, title in re.findall(pattern,html):
        if "taped-out schematic" not in title:
            continue
        if selected and title != selected[1]+" taped-out schematic":
            continue  # static reading keeps the selected drawing; rerun to expand others
        svg = b64decode(data).decode()
        png = cairosvg.svg2png(bytestring=svg.encode(),output_width=1100)
        images.append(nbformat.v4.new_output("display_data",data={
            "image/svg+xml":svg,"image/png":b64encode(png).decode(),
            "text/plain":unescape(title)+" — exported historical topology, light theme"},metadata={}))
    if not images:
        raise ValueError("gallery markup changed; refusing to drop its schematic outputs")
    return images


def selector_outputs(html):
    """A static reader keeps the initially selected input view of the trit selector."""
    import cairosvg
    import nbformat
    view = re.search(r'<div data-key="[^"]+" style="display:block">.*?base64,([^"]+)"',html,flags=re.S)
    if not view:
        raise ValueError("trit selector markup changed; refusing to drop its schematic")
    svg = b64decode(view[1]).decode()
    png = cairosvg.svg2png(bytestring=svg.encode(),output_width=1100)
    return [nbformat.v4.new_output("display_data",data={
        "image/svg+xml":svg,"image/png":b64encode(png).decode(),
        "text/plain":"Mapped half adder, initial input selection; rerun for the selector"},metadata={})]


def gds_viewer_outputs(html):
    """Keep the viewer's real KLayout overview when packaging without a kernel."""
    from html.parser import HTMLParser
    import nbformat

    class Overview(HTMLParser):
        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            if tag == "img" and values.get("data-gds-overview") == "1":
                self.image = values.get("src", "")
                self.title = values.get("alt", "KLayout GDS overview")

    parser = Overview()
    parser.feed(html)
    image = getattr(parser, "image", "")
    prefix = "data:image/png;base64,"
    if not image.startswith(prefix):
        raise ValueError("GDS viewer markup changed; refusing to drop its overview")
    png = b64decode(image[len(prefix):], validate=True)
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("GDS viewer overview is not a PNG")
    png = optimize_png(png)
    return [nbformat.v4.new_output("display_data", data={
        "image/png": b64encode(png).decode(),
        "text/plain": parser.title + "; rerun in Colab for live pan/zoom"}, metadata={})]


def optimize_png(content):
    """Compress identical pixels; discard an alpha channel only if fully opaque."""
    from PIL import Image
    with Image.open(io.BytesIO(content)) as picture:
        if picture.mode == "RGBA" and picture.getextrema()[-1] == (255, 255):
            picture = picture.convert("RGB")
        buffer = io.BytesIO()
        picture.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def portable_outputs(document, replacements, snapshot_dir=None):
    """Keep actual values; normalize machine paths and remove active/web payloads."""
    def normalize(value):
        if isinstance(value, dict):
            return {key:normalize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [normalize(item) for item in value]
        if isinstance(value, str):
            for old, new in replacements.items():
                value = value.replace(old, new)
        return value

    active = []
    for cell in document.cells:
        if cell.cell_type != "code":
            continue
        outputs = []
        for output in cell.outputs:
            if output.output_type == "error":
                raise ValueError("failed execution cannot be packaged")
            data = output.get("data",{})
            if "application/json" in data:
                data["application/json"] = normalize(data["application/json"])
            html = data.get("text/html","")
            if 'data-gds-viewer="1"' in html:
                outputs.extend(gds_viewer_outputs(html))
                continue
            if snapshot_dir is not None and ("<script" in html.lower() or "<svg" in html
                                             or "data:image/svg+xml;base64," in html):
                # v3 controls initialize schematics, PNR replay and Plotly in
                # JavaScript. Freeze their actual selected state in Chromium.
                active.append((output, html))
                outputs.append(output)
                continue
            if 'data-cell-cards="1"' in html:
                # Keep the cards; static readers get PNG schematics instead of SVG data links.
                import cairosvg
                def svg_png(match):
                    png = cairosvg.svg2png(bytestring=b64decode(match[1]),output_width=1100)
                    return 'data:image/png;base64,'+b64encode(png).decode()
                html = re.sub(r'<script>.*?</script>','',html,flags=re.S)        # static: every card visible
                html = re.sub(r'<div data-tabs[^>]*>.*?</div>','',html,count=1,flags=re.S)
                html = re.sub(r' onclick="[^"]*"','',html)
                data['text/html'] = re.sub(r'data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)',svg_png,html)
                outputs.append(output)
                continue
            if 'data-trit-selector="1"' in html:
                outputs.extend(selector_outputs(html))
                continue
            if "data:image/svg+xml;base64," in html:
                outputs.extend(gallery_outputs(html))
                continue
            if '<svg' in html:
                # Optional mapped schematics stay inside their Details block.
                # GitHub's HTML sanitizer may omit inline SVG, so embed a PNG
                # in that same block without unfolding duplicate main views.
                import cairosvg
                def svg_fallback(match):
                    png = cairosvg.svg2png(bytestring=match[0].encode(),output_width=1100)
                    return '<img alt="Mapped schematic" src="data:image/png;base64,'+b64encode(png).decode()+'">'
                data['text/html'] = re.sub(r'<svg\b.*?</svg>',svg_fallback,html,flags=re.S)
            for key in ("text/plain","text/html"):
                if key in data:
                    for old,new in replacements.items():
                        data[key] = data[key].replace(old,new)
            if output.output_type == "stream":
                for old,new in replacements.items():
                    output.text = output.text.replace(old,new)
            if "image/svg+xml" in data and "image/png" not in data:
                # Public SCHEM figures expose native SVG. Preserve that vector
                # and add a static fallback, without changing any circuit data.
                import cairosvg
                png = cairosvg.svg2png(bytestring=data["image/svg+xml"].encode(),output_width=1100)
                data["image/png"] = b64encode(png).decode()
            if any(key.startswith("application/vnd.plotly") for key in data):
                raise ValueError("capture must use static PNG, not large interactive Plotly bundles")
            if "<script" in html.lower():
                raise ValueError("active HTML output needs a static fallback before packaging")
            outputs.append(output)
        cell.outputs = outputs
        cell.metadata.pop("execution",None)
    document.metadata.pop("widgets",None)
    if active:
        from static_html import snapshots
        rendered = snapshots([html for _, html in active], snapshot_dir)
        for (output, _), data in zip(active, rendered, strict=True):
            output["data"] = data
            output["metadata"] = {}
    for cell in document.cells:
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            if "image/png" in data:
                data["image/png"] = b64encode(optimize_png(b64decode(data["image/png"]))).decode()


def embed_assets(document):
    """Bundle pinned project Markdown images without changing numerical outputs."""
    import cairosvg
    records = []
    pattern = re.compile(r"https://(?:raw\.githubusercontent\.com/PenguinEino/tritflow/|cdn\.jsdelivr\.net/gh/PenguinEino/tritflow@)([0-9a-f]{40})/([^\s\)\"<>]+\.(?:png|svg))")
    def replace(match):
        ref, path = match.groups()
        if ".." in Path(path).parts:
            raise ValueError("unsafe pinned figure path")
        content = subprocess.check_output(["git", "-C", str(ROOT), "show", ref+":"+path])
        records.append({"url":match[0], "source_commit":ref, "path":path,
                        "sha256":sha256(content).hexdigest()})
        if path.endswith("svg"):
            content = cairosvg.svg2png(bytestring=content, scale=2)
        return "data:image/png;base64,"+b64encode(optimize_png(content)).decode()
    for cell in document.cells:
        if cell.cell_type == "markdown":
            cell.source = pattern.sub(replace, cell.source)
    return records


def validate(document, source, require_evidence=False, require_static=True):
    """Check saved evidence and exact original code, allowing front matter only."""
    import nbformat
    nbformat.validate(document)
    expected = nbformat.read(source,as_version=4)
    if document.metadata.get("tritflow_submission_assets"):
        records = embed_assets(expected)
        if records != document.metadata.tritflow_submission_assets:
            raise ValueError("pinned Markdown asset provenance changed")
    original = {c["id"]:(c["cell_type"], c["source"]) for c in expected["cells"]}
    known = {"submission-identity", "submission-evidence", "submission-references", "submission-capture-details"}
    for cell in document.cells:
        if cell.id in original and (cell.cell_type, cell.source) != original[cell.id]:
            raise ValueError(f"source cell changed: {cell.id}")
        if cell.id not in original and cell.id not in known:
            raise ValueError(f"unexpected added notebook cell: {cell.id}")
    if not set(original) <= {cell.id for cell in document.cells}:
        raise ValueError("missing source notebook cells")
    if [c.id for c in document.cells if c.id in original] != list(original):
        raise ValueError("source notebook cell order changed")
    code = [c for c in document.cells if c.cell_type=="code"]
    if not code or any(c.execution_count is None for c in code):
        raise ValueError("every source code cell must have executed")
    outputs = [o for c in code for o in c.outputs]
    if any(o.output_type=="error" for o in outputs):
        raise ValueError("error output in submission")
    images = sum("image/png" in o.get("data",{}) for o in outputs)
    embedded = sum(c.source.count('data:image/png;base64,') for c in document.cells if c.cell_type=='markdown')
    tables = sum(o.get("data",{}).get("text/html","").count("<table") for o in outputs)
    if require_static and (images+embedded < 8 or tables < 1):
        raise ValueError("saved figures/tables are incomplete")
    if require_evidence:
        evidence = captured_evidence(document)
        if not evidence or evidence.get("schema_version") != 1:
            raise ValueError("missing executed submission evidence")
        if not re.fullmatch(r"[0-9a-f]{40}", evidence.get("runtime_commit", "")):
            raise ValueError("missing immutable runtime source commit")
        if not re.fullmatch(r"[0-9a-f]{40}", evidence.get("source_ref", "")):
            raise ValueError("missing pinned bootstrap source commit")
        capture = document.metadata.get("tritflow_submission_capture", {})
        if not capture.get("completed") or capture.get("source_sha256") != digest(source):
            raise ValueError("source notebook changed or execution was incomplete")
        front = [cell for cell in document.cells[:2] if cell.id == "submission-identity"]
        if front and (has_placeholders(front[0].source) or "{{" in front[0].source):
            raise ValueError("placeholder in notebook author information")
        from results import result_values, chapter6
        result_values(evidence)
        chapter6(document)
    return {"code_cells":len(code),"saved_outputs":len(outputs),"png_outputs":images,
            "embedded_paper_figures":embedded,"html_tables":tables}


def selected_sources(source=None, japanese=JAPANESE):
    """Prefer EN, package JA once, and never relabel a Japanese fallback."""
    japanese = Path(japanese).resolve()
    primary = Path(source).resolve() if source is not None else (SOURCE if SOURCE.is_file() else japanese)
    if not primary.is_file():
        raise ValueError(f"missing primary notebook: {primary}")
    name = "tritflow_ja.ipynb" if primary == japanese or primary.stem.endswith("_ja") else "tritflow_en.ipynb"
    sources = {name:primary}
    if name != "tritflow_ja.ipynb":
        if not japanese.is_file():
            raise ValueError(f"missing Japanese companion: {japanese}")
        sources["tritflow_ja.ipynb"] = japanese
    return sources


def workspace(path):
    """Contain disposable kernel/browser/sizing files within this stream's tree."""
    path = Path(path).resolve()
    if not path.is_relative_to(HERE):
        raise ValueError("build workdir must be inside submission/")
    locations = {"TMPDIR":"tmp", "XDG_CACHE_HOME":"cache", "MPLCONFIGDIR":"cache/matplotlib",
                 "JUPYTER_DATA_DIR":"jupyter/data", "JUPYTER_RUNTIME_DIR":"jupyter/runtime",
                 "JUPYTER_CONFIG_DIR":"jupyter/config", "IPYTHONDIR":"ipython"}
    for variable, relative in locations.items():
        # Chromium's profile includes Unix sockets with a short path limit.
        folder = HERE/".build/tmp" if variable == "TMPDIR" else path/relative
        folder.mkdir(parents=True, exist_ok=True)
        os.environ[variable] = str(folder)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    tempfile.tempdir = os.environ["TMPDIR"]


def packaging_tools():
    """These versions describe export, separately from kernel-captured EDA tools."""
    versions = {p:importlib.metadata.version(p) for p in
                ("Pillow", "nbformat", "nbclient", "kaleido", "choreographer", "CairoSVG")}
    versions["python"] = platform.python_version()
    browser = shutil.which("google-chrome") or shutil.which("chromium")
    if browser:
        versions["browser"] = tool_version([browser, "--version"])
    return versions


def readiness(records):
    """A captured preview cannot satisfy the final source/evaluation gate."""
    blockers = []
    if "tritflow_en.ipynb" not in records:
        blockers.append("English primary notebook is not yet available; this is a Japanese development preview.")
    for name, record in records.items():
        evidence, evaluation = record["results"], record["evaluation"]
        if not record["release"]["compatible"]:
            blockers.append(f"{name}: pinned release does not contain the same notebook and required helpers.")
        if evidence["runtime_commit"] != evidence["source_ref"]:
            blockers.append(f"{name}: local execution used a different commit from the bootstrap pin.")
        if evidence["runtime_commit"] != evidence.get("runtime_commit_at_end", evidence["runtime_commit"]):
            blockers.append(f"{name}: repository commit changed during execution.")
        changed = [*evidence.get("tracked_working_changes_at_execution", []),
                   *evidence.get("untracked_runtime_sources_at_execution", [])]
        if any(path.startswith(("tritflow/", "notebook/", "cells/", "examples/", "results/")) for path in changed):
            blockers.append(f"{name}: execution used unpublished changes to runtime inputs.")
        if not evaluation["executed_cell_ids"]:
            blockers.append(f"{name}: chapter 6 evaluation has not executed in this source revision.")
        elif not evaluation["tables"]:
            blockers.append(f"{name}: chapter 6 has no executed tabular evaluation summary.")
    return blockers


def package(documents, sources, destination, team, info):
    """Write both executed notebooks and render claims only from captured outputs."""
    import nbformat
    from results import chapter6, result_values

    if has_placeholders(team):
        raise ValueError("team information contains placeholders")
    if set(documents) != set(sources) or not set(documents) <= NOTEBOOK_FILES:
        raise ValueError("notebook inputs do not match the bilingual allowlist")
    destination.mkdir(parents=True, exist_ok=True)
    expected_files = COMMON_FILES | set(documents)
    if {p.name for p in destination.iterdir()} - expected_files:
        raise ValueError("unexpected files in payload")
    primary = info.get("primary_notebook", next(iter(documents)))
    info.update(schema_version=3, primary_notebook=primary, notebooks={})
    rules = json.loads((HERE/"official_sources.json").read_text())
    pins = json.loads((ROOT/"notebook/setup_pins.json").read_text())
    values = preview_values()
    values.update(RULES_DATE=rules["checked_date"], RULES_COMMIT=rules["official_repository_commit"])
    info["official_rules_commit"] = rules["official_repository_commit"]
    info["official_rules_checked_date"] = rules["checked_date"]
    info["official_sources_sha256"] = digest(HERE/"official_sources.json")
    info["recommended_runtime"] = pins
    info["recommended_runtime_sha256"] = digest(ROOT/"notebook/setup_pins.json")
    for name, document in documents.items():
        source = sources[name]
        validate(document, source, require_evidence=True)
        evidence = captured_evidence(document)
        evaluation = document.metadata.get("tritflow_chapter6") or chapter6(document)
        captured_pdk = evidence.get("pdk")
        if captured_pdk and (captured_pdk["qualified_commit"] != pins["pdk_commit"]
                             or captured_pdk["setup_pins_sha256"] != digest(ROOT/"notebook/setup_pins.json")):
            raise ValueError("raw capture used different runtime/PDK pins; execute the notebook again")
        release = release_status(source)
        assets = embed_assets(document)
        document.metadata["tritflow_submission_assets"] = assets
        record = {"source_path":str(source.relative_to(ROOT)), "source_sha256":digest(source),
                  "capture":dict(document.metadata.tritflow_submission_capture),
                  "pinned_source_commit":evidence["source_ref"],
                  "source_commit_at_execution":evidence["runtime_commit"],
                  "runtime_tools":evidence["runtime"], "results":evidence,
                  "evaluation":evaluation, "release":release}
        info["notebooks"][name] = record
    primary_record = info["notebooks"][primary]
    values.update(result_values(primary_record["results"]))
    blockers = readiness(info["notebooks"])
    info["submission_ready"] = not blockers
    info["readiness_notes"] = blockers
    values["PACKAGE_STATUS"] = "Ready for final submission review." if not blockers else "Development package. " + " ".join(blockers)
    values["NOTEBOOKS"] = "\n\n".join(
        f"[{('English primary' if name.endswith('_en.ipynb') else 'Japanese companion' if primary != name else 'Japanese development preview')}]({name}) — executed with saved outputs."
        for name in documents)
    values["CHAPTER6_LINKS"] = ", ".join(
        f"[{('English' if name.endswith('_en.ipynb') else 'Japanese')}]({name})"
        for name in documents)
    ref = primary_record["pinned_source_commit"]
    source_path = primary_record["source_path"]
    values["COLAB_URL"] = f"https://colab.research.google.com/github/PenguinEino/tritflow/blob/{ref}/{source_path}"
    values["RUNTIME"] = (f"Recommended: Python 3.12; KLayout binary/Python {pins['klayout_version']}; "
                         f"ngspice {pins['ngspice_package']['upstream_version']} "
                         f"(Ubuntu package {pins['ngspice_package']['version']}); "
                         f"OpenSUSI TR-1um `{pins['pdk_commit']}`. "
                         "Use the Python packages installed by the notebook bootstrap.")
    info["colab_verified"] = False
    info["colab_verification_scope"] = "This package records local execution of v3; historical v1 Colab evidence is not promoted to v3."
    for name, document in documents.items():
        record = info["notebooks"][name]
        # The call asks for names at the top, not a separate author table.
        # Preserve the source opening's title and authors without repeating them.
        opening = document.cells[0]
        if opening.cell_type != "markdown" or any(author["name"] not in opening.source for author in team["authors"]):
            raise ValueError("team members must be named in the source notebook opening")
        front = "**License: Apache-2.0.**"
        # The license follows the title and authors; the opening text already states the tool versions.
        document.cells.insert(1, nbformat.v4.new_markdown_cell(front, id="submission-identity"))
        references = ("## Submission references and reuse\n\n"
                      "- [TritFlow source](https://github.com/PenguinEino/tritflow).\n"
                      "- [OpenSUSI TR-1um PDK](https://github.com/OpenSUSI/TR-1um).\n"
                      "- [Author's taped-out balanced-ternary cells and 1-trit multiply-add](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic).\n"
                      "- [KLayout](https://www.klayout.de/), [ngspice](https://ngspice.sourceforge.io/), "
                      "[Plotly](https://plotly.com/python/), [Lark](https://github.com/lark-parser/lark).\n\n"
                      "Earlier Code-a-Chip notebooks were consulted for presentation and packaging; no notebook cells or code were copied from those submissions. "
                      "The complete notebook bibliography, when present, remains in the original chapter cells.\n\n"
                      "Saved images are actual captured initial views. Re-execute the unchanged source cells for controls and animation. "
                      "Pinned Markdown images are embedded for offline reading. Machine paths in outputs are normalized; numerical data is unchanged.")
        document.cells.append(nbformat.v4.new_markdown_cell(references, id="submission-references"))
        details = ("<details><summary>Capture and source provenance</summary>\n\n"
                   + release_notice(record["release"]) + "\n\n" + info["colab_verification_scope"]
                   + f"\n\nPinned bootstrap commit: `{record['pinned_source_commit']}`. "
                   + f"Observed execution commit: `{record['source_commit_at_execution']}`.\n\n"
                   + "```json\n"+json.dumps(record["runtime_tools"], indent=2)+"\n```\n\n</details>")
        document.cells.append(nbformat.v4.new_markdown_cell(details, id="submission-capture-details"))
        document.metadata["license"] = {"name":"Apache-2.0", "url":"https://www.apache.org/licenses/LICENSE-2.0"}
        record.update(validate(document, sources[name], require_evidence=True))
        nbformat.write(document, destination/name)
    (destination/"README.md").write_text(render_readme(team, values))
    for name in ("ABSTRACT.md", "PITCH.md", "CHECKLIST.md"):
        (destination/name).write_text(render(read_template(name), values))
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(ROOT/name, destination/name)
    info["files"] = {p.name:{"bytes":p.stat().st_size, "sha256":digest(p)} for p in destination.iterdir()
                     if p.name != "build-info.json"}
    info["file_count"] = len(expected_files)
    for metric in ("code_cells", "saved_outputs", "png_outputs", "embedded_paper_figures", "html_tables"):
        info[metric] = sum(record[metric] for record in info["notebooks"].values())
    info["total_bytes"] = 0
    for _ in range(12):
        raw = json.dumps(info, indent=2, ensure_ascii=False)+"\n"
        total = sum(v["bytes"] for v in info["files"].values())+len(raw.encode())
        if total == info["total_bytes"]:
            break
        info["total_bytes"] = total
    if total > LIMIT_BYTES:
        raise ValueError(f"payload exceeds our {LIMIT_BYTES}-byte budget: {total}")
    (destination/"build-info.json").write_text(raw)
    return info


def check(destination, sources=None):
    """Check every byte, both executions, top author fields and source identity."""
    import nbformat
    destination = Path(destination)
    info = json.loads((destination/"build-info.json").read_text())
    if info.get("schema_version") != 3:
        raise ValueError("payload is not a v3 submission; rebuild it")
    names = set(info["notebooks"])
    expected = COMMON_FILES | names
    if not names or not names <= NOTEBOOK_FILES or {p.name for p in destination.iterdir()} != expected:
        raise ValueError("payload file list differs from the bilingual allowlist")
    if set(info["files"]) != expected - {"build-info.json"}:
        raise ValueError("payload manifest is incomplete")
    blockers = readiness(info["notebooks"])
    if info["readiness_notes"] != blockers or info["submission_ready"] != (not blockers):
        raise ValueError("submission readiness does not match captured evidence")
    for name, record in info["files"].items():
        if digest(destination/name) != record["sha256"] or (destination/name).stat().st_size != record["bytes"]:
            raise ValueError(f"payload hash mismatch: {name}")
    total = sum(p.stat().st_size for p in destination.iterdir())
    if total != info["total_bytes"] or total > LIMIT_BYTES or info["file_count"] != len(expected):
        raise ValueError("payload size mismatch")
    sources = sources or {name:ROOT/record["source_path"] for name, record in info["notebooks"].items()}
    for name, record in info["notebooks"].items():
        source = Path(sources[name])
        if digest(source) != record["source_sha256"]:
            raise ValueError(f"source notebook changed since capture: {name}")
        document = nbformat.read(destination/name, as_version=4)
        metrics = validate(document, source, require_evidence=True)
        if any(record[k] != value for k, value in metrics.items()):
            raise ValueError(f"notebook evidence count mismatch: {name}")
        if document.cells[1].id != "submission-identity":
            raise ValueError("missing submission front matter")
        if captured_evidence(document) != record["results"]:
            raise ValueError(f"executed results differ from manifest: {name}")
        for cell in document.cells:
            if cell.cell_type == "markdown" and re.search(r"\{\{[^}]+\}\}", cell.source):
                raise ValueError("placeholder in packaged notebook")
            for output in cell.get("outputs", []):
                data = output.get("data", {})
                if any(k.startswith("application/vnd.plotly") for k in data) or "<script" in data.get("text/html", "").lower():
                    raise ValueError("active output was not made portable")
    for name in ("README.md", "ABSTRACT.md", "PITCH.md", "CHECKLIST.md"):
        if re.search(r"\{\{[^}]+\}\}", (destination/name).read_text()):
            raise ValueError(f"unresolved placeholder: {name}")
    for name in ("LICENSE", "NOTICE"):
        if (destination/name).read_bytes() != (ROOT/name).read_bytes():
            raise ValueError(f"source license/attribution changed: {name}")
    return info


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="primary v3 notebook; defaults to EN, with JA fallback")
    parser.add_argument("--japanese-source", type=Path, default=JAPANESE)
    parser.add_argument("--output", type=Path, default=DESTINATION)
    parser.add_argument("--workdir", type=Path, default=HERE/".build/submission_capture")
    parser.add_argument("--team", type=Path, default=HERE/"team.json")
    parser.add_argument("--from-executed", type=Path, help="reuse matching successful raw primary capture")
    parser.add_argument("--from-executed-ja", type=Path, help="reuse matching successful raw Japanese capture")
    parser.add_argument("--timeout", type=int, default=900, help="per-cell timeout in seconds")
    parser.add_argument("--check", action="store_true", help="validate payload without EDA execution")
    parser.add_argument("--require-final", action="store_true", help="refuse previews, unfinished evaluation or incompatible pins")
    args = parser.parse_args(argv)
    for name in ("source", "japanese_source", "output", "workdir", "team", "from_executed", "from_executed_ja"):
        value = getattr(args, name)
        if value is not None:
            setattr(args, name, value.expanduser().resolve())
    if not args.output.is_relative_to(HERE):
        raise ValueError("output must be inside submission/")
    if args.check:
        info = check(args.output)
    else:
        workspace(args.workdir)
        sources = selected_sources(args.source, args.japanese_source)
        source_hashes = {name:digest(source) for name, source in sources.items()}
        documents, captures, evaluations = {}, {}, {}
        from results import chapter6
        for index, (name, source) in enumerate(sources.items()):
            workdir = args.workdir/Path(name).stem
            workdir.mkdir(parents=True, exist_ok=True)
            reuse = args.from_executed if index == 0 else args.from_executed_ja
            if index == 0 and name == "tritflow_ja.ipynb" and args.from_executed_ja:
                reuse = args.from_executed_ja
            if reuse:
                document, raw = use_executed(reuse, source), reuse
            else:
                document, raw = execute(source, workdir, args.timeout)
            evaluations[name] = chapter6(document)
            from tritflow import PDK_ROOT
            replacements = {str(args.workdir):"$OUTPUTDIR", str(ROOT):"$TRITFLOW_ROOT", str(PDK_ROOT):"$TR1UM_PDK"}
            portable_outputs(document, replacements, snapshot_dir=workdir/"static")
            documents[name] = document
            captures[name] = {"path":str(raw.relative_to(ROOT)), "sha256":digest(raw)}
        if any(digest(sources[name]) != checksum for name, checksum in source_hashes.items()):
            raise RuntimeError("source notebook changed while building; rerun after its owner finishes")
        info = {"created_utc":datetime.now(timezone.utc).isoformat(),
                "packaging_commit":subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
                "tracked_working_changes_at_packaging":subprocess.check_output(["git", "-C", str(ROOT), "diff", "--name-only", "HEAD"], text=True).splitlines(),
                "packaging_tools":packaging_tools(), "raw_executions_not_in_payload":captures,
                "manifest_scope":"files excludes build-info.json itself; total_bytes includes it",
                "team_fields_completed":not has_placeholders(json.loads(args.team.read_text()))}
        # Preserve the literal executed tables before active controls are frozen.
        for name, evaluation in evaluations.items():
            documents[name].metadata["tritflow_chapter6"] = evaluation
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists() and {p.name for p in args.output.iterdir()} - FILES:
            raise ValueError("output contains files outside this builder's allowlist")
        with tempfile.TemporaryDirectory(prefix=".tritflow-package-", dir=args.output.parent) as temporary:
            staging = Path(temporary)
            info = package(documents, sources, staging, json.loads(args.team.read_text()), info)
            check(staging, sources)
            if args.require_final and not info["submission_ready"]:
                raise ValueError("final submission gate: " + " ".join(info["readiness_notes"]))
            backup = args.output.with_name("."+args.output.name+".previous")
            if backup.exists():
                raise RuntimeError("previous backup exists; inspect it before replacing the payload")
            if args.output.exists():
                args.output.rename(backup)
            try:
                staging.rename(args.output)
            except Exception:
                if backup.exists():
                    backup.rename(args.output)
                raise
            if backup.exists():
                shutil.rmtree(backup)
    if args.require_final and not info["submission_ready"]:
        raise ValueError("final submission gate: " + " ".join(info["readiness_notes"]))
    print(json.dumps({k:info[k] for k in ("file_count", "total_bytes", "code_cells", "saved_outputs", "png_outputs", "html_tables", "submission_ready")}, indent=2))
    print("Payload:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
