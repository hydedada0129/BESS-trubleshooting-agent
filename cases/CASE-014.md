---
id: CASE-014
title: DC contactor feedback fault at startup
symptom_component: dc_side
root_cause_component: dc_side
operating_mode: startup_shutdown
alarm_categories: [contactor_fault]
impact: trip
source: synthetic
reviewed: true
---

## Symptoms

The PCS aborted startup with a DC contactor fault. The log showed that the controller commanded the main DC contactor to close, but did not receive the closed-position feedback in time. Sometimes a second attempt succeeded.

## Conditions

- Startup from standby after a shutdown.
- The unit had a high number of start/stop cycles.
- Precharge completed normally before the contactor command.

## Troubleshooting steps

1. Checked the startup sequence in the log: precharge was normal, the close command was sent, and the feedback signal was missing or late.
2. Checked the contactor coil supply voltage during the close command. It was within range, so a weak coil supply was unlikely.
3. [SAFETY] With the DC circuit isolated, operated the contactor manually as allowed by the maintenance procedure and measured the auxiliary feedback contact. The feedback contact closed intermittently even when the main contacts closed.
4. Inspected the auxiliary contact block: worn and contaminated contact surfaces.

## Root cause

The auxiliary feedback contact on the main DC contactor was worn. The main contacts closed correctly, but the feedback signal was unreliable, so the controller treated the contactor as failed and aborted startup.

## Resolution

[SAFETY] Replaced the auxiliary contact block (and the contactor, following the maintenance policy for its cycle count). Startup was reliable afterward.

## Lessons

A contactor fault at startup can be a feedback problem rather than a failure to close. Check the feedback contact separately from the main contacts.
