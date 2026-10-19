"""Install official .debs with a locked loader, leaving the live Colab OS intact.

KLayout embeds Ruby and Python. Keeping its complete Ubuntu closure together
avoids mixing those libraries with a later Colab image. The simulator uses the
same installation method on amd64 and arm64; no tool is compiled or bundled.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import shlex
import subprocess


TRIPLE = {'amd64': 'x86_64-linux-gnu', 'arm64': 'aarch64-linux-gnu'}
LOADER = {'amd64': 'ld-linux-x86-64.so.2', 'arm64': 'ld-linux-aarch64.so.1'}


def native_root(package, lock_path, prefix):
    """A different package closure always gets a fresh installation directory."""
    identity = sha256(Path(lock_path).read_bytes() + (package or {}).get('sha256', '').encode()).hexdigest()[:16]
    return Path(prefix)/('ubuntu-root-'+identity)


def install_native(package, lock_path, prefix, download):
    """Verify each official archive, unpack it, and create explicit tool wrappers."""
    prefix = Path(prefix)
    lock = json.loads(Path(lock_path).read_text())
    architecture = lock['architecture']
    root = native_root(package, lock_path, prefix)
    cache = prefix/'debs'
    cache.mkdir(parents=True, exist_ok=True)
    packages = list(lock['packages'])
    if package:
        packages.append({**package, 'package': 'klayout', 'version': '0.30.6'})
    def fetch(entry):
        path = cache/(entry['package']+'_'+entry['version']+'_'+architecture+'.deb')
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            download(entry['url'], path, entry['sha256'])
        return path
    with ThreadPoolExecutor(max_workers=8) as pool:
        archives = list(pool.map(fetch, packages))
    # A marker is written only after every verified archive has been unpacked.
    if not (root/'.complete').is_file():
        root.mkdir(parents=True, exist_ok=True)
        for path in archives:
            subprocess.run(['dpkg-deb', '-x', str(path), str(root)], check=True)
        (root/'.complete').write_text('official Ubuntu snapshot packages\n')
    loaders = [p.resolve() for p in root.glob('**/'+LOADER[architecture])
               if p.is_file() and p.resolve().is_relative_to(root.resolve())]
    if not loaders:
        raise RuntimeError('Locked Ubuntu closure lacks its dynamic loader')
    triple = TRIPLE[architecture]
    libraries = [root/('usr/lib/'+triple), root/('lib/'+triple), root/'usr/lib', root/'lib',
                 root/('usr/lib/'+triple+'/pulseaudio')]
    wrappers = {}
    for tool in ('ngspice', 'klayout'):
        payload = root/'usr/bin'/tool
        if not payload.is_file():
            continue
        q = shlex.quote
        # Ubuntu's spinit contains absolute codemodel paths. Relocate only
        # that text file; the official simulator and .cm bytes stay unchanged.
        scripts = root/'tritflow-ngspice-scripts'
        scripts.mkdir(exist_ok=True)
        original = root/'usr/share/ngspice/scripts/spinit'
        if tool == 'ngspice':
            (scripts/'spinit').write_text(original.read_text().replace(
                '/usr/lib/'+triple+'/ngspice/', str(root/'usr/lib'/triple/'ngspice')+'/'))
        environment = {'SPICE_LIB_DIR': str(root/'usr/lib'/triple/'ngspice'),
                       'SPICE_SCRIPTS': str(scripts)}
        if tool == 'klayout':
            environment = {'QT_QPA_PLATFORM': 'offscreen',
                'QT_PLUGIN_PATH': str(root/'usr/lib'/triple/'qt5/plugins'),
                'RUBYLIB': ':'.join(map(str, [root/'usr/lib/ruby/3.2.0', root/'usr/lib'/triple/'ruby/3.2.0'])),
                'PYTHONHOME': str(root/'usr')}
        wrapper = prefix/'bin'/tool
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text('#!/bin/sh\nunset LD_LIBRARY_PATH LD_PRELOAD PYTHONPATH PYTHONHOME RUBYOPT\n'
            + ''.join('export '+key+'='+q(value)+'\n' for key, value in environment.items())
            + 'exec '+q(str(loaders[0]))+' --library-path '
            + q(':'.join(map(str, libraries+[root/'usr/lib/klayout'])))+' '+q(str(payload))+' "$@"\n')
        wrapper.chmod(0o755)
        wrappers[tool] = wrapper
    return root, wrappers
