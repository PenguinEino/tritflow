# Build the reviewer package

Run from the TritFlow source checkout with its existing Python/EDA/PDK tools.
The source notebook remains output-free; the builder executes it in a Jupyter
kernel against `$TR1UM_PDK` (the pinned public PDK), captures real tables and Plotly figures, and publishes an executed copy.

```sh
python3 -m pip install --user --break-system-packages -r submission/requirements-build.txt
python3 submission/build_submission.py
python3 submission/build_submission.py --check
python3 -m pytest submission/tests -q
```

Static figure export also needs installed Chrome/Chromium and Cairo. The local
Chrome was already available; nothing installs a browser or system package.
Build-time dependencies stay in this repository, outside the reviewer payload.
The first compatible combination tested is Kaleido 1.5.0 / Choreographer 1.4.0;
Kaleido 1.1.0 was incompatible with Choreographer 1.4.0 and is not the build pin.

`team.json` follows the integrator-owned `docs/author.md` exactly. Name,
affiliation, student status, email and GitHub are included; no telephone field
is accepted. The user has explicitly released their derived historical
schematic assets under Apache-2.0. Confirm the selected representative's
attendance/poster arrangements before filing.

Default payload: `submission/ISSCC27/submitted_notebooks/TritFlow/`.
**Only that folder** belongs in the eventual official-repository PR. It contains
the notebook, README, Apache license, abstract, pitch, checklist and build
information; no EDA sources, PDK, large cell tree or raw simulation results.
Current rules and inspected accepted-folder examples are linked in the checklist.
The payload budget is 8 MiB, a self-imposed guard rather than an official limit.

Saved figures are static native Plotly PNGs. Repeated SVG gallery HTML becomes
selected embedded SVG/PNG image bundles, so readers need no JavaScript or local
assets. PNG optimization is lossless. Numerical outputs are unchanged; known
machine paths are replaced with `$TRITFLOW_ROOT`, `$TR1UM_PDK`, `$OUTPUTDIR`.
The original notebook cells and bootstrap stay identical. Interactive figures
return on normal re-execution; animation stills show the initial recorded frame.

The raw executed notebook and flow outputs stay under
`build/submission_capture/`. An error leaves diagnostics there and aborts
publication. A successful payload is validated in a staging directory before
replacing the previous payload. For packaging-only edits, reuse a successful
raw capture with the identical source-notebook hash:

```sh
python3 submission/build_submission.py --from-executed build/submission_capture/executed.raw.ipynb
```

That command repackages a recorded execution; it does not claim a new EDA run
or refresh its source/model context. Omit it to execute the current flow afresh.
Use `--workdir`, `--output` or `--team` for isolated drafts. Saved outputs were
generated locally; clean Colab verification remains postponed. This builder
never performs git-writing commands, opens a PR or submits personal information.
