---
id: CASE-018
title: Overcurrent trip caused by gate driver supply dips
symptom_component: power_module
root_cause_component: auxiliary_power
operating_mode: discharging
alarm_categories: [dc_overcurrent, aux_power_fault]
impact: trip
source: synthetic
reviewed: false
---

## Symptoms

The PCS occasionally tripped on DC overcurrent from the power module protection during discharge. Replacing a suspected IGBT module did not stop the trips. The power stage hardware tested normal after each event.

## Conditions

- Discharging at medium to high power.
- Gate driver boards powered from the auxiliary control supply.
- Trips more common when cabinet heaters or pumps switched on.

## Troubleshooting steps

1. Reviewed the fault records: the overcurrent flag came from the gate driver's own protection, not from the main current sensors.
2. Correlated trip times with auxiliary load events. Several trips happened when large auxiliary loads started.
3. Recorded the gate driver supply voltage during operation. It dipped briefly during auxiliary load starts, close to the driver's undervoltage threshold.
4. [SAFETY] Checked the auxiliary supply wiring: the driver supply shared a branch with heaters, and the supply's output capacitors had aged.

## Root cause

Brief dips in the auxiliary supply that powers the gate drivers made the drivers report a fault, which the PCS logged as an overcurrent trip. The power module itself was healthy; the auxiliary supply was the root cause.

## Resolution

[SAFETY] Replaced the aged auxiliary power supply and moved the gate driver supply to a dedicated branch. Trips stopped, and the replaced IGBT module was confirmed healthy.

## Lessons

When power module trips continue after replacing the module, check the supply to the gate drivers and correlate trips with auxiliary load changes.
