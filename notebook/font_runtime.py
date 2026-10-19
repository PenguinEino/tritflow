"""Use exact Nimbus Roman metrics for circuit labels on clean machines.

The figure's padding check depends on font metrics. Register the same four
official Ubuntu OTF files with Matplotlib, independent of system fontconfig.
Only font data is unpacked; no font package scripts or helpers are executed.
"""
from hashlib import sha256
import json
from pathlib import Path
import subprocess


LOCK = Path(__file__).with_name('fonts-lock.json')


def install_fonts(prefix, download):
    pin = json.loads(LOCK.read_text())
    root = Path(prefix)/('fonts-'+pin['sha256'][:16])
    archive = Path(prefix)/'debs'/('fonts-urw-base35_'+pin['version']+'_all.deb')
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.is_file() or sha256(archive.read_bytes()).hexdigest() != pin['sha256']:
        download(pin['url'], archive, pin['sha256'])
    if not (root/'.complete').is_file():
        root.mkdir(parents=True, exist_ok=True)
        subprocess.run(['dpkg-deb','-x',str(archive),str(root)],check=True)
        hashes = {name:sha256((root/pin['directory']/name).read_bytes()).hexdigest() for name in pin['fonts']}
        (root/'.complete').write_text(json.dumps(hashes,sort_keys=True)+'\n')
    return root


def register_fonts(root):
    from matplotlib import font_manager
    pin = json.loads(LOCK.read_text())
    root = Path(root)
    font_manager.fontManager.ttflist[:] = [f for f in font_manager.fontManager.ttflist
                                          if f.name != 'Nimbus Roman']
    for name in pin['fonts']:
        path = root/pin['directory']/name
        if sha256(path.read_bytes()).hexdigest() != pin['font_sha256'][name]:
            raise RuntimeError('Pinned font changed: '+str(path))
        font_manager.fontManager.addfont(str(path))
