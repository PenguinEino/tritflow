# PIN brief: every external dependency at an exact, verified version

User requirement (2026-10-19, absolute): a judge who opens the notebook months from now (review through
ISSCC Feb 2027) must never hit an error caused by a library/OSS version. Pin every library and referenced
OSS completely; where Colab makes pinning impossible, eliminate the dependence or prove compatibility.

Trigger: Colab's apt ngspice (42 today) differs from the local ngspice-46+ dev build used for all evidence;
ngspice-42 treated a bare PWL source as 0 V in .dc (fixed in tritflow/sim/bench.py by an explicit DC value;
keep that fix). The working tree also contains a partially regenerated evidence set from an aborted SIM run
(cells/out/*.char.json, sizing grids, results/sta/propagation/**): ignore/overwrite it, never commit it as is.

Current pins: notebook/setup_pins.json (KLayout 0.30.6 .deb + sha256 per Ubuntu, TR-1um PDK commit + archive
sha256), notebook/requirements-colab.txt (klayout==0.30.6, lark==1.3.1, installed --no-deps), host numpy/
scipy/matplotlib/plotly only minimum-checked (notebook/runtime_support.py), source = tag colab-v0 (movable).

Deliver:
1. ngspice: one exact upstream release (ngspice-46 official tarball, sha256-pinned) used EVERYWHERE.
   - Colab: a prebuilt x86_64 binary for Colab's Ubuntu (check the actual image via the COLABMCP loop,
     briefs/COLABMCP.md), produced reproducibly (preferred: a GitHub Actions workflow in this repo building
     from the pinned tarball and attaching the tarball to a GitHub release; record sha256 in setup_pins.json),
     installed by notebook/setup_colab.py with checksum verification; never apt's ngspice.
   - Local: build the same tarball on this VM (aarch64) into a versioned prefix and make TritFlow use it.
   - TritFlow must locate the pinned binary explicitly (env/runtime.json), and check the version string at
     runtime with a clear message.
2. apt packages pulled by the KLayout .deb (Qt etc.): pin them (e.g. snapshot.ubuntu.com at a fixed date, or
   an explicit package list with versions) so installation is deterministic.
3. Python: list every package the notebook imports. Find out (via COLABMCP, a fresh kernel) which are already
   imported at kernel start. Pin exactly everything that can be pinned without a kernel restart (e.g. install
   into a private target directory placed first on sys.path during setup, --no-deps, hashes). For anything
   preloaded (numpy at least), record the tested versions and run the notebook against the minimum supported
   and current versions locally (uv with pinned Python versions) to prove compatibility.
4. Provide notebook/requirements-lock.txt with hashes and a pinned Dockerfile (base image by digest) for
   fully reproducible local runs; document in README/Appendix briefly (the notebook prose is owned by the
   integrator: propose text in docs/status/PIN.md instead of editing narrative files).
5. A scheduled GitHub Actions job (weekly) that runs the notebook headless in the pinned environment, so drift
   is caught before/through the review period.
6. Recommend the immutable release tag scheme for the final submission (SOURCE_REF must not be a movable tag).
Then: rerun the evidence generation with the pinned ngspice (sizing grid, characterization, cell timing,
post-layout, corners, scaling, paper_evidence) and report any number that changed vs the committed values.
Use the COLABMCP loop to verify the full notebook in real Colab (session isolation: no other Colab sessions).
Confirm Fig. 2 in Colab shows distinct B = −1/0/+1 curves. Do not commit or push; the integrator releases.
Record decisions in docs/status/PIN.md.

## Direction change (user, 2026-10-19 14:40): no bundled binaries, no self-built tools

Avoid bundling binaries and building tools wherever an alternative exists.
- ngspice: use Ubuntu 24.04's package `ngspice=42+ds-3build1` (Colab amd64 and this VM arm64 both run
  Ubuntu 24.04) installed with an exact version from the official snapshot archive (snapshot.ubuntu.com, fixed
  timestamp), together with its exact dependency versions. Same version locally (install it on this VM the same
  way; no ~/.local/opt/ngspice-46). Remove the bundled ngspice archive, its COPYING copy and any build workflow
  for it from the tree. TritFlow still checks the ngspice version string at runtime.
- Keep the explicit DC fix in bench.py (ngspice 42 needs it) and keep the cache key on the binary identity.
- KLayout: the upstream klayout.de .deb (sha256) plus dependency versions from the same snapshot are fine (that
  is a download, not bundling). Prefer plain apt with exact versions from the snapshot over private unpacking if
  it is equally deterministic and simpler; choose the simplest robust option and justify it in PIN.md.
- Python pins as planned (hash-locked downloads, no wheels committed to the repo).
- Then regenerate the evidence ONCE with ngspice 42 and report every changed number versus HEAD.

## Simulation server (user, 2026-10-19 15:15)

Run the heavy evidence producers on `ssh penguin@einosuke-llm-5090` (hostname strata-ubuntu; Ubuntu 24.04.5
x86_64, Ryzen 7 9700X 16 threads, 48 GB RAM, passwordless SSH from this VM; no Docker, no system ngspice/KLayout).
It matches Colab's OS and architecture, so evidence generated there is amd64 like Colab: prefer it as the
authoritative generator. Workspace: ~/tritflow-sim on the remote (rsync the working tree there, excluding
build/ caches; never touch other files in the remote home). Install the pinned toolchain there exactly as Colab
setup does (amd64 snapshot lock, private unpack or apt-snapshot per your design; no sudo). Run the producers
with high parallelism (about 14 jobs), then rsync the regenerated artifacts back into this checkout and
continue verification here. The user stopped the remote's LLM service (strata) for this; do not restart or
modify any remote service yourself — report when the remote is no longer needed.
