---
id: CASE-008
title: DC overvoltage trip caused by a delayed BMS current limit
symptom_component: dc_side
root_cause_component: bms_interface
operating_mode: charging
alarm_categories: [dc_overvoltage, comm_loss]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

The PCS occasionally tripped on DC overvoltage near the end of charging. The PCS alarm pointed at the DC side, but DC voltage measurements and the DC circuit checked out normal. Trips were rare and hard to reproduce.

## Conditions

- Charging at high power near the top of the state of charge.
- The BMS-to-PCS link occasionally logged short communication timeouts.
- Trips did not happen when charging at lower power.

## Troubleshooting steps

1. Lined up the PCS DC voltage trace with BMS limit messages. Just before each trip, the BMS had lowered its charge current limit, but the PCS kept charging at the old current for longer than usual.
2. Found short communication timeouts on the BMS link right before most trips: the reduced limit arrived late.
3. Verified the PCS DC voltage measurement against an independent measurement. It was accurate, so the overvoltage was real, not a sensor fault.
4. Reviewed the PCS behavior on BMS communication loss. It kept the last received limit instead of reducing power, so a late update let the battery voltage overshoot.

## Root cause

The real fault was on the BMS interface. Communication delays meant the reduced charge current limit near the top of charge reached the PCS late. Charging continued at high current, the battery voltage overshot, and the PCS tripped on DC overvoltage. The DC-side alarm was a consequence, not the cause.

## Resolution

Fixed the cause of the communication timeouts on the BMS link and changed the PCS behavior on BMS communication loss to ramp down charging power instead of holding the last limit (agreed with the battery supplier). No further end-of-charge trips occurred.

## Lessons

A DC overvoltage trip at the end of charging with a healthy DC circuit should prompt a check of the timing of BMS limits and communication, not just the DC hardware.
