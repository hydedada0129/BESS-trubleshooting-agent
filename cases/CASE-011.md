---
id: CASE-011
title: Morning insulation fault from moisture in DC cabling
symptom_component: dc_side
root_cause_component: dc_side
operating_mode: standby
alarm_categories: [insulation_fault]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

On humid mornings, the PCS refused to leave standby because of an insulation fault alarm. By late morning the insulation resistance recovered and the unit started normally. On dry days there were no alarms.

## Conditions

- PCS in standby overnight, starting in the early morning.
- High humidity and dew formation in the early hours.
- DC cables run through an outdoor trench and enter the cabinet from below.

## Troubleshooting steps

1. Plotted the insulation resistance readings against time of day and weather. Low values matched humid mornings and recovered as the day warmed up.
2. Checked whether the alarm appeared with the battery side isolated. The fault followed the DC cabling section, not the battery racks.
3. [SAFETY] With the DC circuit isolated, measured the insulation resistance of each DC cable section separately. One section had clearly lower insulation resistance than the others.
4. Inspected that section: a cable gland at the cabinet entry was not sealed and water had collected in the trench and the bottom of the cable entry.

## Root cause

Moisture entered the DC cable entry through an unsealed gland and wet the cable termination area. Overnight condensation lowered the insulation resistance below the threshold until the area dried out.

## Resolution

[SAFETY] Dried and cleaned the terminations, replaced the damaged cable section insulation, sealed the cable glands, and improved trench drainage. Insulation resistance stayed stable through the following humid weeks.

## Lessons

Insulation faults that follow the weather and recover on their own point to moisture ingress. Isolate cable sections one by one to find where it gets in.
