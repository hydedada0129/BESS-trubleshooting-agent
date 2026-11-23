---
id: CASE-005
title: PCS fails to start after auxiliary supply undervoltage
symptom_component: auxiliary_power
root_cause_component: auxiliary_power
operating_mode: startup_shutdown
alarm_categories: [aux_power_fault]
impact: trip
source: synthetic
reviewed: true
---

## Symptoms

After a planned outage, the PCS would not complete its startup sequence. The controller rebooted several times during startup, and the log showed an auxiliary power fault each time the cooling fans and contactor coils switched on.

## Conditions

- First startup after a planned shutdown of the site's auxiliary supply.
- Auxiliary power comes from a dedicated transformer feeding the control and cooling circuits.
- Battery and grid were normal.

## Troubleshooting steps

1. Correlated the controller reboots with startup events in the log: each reboot followed the moment fans and contactor coils were energized.
2. Checked the auxiliary supply voltage at no load: within normal range.
3. Recorded the auxiliary voltage during a startup attempt. It dropped sharply when the fans started, below the controller's minimum supply voltage.
4. [SAFETY] Inspected the auxiliary supply path: transformer tap setting, terminals, and fuses. Found a loose, discolored terminal on the auxiliary supply input.

## Root cause

A high-resistance terminal connection on the auxiliary supply input caused a large voltage drop under load. When fans and contactor coils switched on, the control supply fell below its minimum and the controller reset, aborting the startup sequence.

## Resolution

[SAFETY] Replaced the damaged terminal and re-tightened all auxiliary supply connections. The auxiliary voltage stayed within range during startup, and the PCS started normally.

## Lessons

If startup fails at the moment large auxiliary loads switch on, measure the auxiliary voltage under load, not just at idle.
