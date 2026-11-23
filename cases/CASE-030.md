---
id: CASE-030
title: PCS cannot restart after an outage because the control UPS is depleted
symptom_component: auxiliary_power
root_cause_component: auxiliary_power
operating_mode: startup_shutdown
alarm_categories: [aux_power_fault, controller_fault]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

After a long grid outage, the PCS could not restart when the grid returned. The controller had shut down during the outage and did not record the event properly. The startup sequence failed with auxiliary power and controller faults until a manual reset was done.

## Conditions

- Grid outage lasting several hours.
- Control and communication equipment backed by a small UPS.
- UPS batteries several years old, with no recent capacity test.

## Troubleshooting steps

1. Reviewed the controller log: it stopped recording much earlier in the outage than the UPS's rated backup time.
2. Checked the UPS log: it ran on battery for only a fraction of its rated time before shutting down.
3. Tested the UPS battery capacity: well below its rating, consistent with aging.
4. Confirmed the restart failure came from the controller restarting without a clean shutdown and needing a manual reset of a latched fault.

## Root cause

The aged UPS batteries could no longer power the control system through a long outage. The controller lost power uncontrolled, latched a fault, and could not restart automatically when the grid returned.

## Resolution

[SAFETY] Replaced the UPS batteries, added periodic UPS capacity tests to maintenance, and configured the controller to shut down cleanly when the UPS signals low battery. The next outage test showed a clean shutdown and automatic restart.

## Lessons

Backup power for control systems ages silently. Test UPS capacity regularly and make sure the controller shuts down cleanly before the UPS runs out.
