---
id: CASE-026
title: AC overcurrent trips during upstream grid faults
symptom_component: ac_grid
root_cause_component: ac_grid
operating_mode: discharging
alarm_categories: [ac_overcurrent, grid_voltage_abnormal]
impact: trip
source: synthetic
reviewed: true
---

## Symptoms

Several PCS units tripped at the same moment on AC overcurrent during discharge. The trips happened a few times a year, often during storms. All units restarted normally afterward and no hardware damage was found.

## Conditions

- Discharging at high power.
- All units connected to the same medium-voltage feeder.
- Trips coincided with storms in the area.

## Troubleshooting steps

1. Checked whether the trips were simultaneous across units. They were, which pointed to a common external cause rather than a fault in one unit.
2. Reviewed the fault records: each trip began with a sharp voltage dip, followed by a current rise as the PCS reacted.
3. Asked the grid operator for event records: each event matched a fault on the upstream feeder (e.g., a lightning-induced short circuit) that was cleared by grid protection.
4. Checked the PCS fault ride-through settings against the grid connection requirements. They were set correctly, and the trips happened only for dips deeper than the required ride-through range.

## Root cause

Upstream grid faults caused deep voltage dips. The PCS current rose during the dip and reached the overcurrent protection limit. The PCS behaved as designed; the cause was external.

## Resolution

No hardware change was needed. The events were documented with the grid operator, and the automatic restart behavior after grid events was reviewed so the units return to service quickly within the grid code rules.

## Lessons

Simultaneous trips on several units almost always have an external cause. Match the timestamps with grid operator records before inspecting hardware.
