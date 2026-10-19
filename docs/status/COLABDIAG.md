# COLABDIAG — main-kernel runtime-replacement diagnosis

Date: 2026-10-19 (Asia/Tokyo). Stream: COLABMCP.

## Result: blocked before execution; cause undetermined

No fresh-runtime experiment ran in this attempt. No survival result, boot ID,
Python PID, process count, peak RSS, used-RAM peak, disk peak, or OOM conclusion
can be reported. The prior separate-kernel nbclient passes do not satisfy this
diagnosis.

Target notebook: `b49e5c165446e6337513008efd933e078a8c118a`
(`colab-v0`), `notebook/tritflow_tr1um.ipynb`. Its setup cell selects source
implementation `7d981896bd8e22963664483dc8a1ab8642496357` by default.

## Tool blocker and actions attempted

Read `docs/concept.md`, `docs/interfaces.md`, and `briefs/COLABMCP.md`.
Called the Colab MCP bridge's `connect(wait_s=1)`; it returned:

```text
pending: approve the 'connect to a local MCP server' dialog in the new Colab tab, then call connect
```

The authorised Chrome surface could not inventory or operate tabs:

```text
Unable to load browser request-header policy. Retry the browser command.
```

This occurred on two `cua.getState()` calls. After a CUA session reset,
`cua.getBrowser({id:"chrome"})` selected Chrome (extension browser ID `1`),
but the subsequent session-name/tab-inventory attempt failed with the same
error. A direct `chrome.tabs.list()` retry also failed with that error.
No browser click was performed. A subsequent bridge `connect(wait_s=1)` returned:

```text
timed out: call connect again (a new Colab tab opens) and approve its dialog
```

Consequently Runtime → Manage sessions could not be inspected, leftover test
sessions could not be terminated, and a fresh scratch runtime could not be
verified. The local-MCP dialog was not approved. No notebook cell was added,
edited, executed, or deleted. The bridge-created connection tab could not be
inspected or cleaned up through the unavailable Chrome surface. No sign-in,
OAuth, Save, or Share action occurred.

## Requested measurements

| Step | Status | boot_id / PID change | RAM / RSS / disk |
|---|---|---|---|
| Manage sessions; provision fresh runtime | Blocked by Chrome surface | Not measured | Not measured |
| Verify `/content/tritflow` absent and uptime <600 s; record `free -m`, `df` | Not run | Not measured | Not measured |
| Fetch exact notebook; execute `setup` via `get_ipython().run_cell(src)` with 2 s file sampler | Not run | Not measured | Not measured |
| Wait 60 s; inspect identity in a new MCP cell | Not run | Not measured | Not measured |
| Execute `imports`; inspect identity again | Not run | Not measured | Not measured |
| Execute `opening_inputs`; inspect identity again | Not run | Not measured | Not measured |
| Execute `method-opening`; inspect identity again | Not run | Not measured | Not measured |
| Repeat entire fresh-runtime experiment if first survives | Not reached | Not measured | Not measured |

`/var/log/*colab*`, `/var/colab/app.log`, other Jupyter logs, and `dmesg`
were not queried in the Colab runtime. Their accessibility is unknown, not
established as permission-denied or absent. Local-machine logs were not used
as a substitute.

## Existing evidence reviewed (not a new reproduction)

Read the retained [round-15 report](COLAB.md) and its
[188 runtime-log entries](../../logs/colab/round15-runtime-log-entries.json).
The relevant retained entries, in chronological order (JST), are:

```text
18:09:10 Kernel started: b00d404c-dc13-4d96-89d8-924a29573e12
18:11:08 Successfully installed contourpy-1.4.0 fonttools-4.67.0 klayout-0.30.6 lark-1.3.1 plotly-5.24.1 scipy-1.16.3 tenacity-9.2.1
18:11:12 TritFlow: KLayout Ruby DRC engine ready
18:11:13 KLayout executable: /content/tritflow-runtime/bin/klayout
18:11:13 KLayout 0.30.6
18:11:13 ngspice executable: /content/tritflow-runtime/bin/ngspice
18:11:13 ** ngspice-42 : Circuit level simulation program
18:11:39 Jupyter Server 2.20.0 is running at:
18:11:46 Kernel started: b9f032be-95dc-471b-9b31-156cab149a53
```

These show a new Jupyter server and a different kernel UUID after the tool
output, but supply neither OS boot IDs nor Python PIDs. They do not locate the
failure between setup return and the next cell, or establish why the runtime
was replaced. No OOM-killer explanation appears in these retained entries.

The prior report observed RAM 1.34/12.67 GB and disk 22.25/107.72 GB during
setup, returning to approximately 1.23–1.26/12.67 GB and 20.50/107.72 GB
after reconnect. These are sparse UI observations, **not measured peaks**;
they cannot exclude an unobserved memory spike or an external termination.

Read-only inspection of the exact locally available Git objects confirms:

- After `print_tool_versions()`, the setup cell only assigns
  `_TRITFLOW_SETUP_READY = True`.
- In the pinned `runtime_support.py`, `print_tool_versions()` launches the
  KLayout and ngspice `-v` commands as subprocesses with a 15 s timeout, prints
  their output, and returns. That function and the setup-cell tail contain no
  explicit runtime-restart request. This does not rule out other code,
  callbacks, native failures, or Colab infrastructure behaviour.
- The requested four cell sources were inspected using `git show`; the raw
  URL was not fetched inside Colab, and none was executed in a main kernel.

## Handoff

Restore Chrome-surface operation, then begin at Manage sessions; do not reuse
an unverified runtime. Perform the requested main-kernel sequence with a
background sampler writing and flushing every 2 s, retaining output after each
stage before any possible disk loss. Compare both boot ID and PID in new MCP
cells after each wait, and capture runtime logs and `dmesg` before cleanup.
If all stages survive, repeat from a separately fresh runtime as requested.

No repository implementation changed. Only this status file was added; no
commit, checkout, reset, stash, push, or local package installation occurred.
No automated test applies to this documentation-only blocker record; the
required main-kernel verification remains outstanding.
