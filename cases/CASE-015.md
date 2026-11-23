---
id: CASE-015
title: Communication loss from an overheating network switch
symptom_component: communication
root_cause_component: communication
operating_mode: discharging
alarm_categories: [comm_loss]
impact: warning
source: synthetic
reviewed: true
---

## Symptoms

The EMS lost communication with several PCS units at the same time on hot afternoons. Communication recovered after some minutes. The PCS units kept running on their last setpoints, but the EMS could not dispatch them during the dropouts.

## Conditions

- Hot afternoons, during discharge.
- All affected units were connected through the same network switch in a small communication cabinet.
- The communication cabinet had no active cooling.

## Troubleshooting steps

1. Grouped the dropouts by unit: every affected unit used the same network switch, while units on other switches were unaffected.
2. Checked the switch's event log: it showed restarts at the dropout times.
3. Measured the temperature inside the communication cabinet in the afternoon. It was well above the switch's rated operating temperature.
4. Checked the cabinet: the ventilation opening was blocked and the cabinet was in direct sun.

## Root cause

The network switch overheated in a poorly ventilated cabinet exposed to direct sun and restarted, dropping communication to every unit connected through it.

## Resolution

Cleared the ventilation, added a sun shield, and replaced the switch with an industrial model rated for a higher temperature. No further dropouts were recorded through the rest of the summer.

## Lessons

When several units lose communication at the same moment, look for the shared network device and its environment.
