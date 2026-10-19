"""Install the official pinned Ubuntu simulator on this VM, without compiling.

The VM has no passwordless sudo. Downloading and unpacking the identical
snapshot packages is deterministic and works without altering its system OS.
"""
import argparse
import json
from pathlib import Path
import platform
from native_runtime import install_native
from setup_colab import download


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', type=Path, default=Path.home()/'.local/opt/tritflow-ubuntu-24.04')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    arch = {'aarch64':'arm64', 'x86_64':'amd64'}[platform.machine()]
    root, wrappers = install_native(None, here/f'ngspice-24.04-{arch}-lock.json', args.prefix, download)
    config = {'NGSPICE_BINARY':str(wrappers['ngspice'].resolve()),
              'NGSPICE_PAYLOAD':str(root/'usr/bin/ngspice')}
    (args.prefix/'ngspice.json').write_text(json.dumps(config, indent=2)+'\n')
    print(json.dumps(config, indent=2))


if __name__ == '__main__':
    main()
