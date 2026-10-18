"""Recorded evidence retains real native checks and rejects edited inputs/files."""

from pathlib import Path
import gzip
import json
import sys
import zipfile

import numpy as np
import pytest

from tritflow import ROOT, PDK_ROOT, flow

sys.path.insert(0,str(ROOT/"notebook"))
from cache import Cache, source_manifest, runtime_fingerprint
from campaign import RecordedCampaign, publish_campaign
from experiments import complete_design, experiment_artifacts


def test_publish_actual_inv_retain_native_evidence_and_reject_corruption(tmp_path):
    net = flow.loads("module recorded_inv(input trit a,output trit y); assign y=~a; endmodule").synthesize()
    folder = tmp_path/net.top
    vectors=[(-1,),(0,),(1,)]
    options={"net":net.to_json(),"vectors":vectors,"load":100e-15}
    cache=Cache(tmp_path/"cache",runtime_fingerprint(ROOT,PDK_ROOT),sources=source_manifest(ROOT,PDK_ROOT))
    result=cache.run("four-"+net.top,options,
        lambda:complete_design(net,folder,vectors,lambda v:{"y":-v[0]},load_f=100e-15,anneal_steps=0),
        artifacts=lambda r:experiment_artifacts(r,folder,net.top))
    archive=tmp_path/"campaign.zip"
    manifest=publish_campaign(cache.directory,archive,ROOT,PDK_ROOT,designs=(net.top,))
    assert any(p.endswith(".gds") for p in manifest["files"])
    assert any(p.endswith(".lvsdb") for p in manifest["files"])
    assert any(p.endswith("reference.spice") for p in manifest["files"])
    recorded=RecordedCampaign(archive,ROOT,PDK_ROOT)
    restored=recorded.get(net.top,options)
    assert restored["lvs"]["matched"] and restored["drc"]["clean"]
    np.testing.assert_array_equal(restored["post"]["waveforms"]["time"],result["post"]["waveforms"]["time"])
    assert recorded.get(net.top,{**options,"load":1e-12}) is None
    assert RecordedCampaign(archive,tmp_path/"missing-root",PDK_ROOT).get(net.top,options) is None
    assert RecordedCampaign(tmp_path/"missing.zip",ROOT,PDK_ROOT).manifest is None
    corrupted=tmp_path/"corrupt.zip"
    with zipfile.ZipFile(archive) as original, zipfile.ZipFile(corrupted,"w") as copy:
        for name in original.namelist():
            data=original.read(name)
            if name.endswith(".gds"): data += b"changed physical evidence"
            copy.writestr(name,data)
    with pytest.raises(ValueError,match="evidence hash mismatch"):
        RecordedCampaign(corrupted,ROOT,PDK_ROOT)
    assert RecordedCampaign(corrupted,ROOT,PDK_ROOT,enabled=False).manifest is None
    saved_path=cache.directory/f"four-{net.top}.json.gz"
    with gzip.open(saved_path,"rt") as stream: saved=json.load(stream)
    saved["options"]["load"]=1e-12
    with gzip.open(saved_path,"wt") as stream: json.dump(saved,stream)
    with pytest.raises(ValueError,match="execution cache key"):
        publish_campaign(cache.directory,tmp_path/"invalid.zip",ROOT,PDK_ROOT,designs=(net.top,))
