"""Supplement a finished campaign with actual ELF/shared-library content hashes.

Run on its producer host, after the completed review. This reads only the
qualified runtime cache and writes only this campaign. Launch-wrapper hashes
remain in the original cache identity; this separate supplement also identifies
the KLayout ELF and its KLayout shared libraries, without relabeling a cache key.
"""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "results/dot_scaling"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def main():
    publication = ROOT / "results/dot_scaling.json"
    data = json.loads(publication.read_text())
    if not data.get("complete") or data.get("review_state") != "complete":
        raise RuntimeError("Record native payloads only after the campaign and review finish")
    host = platform.node()
    if any(row["producer"]["hostname"] != host for row in data["rows"]):
        raise RuntimeError("Native payloads must be recorded on the actual producer host")
    runtime = json.loads((DIRECTORY / "remote_environment.json").read_text())["resolved_runtime"]
    spice = Path(runtime["NGSPICE_PAYLOAD"])
    native_root = spice.parents[2]
    klayout = native_root / "usr/bin/klayout"
    paths = [spice, klayout, Path(runtime["NGSPICE_BINARY"]), Path(runtime["KLAYOUT_BINARY"]),
             *sorted((native_root / "usr/lib/klayout").glob("*.so*")),
             *sorted((native_root / "usr/lib/x86_64-linux-gnu").glob("ld-linux*.so*"))]
    for path in paths:
        if not path.resolve().is_relative_to(ROOT):
            raise RuntimeError("The qualified cache must remain inside this checkout")
    if digest(spice) != data["provenance"]["simulator"]["binary_sha256"]:
        raise RuntimeError("The simulator payload differs from the one recorded by the experiment")
    manifest = dict(hostname=host, machine=platform.machine(), recorded_utc=datetime.now(timezone.utc).isoformat(),
                    ngspice_payload_sha256=digest(spice), klayout_payload_sha256=digest(klayout),
                    files_sha256={str(p.relative_to(ROOT)): digest(p) for p in paths},
                    scope="Supplementary hashes read from the same qualified runtime cache after the completed runs; "
                          "the original launch-wrapper and simulator payload identities are retained unchanged.")
    path = DIRECTORY / "native_binary_hashes.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    data["native_payload_provenance"] = dict(hostname=host, manifest=str(path.relative_to(ROOT)),
                                            ngspice_payload_sha256=manifest["ngspice_payload_sha256"],
                                            klayout_payload_sha256=manifest["klayout_payload_sha256"])
    for row in data["rows"] + data.get("optional_attempts", []):
        row["native_payload_provenance"] = data["native_payload_provenance"]
    data["evidence_sha256"].update({str(p.relative_to(ROOT)): digest(p) for p in (path, Path(__file__).resolve())})
    temporary = publication.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temporary.replace(publication)
    print(json.dumps(data["native_payload_provenance"], indent=2))


if __name__ == "__main__":
    main()
