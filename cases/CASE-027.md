---
id: CASE-027
title: Overtemperature trip from air in the liquid cooling loop
symptom_component: power_module
root_cause_component: cooling
operating_mode: discharging
alarm_categories: [overtemperature]
impact: trip
source: synthetic
reviewed: true
---

## Symptoms

A liquid-cooled PCS tripped on power module overtemperature during discharge, a few weeks after maintenance on the cooling loop. The coolant pump reported running normally, and the coolant supply temperature was normal.

## Conditions

- Discharging at medium to high power.
- Liquid cooling loop drained and refilled during recent maintenance.
- Ambient temperature moderate.

## Troubleshooting steps

1. Compared module temperatures: the modules at the highest point of the cooling loop were much hotter than the rest.
2. Checked the coolant flow and pressure readings: flow was lower than normal, and pressure fluctuated.
3. Listened at the pump and pipes: heard gurgling consistent with trapped air.
4. Checked the maintenance record: the loop had been refilled, but not fully vented at its high points.

## Root cause

Air trapped in the liquid cooling loop after maintenance reduced coolant flow, especially through the cold plates at the highest point. Those power modules overheated. The alarm was on the modules, but the root cause was the cooling loop.

## Resolution

Vented the cooling loop at all high points following the manufacturer's procedure, topped up coolant, and confirmed normal flow and stable pressure. Module temperatures became even and the trips stopped. Venting was added to the maintenance checklist.

## Lessons

After any cooling loop maintenance, check flow and pressure stability. Hot spots at the highest points of a liquid loop suggest trapped air.
