"""Explicit DC biases must hold side inputs during ngspice DC sweeps."""
import re
import shutil

import numpy as np
import pytest

from tritflow import CELLS_DIR, PDK_ROOT
from tritflow.sim import build_testbench, dc_transfer


@pytest.mark.parametrize('scale',[1.,.9])
def test_every_input_source_has_explicit_initial_dc_value(scale):
    circuit='.subckt three A B C Y VDD VMID VSS\nR1 A Y 1k\n.ends three\n'
    bench=build_testbench(circuit,'three',['A','B','C'],['Y'],[(-1,0,1),(1,-1,0)],
                          supplies_v={'VDD':5*scale,'VMID':0.,'VSS':-5*scale})
    sources=[line for line in bench['netlist'].splitlines() if line.startswith('Vin')]
    assert len(sources)==3
    for col,(source,voltage) in enumerate(zip(sources,(-5*scale,0.,5*scale))):
        match=re.fullmatch(rf'Vin{col} \S+ 0 DC (\S+) PWL\(0 (\S+) .+\)',source)
        assert match is not None,source
        assert float(match[1])==float(match[2])==voltage


@pytest.mark.skipif(not shutil.which('ngspice') or not (PDK_ROOT/'libs.tech/spice/models/ip62_models').exists(),
                    reason='ngspice and pinned TR-1um PDK required')
def test_nand_dc_sweep_preserves_negative_and_positive_side_inputs(tmp_path):
    circuit=(CELLS_DIR/'out/NAND/NAND.ext.spice').read_text()
    outputs={}
    for b in (-1,1):
        run=dc_transfer(circuit,'NAND',['A','B'],['Y'],'A',fixed_trits={'B':b},
                        step_v=5,workdir=tmp_path/f'B_{b}')
        data=run['data']
        assert data['v-sweep'][-1]==pytest.approx(5.)
        assert np.allclose(data['v(B)'],5*b,atol=1e-9)
        outputs[b]=data['v(Y)'][-1]
    # At A=+5 V, -min(A,B) changes from +5 to -5 V as B changes.
    assert outputs[-1]==pytest.approx(5.,abs=.5)
    assert outputs[1]==pytest.approx(-5.,abs=.5)
    assert outputs[-1]-outputs[1]>9.
