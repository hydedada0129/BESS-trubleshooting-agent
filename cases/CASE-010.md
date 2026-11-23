---
id: CASE-010
title: Communication loss caused by auxiliary supply dips
symptom_component: communication
root_cause_component: auxiliary_power
operating_mode: standby
alarm_categories: [comm_loss, aux_power_fault]
impact: warning
source: synthetic
reviewed: true
---

## Symptoms

The EMS reported short communication losses with the PCS, a few times a day, while the PCS was in standby. The communication cabling, settings, and shield grounding all checked out fine, and replacing the communication cable did not help.

## Conditions

- PCS in standby, cooling running intermittently.
- The communication gateway is powered from the same auxiliary supply as the cabinet fans and heaters.
- Dropouts happened at irregular times of day.

## Troubleshooting steps

1. Compared dropout times with auxiliary load events. Each dropout matched a moment when cabinet heaters or fans switched on.
2. Checked the gateway's own log: it showed reboots matching the dropouts, not link errors.
3. Recorded the auxiliary voltage at the gateway's supply input. It dipped briefly below the gateway's minimum input voltage when large auxiliary loads started.
4. [SAFETY] Inspected the auxiliary distribution: the gateway shared a long, undersized branch circuit with the heaters.

## Root cause

The communication gateway rebooted during short auxiliary voltage dips caused by heaters and fans starting on the same undersized branch circuit. The problem showed up as communication loss, but the root cause was the auxiliary power supply.

## Resolution

[SAFETY] Moved the gateway to a separate, protected control supply branch with ride-through capability. Communication dropouts stopped.

## Lessons

If communication loss persists after the cabling checks out, check whether the communication device itself is rebooting, and look at its power supply.
