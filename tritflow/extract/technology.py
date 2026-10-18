"""Reviewed IP62 process facts, distinguished from unprovided interconnect data.

Page numbers are one-based PDF/printed pages (they agree in OS00). The open
manual's resistor sheet values and capacitor-device density are not metal R/C.
No resistor model is replaced by a simplified sheet approximation here.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from tritflow import PDK_ROOT

REFERENCE = 'OS00_リファレンスマニュアル_rev1.1.pdf'
ESD = 'OS04_ESD保護素子ガイドライン_rev1.pdf'

# No metal/contact resistance or metal-to-substrate area/fringe coefficients
# were found in the seven open IP62 documents or the four model libraries.
DEFAULT_SHEET_OHM = {'M1':.05, 'M2':.05}
DEFAULT_VIA_OHM = .05
DEFAULT_CAP_COEFFICIENTS = {
    'M1':{'area_f_per_um2':.03453e-15,'fringe_f_per_um':.02e-15},
    'M2':{'area_f_per_um2':.01727e-15,'fringe_f_per_um':.02e-15}}

EM_LIMITS = {
    'source':REFERENCE, 'page':17, 'tables':['I-3-1','I-3-3'],
    'M1_field':{'width_um':2.,'current_a':900e-6},
    'M2_field':{'width_um':3.,'current_a':3.7e-3},
    'M1_step':{'width_um':2.,'current_a':500e-6},
    'TC':{'cut_um':1.4,'current_a':780e-6,'instantaneous_current_a':7.8e-3},
    'scope':'Published width/cut-specific limits; no lifetime/temperature derating supplied. Linear metal-width scaling is an engineering interpretation.'}


def parameter_audit(pdk=PDK_ROOT):
    """Return portable facts, absent-data decisions and hashes of reviewed sources."""
    root = Path(pdk).expanduser()
    docs = root/'openIP62/IP62/Technology/doc'
    models = root/'libs.tech/spice/models'
    paths = sorted(docs.glob('*.pdf')) + sorted(models.glob('*'))
    hashes = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in paths if p.is_file()}
    return {
        'source_sha256':hashes,
        'metal_sheet_ohm_per_square':{'values':dict(DEFAULT_SHEET_OHM),'origin':'assumption',
            'reason':'No metal sheet resistance found; retain assumed aluminum rho=2.5e-8 ohm m / 0.5 um thickness.'},
        'via_ohm':{'value':DEFAULT_VIA_OHM,'origin':'assumption',
            'reason':'No TC resistance or generic contact resistance found.'},
        'wire_capacitance':{'values':deepcopy(DEFAULT_CAP_COEFFICIENTS),'origin':'assumption',
            'reason':'No metal-to-substrate area/fringe coefficients found; retain SiO2 er=3.9, effective heights 1/2 um and 0.02 fF/um fringe.'},
        'document_resistor_sheet_ohm_per_square':{
            'RR':1000.,'RS_poly':120.,'width_um':6.,'tolerance_percent':15.,
            'source':REFERENCE,'page':9,'table':'I-2-4',
            'use':'Device-resistor specifications, not metal. Existing nonlinear PDK device models remain authoritative in SPICE.'},
        'model_resistors':{'source':'models_IP62_res_v5.lib',
            'RS_geometry_coefficient_ohm':95.,'RR_geometry_coefficient_ohm':834.54,
            'use':'Empirical width/length, voltage, end and temperature corrections; constants are not generic contact or metal sheet resistance.'},
        'capacitor_device':{'source':REFERENCE,'page':10,'table':'I-2-5',
            'CSIO_f_per_um2':.6e-15,'use':'Capacitor device, not metal-to-substrate interconnect.'},
        'intermetal_esd_rule':{'source':ESD,'page':7,'overlap_um2':64000.,
            'capacitance_at_least_f':2e-12,'derived_f_per_um2':2e-12/64000.,
            'use':'ESD M1/M2 overlap sizing rule (31.25 aF/um2 derived); not a characterized substrate/fringe coefficient. Not substituted or added as generic coupling.'},
        'parasitic_extraction':{'source':REFERENCE,'page':5,'table':'I-1-2','available':False},
        'em_limits':deepcopy(EM_LIMITS)}
