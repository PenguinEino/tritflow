# COLABMCP: real-Colab test of colab-v0

Date: 2026-10-19 (Asia/Tokyo).

## Result

PASS: all 35 code cells completed with status `ok`; zero error outputs.
This completed run supersedes the earlier pre-execution tool-discovery blocker.

- Ref: `colab-v0`.
- Repository: https://github.com/PenguinEino/tritflow
- Commit: `839adbf19f7590221d18d171adaaddb95c8fd27a`.
- Notebook: `/content/tritflow/notebook/tritflow_tr1um.ipynb`.
- Total runner time, including clone: **419.620230 s**.
- nbclient execution time, including notebook setup: **412.107695 s**.
- Settings: `timeout=1800`, `kernel_name="python3"`, `allow_errors=True`,
  `resources={"metadata":{"path":"/content/tritflow"}}`.
- One unmodified run; no patches or retries.
- A fresh clone and a new nbclient kernel ran in an existing Colab runtime;
  this does not establish a newly provisioned VM or an interactive UI Run all.
- All notebook work used Colab MCP. Chrome was used only to approve the
  authorised local-MCP connection dialog. No sign-in, OAuth, Save, or Share action.

## Per-cell results

Indices are zero-based positions in the source notebook, including Markdown cells.

| Index | Cell ID | Status |
|---:|---|---|
| 1 | `setup` | ok |
| 2 | `imports` | ok |
| 4 | `opening_inputs` | ok |
| 5 | `method-opening` | ok |
| 6 | `opening` | ok |
| 8 | `method-gates` | ok |
| 10 | `gates` | ok |
| 12 | `method-sizing` | ok |
| 13 | `sizing` | ok |
| 15 | `method-cells` | ok |
| 16 | `cells` | ok |
| 19 | `method-arithmetic` | ok |
| 20 | `arithmetic` | ok |
| 22 | `method-synthesis` | ok |
| 23 | `synthesis` | ok |
| 24 | `method-schematic` | ok |
| 26 | `method-pnr` | ok |
| 27 | `pnr` | ok |
| 29 | `method-pre` | ok |
| 30 | `pre` | ok |
| 32 | `published` | ok |
| 34 | `method-sta` | ok |
| 35 | `sta` | ok |
| 38 | `method-edit` | ok |
| 39 | `method-pick` | ok |
| 40 | `method-custom` | ok |
| 41 | `custom_check` | ok |
| 42 | `method-custom_layout` | ok |
| 43 | `custom` | ok |
| 45 | `method-broken` | ok |
| 48 | `method-shuttle` | ok |
| 49 | `shuttle` | ok |
| 53 | `characterization` | ok |
| 54 | `four` | ok |
| 55 | `final` | ok |

## Full tracebacks

None. Every code cell's error-output list was empty; nbclient raised no execution exception.

## Reproduction

Follow `briefs/COLABMCP.md` with REF=colab-v0: remove /content/tritflow,
shallow-clone the ref, print its commit, then execute the notebook with the
nbclient settings above. Print each code cell's index, ID, status, and full
ANSI-stripped error tracebacks.

## Completion / handoff

- Done: connection, clone, one nbclient execution, per-cell/error collection.
- Deleted temporary runner cell `48uI3ouwJFPB`; `get_cells` verified that only
  the original empty cell `lIYdn1woOS1n` remains.
- In progress: none.
- Blockers: none.
- Interface requests: none.
- Local packages installed: none.
- No stream implementation was changed, committed, or pushed.
- Validation: this real-Colab notebook execution is the stream test; there is
  no COLABMCP unit-test directory.


---

# PIN continuation: official ngspice 42, fresh-kernel check

2026-10-19. PASS: all 35 code cells, zero error outputs.

