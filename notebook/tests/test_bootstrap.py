"""Exercise the standalone Colab cell; git mutations and installations are mocked."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"notebook"))
import runtime_support
from stages import SETUP as CELL
COMMIT = "a"*40
URL = "https://github.com/PenguinEino/tritflow.git"


def run_colab(monkeypatch, tmp_path, *, existing=False, ref=None, mismatch=False, dirty=False,
              clone_failure=False, configured=False, missing_helper=False):
    """Use real temporary files, intercept every command, and substitute only /content."""
    target = tmp_path/"tritflow"
    commands = []

    def seed():
        (target/".git").mkdir(parents=True)
        (target/"notebook").mkdir()
        if not missing_helper:
            (target/"notebook/runtime_support.py").write_text("# source-asset presence fixture\n")

    if existing:
        seed()
    if configured:
        (target/"notebook/runtime.json").write_text(json.dumps({"TRITFLOW_SETUP_SCHEMA":runtime_support.SETUP_SCHEMA,
            "TRITFLOW_SETUP_SHA256":"fixture", "TRITFLOW_PYTHON_TARGET":str(tmp_path/"python")}))
    monkeypatch.delenv("TRITFLOW_REF", raising=False)
    if ref:
        monkeypatch.setenv("TRITFLOW_REF", ref)

    def run(command, **kwargs):
        commands.append(command)
        assert kwargs["check"] is True
        if command[:2] == ["git", "clone"]:
            if clone_failure:
                raise subprocess.CalledProcessError(128, command)
            seed()
        elif command[:3] == ["git", "-C", str(target)] and command[3] in {"fetch", "switch"}:
            pass
        elif command[0] == "bash":
            (target/"notebook/runtime.json").write_text(json.dumps({"TRITFLOW_ROOT": str(target),
                "TRITFLOW_SETUP_SCHEMA":runtime_support.SETUP_SCHEMA,
                "TRITFLOW_PYTHON_TARGET":str(tmp_path/"python")}))
        elif command[-1] == "-v":
            return SimpleNamespace(returncode=0,stdout=f"{command[0]} version (unit fixture)",stderr="")
        else:
            raise AssertionError(f"unexpected subprocess: {command}")
        return SimpleNamespace(returncode=0)

    def check_output(command, **kwargs):
        commands.append(command)
        args = command[3:]
        assert command[:3] == ["git", "-C", str(target)]
        if args == ["remote", "get-url", "origin"]:
            return URL+"\n"
        if args[:2] == ["rev-parse", "--verify"]:
            return ("b"*40 if mismatch and args[2] != "HEAD^{commit}" else COMMIT)+"\n"
        if args == ["status", "--porcelain", "--untracked-files=no"]:
            return " M pyproject.toml\n" if dirty else ""
        raise AssertionError(f"unexpected read: {command}")

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "check_output", check_output)
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(runtime_support,"check_runtime",lambda:{})
    monkeypatch.setattr(runtime_support,"setup_identity",lambda root:"fixture")
    from tritflow.sim import tools
    monkeypatch.setattr(tools,"ngspice_binary",lambda:"/fixture/ngspice")
    # Patch this import only, preserving pathlib itself for pytest and real files.
    proxy = SimpleNamespace(Path=lambda p: target if str(p) == "/content/tritflow" else Path(p))
    namespace = {}
    with monkeypatch.context() as context:
        context.setitem(sys.modules, "pathlib", proxy)
        context.setattr(sys, "path", sys.path.copy())
        exec(compile(CELL, "standalone-colab-cell", "exec"), namespace)
    return commands, namespace


@pytest.mark.parametrize("ref", [None, COMMIT])
def test_immutable_clone_prints_hash_and_installs(monkeypatch, tmp_path, capsys, ref):
    commands, ns = run_colab(monkeypatch, tmp_path, ref=ref)
    assert commands[0] == ["git", "clone", "--no-checkout", "--depth", "1", "--filter=blob:none",
                           URL, str(tmp_path/"tritflow")]
    assert commands[1][:4] == ["git", "-C", str(tmp_path/"tritflow"), "fetch"]
    assert commands[2][:5] == ["git", "-C", str(tmp_path/"tritflow"), "switch", "--detach"]
    assert ["bash", str(tmp_path/"tritflow/notebook/colab_setup.sh"),
            "--source", str(tmp_path/"tritflow")] in commands
    assert ns["SOURCE_COMMIT"] == COMMIT
    output = capsys.readouterr().out
    assert COMMIT in output and "KLayout executable" in output and "ngspice executable" in output
    assert ns["_TRITFLOW_SETUP_READY"] is True


def test_existing_matching_checkout_can_be_rerun(monkeypatch, tmp_path):
    commands, _ = run_colab(monkeypatch, tmp_path, existing=True)
    assert not any(c[:2] == ["git", "clone"] for c in commands)


def test_current_setup_is_reused_but_versions_are_still_printed(monkeypatch,tmp_path):
    commands,_ = run_colab(monkeypatch,tmp_path,existing=True,configured=True)
    assert not any(c[0] == "bash" for c in commands)
    assert sum(c[-1] == "-v" for c in commands) == 2


@pytest.mark.parametrize("condition", ["mismatch", "dirty"])
def test_existing_modified_checkout_is_not_silently_used(monkeypatch, tmp_path, condition):
    with pytest.raises(RuntimeError, match="differs from TRITFLOW_REF"):
        run_colab(monkeypatch, tmp_path, existing=True, **{condition: True})


def test_missing_tag_does_not_fall_back_to_main(monkeypatch, tmp_path):
    with pytest.raises(subprocess.CalledProcessError) as error:
        run_colab(monkeypatch, tmp_path, clone_failure=True)
    assert URL in error.value.cmd


def test_old_release_missing_setup_helper_explains_matching_ref(monkeypatch,tmp_path):
    with pytest.raises(RuntimeError,match="TRITFLOW_REF predates.*matching immutable release"):
        run_colab(monkeypatch,tmp_path,missing_helper=True)


@pytest.mark.parametrize("ref",["main","colab-v0","-bad","a"*39])
def test_movable_or_invalid_source_refs_fail_before_clone(monkeypatch,tmp_path,ref):
    with pytest.raises(ValueError,match="immutable full 40-character"):
        run_colab(monkeypatch,tmp_path,ref=ref)
