# Runtime identities

The notebook imports NumPy, SciPy, Matplotlib, Plotly, KLayout, Lark, Pillow
(`PIL`) and IPython directly, as well as Python's standard library. Widgets are
HTML/Plotly controls; they do not require ipywidgets. Colab nevertheless imports
ipywidgets and several Matplotlib dependencies before the first cell.

`requirements-lock.txt` pins the complete local execution and test environment,
including transitive dependencies and accepted wheel hashes. Install it in a
fresh Python 3.12/3.13 venv with `--no-deps --require-hashes --only-binary=:all:`.
`requirements-minimum-lock.txt` supplies the lower scientific compatibility
boundary on Python 3.12.12. `requirements-colab.txt` installs only packages not
preloaded by the tested Colab kernel, into setup's private target directory.
No live NumPy, Matplotlib, Pillow or IPython installation is replaced.

Ubuntu's official `ngspice=42+ds-3build1` and its 38-package dependency
closure are locked for both amd64 and arm64. `install_ngspice.py` installs the
local VM runtime in `~/.local/opt/tritflow-ubuntu-24.04`; Colab setup installs the
same simulator version beside KLayout. No binaries or wheels are committed,
and no native tool is built. TritFlow resolves an absolute `NGSPICE_BINARY`,
setup's `runtime.json`, or that local package wrapper and rejects other
ngspice releases. Electrical caches include the ELF SHA-256 and wrapper identity.

KLayout 0.30.6 is downloaded from its official upstream .deb URL and verified
by SHA-256. Its dependency closure and ngspice are unpacked into a private
Ubuntu root. Every .deb has an exact version, snapshot URL and SHA-256 in
`ubuntu-24.04-lock.json`; the smaller `ngspice-24.04-*-lock.json` files install
the simulator alone. The fixed [Ubuntu snapshot](https://snapshot.ubuntu.com/) is `20261019T000000Z`. Wrappers use
that root's dynamic loader, Qt, Ruby, Python and simulator libraries. Only
absolute codemodel paths in the packaged text `spinit` are relocated. The
simulator ELF and codemodel bytes stay unchanged.

Circuit-label metrics also use the exact `fonts-urw-base35=20200910-8` data
package from that snapshot. `fonts-lock.json` records the package SHA-256 and
the four Nimbus Roman OTF hashes; setup unpacks them privately and Matplotlib
registers those exact faces instead of depending on host fontconfig.

Private unpacking avoids replacing Colab's live OS libraries and requires no
sudo on the VM. `lock_native.py` refreshes locks deliberately from signed apt
metadata against an empty package state; notebook setup performs no resolution.
The tested Colab target is Ubuntu 24.04 amd64. Native simulator installation
also supports Ubuntu 24.04 arm64. Other hosts can use the digest-pinned Docker
image (execute as linux/amd64).

From the repository root:

```sh
docker build --platform linux/amd64 -f notebook/Dockerfile -t tritflow-pinned .
docker run --rm --platform linux/amd64 tritflow-pinned
```

The weekly Actions workflow builds this environment and executes every notebook
code cell. Qualification dates, Python boundaries and measured deltas are
recorded in `docs/status/PIN.md`.

The final notebook must be generated *after* the implementation commit exists:
`python3 notebook/make_notebook.py` stamps that full SHA into SOURCE_REF. Ship
this generated notebook in the submission payload. Use signed annotated tags
`isscc2027-v1.0.0`, `isscc2027-v1.0.1`, etc.; never move or reuse a published tag.
Runtime updates require changed locks and a new qualified source commit. A tag alone is never the notebook's executable identity.

Colab's kernel and services are outside this repository's control. Boundary
qualification and weekly checks establish tested compatibility, not a proof for
arbitrary future Colab changes. The pinned Docker environment is the independent
reproduction route if Colab changes its OS or live scientific stack.
