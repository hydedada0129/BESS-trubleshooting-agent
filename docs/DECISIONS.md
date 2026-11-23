# Design Decisions

Decisions agreed during the v1 design review. Each entry: decision, why, alternatives considered. Referenced from [SPEC.md](SPEC.md).

## Scope

### D-01 Primary persona: remote support engineer
- **Decision:** Design for a remote support engineer triaging from a description and a log. Main value: faster first-pass triage; secondary: capturing field experience.
- **Why:** Matches the privacy design (logs stay local, summaries go out) and showcases field expertise.
- **Alternatives:** On-site technician (mobile UX, offline constraints); pure recruiter demo (no real user to design for).

### D-02 Read-only advice with citations
- **Decision:** Output is advice only: ranked hypotheses, next checks, cited cases. No control commands. Safety notice wording is provided by the owner.
- **Why:** Safety. A wrong command on high-voltage or battery equipment is dangerous; Claude must not invent safety rules.
- **Alternatives:** Suggesting parameter changes (rejected: safety and liability).

### D-03 Input: description + alarm log
- **Decision:** Natural-language description plus a CSV/text alarm log. Images deferred to v2+.
- **Why:** Log parsing and anonymization happen locally, which exercises the privacy rule.
- **Alternatives:** Text only (too little signal); images (scope).

## Data

### D-04 Synthetic case drafts, owner review required
- **Decision:** Claude drafts cases (`source: synthetic`, `reviewed: false`); the owner corrects them; ingest accepts only `reviewed: true`.
- **Why:** The owner asked Claude to create the cases, but cases encode diagnostic rules, and CLAUDE.md forbids Claude inventing them. The review gate keeps the domain judgement with the owner.
- **Alternatives:** Owner writes all cases (slower); Claude writes unreviewed cases (violates CLAUDE.md, weak portfolio value).

### D-05 Generic fault categories, ~30 cases
- **Decision:** Use generic fault descriptions, no vendor codes. Start with ~30 high-quality cases.
- **Why:** Confidentiality rules; quality over quantity.

### D-06 English cases, bilingual queries
- **Decision:** Cases in English; queries in Chinese or English; multilingual embeddings (bge-m3).
- **Why:** English for an international portfolio; real users may ask in Chinese.
- **Alternatives:** All English (excludes real usage); fully bilingual corpus (double authoring cost).

### D-17 Taxonomy drafted by Claude, refined by owner
- **Decision:** Components: DC side, power module (IGBT), AC side / grid, cooling, auxiliary power, communication, BMS interface. Modes: charging, discharging, standby, startup / shutdown.
- **Why:** Needed for metadata filters and eval labels; content is domain judgement, so the owner has final say.

### D-20 Single generic log format
- **Decision:** `timestamp, device_id, severity, alarm_category, message, value, unit`. Other formats via adapters, out of v1 scope.
- **Why:** Vendor formats are proprietary; one format keeps parsing testable.

## Models and routing

### D-07 Kimi as first cloud provider, via an OpenAI-compatible client
- **Decision:** `OpenAICompatClient` (base URL, model and key from config; default Kimi international endpoint `https://api.moonshot.ai/v1`, key in `MOONSHOT_API_KEY`) + `OllamaClient`, both implementing `llm/base.py`.
- **Why:** The owner has a Kimi API key, not a Claude one. One OpenAI-compatible client covers Kimi and other compatible providers by configuration. CLAUDE.md requires interchangeable models; the interface stays provider-neutral.
- **History:** Originally Anthropic (`AnthropicClient`); changed before implementation.

### D-08 Spike 0 before trusting local tool calling
- **Decision:** Measure local tool-call validity on 20–30 fixed prompts; require ≥ 95% before letting the local model run multi-step tool loops.
- **Why:** "Supports tool calling" is not "reliable". Q4-quantized local models often drop arguments or emit invalid JSON.

