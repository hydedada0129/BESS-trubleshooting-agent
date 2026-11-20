# Troubleshooting Cases

The RAG corpus: one anonymized troubleshooting case per file (`CASE-###.md`). See D-04, D-33.

## Review workflow

1. Claude drafts cases with `source: synthetic` and `reviewed: false`.
2. The owner checks each case against real field experience: root cause, troubleshooting order, and every `[SAFETY]` step.
3. After corrections, set `reviewed: true`. If the case was rewritten from a real (anonymized) case, set `source: field_anonymized`.
4. Ingest (M4) only uses `reviewed: true` cases.

## Format

- Front matter fields and allowed values: see `_template.md` and `config/taxonomy.toml`.
- `symptom_component`: where the alarm or symptom appears. `root_cause_component`: where the fault actually was. They differ in "misleading" cases.
- Required sections: Symptoms, Conditions, Troubleshooting steps, Root cause, Resolution. Optional: Lessons.
- English, about 300–800 words.

## Rules

- No vendor manuals, fault code tables, site names, customer names, or serial numbers. `pytest` scans for IPs, MACs, emails and serial-like codes.
- Use relative values ("about 5% above rated DC bus voltage"), not product-specific numbers.
- `[SAFETY]` marks steps involving high voltage, batteries, or de-energization. Safety procedures are written by the owner, not by Claude.
