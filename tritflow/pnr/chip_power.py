"""Three-domain MPW power header using the published DC width/cut limits.

Compact M2 banks contact wider M1 through tall TC arrays. Common rails stay in M2;
supply-pad feeders divide current among multiple wide M1 fingers and TC cuts.
"""

import math
import numpy as np
from tritflow import RAILS


def _via_array(vias, net, x, y, width, height):
    """Real 1.4 um TC cuts at 2.9 um pitch, with at least 1 um enclosure."""
    pitch = 2.9
    nx, ny = max(1, math.floor((width - 3.4) / pitch) + 1), max(
        1, math.floor((height - 3.4) / pitch) + 1
    )
    for i in range(nx):
        for j in range(ny):
            vias.append(
                {
                    "net": net,
                    "x": round(x + (i - (nx - 1) / 2) * pitch, 3),
                    "y": round(y + (j - (ny - 1) / 2) * pitch, 3),
                }
            )


def _power_header(data, macro_pins, core, margin):
    """Three M2 distribution bars, M1 bank fingers, and parallel M1 pad feeds.

    Long common links use M2. M1 pad feeders split the total rail current into
    enough <=44 um strips for the conservative stepped-M1 rating and reserve.
    No new via is placed in a pad opening; the imported PDK cut array is used.
    """
    x0, y0, x1, y1 = core
    totals = {
        r: sum(v[r] for v in data["power"]["rail_currents_a"].values()) for r in RAILS
    }
    widths = {
        r: max(
            6.4 if r == "VMID" else 44.0,
            math.ceil(totals[r] / ((3.7e-3 / 3) * (1 - margin)) * 10) / 10,
        )
        for r in RAILS
    }
    if any(w > 44.0 for w in widths.values()):
        raise ValueError(
            "Chip supply needs parallel M2 bars; reduce the macro size or split the allocation"
        )
    bars, cursor = {}, y1 + 80.0
    for rail in RAILS:
        w = widths[rail]
        bars[rail] = cursor + w / 2
        cursor += w + 8.0
    collector_y = max(cursor + 8.0, 1008.0)
    if collector_y + 16 > 1050.0:
        raise ValueError(
            "Macro leaves insufficient top power-channel space; use fewer rows or more placement effort"
        )
    power = data["power"]
    fingers = []
    for pin in macro_pins:
        rail = pin["name"]
        a, b, c, d = pin["rect"]
        x, w = (a + c) / 2, c - a
        finger_w = 3.4 if rail == "VMID" else min(44.0, 2 * (w + 2.4 - 3.75))
        contact_h = 9.4 if rail == "VMID" else 32.7
        contact_y = y1 + 1 if rail == "VMID" else y1 + 12.65
        extension = 7.0 if rail == "VMID" else 29.0
        power["straps"].append(
            {
                "net": rail,
                "layer": "M2",
                "width": w,
                "points": [[x, y1 - w / 2], [x, y1 + extension - 1.7]],
                "rect": [a, y1 - 6, c, y1 + extension],
            }
        )
        _via_array(power["vias"], rail, x, contact_y, min(w, finger_w), contact_h)
        if rail == "VMID":
            power["rails"].append(
                {
                    "net": rail,
                    "layer": "M1",
                    "width": 3.4,
                    "points": [[x, y1 - 3], [x, bars[rail] + widths[rail] / 2 - 1.7]],
                    "rect": [x - 1.7, y1 - 4.7, x + 1.7, bars[rail] + widths[rail] / 2],
                }
            )
            _via_array(power["vias"], rail, x, bars[rail], 3.4, widths[rail])
            fingers.append((x - 1.7, x + 1.7))
            continue
        # A wide aligned input contact feeds four parallel M1 fingers. Their
        # finite metal resistance shares current across the upper TC arrays;
        # no individual cut or narrow common neck carries the entire bank.
        upper_x = x + (-14.0 if rail == "VDD" else 14.0)
        column_w = (44.0 - 3 * 2.4) / 4
        column_xs = [upper_x + (i - 1.5) * (column_w + 2.4) for i in range(4)]
        power["rails"].append(
            {
                "net": rail,
                "layer": "M1",
                "width": finger_w,
                "points": [[x, y1 - 3], [x, y1 + 50.0]],
                "rect": [
                    x - finger_w / 2,
                    y1 - 4.7,
                    x + finger_w / 2,
                    y1 + 50.0 + finger_w / 2,
                ],
            }
        )
        power["rails"].append(
            {
                "net": rail,
                "layer": "M1",
                "width": finger_w,
                "points": [
                    [min(x, min(column_xs)), y1 + 50.0],
                    [max(x, max(column_xs)), y1 + 50.0],
                ],
            }
        )
        for cx in column_xs:
            high = bars[rail] + widths[rail] / 2
            power["rails"].append(
                {
                    "net": rail,
                    "layer": "M1",
                    "width": column_w,
                    "points": [[cx, y1 + 50.0], [cx, high - 1.7]],
                    "rect": [
                        cx - column_w / 2,
                        y1 + 50.0 - column_w / 2,
                        cx + column_w / 2,
                        high,
                    ],
                }
            )
            _via_array(power["vias"], rail, cx, bars[rail], column_w, widths[rail])
        fingers.append(
            (min(x - finger_w / 2, upper_x - 22), max(x + finger_w / 2, upper_x + 22))
        )
    # Find three genuinely empty M1 corridors, also disjoint from each other.
    used, pads = list(fingers), []
    left = min(
        min(p["rect"][0] for p in macro_pins) - 24, min(a for a, b in fingers) - 10
    )
    right = max(
        max(p["rect"][2] for p in macro_pins) + 24, max(b for a, b in fingers) + 10
    )
    main_bars = {}
    for rail in RAILS:
        bar = {
            "net": rail,
            "layer": "M2",
            "width": widths[rail],
            "points": [[left, bars[rail]], [right, bars[rail]]],
        }
        main_bars[rail] = bar
        power["straps"].append(bar)
    requests = []
    for rail, preferred in zip(RAILS, (-150.0, 650.0, 150.0)):
        if rail == "VMID":
            continue
        pad_count = max(1, math.ceil(totals[rail] / 0.008))
        preferreds = (
            [preferred]
            if pad_count == 1
            else np.linspace(
                -840 if rail == "VDD" else -700,
                840 if rail == "VDD" else 980,
                pad_count,
            )
        )
        requests += [(rail, float(p), pad_count) for p in preferreds]
    for rail, preferred, pad_count in requests:
        required = (totals[rail] / pad_count) * 1.25 / (0.00025 * (1 - margin))
        count = max(1, math.ceil(required / 44.8))
        leg_width = max(6.4, math.ceil(required / count * 10) / 10)
        pitch = leg_width + 4.0
        span = count * leg_width + (count - 1) * 4.0
        candidates = sorted(
            np.arange(-900.0, 901.0, 2.0), key=lambda x: (abs(x - preferred), x)
        )
        cx = next(
            (
                float(x)
                for x in candidates
                if all(x + span / 2 + 3 <= a or x - span / 2 - 3 >= b for a, b in used)
                and all(abs(x - px) >= 150 for _, px, _ in pads)
            ),
            None,
        )
        if cx is None:
            raise ValueError(
                f"No M1 supply corridor for {rail}; use a narrower macro or more rows"
            )
        used.append((cx - span / 2, cx + span / 2))
        main_bars[rail]["points"][0][0] = min(
            main_bars[rail]["points"][0][0], cx - span / 2 - 2
        )
        main_bars[rail]["points"][1][0] = max(
            main_bars[rail]["points"][1][0], cx + span / 2 + 2
        )
        pads.append((rail, cx, 1100.0))
        for i in range(count):
            x = cx + (i - (count - 1) / 2) * pitch
            collector_width = max(16.0, widths[rail])
            power["rails"].append(
                {
                    "net": rail,
                    "layer": "M1",
                    "width": leg_width,
                    "points": [
                        [x, bars[rail] - widths[rail] / 2 + 1.7],
                        [x, collector_y + collector_width / 2 - 1.7],
                    ],
                    "rect": [
                        x - leg_width / 2,
                        bars[rail] - widths[rail] / 2,
                        x + leg_width / 2,
                        collector_y + collector_width / 2,
                    ],
                }
            )
            _via_array(power["vias"], rail, x, bars[rail], leg_width, widths[rail])
            # A shallow cut array stays well away from the PRO opening.
            _via_array(
                power["vias"], rail, x, collector_y, leg_width, max(16.0, widths[rail])
            )
        power["straps"] += [
            {
                "net": rail,
                "layer": "M2",
                "width": max(16.0, widths[rail]),
                "points": [[cx - span / 2, collector_y], [cx + span / 2, collector_y]],
            },
        ]
        # Five touching 8 um strips are physically one 40 um pad neck. Keep
        # separate centerlines and ideal taps across the actual pad metal in
        # the resistor model, rather than forcing all current into its center.
        for offset in (-16.0, -8.0, 0.0, 8.0, 16.0):
            power["straps"].append(
                {
                    "net": rail,
                    "layer": "M2",
                    "width": 8.0,
                    "points": [[cx + offset, collector_y], [cx + offset, 1100.0]],
                }
            )
        power["straps"].append(
            {
                "net": rail,
                "layer": "M2",
                "width": 40.0,
                "points": [[cx, 1030.0], [cx, 1050.0]],
                "rect": [cx - 20, 1030.0, cx + 20, 1050.0],
            }
        )
    # Keep the VMID crossover outside every supply feeder and pad keep-out.
    main_bars["VMID"]["points"][0][0] = -960.0
    return pads, {
        "rail_current_envelope_a": totals,
        "M2_width_um": widths,
        "reserve": margin,
        "collector_y_um": collector_y,
        "vmid_escape_um": [-960.0, bars["VMID"]],
        "M1_step_limit_a_per_um": 0.00025,
        "M2_field_limit_a_per_um": 3.7e-3 / 3,
    }
