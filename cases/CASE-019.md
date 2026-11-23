---
id: CASE-019
title: Grid voltage trips caused by a wrong reactive power setpoint after an EMS update
symptom_component: ac_grid
root_cause_component: communication
operating_mode: charging
alarm_categories: [grid_voltage_abnormal]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

After an EMS software update, the PCS began tripping on grid voltage abnormal while charging. Before the update, the same unit had run for months without voltage trips. The grid operator reported no changes on the grid.

## Conditions

- Charging, with the EMS sending reactive power setpoints.
- EMS software updated a few days before the first trip.
- No changes to PCS firmware or settings.

## Troubleshooting steps

1. Checked PCS reactive power output at the trip times: it was far higher than expected for the site's voltage control strategy.
2. Compared the reactive power setpoint received by the PCS with the value the EMS intended to send. The received value was off by a constant factor.
3. Reviewed the EMS update notes and the register mapping: the update had changed the scaling of the reactive power setpoint, but the PCS still used the old scaling.
4. Confirmed that the excessive reactive power pushed the local voltage above the protection limit.

## Root cause

The EMS update changed the scaling of the reactive power setpoint in the communication interface. The PCS interpreted the value with the old scaling and produced far too much reactive power, which raised the local voltage until it tripped. The grid voltage alarm was a consequence; the cause was in the communication interface.

## Resolution

The EMS scaling was corrected to match the PCS interface definition, and a check of key setpoints was added to the EMS update procedure. Voltage trips stopped.

## Lessons

When trips start right after a software update elsewhere in the system, compare sent and received setpoints before investigating the PCS or the grid.
