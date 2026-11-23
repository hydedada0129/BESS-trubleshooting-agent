---
id: CASE-020
title: Power stage derating from aged DC-link capacitors
symptom_component: power_module
root_cause_component: power_module
operating_mode: discharging
alarm_categories: [overtemperature]
impact: derate
source: synthetic
reviewed: true
---

## Symptoms

The PCS increasingly reduced discharge power due to internal temperature warnings in the power stage area, even on mild days. Fans and filters were in good condition. The DC bus voltage also showed more ripple than in older trend data.

## Conditions

- Discharging at medium to high power.
- Unit with many years of operation in a warm environment.
- Cooling system recently serviced with no findings.

## Troubleshooting steps

1. Confirmed cooling was not the cause: airflow, fan speed, and filters were normal, and inlet air temperature was moderate.
2. Compared DC bus voltage ripple with historical trend data from the same power level. Ripple had increased steadily over time.
3. Checked temperature sensors near the DC-link capacitor bank: they ran hotter than the power modules nearby.
4. [SAFETY] After de-energizing and confirming the DC link was discharged, inspected the capacitors: some showed bulging, and capacitance measurements were well below rated values.

## Root cause

Aged DC-link capacitors lost capacitance and had higher internal losses. This increased DC ripple and heat in the power stage, and the PCS derated to protect the capacitors.

## Resolution

[SAFETY] Replaced the DC-link capacitor bank. DC ripple and capacitor temperatures returned to normal, and derating stopped.

## Lessons

Gradually increasing DC ripple together with power stage temperature warnings, with healthy cooling, suggests DC-link capacitor aging. Trend data makes this visible early.
