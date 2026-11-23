---
id: CASE-024
title: Controller restarts after long uptime
symptom_component: control_system
root_cause_component: control_system
operating_mode: standby
alarm_categories: [controller_fault, comm_loss]
impact: warning
source: synthetic
reviewed: false
---

## Symptoms

The PCS controller restarted on its own every few weeks. Each restart caused a short communication loss with the EMS and a controller fault entry in the log. Restarts happened most often after long periods in standby.

## Conditions

- Long periods in standby between dispatch events.
- Controller firmware unchanged for a long time.
- Auxiliary supply measured stable during the restarts.

## Troubleshooting steps

1. Checked the auxiliary supply at the controller during restarts (recorded with a logger). It stayed stable, ruling out a supply problem (compare CASE-010).
2. Reviewed the controller's diagnostic log: each restart was triggered by its watchdog, after its free memory had declined steadily since the previous restart.
3. Compared with other units running the same firmware: they showed the same slow memory decline, but most had been restarted for maintenance before reaching the limit.
4. Contacted the manufacturer, which confirmed a known memory leak in that firmware version.

## Root cause

A firmware memory leak slowly used up the controller's memory during long uptime. When memory ran out, the watchdog restarted the controller, causing a short loss of communication.

## Resolution

Updated the controller firmware to the version with the memory leak fixed, following the manufacturer's procedure. Memory use stayed stable afterward and the restarts stopped.

## Lessons

Regular restarts after long uptime with a stable power supply suggest a firmware resource leak. Watch memory trends in controller diagnostics.
