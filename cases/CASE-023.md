---
id: CASE-023
title: Overtemperature derating from a faulty temperature sensor
symptom_component: power_module
root_cause_component: control_system
operating_mode: charging
alarm_categories: [overtemperature]
impact: derate
source: synthetic
reviewed: false
---

## Symptoms

The PCS derated charging power because of a power module overtemperature warning, sometimes right after starting at low power. The reported temperature occasionally jumped by a large amount within a second, which is not physically possible for a module with a heatsink.

## Conditions

- Charging, often at low or medium power.
- Normal ambient temperature, fans and airflow normal.
- Other modules in the same unit showed normal temperatures.

## Troubleshooting steps

1. Plotted the module temperature at high resolution: the reading jumped up and down abruptly instead of changing gradually.
2. Compared it with neighboring modules under the same load: their temperatures were stable and much lower.
3. Checked cooling (fans, filters, inlet temperature): all normal.
4. [SAFETY] With the unit de-energized, inspected the temperature sensor wiring: found a damaged connector giving an intermittent contact on the sensor signal.

## Root cause

An intermittent connection in the module temperature sensor wiring produced false high readings. The PCS derated to protect a module that was not actually hot.

## Resolution

[SAFETY] Replaced the damaged connector and sensor cable. Temperature readings became smooth and consistent with neighboring modules, and derating stopped.

## Lessons

Temperature readings that jump faster than physically possible indicate a sensor or wiring problem, not real overheating.
