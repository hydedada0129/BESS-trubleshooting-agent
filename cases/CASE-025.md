---
id: CASE-025
title: AC ground fault from a damaged cable in the AC trench
symptom_component: ac_grid
root_cause_component: ac_grid
operating_mode: discharging
alarm_categories: [ground_fault]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

The PCS tripped on an AC ground fault during discharge after a period of heavy rain. Restart attempts failed with the same alarm. The DC side insulation readings were normal.

## Conditions

- Discharging, shortly after heavy rain.
- AC cables between the PCS and the transformer run in a buried trench.
- Recent civil work near the trench.

## Troubleshooting steps

1. Confirmed the alarm was on the AC side: DC insulation monitoring was normal.
2. [SAFETY] Isolated the AC side and measured insulation resistance of the PCS output, the AC cables, and the transformer winding separately. The AC cable section had very low insulation resistance on one phase.
3. Walked the trench route: found disturbed soil where recent civil work had crossed the trench.
4. [SAFETY] Exposed the cable at that point: the outer sheath and insulation were damaged, and water had entered.

## Root cause

The AC cable was mechanically damaged during nearby civil work. Rainwater then reached the damaged insulation and created a path to ground, causing the ground fault trip.

## Resolution

[SAFETY] Replaced the damaged cable section with a proper joint and tested insulation before re-energizing. The trench route was marked to prevent future damage.

## Lessons

Sectional insulation testing (PCS, cable, transformer) quickly locates AC ground faults. Recent civil work near cable routes is a strong hint.
