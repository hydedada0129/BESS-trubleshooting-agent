---
id: CASE-007
title: Charge power limited by BMS cell-voltage limit
symptom_component: bms_interface
root_cause_component: bms_interface
operating_mode: charging
alarm_categories: [bms_alarm]
impact: derate
source: synthetic
reviewed: true
---

## Symptoms

The PCS could not reach its commanded charging power. Charging power fell well below the setpoint long before the battery appeared full, and the batteries reached a lower state of charge than expected at the end of each charging window. No PCS fault was logged; the PCS was following a reduced charge current limit sent by the BMS.

## Conditions

- Charging, starting from a medium state of charge.
- The BMS reported one rack with a much wider cell voltage spread than the others.
- No recent changes to PCS or EMS settings.

## Troubleshooting steps

1. Confirmed the PCS was following the BMS charge current limit, not its own protection: the power reduction matched the limit received from the BMS.
2. Reviewed BMS data: the highest cell voltage in one rack reached the upper limit early, while the average cell voltage was still moderate.
3. Compared racks: the affected rack showed a larger imbalance between cells and had not completed balancing.
4. Checked the BMS balancing status and history; balancing had been inactive for that rack for an extended period.

## Root cause

Cell imbalance in one battery rack caused its highest cell to reach the voltage limit early. The BMS correctly reduced the allowed charging current for the whole system to protect that cell, which limited PCS charging power. The PCS was operating correctly.

## Resolution

The battery maintenance team restored the rack's balancing function and ran a balancing cycle. After balancing, charging power stayed at the setpoint for most of the charging window.

## Lessons

When the PCS derates without its own fault, check the BMS limits first. A single imbalanced rack can limit the whole system.
