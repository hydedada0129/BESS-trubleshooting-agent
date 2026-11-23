---
id: CASE-012
title: AC overcurrent trip from a failing gate driver
symptom_component: power_module
root_cause_component: power_module
operating_mode: discharging
alarm_categories: [ac_overcurrent]
impact: trip
source: synthetic
reviewed: true
---

## Symptoms

The PCS tripped on AC overcurrent at random moments during discharge, sometimes at low power. The grid was stable at each trip, and no other units on the same connection tripped. The trips became more frequent over several weeks.

## Conditions

- Discharging at various power levels, not only at high power.
- No grid events recorded at the trip times.
- The unit had passed its last scheduled maintenance without findings.

## Troubleshooting steps

1. Checked grid measurements at each trip: no voltage dips, frequency changes, or faults on the grid side.
2. Reviewed the fault records captured at the trip: one phase showed a sudden current spike while the other phases stayed normal.
3. Ran the unit at low power under observation. A short current distortion appeared on the same phase before a trip.
4. [SAFETY] With the unit de-energized, inspected the gate driver board for that phase: found signs of overheating near a driver component and a cracked solder joint.

## Root cause

A failing gate driver on one phase caused irregular switching of the IGBTs. The irregular switching produced current spikes that triggered the AC overcurrent protection, regardless of power level.

## Resolution

[SAFETY] Replaced the gate driver board for the affected phase and checked the IGBT module for damage (none found). The unit ran for several weeks at varying power without further trips.

## Lessons

AC overcurrent trips at low power with a stable grid and a single affected phase point to the switching path inside the PCS, not to the grid.
