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
sys.path.insert(0,str(ROOT))
SOURCE = ROOT/"notebook/tritflow_tr1um.ipynb"
DESTINATION = HERE/"ISSCC27/submitted_notebooks/TritFlow"
FILES = {"tritflow_tr1um.ipynb", "README.md", "LICENSE", "NOTICE", "ABSTRACT.md", "PITCH.md", "CHECKLIST.md", "build-info.json"}
LIMIT_BYTES = 8*1024*1024  # own packaging budget, not an official limit


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


def render_readme(team, release_text="Release compatibility must be checked before filing.", source_commit=None):
    text = read_template("README.md")
    for key, value in {"TEAM_NAME":team["team_name"], "AUTHORS_TABLE":authors_table(team),
                       "REPRESENTATIVE":team["representative"], "ATTENDANCE":team["attendance_and_poster"],
                       "ASSET_RIGHTS":team["asset_rights_confirmation"],"RELEASE_STATUS":release_text,
                       "AUTHOR_DETAILS":author_details(team),
                       "SOURCE_LINK":f'[{source_commit}](https://github.com/PenguinEino/tritflow/tree/{source_commit})'
                           if source_commit else "see build-info.json (commit print unavailable)"}.items():
        text = text.replace("{{"+key+"}}",str(value))
    return text


def tool_version(command):
    result = subprocess.run(command,capture_output=True,text=True,timeout=15,check=True)
    return (result.stdout+result.stderr).strip()


def release_status(source):
    """Read local release objects without fetching or changing git state."""
    ref="colab-v0"
    result=subprocess.run(["git","-C",str(ROOT),"rev-parse","--verify",ref+"^{commit}"],
                          capture_output=True,text=True)
    info={"default_ref":ref,"commit":result.stdout.strip() if not result.returncode else None,
          "matches_source_notebook":False,"missing_required_helpers":[]}
    if info["commit"]:
        notebook=subprocess.run(["git","-C",str(ROOT),"show",ref+":notebook/tritflow_tr1um.ipynb"],capture_output=True)
        info["matches_source_notebook"]=(not notebook.returncode and sha256(notebook.stdout).hexdigest()==digest(source))
        for name in ("notebook/experiments.py","examples/curated.py"):
            test=subprocess.run(["git","-C",str(ROOT),"cat-file","-e",ref+":"+name],capture_output=True)
            if test.returncode: info["missing_required_helpers"].append(name)
    info["compatible"] = bool(info["matches_source_notebook"] and not info["missing_required_helpers"])
    return info


def release_notice(info):
    if info.get("compatible"):
        return f'Default source tag `{info["default_ref"]}` matches the packaged notebook at `{info["commit"]}` (local git-object check).'
    return ("**Release TODO before filing:** the default `colab-v0` release does not match this submitted notebook "
            "or could not be verified. The integrator must publish a corresponding immutable source tag and "
            "configure `TRITFLOW_REF` before the bootstrap. "
            "See `build-info.json` for the checked commit/missing helpers. Saved outputs remain readable offline; "
            "the existing badge is not a verified reproducer of this captured version.")