### D-12 Local model limited to single-step tasks; embeddings on CPU
- **Decision:** Local model (Qwen 27B Q4_K_M, Ollama, 16 GB VRAM) only writes event summaries. Context reduced from 16k to 8k. Embeddings run on CPU.
- **Why:** Measured 30% CPU / 70% GPU offload at 16k; 23.3 tokens/s is fine for single steps. Smaller context frees VRAM; CPU embeddings avoid competing for it.
- **Alternatives:** Local model as primary reasoner (slow, untested tool calling); smaller fully-GPU model (not needed at 23 tok/s, kept as backup).

### D-13 Rule-based routing
- **Decision:** Route by task type with fixed rules; no LLM router.
- **Why:** Deterministic, testable, explainable. Only two task types exist.

### D-18 Cloud model: Kimi K2 series, configurable
- **Decision:** Diagnosis uses a Kimi K2-series model with tool calling; the exact model ID lives in `config/settings.toml` and is left empty until confirmed from the provider's model list.
- **Why:** Matches the available API key; switching models needs no code change.
- **History:** Originally `claude-sonnet-5-5`; changed with D-07.

### D-22 Agent loop limits
- **Decision:** Max 6 tool calls, 90 s total; on limit, answer with what is known and set `truncated: true`.
- **Why:** Bounds cost and latency; avoids runaway loops.

## Fallback

### D-15 Degraded mode triggers
- **Decision:** 30 s timeout; 429/5xx after 2 retries with backoff; no key / no network → local summary + retrieved cases, labelled degraded.
- **Why:** The tool stays useful offline, and the user always knows when full reasoning did not happen.

### D-16 Privacy block never falls back to another cloud
- **Decision:** If the pre-send check blocks a payload, it stays local.
- **Why:** A privacy failure is not an availability failure; rerouting would defeat the check.

## Privacy

### D-19 Rule-based anonymization, LLM never judges sensitivity
- **Decision:** Regex + denylist anonymization locally; pre-send re-scan blocks any hit. The local LLM only summarizes already-anonymized events.
- **Why:** Rules are deterministic and testable; LLM output is not guaranteed to be consistent.
- **Alternatives:** LLM-based PII detection (non-deterministic, untestable).

### D-23 Local anonymized traces
- **Decision:** JSONL trace per run in gitignored `traces/`, anonymized content only.
- **Why:** Debugging and evidence that routing works, without creating a new leak path.

### D-24 Denylist is itself confidential
- **Decision:** Real list in gitignored `config/denylist.local.txt`; fictional `config/denylist.example.txt` in the repo; a test fails if any `*.local.*` file is tracked.
- **Why:** The denylist contains real site and customer names.

## Retrieval

### D-09 One case per chunk
- **Decision:** Whole case as one chunk, structured fields as metadata; split by section only above ~1,500 tokens, keeping the case ID.
- **Why:** Cases are short (300–800 words); splitting would separate symptoms from root causes.

### D-10 Hybrid BM25 + vector with RRF, k = 5, no reranker
- **Decision:** Fuse BM25 and vector rankings with RRF; top 5.
- **Why:** BM25 catches exact alarm/component terms; vectors catch synonyms and cross-language matches. RRF uses ranks only, so score scales don't matter. Add a reranker only if eval shows the need.

### D-11 Five tools in v1
- **Decision:** `parse_log`, `anonymize`, `search_cases`, `get_case`, `summarize_events`.
- **Why:** Few, reliable tools beat many unreliable ones.

## Output and interaction

### D-14 Structured pydantic output
- **Decision:** JSON with `mode`, `timeline`, `hypotheses` (with cited case IDs), `next_checks`, `safety_notice`, `truncated`; CLI renders Markdown.
- **Why:** Enables automatic evaluation (e.g. citation checks).

### D-21 Single request in v1
- **Decision:** One input → one diagnosis; no follow-up turns.
- **Why:** Multi-turn adds state management and eval complexity; deferred to v2.

## Stack

### D-29 Python, Chroma, CLI + FastAPI
- **Decision:** Python 3.11+, Chroma, CLI and FastAPI in v1; Docker and MCP wrapper after v1. Owner writes `retrieval.py` and `agent.py`; Claude writes boilerplate.
- **Why:** Matches the working agreement in CLAUDE.md.

## Evaluation

