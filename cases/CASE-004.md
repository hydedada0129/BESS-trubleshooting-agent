---
id: CASE-004
title: Summer derating from clogged air filters
symptom_component: cooling
root_cause_component: cooling
operating_mode: charging
alarm_categories: [overtemperature]
impact: derate
source: synthetic
reviewed: true
---

## Symptoms

During hot afternoons, the PCS repeatedly reduced charging power with a cabinet temperature warning. It never tripped, but daily charged energy dropped noticeably. The derating started earlier in the day than in the previous summer.

## Conditions

- Charging during the hottest part of the day.
- High ambient temperature and a dusty environment.
- Air filters had not been replaced on the planned schedule.

## Troubleshooting steps

1. Compared cabinet internal temperature with ambient temperature. The difference was larger than in the same period last year at similar power.
2. Checked fan status: all fans reported running at full speed, so fan failure was unlikely.
3. Inspected the air inlet and filters (no need to open live compartments). Filters were heavily clogged with dust.
4. Checked the exhaust path for obstructions; it was clear.

## Root cause

Clogged air filters reduced cooling airflow. On hot days, the internal temperature reached the derating threshold, and the PCS reduced power to protect itself.

## Resolution

Replaced the air filters and cleaned the inlet grilles. Cabinet temperature rise at full power returned to its normal range, and derating stopped. The filter replacement interval was shortened for the dusty season.

## Lessons

If fans run at full speed but the internal-to-ambient temperature difference grows over time, check airflow restrictions such as filters before suspecting components.
