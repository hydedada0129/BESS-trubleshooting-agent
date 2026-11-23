---
id: CASE-016
title: Insulation fault caused by cooling unit condensation
symptom_component: dc_side
root_cause_component: cooling
operating_mode: standby
alarm_categories: [insulation_fault]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

The PCS reported an insulation fault while in standby, usually in the evening. The DC cabling had passed insulation tests, and the cable entries were sealed. The fault cleared after some hours.

## Conditions

- PCS in standby, with the cabinet air conditioner running.
- Warm, humid ambient conditions.
- The air conditioner had recently been serviced.

## Troubleshooting steps

1. Insulation tests on the DC cable sections were normal, which made the external cabling unlikely.
2. Compared alarm times with air conditioner operation: alarms followed long periods of cooling in standby, when the cabinet was cooled far below the ambient dew point.
3. [SAFETY] Inspected the cabinet interior after isolation: found water traces below the air conditioner and on parts of the DC busbar area.
4. Checked the air conditioner: the condensate drain was blocked, and the temperature setpoint had been set too low during the service.

## Root cause

The cooling unit was over-cooling the cabinet with a blocked condensate drain. Condensed water dripped or formed on DC parts, lowering insulation resistance. The insulation alarm appeared on the DC side, but the cause was the cooling system.

## Resolution

Cleared the condensate drain, restored the correct temperature setpoint, and added a drip shield above the DC area. [SAFETY] Dried and inspected the affected DC parts before re-energizing. No further insulation alarms occurred.

## Lessons

If insulation faults appear inside a sealed cabinet with healthy cabling, check where condensation can form, especially near cooling units.
