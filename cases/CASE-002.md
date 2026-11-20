---
id: CASE-002
title: Precharge failure at startup
symptom_component: dc_side
root_cause_component: dc_side
operating_mode: startup_shutdown
alarm_categories: [precharge_failure, dc_undervoltage]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

The PCS failed to start. Each startup attempt ended with a precharge failure alarm after the precharge timeout. The DC bus voltage rose slowly and never reached the level needed to close the main DC contactor. Before this, the unit had started normally.

## Conditions

- Startup from a fully shut-down state.
- Battery system reported normal voltage and no BMS alarms.
- No recent maintenance or parameter changes.

## Troubleshooting steps

1. Reviewed the startup sequence in the log: the precharge contactor closed, but the DC bus voltage rose much more slowly than in previous successful startups.
2. Confirmed with the BMS data that the battery-side voltage was normal, ruling out a low battery as the cause.
3. Checked for DC bus loading during precharge (auxiliary loads connected to the DC bus, or a leaking capacitor). None found.
4. [SAFETY] With the system de-energized and isolated, measured the resistance of the precharge resistor. It was far above its rated value, indicating an open or degraded resistor.
5. Inspected the precharge circuit for burned connections; found heat damage at the resistor.

## Root cause

The precharge resistor had degraded, most likely from repeated precharge cycles or an earlier event that overloaded it. Its higher resistance limited charging current so much that the DC bus could not reach the required voltage before the precharge timeout.

## Resolution

[SAFETY] Replaced the precharge resistor and the damaged wiring. Several startup tests followed, each with normal precharge time and successful contactor closing.

## Lessons

A slow DC bus voltage rise during precharge with normal battery voltage points to the precharge path (resistor, contactor, wiring) rather than the battery.
