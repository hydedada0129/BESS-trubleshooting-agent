---
id: CASE-001
title: IGBT module overtemperature at sustained high discharge power
symptom_component: power_module
root_cause_component: power_module
operating_mode: discharging
alarm_categories: [overtemperature]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

The PCS tripped on a power module overtemperature alarm during long evening discharge periods. Trips happened only after one to two hours at or near rated power. Shorter discharge periods and partial-power operation ran without alarms. After cooling down, the unit restarted normally.

## Conditions

- Discharging at close to rated power for extended periods.
- Moderate ambient temperature; the cooling system reported normal operation.
- The unit had several years of operation with frequent full-power cycles.
- Other PCS units at the same location, under similar load, did not trip.

## Troubleshooting steps

1. Reviewed the alarm log: the overtemperature alarm was always on the same phase module, and its temperature rose faster than the other phases under the same current.
2. Compared module temperature trends with inlet air temperature and fan status. Inlet air and fan speed were normal, which made a cooling-side cause less likely.
3. Checked whether phase currents were balanced. They were within normal tolerance, so uneven loading was not the cause.
4. [SAFETY] Inspected the affected module after de-energizing the unit: checked mounting torque, the thermal interface between module and heatsink, and signs of discoloration.
5. Found dried-out, uneven thermal interface material under the affected module.

## Root cause

Degraded thermal interface material between the IGBT module and the heatsink increased thermal resistance. At sustained high power, the module's temperature rose faster than the others and reached the protection threshold, even though the cooling system itself was working.

## Resolution

[SAFETY] Cleaned the contact surfaces, reapplied thermal interface material, and remounted the module at the specified torque. A follow-up full-power discharge test showed the phase temperatures tracking each other again, with no further trips.

## Lessons

When only one phase module overheats while inlet air and fans are normal, suspect the module-to-heatsink thermal path before the cooling system.
