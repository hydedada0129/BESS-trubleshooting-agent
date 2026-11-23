---
id: CASE-009
title: Module overtemperature caused by a failed cooling fan
symptom_component: power_module
root_cause_component: cooling
operating_mode: discharging
alarm_categories: [overtemperature, fan_fault]
impact: trip
source: synthetic
reviewed: true
---

## Symptoms

The PCS tripped on power module overtemperature during discharge. Unlike earlier events, the trip happened at moderate power and moderate ambient temperature. A short fan fault warning appeared in the log hours before the trip and was missed because it cleared itself.

## Conditions

- Discharging at moderate power.
- Moderate ambient temperature.
- Multiple fans in the cabinet; the controller logs a fan fault when a fan's speed feedback stops.

## Troubleshooting steps

1. Reviewed the full log, not only the trip alarm. An intermittent fan fault warning appeared earlier the same day.
2. Compared temperatures across the modules: the modules cooled by one fan group were clearly hotter than the rest.
3. Checked fan speed feedback: one fan reported zero speed intermittently.
4. [SAFETY] Inspected the fan after isolating its supply: the bearing was worn and the fan stalled when warm.

## Root cause

A failing cooling fan stalled intermittently, reducing airflow to part of the power stage. The modules in that airflow path overheated and triggered the overtemperature trip. The module alarm was a symptom; the cooling system was the root cause.

## Resolution

[SAFETY] Replaced the failed fan and checked the other fans of the same age. The fan fault warning was raised in priority so that it notifies the remote engineer instead of only being logged.

## Lessons

Before treating an overtemperature trip as a module problem, look for fan warnings earlier in the log and compare temperatures between airflow zones.
