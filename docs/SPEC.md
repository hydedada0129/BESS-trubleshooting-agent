# BESS PCS Troubleshooting Agent — Specification (v1)

Status: agreed design, pre-implementation. Rationale for each decision is in [DECISIONS.md](DECISIONS.md) (referenced as `D-xx`).

## 1. Problem statement

A remote support engineer receives a customer report ("the PCS keeps tripping") plus an alarm log. Today they manually scan the log, find the first relevant alarm, and recall similar past cases. This is slow and depends on individual experience.

The agent shortens this first-pass triage. Given a description and an alarm log, it returns:

- an event timeline,
- ranked root-cause hypotheses, each citing similar past cases,
- recommended next checks.

Secondary goal: capture senior field experience as structured, searchable cases so it is not lost. (D-01)

### Non-goals and limitations

- Does not replace on-site measurement or inspection.
- Read-only advice. Never issues control commands or parameter changes to equipment. (D-02)
- Quality is bounded by the case corpus (~30 cases in v1 covers common faults only).
- Not validated on real fleet data; evaluation uses synthetic scenarios reviewed by the owner.
- Single-request only; no multi-turn conversation in v1. (D-21)
- Only one log format (Section 4.2); vendor formats need adapters, out of scope. (D-20)

## 2. Users

Primary persona: remote technical support engineer triaging a fault from a description and a log. (D-01)

## 3. Architecture overview

```
 description + alarm log (CSV)
            │
            ▼
   ┌─────────────────── local machine ───────────────────┐
   │ parse_log ─► anonymize ─► summarize_events (local LLM)│
   │                     │                                 │
   │              pre-send check ──(blocked)──► degraded   │
   └─────────────────────┼───────────────────────────────┘
                         │ anonymized summary only
                         ▼
         cloud LLM agent loop (search_cases, get_case)
                         │
                         ▼
           structured diagnosis (pydantic JSON)
```

- All LLM access goes through the `LLMClient` interface in `llm/base.py`. Implementations: `OpenAICompatClient` (cloud, default Kimi), `OllamaClient` (local). (D-07, D-31)
- Raw logs never leave the machine. Only anonymized summaries and retrieved cases go to the cloud model. (D-19)

## 4. Data

### 4.1 Case corpus

- Format: one Markdown file per case at `cases/CASE-###.md`, YAML front matter, English, ~300–800 words. (D-04, D-06, D-33)
- Front matter: `id`, `title`, `symptom_component`, `root_cause_component`, `operating_mode`, `alarm_categories`, `impact` (trip / derate / warning), `source` (synthetic / field_anonymized), `reviewed`.
- `symptom_component` is where the alarm appears; `root_cause_component` is where the fault actually was. About a third of cases are "misleading" (they differ).
- Sections: Symptoms, Conditions, Troubleshooting steps, Root cause, Resolution, optional Lessons.
- Relative values only ("about 5% above rated"), no product-specific numbers. `[SAFETY]` marks steps involving high voltage, batteries or de-energization; safety content comes from the owner.
- `pytest` validates every case against `config/taxonomy.toml` and scans for IPs, MACs, emails and serial-like codes.
- Uses generic fault categories only. No vendor manuals, fault code tables, site names, or serial numbers.
- Authoring workflow (D-04):
  1. Claude drafts cases marked `source: synthetic`, `reviewed: false`.
  2. The owner corrects each against real field experience and sets `reviewed: true`.
  3. Ingest accepts only `reviewed: true` cases.
- Target size: 30 cases for v1, drafted in three batches of 10. Every component has at least 3 cases by `root_cause_component`; all operating modes covered.

### 4.2 Alarm log format

Generic CSV defined by this project (D-20):

```
timestamp, device_id, severity, alarm_category, message, value, unit
```

### 4.3 Taxonomy (draft, owner to refine)

Single source of truth: `config/taxonomy.toml`. Used for metadata filtering, case validation, log parsing, and as root-cause labels in evaluation (`root_cause_component`). (D-17, D-33)

- Component: `dc_side`, `power_module`, `ac_grid`, `cooling`, `auxiliary_power`, `communication`, `bms_interface`, `control_system`
- Operating mode: `charging`, `discharging`, `standby`, `startup_shutdown`
- Alarm category (shared with the log format): `dc_overvoltage`, `dc_undervoltage`, `dc_overcurrent`, `ac_overcurrent`, `grid_voltage_abnormal`, `grid_frequency_abnormal`, `insulation_fault`, `ground_fault`, `overtemperature`, `fan_fault`, `precharge_failure`, `contactor_fault`, `aux_power_fault`, `comm_loss`, `bms_alarm`, `controller_fault`
- Impact: `trip`, `derate`, `warning`

## 5. Retrieval (RAG)

