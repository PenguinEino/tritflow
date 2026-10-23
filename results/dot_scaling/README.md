# Recorded ternary-weight dot-product scaling

The publication is `../dot_scaling.json`. The default notebook reader
`scale_views.load_scaling()` verifies the recorded source, published cell, PDK
and evidence hashes without running a simulator or requiring the recording
host's binaries. It rejects incomplete/stale campaigns. Plotting never launches
physical tools.

Explicitly recompute with:

```sh
python3 -B examples/dot_scaling.py --recompute --jobs 4
```

Use the qualified `NGSPICE_BINARY`, `NGSPICE_PAYLOAD`, `KLAYOUT_BINARY`,
`TR1UM_PDK` and Python package target from the host's setup. For the recorded
server run the integrator authorized the existing `runtime/native` cache after
`build/setupmem` vanished on reboot; `remote_environment.json` preserves both
path sets. The top-level provenance and each row identify the host, architecture
and simulator/KLayout hashes. The source commit is a base revision; the content
hashes identify the actual uncommitted producer inputs.

The juror-review extension preserves the byte-exact base producer as
`producer_before_juror.py`, checks every other base dependency against live
content, and records a separate `review_provenance` for the added analyses.
`python3 -B examples/dot_scaling.py --review` explicitly resumes that extension;
`--recompute` produces the expanded experiment from current source. An optional
N=32 attempt that cannot complete P&R is disclosed under `optional_attempts`,
with its failure evidence, and is excluded from the qualified 2/4/8/16 curves.

Each `dotN/` directory contains deterministic gzip copies of the source HDL,
gate netlist, actual GDS/PNR record, PDK DRC report/log, strict LVS report and
extracted circuit, capacitance, vectors, timing report, transient measurements
and simulator deck/log, and independent DC measurements/decks/logs. Top-level
`evidence_sha256` covers these compressed files. Full local waveform arrays and
resumable per-stage caches are in ignored `work/`; they are not needed to read
the portable publication. Chrome profiles are ignored as well.

`scale_views.py` also provides synthesis, scaling, timing and power tables and
two Plotly figures. Table functions return IPython HTML; figures return Plotly
figures. To recreate their standalone HTML/PNG previews with headless Chrome:

```sh
python3 -B notebook/scale_views.py
```

`layout_penalty_table(data)` compares STA with/without wire C for every
qualified size, and device-only/wire-C SPICE for N=4. Power tables distinguish
all-zero-activation static power from the true transient supply-power average
over all eleven holds. Switching-only energy is not separated.

All capacitances are area/perimeter estimates, not calibrated sign-off PEX.
The same LVS-mapped full-GDS signal capacitance is used by STA and SPICE. Timing
is final entry into the ideal ±0.5 V band on the documented fixed-weight
sequence; it is not an all-transition bound. Static power is an independent DC
measurement and includes both +5 V and -5 V source power. Its observed spread
does not establish a global power bound. See `docs/status/SCALE.md` for the
measurement conditions, floorplan decisions, results and limitations.

`native_binary_hashes.json` supplements the original launch-wrapper identities
with the actual ngspice/KLayout ELF, KLayout shared-library and loader hashes.
`record_native.py` creates this supplement on the producer host after a completed
run, without changing the historical cache identities or numerical results.
