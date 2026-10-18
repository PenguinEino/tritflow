"""Name a routed realization by dataset/seed, retaining its exact native hashes.

A seed explains why two placements differ; it is not an artifact identifier.
Keep both PNR and GDS digests with every displayed routing realization.
"""

from hashlib import sha256
import json
from pathlib import Path
import zipfile


def routing_record(pnr_bytes, gds_bytes, dataset):
    pnr = json.loads(pnr_bytes)
    return {"dataset":dataset,"top":pnr["top"],"seed":pnr["seed"],
            "pnr_sha256":sha256(pnr_bytes).hexdigest(),
            "gds_sha256":sha256(gds_bytes).hexdigest()}


def routing_files(pnr, gds, dataset):
    return routing_record(Path(pnr).read_bytes(),Path(gds).read_bytes(),dataset)


def routing_label(record, *, state=None, digest=False):
    label = f"{record['dataset']}/{record['top']} · seed {record['seed']}"
    if digest:
        label += " · GDS "+record['gds_sha256'][:12]
    if state:
        label += f" ({state})"
    return label


def archive_routing(path):
    """Read portable identities from hash-checked ZIP members, without extraction."""
    records = {}
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        for name in manifest['records']:
            data = []
            for suffix in ('pnr.json','gds'):
                member = f'{name}/{name}.{suffix}'
                raw = archive.read(member)
                if sha256(raw).hexdigest() != manifest['files'][member]:
                    raise ValueError(f'Recorded routing artifact hash mismatch: {member}')
                data.append(raw)
            records[name] = routing_record(*data,'four-design')
    return records
