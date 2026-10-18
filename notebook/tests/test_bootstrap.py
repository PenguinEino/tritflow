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
CELL = json.loads((ROOT/"notebook/tritflow_tr1um.ipynb").read_text())["cells"][1]["source"]
COMMIT = "a"*40
URL = "https://github.com/PenguinEino/tritflow.git"


def run_colab(monkeypatch, tmp_path, *, existing=False, ref=None, mismatch=False, dirty=False,
              clone_failure=False, configured=False):
    """Use real temporary files, intercept every command, and substitute only /content."""
    target = tmp_path/"tritflow"
    commands = []

    def seed():
        (target/".git").mkdir(parents=True)
        (target/"notebook").mkdir()
        (target/"notebook/runtime_support.py").write_text("# source-asset presence fixture\n")

    if existing:
        seed()
    if configured:
        (target/"notebook/runtime.json").write_text(json.dumps({"TRITFLOW_SETUP_SCHEMA":runtime_support.SETUP_SCHEMA}))
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
        elif command[0] == "bash":
            (target/"notebook/runtime.json").write_text(json.dumps({"TRITFLOW_ROOT": str(target),
                "TRITFLOW_SETUP_SCHEMA":runtime_support.SETUP_SCHEMA}))
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
    # Patch this import only, preserving pathlib itself for pytest and real files.
    proxy = SimpleNamespace(Path=lambda p: target if str(p) == "/content/tritflow" else Path(p))
    namespace = {}
    with monkeypatch.context() as context:
        context.setitem(sys.modules, "pathlib", proxy)
        context.setattr(sys, "path", sys.path.copy())
        exec(compile(CELL, "standalone-colab-cell", "exec"), namespace)
    return commands, namespace


@pytest.mark.parametrize("ref", [None, "release-test"])
def test_shallow_pinned_clone_prints_hash_and_installs(monkeypatch, tmp_path, capsys, ref):
    commands, ns = run_colab(monkeypatch, tmp_path, ref=ref)
    assert commands[0] == ["git", "clone", "--depth", "1", "--single-branch", "--branch",
                           ref or "colab-v0", URL, str(tmp_path/"tritflow")]
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
    assert "colab-v0" in error.value.cmd
