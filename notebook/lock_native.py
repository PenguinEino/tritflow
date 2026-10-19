"""Resolve official Ubuntu packages against an empty, signed snapshot index.

Only maintainers run this when deliberately refreshing the native runtime.
Judges download the exact URLs and verify the hashes in the resulting lock.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import unquote


def resolve(architecture, packages, snapshot, output):
    with tempfile.TemporaryDirectory(prefix='tritflow-apt-') as temporary:
        root = Path(temporary)
        for name in ('lists/partial', 'archives/partial'):
            (root/name).mkdir(parents=True)
        (root/'status').write_text('')
        (root/'sources.list').write_text(''.join(
            f'deb [arch={architecture} signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] '
            f'https://snapshot.ubuntu.com/ubuntu/{snapshot}/ {suite} main universe\n'
            for suite in ('noble', 'noble-updates', 'noble-security')))
        options = ['-o', f'APT::Architecture={architecture}', '-o', 'APT::Architectures::='+architecture,
                   '-o', f'Dir::Etc::sourcelist={root}/sources.list', '-o', 'Dir::Etc::sourceparts=-',
                   '-o', f'Dir::State::lists={root}/lists', '-o', f'Dir::State::status={root}/status',
                   '-o', f'Dir::Cache::archives={root}/archives', '-o', 'Acquire::Check-Valid-Until=false',
                   '-o', 'Debug::NoLocking=true', '-o', 'APT::Update::Error-Mode=any',
                   '-o', 'Dir::Cache::pkgcache=', '-o', 'Dir::Cache::srcpkgcache=']
        subprocess.run(['apt-get', *options, 'update'], check=True)
        uris = subprocess.check_output(['apt-get', *options, '--print-uris', '--yes', '--download-only',
                                       '--no-install-recommends', 'install', *packages], text=True)
        entries = []
        for line in uris.splitlines():
            if not line.startswith("'https:"):
                continue
            url, name, size, _ = line.split()
            package, version = name.split('_')[:2]
            version = unquote(unquote(version))
            meta = subprocess.check_output(['apt-cache', *options, 'show', package+'='+version], text=True)
            checksum = re.search(r'^SHA256: (.+)$', meta, re.M)[1]
            entries.append(dict(package=package, version=version, url=url.strip("'"),
                                sha256=checksum, size=int(size)))
        Path(output).write_text(json.dumps(dict(snapshot=snapshot, architecture=architecture,
                                              requested=packages, packages=entries), indent=2)+'\n')
        print('Locked', architecture, len(entries), 'packages', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arch', choices=['amd64', 'arm64'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('packages', nargs='+')
    args = parser.parse_args()
    pins = json.loads((Path(__file__).parent/'setup_pins.json').read_text())
    resolve(args.arch, args.packages, pins['ubuntu_snapshot'], args.output)
