# STA stream

## In progress

Read AGENTS.md, concept, interfaces, STA brief and CELLS/SIM/PNR handoffs.
Implementing published-table interpolation, transition-conditioned graph timing,
exact settled endpoint sensitization, Plotly reports and pinned-PDK validation.
Only STA-owned paths are modified. No packages installed or git state changed.

## Decisions

- Consume CELLS schema-1 `.timing.json`, including separate synchronous multi-pin
  observations and per-pin maximum biased AC input C. A partial `.char.json`
  sequence cannot replace missing directed timing surfaces; fail explicitly.
- Linear interpolation in physical load/ramp units. Strict interpolation is
  available; default graph analysis explicitly records endpoint load extension
  between zero and twice the largest measured load. Never extrapolate ramps or
  interpolate through failed/null samples. Some real adder nets exceed 1 pF.
- Keep all graph predecessors per directed transition, then use best-first
  backward search with reduced ternary decision diagrams to reject incompatible
  reconvergent endpoint conditions. Critical paths include complete primary-input
  before/after patterns. No random sensitization or silent path truncation.
- Add measured cell settling with a fixed full 1 ns ramp per stage. This is a
  nominal engineering estimate: no propagated slew, waveform shape or skew;
  intermediate endpoint-stable glitches do not propagate. Synchronous multi-pin
  observations cannot validate arbitrarily skewed signals. No upper-bound claim.
- Fanout uses maximum biased AC C, plus merged route C (public extraction API)
  and 10 fF external load by default. Validation will also use LVS-mapped full
  top-net GDS C to match SIM. This includes connected cell terminal metal once.
- Compare all endpoint-pair STA and STA restricted to SIM's actual consecutive
  vector pairs separately; measured vector maxima are not global SPICE bounds.

## Validation / blockers

Implementation checks and the first real-netlist probes are running. SIM/PNR
are republishing; validation will record source freshness and repeat on changes.
No user decision or interface change is needed.

## Interface requests

None.

## Commands

`python3 -m pytest tests/sta -q` (tests under construction).
