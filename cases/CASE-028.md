---
id: CASE-028
title: DC ground fault from rodent damage to cable insulation
symptom_component: dc_side
root_cause_component: dc_side
operating_mode: standby
alarm_categories: [ground_fault, insulation_fault]
impact: trip
source: synthetic
reviewed: true
---

## Symptoms

The PCS reported a DC ground fault while in standby and would not restart. Unlike weather-related insulation faults (see CASE-011), the fault did not recover as conditions dried out.

## Conditions

- Rural location, PCS in standby for several days.
- DC cables run through a cable trench with removable covers.
- Signs of animal activity around the equipment area.

## Troubleshooting steps

1. Confirmed the fault was persistent and not related to humidity: insulation resistance stayed low in dry weather.
2. [SAFETY] Isolated the DC circuit and measured insulation resistance section by section. One cable section in the trench had a very low reading.
3. [SAFETY] Opened the trench covers along that section: found chewed cable insulation and nesting material.

## Root cause

Rodents had chewed through the cable insulation in the trench, exposing a conductor and creating a path to ground.

## Resolution

[SAFETY] Replaced the damaged cable section, sealed trench openings, and added rodent protection to the cable route. Insulation tests passed and the unit returned to service.

## Lessons

A persistent ground fault that does not follow the weather points to physical damage. Check cable routes for animal activity at rural locations.