- Chunking: one case = one chunk; structured fields stored as metadata. If a case exceeds ~1,500 tokens, split by section while keeping the case ID. (D-09)
- Hybrid retrieval: BM25 + vector search, fused with Reciprocal Rank Fusion (`score = Σ 1/(60 + rank)`); top k = 5. No reranker in v1. (D-10)
- Embeddings: multilingual (bge-m3) so Chinese queries match English cases; runs on CPU to keep VRAM for the LLM. (D-06, D-12)
- Vector store: Chroma.
- `retrieval.py` is written by the owner.

## 6. Tools (v1)

| Tool | Runs | Purpose |
|---|---|---|
| `parse_log` | local | Parse the CSV log into a structured event sequence |
| `anonymize` | local | Remove serials, IPs, MACs, emails, denylisted names; convert timestamps to relative time |
| `summarize_events` | local | Alarm frequency, first event, timeline summary |
| `search_cases` | — | Hybrid search with optional metadata filters |
| `get_case` | — | Fetch a full case by ID |

No other tools in v1. (D-11)

## 7. Model routing

Deterministic, rule-based by task type; no LLM router. (D-13)

| Task | Model |
|---|---|
| Log parsing, anonymization | Code (no LLM) |
| Event summary (single step) | Local: Qwen 27B Q4_K_M via Ollama, context 8k |
| Diagnosis reasoning + tool loop | Cloud: Kimi K2 series via OpenAI-compatible API (exact model ID in config, to be confirmed) (D-18) |

- Local model scope is limited to single-step, fixed-format tasks until Spike 0 shows tool calling is reliable. (D-08, D-12)
- Agent loop limits: max 6 tool calls, 90 s total. On limit, answer with available information and set `truncated: true`. (D-22)
- `agent.py` is written by the owner.

## 8. Fallback (degraded mode)

Enter degraded mode if any of (D-15):

- cloud request times out after 30 s,
- 429 or 5xx persists after 2 retries with backoff,
- no API key or no network.

Degraded output: local event summary + retrieved similar cases, `mode: degraded`, clearly labelled "no full reasoning".

Hard rule: if the pre-send privacy check blocks a payload, the request stays local (degraded). It is never rerouted to another cloud provider. (D-16)

## 9. Privacy

- Anonymization is rule-based: regex (serial patterns, IP, MAC, email) + owner-maintained denylist. The LLM does not decide what is sensitive. (D-19)
- Pre-send check: re-scan every cloud payload with the same rules; any hit blocks the whole request.
- Denylist: real list at `config/denylist.local.txt` (gitignored); repo contains only `config/denylist.example.txt` with fictional entries. A test fails if any `*.local.*` file is tracked. (D-24)
- Traces store anonymized content only. (D-23)

## 10. Output schema

Pydantic model, rendered to Markdown by the CLI (D-14):

- `mode`: `full` | `degraded`
- `timeline`: ordered events
- `hypotheses`: list of {cause, rank, evidence, cited_case_ids}
- `next_checks`: list of recommended checks
- `safety_notice`: safety reminder; wording provided by the owner (D-02)
- `truncated`: bool

## 11. Observability

One JSONL trace per run in `traces/` (gitignored): route taken, model, token usage, latency, tool calls, degraded flag. Anonymized content only. (D-23)

## 12. Evaluation

- Eval set: 20 scenarios, separate from the corpus. Each has input (description + log), expected relevant case IDs, expected `root_cause_component`. Drafted by Claude, reviewed by the owner. (D-25)
- Metrics (all deterministic, no LLM-as-judge in v1) (D-26):

| Area | Metric | Target |
|---|---|---|
| Retrieval | recall@5, MRR | baseline in M6 |
| Diagnosis | top-3 `root_cause_component` hit rate (exact match) | baseline in M6 |
| Citations | cited IDs ⊆ retrieved IDs | 100% |
| Privacy | leaks of seeded fake serials/IPs in cloud payloads | 0 |
| Tool calling | valid call rate (local model) | ≥ 95% to expand local scope |

- `pytest`: all external calls mocked; no network, no cost; run before every commit. `python -m eval.run`: real model calls, run manually, writes a report. (D-27)

## 13. Milestones

| ID | Scope | Owner |
|---|---|---|
| M0 | Spike 0: measure local tool-calling validity on 20–30 fixed prompts. **Deferred:** code done, not yet run | Claude + owner |
| M1 | `LLMClient` interface, OpenAI-compatible (Kimi) and Ollama clients, pytest skeleton | Claude |
| M2 | Case template, taxonomy, 30 case drafts; owner review | Claude drafts, owner reviews |
| M3 | `parse_log`, `anonymize`, pre-send check, privacy tests | Claude |
| M4 | Ingest (Claude), `retrieval.py` (owner) | both |
| M5 | `agent.py` with routing and fallback | owner |
| M6 | Eval set and `eval.run` | Claude drafts, owner reviews |
| M7 | FastAPI and CLI | Claude |
| post-v1 | Docker, MCP wrapper | Claude |

Privacy (M3) lands before any cloud call is made with real data. (D-28)
