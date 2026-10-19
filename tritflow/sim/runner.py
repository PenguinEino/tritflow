"""Isolated batch ngspice execution and real-valued ASCII waveform readers."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile

import numpy as np
from .tools import ngspice_binary


class SimulationError(RuntimeError):
    """A simulator failed, timed out, or did not produce complete finite data."""


def read_wrdata(path: str | Path) -> dict[str, np.ndarray]:
    """Read ngspice wrdata with wr_vecnames and wr_singlescale enabled."""
    with Path(path).open() as stream:
        names = stream.readline().split()
    try:
        values = np.loadtxt(path, skiprows=1, ndmin=2)
    except ValueError as exc:
        raise SimulationError(f'Malformed waveform: {path}') from exc
    if not names or not values.size or values.shape[1] != len(names) or not np.isfinite(values).all():
        raise SimulationError(f"Malformed or non-finite waveform: {path}")
    return {name.lower(): values[:, i] for i, name in enumerate(names)}


def read_ascii_raw(path: str | Path) -> dict[str, np.ndarray]:
    """Read one real-valued ngspice ASCII raw plot (set filetype=ascii)."""
    raw = Path(path).read_text()
    if re.search(r'^Flags:.*complex', raw, re.M | re.I):
        raise SimulationError("Complex raw plots are not supported; export real/imaginary vectors")
    try:
        nv = int(re.search(r'No. Variables:\s*(\d+)', raw)[1])
        np_ = int(re.search(r'No. Points:\s*(\d+)', raw)[1])
        definitions, body = re.split(r'(?m)^Variables:\s*$', raw, maxsplit=1)[1].split('Values:', 1)
        names = [line.split()[1].lower() for line in definitions.splitlines() if line.strip()]
        lines = [line.split() for line in body.splitlines() if line.strip()]
        values = np.array([float(line[-1]) for line in lines]).reshape(np_, nv)
        if nv <= 0 or np_ <= 0 or len(names) != nv or not np.isfinite(values).all():
            raise ValueError("Invalid raw vectors")
    except (AttributeError, IndexError, ValueError) as exc:
        raise SimulationError(f"Malformed ASCII raw file: {path}") from exc
    return {name: values[:, i] for i, name in enumerate(names)}


def run_ngspice(netlist: str, commands: str, vectors: list[str], *,
                timeout: float = 120, executable: str | None = None,
                workdir: str | Path | None = None) -> dict:
    """Run a circuit and analysis, returning {data, log, deck}.

    The circuit contains no .control section. Relative includes are discouraged:
    the run is isolated in a temporary directory. Set workdir to retain artifacts.
    """
    if re.search(r'^\s*\.control\b', netlist, re.M | re.I):
        raise ValueError("Pass analysis commands separately from the circuit")
    if not vectors:
        raise ValueError("At least one output vector is required")
    executable = ngspice_binary(executable)
    circuit = re.sub(r'^\s*\.end\s*$', '', netlist, flags=re.M | re.I)
    # Nutmeg treats square brackets as vector indexing unless the node is quoted.
    # Preserve SPICE's bit-blasted names and the canonical wrdata column names.
    def control_expression(expression):
        return re.sub(r'(?i)\bv\(([^()]+)\)',
                      lambda m: 'v(' + ','.join(
                          f'"{node}"' if '[' in node or ']' in node else node
                          for node in m[1].split(',')) + ')', expression)
    exported_vectors = [control_expression(v) for v in vectors]
    deck = (circuit + '\n.control\nset noaskquit\nset wr_singlescale\nset wr_vecnames\n'
            'set numdgt=15\n' + commands + '\nwrdata waveform.txt ' + ' '.join(exported_vectors)
            + '\nquit\n.endc\n.end\n')

    def execute(folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'tb.spice').write_text(deck)
        (folder / 'waveform.txt').unlink(missing_ok=True)
        try:
            process = subprocess.run([executable, '-n', '-b', 'tb.spice'], cwd=folder,
                                     capture_output=True, text=True, timeout=timeout,
                                     env={**os.environ, 'LC_ALL': 'C'})
        except subprocess.TimeoutExpired as exc:
            raise SimulationError(f"ngspice timeout after {timeout:g} s") from exc
        except OSError as exc:
            raise SimulationError(f"Cannot execute {executable}: {exc}") from exc
        log = process.stdout + process.stderr
        (folder / 'ngspice.log').write_text(log)
        if process.returncode or re.search(r'(?im)^\s*(?:error\b|fatal\b)|timestep too small|simulation interrupted|no such vector', log):
            raise SimulationError(f"ngspice failed (exit {process.returncode}):\n{log[-6000:]}")
        if not (folder / 'waveform.txt').exists():
            raise SimulationError(f"ngspice produced no waveform:\n{log[-3000:]}")
        return {'data': read_wrdata(folder / 'waveform.txt'), 'log': log, 'deck': deck}

    if workdir is not None:
        return execute(workdir)
    with tempfile.TemporaryDirectory(prefix='tritflow-ngspice-') as folder:
        return execute(folder)
