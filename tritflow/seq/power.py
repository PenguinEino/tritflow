"""Channel-side supply-rail reinforcement for high-current ternary registers.

TDFF has several resistor-divider inverters at zero. A 4-um VSS row rail cannot
carry the worst static load through only two ends. Extend VSS 8 um into the
channel below and VDD 4 um above the cell: both become real 12-um M1 conductors.
An explicit 18-um option adds further row capacity for larger sequential examples.
Cell GDS/template bytes remain unchanged. VMID carries no TDFF current and
retains its original 4-um rail. PDK DRC and the ordinary solved EM check qualify
this geometry; this is not internal-cell or transient EM signoff.
"""


def bands(template, enabled=False):
    rails = {n: list(band) for n, band in template['rails'].items()}
    if enabled:
        width = 12. if isinstance(enabled, bool) else float(enabled)
        if width not in (12.,18.):
            raise ValueError('sequential rail reinforcement supports 12 or 18 um')
        rails['VSS'][0] = rails['VSS'][1] - width
        rails['VDD'][1] = rails['VDD'][0] + width
    return rails


def reserve_channels(data, template):
    """Remove M1 tracks that cannot clear the actual widened rail rectangles."""
    enlarged = data['power']['assumptions']['row_rail_bands_um']
    pad = template['rules']['V1'] + 2*template['rules']['V1_enc_M1']
    clearance = pad/2 + max(2., template['rules']['M1_s'])
    forbidden = [(row['y']+a-clearance, row['y']+b+clearance)
                 for row in data['rows'] for rail, (a,b) in enlarged.items()
                 if rail != 'VMID']
    for channel in data['channels']:
        channel['tracks'] = [y for y in channel['tracks']
                             if not any(a < y < b for a,b in forbidden)]
