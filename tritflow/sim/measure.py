"""Voltage-band measurements; delay means final entry into the ternary band."""
from __future__ import annotations
import numpy as np
from tritflow import PASS_BAND, TRIT_VOLTS
from .spice import signal_waveform


def settling_time(time, voltage, ideal_v: float, start_s: float, end_s: float,
                  band_v: float = PASS_BAND) -> float | None:
    """Time since edge START of the final band entry, under linear interpolation.

    The output must remain in band through end_s; return None if it does not.
    Resolution is limited by simulator sampling; this is not an analog proof
    between samples. An output already in band and staying there takes zero.
    """
    t, y = np.asarray(time), np.asarray(voltage)
    tolerance = 32*np.finfo(float).eps*max(abs(start_s), abs(end_s), np.max(np.abs(t)) if t.size else 0)
    if (len(t) < 2 or y.shape != t.shape or not np.isfinite(t).all()
            or not np.isfinite(y).all() or np.any(np.diff(t) < 0)
            or band_v <= 0 or start_s >= end_s or t[0] > start_s+tolerance or t[-1] < end_s-tolerance):
        raise ValueError('Invalid or incomplete settling waveform/window')
    # SPICE decimal output can round the requested final time by a few ulps.
    # Permit only floating-point roundoff, never a genuinely truncated run.
    start_s, end_s = max(start_s,float(t[0])), min(end_s,float(t[-1]))
    tt = np.r_[start_s, t[(t > start_s) & (t < end_s)], end_s]
    yy = np.interp(tt, t, y)
    bad = np.flatnonzero(np.abs(yy - ideal_v) > band_v)
    if not len(bad):
        return 0.0
    last = bad[-1]
    if last == len(tt) - 1:
        return None
    boundary = ideal_v + np.sign(yy[last] - ideal_v) * band_v
    fraction = (boundary - yy[last]) / (yy[last + 1] - yy[last])
    crossing = tt[last] + fraction * (tt[last + 1] - tt[last])
    return float(max(0, crossing - start_s))


def measure_sequence(data: dict, bench: dict, expected, *, ideal_volts=None) -> dict:
    """Check 1 ns before segment ends, and watch settling through the whole hold."""
    time = data['time']
    if ideal_volts is None:
        rails=bench.get('supplies_v',{'VDD':5.,'VMID':0.,'VSS':-5.})
        ideal_volts={-1:rails['VSS'],0:rails['VMID'],1:rails['VDD']}
    rows = []
    for k, vector in enumerate(bench['vectors']):
        start = k * bench['hold_s']
        end = (k + 1) * bench['hold_s']
        check = end - 1e-9
        ideal = expected(vector)
        outputs = {}
        for pin in bench['outputs']:
            target = ideal_volts[ideal[pin]]
            waveform = signal_waveform(data, pin)
            observed = float(np.interp(check, time, waveform))
            error = observed - target
            settle = settling_time(time, waveform, target, start, end)
            outputs[pin] = dict(ideal_trit=ideal[pin],ideal_voltage_v=target, voltage_v=observed, error_v=error,
                                passed=abs(error) <= PASS_BAND, settling_s=settle)
        currents = {rail: float(np.interp(check, time, data[f'i({rail.lower()})']))
                    for rail in ('VDD', 'VMID', 'VSS')}
        rows.append(dict(input_trits=list(vector), previous_trits=list(bench['vectors'][k-1]) if k else None,
                         check_s=check, outputs=outputs, rail_current_a=currents,
                         passed=all(v['passed'] and v['settling_s'] is not None for v in outputs.values())))
    return dict(passed=all(r['passed'] for r in rows), rows=rows,ideal_volts={str(k):v for k,v in ideal_volts.items()},
                max_error_v=max((abs(v['error_v']) for r in rows for v in r['outputs'].values()), default=0),
                max_settling_s={p: max((r['outputs'][p]['settling_s'] for r in rows[1:]
                                       if r['outputs'][p]['settling_s'] is not None), default=None)
                                for p in bench['outputs']},
                unsettled=sum(v['settling_s'] is None for r in rows for v in r['outputs'].values()),
                sample_step_s=bench['step_s'])