- Base commit: `839adbf19f7590221d18d171adaaddb95c8fd27a`.
- Tested working patch archive SHA-256: `23bc1f3fd193485351f0dca9fee1b0fc150c6a0a3adbadcae3c38941a8bb978c` (857 files; 18,508,543 bytes).
- Notebook SHA-256: `e04341e12be34ed5228e29b5e153e6b4ea9decf86bec30154dcd01409bb3c0f3`.
- nbclient time: **307.769739 s**; outer runner: **310.640253 s**.
- Ubuntu 24.04.5 x86_64; Python 3.13.16; official ngspice 42+ds-3build1; native KLayout 0.30.6.
- Fresh nbclient kernel in the existing Colab VM; one connected scratch notebook and no concurrent Colab run. This is not a newly provisioned VM or an interactive UI Run all.
- Actual IN_COLAB/setup branch executed after removing runtime.json. Only the dirty-tree rejection was relaxed for the explicitly transferred patch; full-SHA/origin/version/marker checks remained active. No source commit or release was published.
- `timeout=1800`, `allow_errors=True`, exact interpreter/prefix assertion.
- Preloaded NumPy 2.1.3, Matplotlib 3.10.0, Pillow 11.3.0, IPython 7.34.0 and widgets/dependencies were preserved. SciPy 1.16.3, Plotly 5.24.1 and the other unloaded packages used the hashed private target.
- Setup, Ruby smoke and font registration passed. Both loader audits resolve all entries inside the locked root (ngspice 33, KLayout 114).
- Fig. 2: ten DC sweeps, numerical assertions and final PNG inspection passed. Every pair of B curves differs somewhere; min-pair/max-sweep differences are NAND 4.898209089107485 V, NOR 4.990533432519134 V, NANY 5.118287635735347 V.
- Records: `build/pin42/colab-final-report.json`, `colab-final.log`, `colab-fig2-final.json`, `colab-fig2-final.png`.

## Per-cell results

| Index | Cell ID | Status |
|---:|---|---|
| 1 | `setup` | ok |
| 2 | `imports` | ok |
| 4 | `opening_inputs` | ok |
| 5 | `method-opening` | ok |
| 6 | `opening` | ok |
| 8 | `method-gates` | ok |
| 10 | `gates` | ok |
| 12 | `method-sizing` | ok |
| 13 | `sizing` | ok |
| 15 | `method-cells` | ok |
| 16 | `cells` | ok |
| 19 | `method-arithmetic` | ok |
| 20 | `arithmetic` | ok |
| 22 | `method-synthesis` | ok |
| 23 | `synthesis` | ok |
| 24 | `method-schematic` | ok |
| 26 | `method-pnr` | ok |
| 27 | `pnr` | ok |
| 29 | `method-pre` | ok |
| 30 | `pre` | ok |
| 32 | `published` | ok |
| 34 | `method-sta` | ok |
| 35 | `sta` | ok |
| 38 | `method-edit` | ok |
| 39 | `method-pick` | ok |
| 40 | `method-custom` | ok |
| 41 | `custom_check` | ok |
| 42 | `method-custom_layout` | ok |
| 43 | `custom` | ok |
| 45 | `method-broken` | ok |
| 48 | `method-shuttle` | ok |
| 49 | `shuttle` | ok |
| 53 | `characterization` | ok |
| 54 | `four` | ok |
| 55 | `final` | ok |

## Full tracebacks

None in the accepted real-Colab run. Every code cell has an empty traceback list. Frozen-module debugger and already-existing private-target warnings were nonfatal.

The initial 30-second MCP response contained only progress; completion was accepted only after get_cells showed the completed execution and full report. Chrome was used solely to approve the local-MCP connection dialog. No sign-in, OAuth, Save or Share action. Temporary-cell cleanup is recorded below.

Cleanup complete: deleted added runner cell `Gu8NRlucwvC_`; get_cells verified
that only the original empty cell `lIYdn1woOS1n` remains.

## Final metadata recheck

After restoring historical comparison summaries and fixing archive-backed PDK qualification, applied reader/report patch SHA-256 `f6c4e4f293f33028d09269c0585d9d9931167619ac27c6667f4e3d4f7ecd3574`. The notebook SHA is unchanged. A new kernel completed **35/35 cells in 277.825883 s**, outer time 279.559074 s. The same dirty-tree-only adapter was used. This warm pass used the valid existing runtime marker; the earlier 307.769739 s pass exercised installation. All 10 designs / 39 outputs are qualified/current.

| Index | Cell ID | Status |
|---:|---|---|
| 1 | `setup` | ok |
| 2 | `imports` | ok |
| 4 | `opening_inputs` | ok |
| 5 | `method-opening` | ok |
| 6 | `opening` | ok |
| 8 | `method-gates` | ok |
| 10 | `gates` | ok |
| 12 | `method-sizing` | ok |
| 13 | `sizing` | ok |
| 15 | `method-cells` | ok |
| 16 | `cells` | ok |
| 19 | `method-arithmetic` | ok |
| 20 | `arithmetic` | ok |
| 22 | `method-synthesis` | ok |
| 23 | `synthesis` | ok |
| 24 | `method-schematic` | ok |
| 26 | `method-pnr` | ok |
| 27 | `pnr` | ok |
| 29 | `method-pre` | ok |
| 30 | `pre` | ok |
| 32 | `published` | ok |
| 34 | `method-sta` | ok |
| 35 | `sta` | ok |
| 38 | `method-edit` | ok |
| 39 | `method-pick` | ok |
| 40 | `method-custom` | ok |
| 41 | `custom_check` | ok |
| 42 | `method-custom_layout` | ok |
| 43 | `custom` | ok |
| 45 | `method-broken` | ok |
| 48 | `method-shuttle` | ok |
| 49 | `shuttle` | ok |
| 53 | `characterization` | ok |
| 54 | `four` | ok |
| 55 | `final` | ok |