def captured_commit(document):
    """Use the notebook's actual bootstrap print, not a later integrator commit."""
    for cell in document.cells:
        for output in cell.get("outputs",[]):
            if output.get("output_type") == "stream":
                match=re.search(r"Source: .*?commit=([0-9a-f]{40})\b",output.text)
                if match: return match[1]
    return None


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
    setup = nbformat.v4.new_code_cell(
        "import os\n"
        "os.environ.pop('TRITFLOW_NOTEBOOK_HEADLESS',None)\n"
        "import plotly.io as pio\n"
        "pio.renderers.default='png'\n"
        "pio.defaults.default_width=1100\n"
        "pio.defaults.default_scale=1\n"
        "pio.defaults.mathjax=None\n",id="submission-render-setup")
    document.cells.insert(0,setup)
    environment = os.environ.copy()
    environment.update(TRITFLOW_ROOT=str(ROOT),TRITFLOW_NOTEBOOK_BUILD=str(workdir/"flow"),
                       TRITFLOW_EXTENDED="0",TRITFLOW_CIRCUIT="minmax",QT_QPA_PLATFORM="offscreen")
    environment.pop("TRITFLOW_NOTEBOOK_HEADLESS",None)
    client = NotebookClient(document,timeout=timeout,kernel_name="python3",allow_errors=False,
                            resources={"metadata":{"path":str(ROOT)}},store_widget_state=False)
    client.on_cell_start = lambda cell,cell_index: print(f"Executing {cell_index}: {cell.id}",flush=True)
    started = time.monotonic()
    raw = workdir/"executed.raw.ipynb"
    succeeded = False
    try:
        client.execute(env=environment)
        succeeded = True
    finally:
        # A failed notebook stays outside the PR payload and is never a pass.
        document.metadata["tritflow_submission_capture"] = {
            "source_sha256":digest(source),"elapsed_s":time.monotonic()-started,
            "renderer":"png", "completed":succeeded
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
    if document.cells[0].id == "submission-render-setup":
        document.cells.pop(0)
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


def portable_outputs(document, replacements):
    """Keep actual values; normalize machine paths and remove active/web payloads."""
    from PIL import Image
    for cell in document.cells:
        if cell.cell_type != "code":
            continue
        outputs = []
        for output in cell.outputs:
            if output.output_type == "error":
                raise ValueError("failed execution cannot be packaged")
            data = output.get("data",{})
            html = data.get("text/html","")
            if "data:image/svg+xml;base64," in html:
                outputs.extend(gallery_outputs(html))
                continue
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
            if "image/png" in data:
                # Lossless optimization, not a redraw or resampling of results.
                with Image.open(io.BytesIO(b64decode(data["image/png"]))) as image:
                    buffer=io.BytesIO();image.save(buffer,format="PNG",optimize=True)
                data["image/png"] = b64encode(buffer.getvalue()).decode()
            if any(key.startswith("application/vnd.plotly") for key in data):
                raise ValueError("capture must use static PNG, not large interactive Plotly bundles")
            if "<script" in html.lower():
                raise ValueError("active HTML output needs a static fallback before packaging")
            outputs.append(output)
        cell.outputs = outputs
        cell.metadata.pop("execution",None)
    document.metadata.pop("widgets",None)


def validate(document, source):
    """Check saved evidence and exact original code, allowing front matter only."""
    import nbformat
    nbformat.validate(document)
    expected = nbformat.read(source,as_version=4)
    original = {c["id"]:c["source"] for c in expected["cells"]}
    for cell in document.cells:
        if cell.id in original and cell.source != original[cell.id]:
            raise ValueError(f"source cell changed: {cell.id}")
    if not set(original) <= {cell.id for cell in document.cells}:
        raise ValueError("missing source notebook cells")
    code = [c for c in document.cells if c.cell_type=="code"]
    if not code or any(c.execution_count is None for c in code):
        raise ValueError("every source code cell must have executed")
    outputs = [o for c in code for o in c.outputs]
    if any(o.output_type=="error" for o in outputs):
        raise ValueError("error output in submission")
    images = sum("image/png" in o.get("data",{}) for o in outputs)
    tables = sum("<table" in o.get("data",{}).get("text/html","") for o in outputs)
    if images < 8 or tables < 8:
        raise ValueError("saved figures/tables are incomplete")
    return {"code_cells":len(code),"saved_outputs":len(outputs),"png_outputs":images,"html_tables":tables}


def package(document, source, destination, team, info):
    import nbformat
    destination.mkdir(parents=True,exist_ok=True)
    extra = {p.name for p in destination.iterdir()}-FILES
    if extra:
        raise ValueError(f"unexpected files in payload; remove explicitly: {sorted(extra)}")
    abstract = read_template("ABSTRACT.md").split("\n\n",1)[1].strip()
    front = "# TritFlow — Code-a-Chip ISSCC 2027\n\n"+authors_table(team)
    front += "\n\n"+author_details(team)
    front += f"\n\nTeam: {team['team_name']}. Representative: {team['representative']}.\n\n"
    front += "**Apache-2.0.** "+team["asset_rights_confirmation"]+"\n\n"+abstract
    front += "\n\nSaved outputs were executed locally, with static PNG figures for reading without running. "
    front += "Animation stills show their initial frame. Machine paths are normalized; numerical results are unchanged. "
    front += "Schematic captures show the selected drawing; rerun to expand alternatives. "
    front += "The original source cells and bootstrap are preserved; rerun them for interactive figures. "
    front += "Clean Colab installation remains unverified/postponed.\n\n"
    front += release_notice(info.get("release",{}))+"\n\n"
    front += "<details><summary>Tool versions observed at packaging (runtime pins are in the bootstrap)</summary>\n\n"
    front += "```json\n"+json.dumps(info["tools"],indent=2)+"\n```\n</details>\n"
    document.cells.insert(0,nbformat.v4.new_markdown_cell(front,id="submission-identity"))
    info.update(validate(document,source))
    document.metadata["license"] = {"name":"Apache-2.0","url":"https://www.apache.org/licenses/LICENSE-2.0"}
    nbformat.write(document,destination/"tritflow_tr1um.ipynb")
    (destination/"README.md").write_text(render_readme(team,release_notice(info.get("release",{})),
                                                    info.get("source_commit_at_bootstrap")))
    for name in ("ABSTRACT.md","PITCH.md","CHECKLIST.md"):
        (destination/name).write_text(read_template(name))
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(ROOT/name,destination/name)
    info["files"] = {p.name:{"bytes":p.stat().st_size,"sha256":digest(p)} for p in destination.iterdir()
                     if p.name != "build-info.json"}
    info["file_count"] = len(FILES)
    info["total_bytes"] = 0
    for _ in range(8):
        raw = json.dumps(info,indent=2)+"\n"
        total = sum(v["bytes"] for v in info["files"].values())+len(raw.encode())
        if total == info["total_bytes"]:
            break
        info["total_bytes"] = total
    if total > LIMIT_BYTES:
        raise ValueError(f"payload exceeds our {LIMIT_BYTES}-byte budget: {total}")
    (destination/"build-info.json").write_text(json.dumps(info,indent=2)+"\n")
    return info


def check(destination, source):
    import nbformat
    if {p.name for p in destination.iterdir()} != FILES:
        raise ValueError("payload file list differs from the small allowlist")
    info = json.loads((destination/"build-info.json").read_text())
    for name,record in info["files"].items():
        if digest(destination/name) != record["sha256"]:
            raise ValueError(f"payload hash mismatch: {name}")
    total = sum(p.stat().st_size for p in destination.iterdir())
    if total != info["total_bytes"] or total > LIMIT_BYTES:
        raise ValueError("payload size mismatch")
    validate(nbformat.read(destination/"tritflow_tr1um.ipynb",as_version=4),source)
    return info


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=SOURCE)
    parser.add_argument("--output",type=Path,default=DESTINATION)
    parser.add_argument("--workdir",type=Path,default=ROOT/"build/submission_capture")
    parser.add_argument("--team",type=Path,default=HERE/"team.json")
    parser.add_argument("--from-executed",type=Path,help="reuse this builder's successful raw capture for packaging edits")
    parser.add_argument("--timeout",type=int,default=900,help="per-cell timeout in seconds")
    parser.add_argument("--check",action="store_true",help="validate payload hashes/schema/evidence without execution")
    args=parser.parse_args(argv)
    for name in ("source","output","workdir","team","from_executed"):
        value=getattr(args,name)
        if value is not None: setattr(args,name,value.expanduser().resolve())
    if args.check:
        info=check(args.output,args.source)
    else:
        args.workdir.mkdir(parents=True,exist_ok=True)
        source_hash=digest(args.source)
        if args.from_executed:
            document=use_executed(args.from_executed,args.source);raw=args.from_executed
        else:
            document,raw=execute(args.source,args.workdir,args.timeout)
        if source_hash != digest(args.source):
            raise RuntimeError("source notebook changed while building")
        from tritflow import PDK_ROOT
        replacements={str(args.workdir.resolve()):"$OUTPUTDIR",str(ROOT):"$TRITFLOW_ROOT",str(PDK_ROOT):"$TR1UM_PDK"}
        portable_outputs(document,replacements)
        binary=os.environ.get("KLAYOUT_BINARY") or shutil.which("klayout") or Path.home()/"bin/klayout/klayout"
        tools={p:importlib.metadata.version(p) for p in ("numpy","scipy","plotly","klayout","lark","matplotlib",
               "Pillow","nbformat","nbclient","kaleido","choreographer","CairoSVG")}
        tools.update(python=platform.python_version(),ngspice=tool_version(["ngspice","-v"]),
                     klayout_binary=tool_version([str(binary),"-v"]))
        version=re.search(r"ngspice-[^\s]+",tools["ngspice"])
        if version: tools["ngspice"]=version[0]
        browser=shutil.which("google-chrome") or shutil.which("chromium")
        if browser: tools["static_export_browser"]=tool_version([browser,"--version"])
        info={"schema_version":1,"created_utc":datetime.now(timezone.utc).isoformat(),
              "source_notebook_sha256":source_hash,
              "source_commit_at_bootstrap":captured_commit(document),
              "packaging_commit":subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip(),
              "tracked_working_changes_at_packaging":subprocess.check_output(["git","-C",str(ROOT),"diff","--name-only","HEAD"],text=True).splitlines(),
              "capture":dict(document.metadata["tritflow_submission_capture"]),"tools":tools,
              "tools_observation":"packaging environment; the raw capture does not store a separate version snapshot",
              "official_rules_commit":"a502a6ba01260d3492df9137dddae0bb5fabeb3c",
              "release":release_status(args.source),
              "colab_verified":False,"team_fields_completed":not has_placeholders(json.loads(args.team.read_text())),
              "identity_fields_completed":not has_placeholders(json.loads(args.team.read_text())["authors"]),
              "raw_execution_not_in_payload":str(raw.relative_to(ROOT)) if raw.is_relative_to(ROOT) else str(raw),
              "manifest_scope":"files excludes build-info.json itself; total_bytes includes it"}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        if args.output.exists() and {p.name for p in args.output.iterdir()}-FILES:
            raise ValueError("output contains files outside this builder's allowlist")
        with tempfile.TemporaryDirectory(prefix=".tritflow-package-",dir=args.output.parent) as temporary:
            staging=Path(temporary)
            info=package(document,args.source,staging,json.loads(args.team.read_text()),info)
            check(staging,args.source)
            backup=args.output.with_name(".TritFlow.previous")
            if backup.exists():
                raise RuntimeError("previous backup exists; inspect it before replacing the payload")
            if args.output.exists():
                args.output.rename(backup)
            try:
                staging.rename(args.output)
            except Exception:
                if backup.exists(): backup.rename(args.output)
                raise
            if backup.exists(): shutil.rmtree(backup)
    print(json.dumps({k:info[k] for k in ("file_count","total_bytes","code_cells","saved_outputs","png_outputs","html_tables")},indent=2))
    print("Payload:",args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
