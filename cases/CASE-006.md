---
id: CASE-006
title: Intermittent EMS communication loss from poor shield grounding
symptom_component: communication
root_cause_component: communication
operating_mode: standby
alarm_categories: [comm_loss]
impact: warning
source: synthetic
reviewed: false
---

## Symptoms

The energy management system (EMS) reported intermittent communication loss with one PCS. Each dropout lasted a few seconds and recovered on its own. The PCS stayed in standby and did not trip, but dispatch commands were sometimes missed.

## Conditions

- PCS mostly in standby, waiting for dispatch.
- Serial fieldbus link between the EMS and PCS, routed near power cables.
- Dropouts were more frequent when neighboring units were switching at high power.

## Troubleshooting steps

1. Compared dropout timestamps with the operating state of neighboring units. Dropouts clustered when nearby PCS units were running at high power.
2. Checked communication settings (address, baud rate, termination) on both ends. Settings were correct and bus termination was present.
3. Inspected the cable route: the communication cable ran in parallel with power cables for a long section.
4. Checked the cable shield: it was grounded at neither end on one segment, and an intermediate junction box had broken the shield continuity.

## Root cause

The communication cable shield was not continuous or properly grounded, so electrical noise from nearby power switching coupled into the signal and corrupted messages, causing intermittent communication loss.

## Resolution

Restored shield continuity through the junction box, grounded the shield according to the communication system's grounding practice, and rerouted the worst section away from power cables. No further dropouts were recorded over the following weeks.

## Lessons

Intermittent communication loss that correlates with high-power switching nearby usually points to noise coupling, so check shield grounding and cable routing before replacing communication hardware.
