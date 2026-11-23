---
id: CASE-022
title: False DC overvoltage trips from a DC voltage sensor offset
symptom_component: dc_side
root_cause_component: control_system
operating_mode: charging
alarm_categories: [dc_overvoltage]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

The PCS tripped on DC overvoltage near the end of charging, before the BMS reported that the battery was near its voltage limit. The BMS logs showed battery voltage within normal limits at each trip.

## Conditions

- Charging near the top of the state of charge.
- BMS communication was stable, with no timeouts (unlike CASE-008).
- No changes to charging settings.

## Troubleshooting steps

1. Compared the DC voltage measured by the PCS with the battery voltage reported by the BMS. The PCS reading was consistently higher by a roughly constant amount.
2. Checked the BMS limits and their timing: limits arrived on time and were followed correctly, ruling out a BMS interface problem.
3. [SAFETY] Measured the DC bus voltage with a calibrated instrument following the safety procedure. The real voltage matched the BMS value, not the PCS reading.
4. Traced the difference to the PCS DC voltage sensor, which had developed an offset.

## Root cause

An offset in the PCS DC voltage sensor made the PCS believe the DC voltage was higher than it was. Near the top of charge, the false reading crossed the overvoltage threshold and the PCS tripped, even though the real voltage was normal.

## Resolution

[SAFETY] Replaced the DC voltage sensor and verified the reading against the calibrated instrument and the BMS. End-of-charge trips stopped.

## Lessons

When a DC overvoltage trip comes with healthy BMS voltage and timely limits, compare the PCS and BMS voltage readings. A constant difference points to a sensor offset.