### D-25 Separate eval set
- **Decision:** 20 scenarios not in the corpus, drafted by Claude and reviewed by the owner.
- **Why:** Testing on corpus cases would be testing on the answer key.

### D-26 Deterministic metrics only
- **Decision:** recall@5, MRR, top-3 root-cause category hit rate, citation faithfulness (100%), privacy leaks (0), tool-call validity. No LLM-as-judge in v1.
- **Why:** Repeatable numbers. LLM-as-judge may be added in v2 for text quality.

### D-27 Mocked pytest vs real eval
- **Decision:** `pytest` mocks all external calls and runs before every commit; `python -m eval.run` uses real models and is run manually.
- **Why:** Pre-commit tests must be fast and free.

## Process

### D-28 Milestone order with privacy first
- **Decision:** M0 Spike 0 → M1 LLMClient → M2 cases → M3 privacy → M4 retrieval → M5 agent → M6 eval → M7 API/CLI → post-v1 Docker/MCP.
- **Why:** Privacy controls must exist before any cloud call with real data; Spike 0 first because it decides the local model's scope.

### D-30 Spike 0 calls Ollama directly
- **Decision:** `spikes/spike0_tool_calling/` calls Ollama's `/api/chat` directly instead of going through `LLMClient`. Production code never imports from `spikes/`.
- **Why:** `LLMClient` does not exist until M1, and the spike's results should inform its design (e.g. tool-call validation and retries).
- **Alternatives:** Build M1 first (spike results could no longer shape the interface).

### D-31 No `AnthropicClient` in M1
- **Decision:** M1 builds only `OpenAICompatClient` and `OllamaClient`. A shared contract test suite proves they are interchangeable.
- **Why:** No Claude key to verify against; a mock-only client would be unused code. Add it when a key is available.

### D-32 M1 client design
- **Decision:** One method `chat(messages, tools, *, max_tokens, temperature) -> LLMResponse`; synchronous, no streaming. Errors normalized to `LLMTimeoutError`, `LLMRateLimitError`, `LLMUnavailableError` (with `retryable`), `LLMResponseError`. Timeouts, 429, 5xx and connection failures are retried with exponential backoff; auth/config errors are not. Unparsable tool arguments set `ToolCall.parse_error` instead of raising; schema validation is optional (`llm/validation.py`). Both clients use `httpx`; tests mock HTTP with `respx`. Settings in `config/settings.toml`, keys only in environment variables or `.env`.
- **Why:** Small interface is easy to swap; retries are a client concern, fallback is a router concern (D-15); the agent decides how to handle bad tool calls until Spike 0 data exists.

### D-33 Case schema: symptom vs root-cause component
- **Decision:** Cases live at `cases/CASE-###.md` with front matter `id, title, symptom_component, root_cause_component, operating_mode, alarm_categories, impact, source, reviewed`, fixed sections, relative values only, and `[SAFETY]` markers whose content the owner writes. All categorical values come from `config/taxonomy.toml`. `pytest` validates every case and scans for confidential identifiers. Evaluation's root-cause label is `root_cause_component`. Cases are drafted in batches of 10, about a third "misleading" (symptom and root cause in different components).
- **Why:** In the field the alarm often appears in one component while the fault is in another; separating the two fields captures that judgement and makes evaluation meaningful. One taxonomy file keeps cases, logs and tools consistent.
- **Alternatives:** Single `component` field (loses the misleading-alarm distinction); taxonomy duplicated per module (drifts).

### D-34 Add `control_system` component
- **Decision:** Add `control_system` (controller, measurement and sensing circuits) to the component taxonomy.
- **Why:** Measurement or control faults (e.g. drifting voltage sensing that produces false grid alarms) had no fitting category, and they are typical misleading cases.
- **Alternatives:** Fold into `power_module` (hides a distinct root-cause class).
- **Note:** `spikes/spike0_tool_calling/tools.py` keeps its own frozen copy of the original seven components; spikes are snapshots and are not updated.

### D-35 Add `controller_fault` alarm category
- **Decision:** Add `controller_fault` to the alarm categories (controller resets, watchdog, internal control errors).
- **Why:** Controller-side failures had no matching alarm category; logging them as `comm_loss` hides the real signal.
