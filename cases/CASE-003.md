---
id: CASE-003
title: Repeated grid-voltage trips at a weak grid connection
symptom_component: ac_grid
root_cause_component: ac_grid
operating_mode: discharging
alarm_categories: [grid_voltage_abnormal]
impact: trip
source: synthetic
reviewed: true
---

## Symptoms

The PCS tripped several times a week on a grid overvoltage alarm, always while discharging at high power. The grid voltage was normal when the PCS was idle. Trips clustered in hours when local load was low.

## Conditions

- Discharging at high export power.
- Connection point at the end of a long feeder, far from the substation.
- Local load low during the trip hours (night or weekends).

## Troubleshooting steps

1. Compared the voltage at the point of connection with PCS output power. Voltage rose clearly as export power increased.
2. Confirmed the voltage measurement was accurate by comparing PCS readings with an independent power quality meter.
3. Checked whether the PCS reactive power settings matched the grid connection requirements. The unit ran at unity power factor with no voltage support function enabled.
4. Reviewed with the grid operator whether feeder voltage was already near its upper limit at low load. It was.

## Root cause

The connection point had high grid impedance. Exporting high active power at unity power factor raised the local voltage above the protection threshold, especially when local load was low and feeder voltage was already high. The PCS itself was working correctly.

## Resolution

After agreement with the grid operator, a voltage-dependent reactive power function was enabled within the allowed limits, and an active power limit was applied when voltage approached the upper threshold. Overvoltage trips stopped; the energy lost to the power limit was small.

## Lessons

Grid overvoltage trips that correlate with export power and low local load usually point to grid impedance, not a PCS fault. Involve the grid operator before changing any grid support settings.
