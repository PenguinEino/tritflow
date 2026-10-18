"""Re-run the taped-out DC neighborhoods, directed transitions and cascades."""
from pathlib import Path
import json

import pytest
from tritflow.cells.equivalence import equivalence


@pytest.fixture(scope='module')
def proof(library):
    out,_,_=library
    reference=Path.home()/'balanced-ternary-logic'
    if not reference.is_dir():pytest.skip('Independent taped-out reference checkout unavailable')
    result=equivalence(out,reference)
    assert result['passed'],json.dumps({
        'cells':{k:v['passed'] for k,v in result['cells'].items()},
        'chains':{k:v['passed'] for k,v in result['chains'].items()}},indent=2)
    return result


@pytest.mark.parametrize('cell',['INV','NAND','NOR','NANY','BUF'])
def test_independent_physical_and_analog_equivalence(proof,cell):
    result=proof['cells'][cell]
    assert proof['schematic_equivalence'][cell]['passed']
    assert result['intrinsic_parameters_identical']
    assert result['dc_grid']['original']['points']==(81 if cell in ('INV','BUF') else 81*81)
    for label in ('original','compact'):
        assert result['dc_grid'][label]['max_half_volt_band_error_v']<=.5
        count=6 if cell in ('INV','BUF') else 72
        assert result['transient'][label]['10f']['transitions']==count
        assert result['transient'][label]['100f']['transitions']==count
        if cell=='NANY':
            assert result['transient'][label]['skew_A']['transitions']==72
            assert result['transient'][label]['skew_B']['transitions']==72
    assert result['passed']


@pytest.mark.parametrize('kind',['inverter_two','nor_six','nany_six','mixed_six'])
def test_taped_out_cascade_protocols(proof,kind):
    result=proof['chains'][kind]
    assert result['original']['passed'] and result['compact']['passed']
    assert result['passed']
