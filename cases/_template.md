---
id: CASE-000
title: Short description of the fault
symptom_component: dc_side          # where the symptom appears (taxonomy.components)
root_cause_component: dc_side       # where the fault actually was (taxonomy.components)
operating_mode: charging            # taxonomy.operating_modes
alarm_categories: [dc_overvoltage]  # taxonomy.alarm_categories
impact: trip                        # trip | derate | warning
source: synthetic                   # synthetic | field_anonymized
reviewed: false
---

## Symptoms

What the operator or remote engineer saw: alarms, behavior, timing.

## Conditions

Operating mode, power level, ambient conditions, recent changes.

## Troubleshooting steps

1. Step one.
2. [SAFETY] A step that involves high voltage, batteries, or de-energization.

## Root cause

What was actually wrong and why it produced the symptoms.

## Resolution

What fixed it and how it was verified.

## Lessons

Optional: what to check first next time.