Full tracebacks: none; every traceback list is empty. Report/log: `build/pin42/colab-after-readers-report.json`, `colab-after-readers.log`. Deleted final runner `AgrTijl7IrRg`; get_cells again verified only the original empty `lIYdn1woOS1n`. No sign-in, OAuth, Save, Share or other Chrome action.

## Latest concurrent-source qualification

Final notebook SHA-256: `7e4ce664606f116103dd959c6ceb3857f281a45392dba5a5ff749a6c52074a62`. Source base remains `839adbf19f7590221d18d171adaaddb95c8fd27a` with an explicitly transferred uncommitted working-tree patch. Concurrent frontend changes in learning.py, methods.py, stages.py and the generated notebook invalidated the preceding archive as intended. The server exported a new verified archive; the minimum, observed-Colab and Docker-lock Python boundaries then each passed 35/35 cells.

Latest transfer: `build/pin42/colab-latest.tar.gz`, 35 files / 7,602,925 bytes, SHA-256 `63f2344972eac84d0b82337e7238a7763afcbcf5e43547c4d2b0699d605f2bbd`. The actual Colab pass used a fresh Python 3.13.16 nbclient kernel in the existing Ubuntu 24.04.5 amd64 VM, executing the actual Colab setup branch with its valid runtime marker. Only the dirty-checkout rejection was relaxed for this known patch. Origin, full source commit and runtime/version checks remained active. This is working-tree qualification; the integrator must separately verify the final immutable release. The earlier 307.769739 s pass exercised installation after removing runtime.json on notebook SHA e04341e12be34ed5228e29b5e153e6b4ea9decf86bec30154dcd01409bb3c0f3.

**35/35 code cells passed in 313.806194 s**; outer time 315.754948 s. Report/log: `build/pin42/colab-latest-report.json` and `colab-latest.log`. Every traceback list is empty.

| Index | Cell ID | Status |
|---:|---|---|
| 1 | `setup` | ok |
| 2 | `imports` | ok |
| 4 | `opening_inputs` | ok |
| 5 | `method-opening` | ok |
| 6 | `opening` | ok |
| 8 | `method-gates` | ok |
| 10 | `gates` | ok |
| 12 | `method-sizing` | ok |
| 13 | `sizing` | ok |
| 15 | `method-cells` | ok |
| 16 | `cells` | ok |
| 19 | `method-arithmetic` | ok |
| 20 | `arithmetic` | ok |
| 22 | `method-synthesis` | ok |
| 23 | `synthesis` | ok |
| 24 | `method-schematic` | ok |
| 26 | `method-pnr` | ok |
| 27 | `pnr` | ok |
| 29 | `method-pre` | ok |
| 30 | `pre` | ok |
| 32 | `published` | ok |
| 34 | `method-sta` | ok |
| 35 | `sta` | ok |
| 38 | `method-edit` | ok |
| 39 | `method-pick` | ok |
| 40 | `method-custom` | ok |
| 41 | `custom_check` | ok |
| 42 | `method-custom_layout` | ok |
| 43 | `custom` | ok |
| 45 | `method-broken` | ok |
| 48 | `method-shuttle` | ok |
| 49 | `shuttle` | ok |
| 53 | `characterization` | ok |
| 54 | `four` | ok |
| 55 | `final` | ok |

Post-check in Colab: no source-manifest mismatches, all 54 native evidence hashes valid, TRITFLOW_FORCE_RUN unset. The source fingerprint also matches locally. Archive SHA-256: `a510d898c31225c01ccbd0794bbd05b4146513c0bb6741789f0c6b48bd82978`.

Deleted both final temporary cells `1sLF4Ju8M5jF` and `hp_TvwJ9PZzY`. A final get_cells returned only original empty cell `lIYdn1woOS1n`. No sign-in, OAuth, Save or Share action. The simulation server is no longer needed; no remote service was modified.
