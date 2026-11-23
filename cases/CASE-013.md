---
id: CASE-013
title: Grid frequency trips from protection settings tighter than required
symptom_component: ac_grid
root_cause_component: ac_grid
operating_mode: charging
alarm_categories: [grid_frequency_abnormal]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

The PCS tripped on grid frequency abnormal a few times a month while charging. Each time, the grid operator reported that the frequency had stayed within the normal operating range defined by the grid connection requirements.

## Conditions

- Charging during periods of fast frequency changes (e.g., large generator or load changes on the grid).
- Unit commissioned recently; protection settings were copied from another project.
- Other generators in the area did not disconnect at those times.

## Troubleshooting steps

1. Compared the PCS frequency measurements at each trip with independent grid recordings. The measurements agreed, so the sensing was correct.
2. Reviewed the active frequency protection settings: both the frequency limits and the rate-of-change-of-frequency limit were tighter than required by the local grid connection requirements.
3. Compared the trip events with the settings: each trip was caused by the rate-of-change limit during short, normal grid disturbances.

## Root cause

The frequency protection settings had been copied from a project with different requirements. They were tighter than the local requirements, so the PCS disconnected during normal grid disturbances it should have ridden through.

## Resolution

With approval from the grid operator, the protection settings were corrected to the local requirements and documented. No further frequency trips occurred during similar grid events.

## Lessons

When the PCS trips on grid frequency but the grid operator sees nothing abnormal, compare the protection settings with the local requirements before suspecting hardware.
