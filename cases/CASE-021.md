---
id: CASE-021
title: False grid voltage trips from drifting AC voltage sensing
symptom_component: ac_grid
root_cause_component: control_system
operating_mode: discharging
alarm_categories: [grid_voltage_abnormal]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

One PCS tripped on grid overvoltage several times while discharging. Other PCS units on the same connection point, seeing the same grid, did not trip. The grid operator confirmed the voltage was within the normal range.

## Conditions

- Discharging at medium to high power.
- Several identical PCS units connected to the same transformer.
- The affected unit had been in service for several years.

## Troubleshooting steps

1. Compared the AC voltage reported by the affected unit with neighboring units at the same moment. The affected unit consistently read higher than the others.
2. Compared its readings with an independent power quality meter at the connection point. The meter agreed with the neighboring units, not with the affected unit.
3. Checked the protection settings: identical across all units, so settings were not the cause.
4. [SAFETY] Inspected the voltage sensing circuit following the maintenance procedure: found a degraded component on the voltage measurement board, causing a gain error.

## Root cause

The AC voltage measurement circuit had drifted and read higher than the real grid voltage. The PCS therefore saw an overvoltage that did not exist and tripped. The alarm pointed at the grid, but the fault was in the PCS's own sensing.

## Resolution

[SAFETY] Replaced the voltage measurement board and verified the readings against the independent meter. The unit's readings matched its neighbors, and false trips stopped.

## Lessons

If only one unit among several on the same grid trips on grid voltage, compare its measurements with its neighbors and an independent meter before blaming the grid.
