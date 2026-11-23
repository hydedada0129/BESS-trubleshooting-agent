---
id: CASE-029
title: Charging ends early from BMS state-of-charge drift
symptom_component: bms_interface
root_cause_component: bms_interface
operating_mode: charging
alarm_categories: [bms_alarm]
impact: derate
source: synthetic
reviewed: false
---

## Symptoms

The BMS reported 100% state of charge and stopped charging much earlier than expected, with noticeably less energy charged than the rated capacity. Discharge then also ended early. No PCS faults were logged.

## Conditions

- Daily charge and discharge cycles.
- The system rarely reached fully charged or fully discharged states, so the BMS had few chances to recalibrate.
- Cell voltages at the "100%" point were below the normal full-charge voltage.

## Troubleshooting steps

1. Confirmed the PCS stopped charging because the BMS charge limit dropped to zero at a reported 100% state of charge, not because of PCS protection.
2. Compared reported state of charge with cell voltages: at the reported 100%, cell voltages were clearly below the expected full-charge level.
3. Compared the energy charged per cycle with earlier months: it had declined gradually, while cell voltages showed no sign of capacity loss.
4. Reviewed BMS calibration history: no full-charge calibration had happened for a long time.

## Root cause

The BMS state-of-charge estimate had drifted because the system never reached the conditions needed to recalibrate. The BMS thought the battery was full when it was not, so it ended charging early and reduced usable capacity.

## Resolution

The battery team ran a controlled full charge and calibration procedure following the supplier's instructions, and the EMS schedule was changed to include periodic calibration cycles. Charged energy returned to the expected range.

## Lessons

Lower usable energy with normal cell voltages and no capacity fade points to state-of-charge estimation drift, not battery degradation.
