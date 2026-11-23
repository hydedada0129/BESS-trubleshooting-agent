---
id: CASE-017
title: DC undervoltage trip caused by a battery rack disconnecting under load
symptom_component: dc_side
root_cause_component: bms_interface
operating_mode: discharging
alarm_categories: [dc_undervoltage, bms_alarm]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

The PCS tripped on DC undervoltage during high-power discharge. The state of charge was still well above the minimum, so a low battery did not explain the trip. A BMS alarm appeared in the BMS log at almost the same time, but the PCS log only showed the DC undervoltage.

## Conditions

- High-power discharge at a medium state of charge.
- Several battery racks in parallel on the same DC bus.
- No PCS parameter changes.

## Troubleshooting steps

1. Merged the PCS and BMS logs on one timeline. A rack disconnection by the BMS came just before the DC undervoltage trip.
2. Checked the BMS reason for the disconnection: one rack's protection had opened its contactor because of a cell temperature alarm.
3. With fewer racks connected, the remaining racks had to supply the same power, so the DC voltage dropped sharply and reached the PCS undervoltage limit.
4. Checked why the BMS did not reduce the discharge current limit before opening the rack. The limit update and the rack disconnection were not coordinated.

## Root cause

A battery rack was disconnected under load by its own protection, and the BMS did not lower the system discharge limit first. The sudden loss of a rack caused the DC voltage dip that tripped the PCS. The root cause was on the battery and BMS side, not the PCS DC circuit.

## Resolution

The battery supplier corrected the sequence so that the system current limit is reduced before a rack is disconnected, and the rack's cell temperature issue was repaired. No further undervoltage trips occurred.

## Lessons

A DC undervoltage trip at a healthy state of charge calls for merging PCS and BMS logs on one timeline. The BMS log often shows what happened first.
