# Spike 0: Local Tool-Calling Validity

Measures whether the local model calls tools reliably enough to run multi-step tool loops (D-08). Pass threshold: valid rate ≥ 95%.

> **Exception (D-30):** this throwaway spike calls Ollama's `/api/chat` directly instead of going through `LLMClient`, which does not exist yet (M1). Production code must never import from `spikes/`.

## What it does

- Offers the five v1 tool schemas (`tools.py`) on every request.
- Sends 24 fictional prompts (`prompts.py`): 16 should call a tool (8 English, 8 Chinese), 4 should not, 4 need enum filters.
- Runs each prompt 3 times (72 requests) with `temperature=0`, `num_ctx=8192`.
- A call is valid when the tool is correct, arguments are valid JSON, required arguments are present, enum/pattern/range constraints hold, and key values match the prompt.

Reported metrics: `valid_rate`, `tool_selection_accuracy`, `arg_validity`, `false_call_rate`, `miss_rate`, `hard_valid_rate`, latency.

## Run (Windows)

Requires Python 3.10+ and Ollama running locally. No packages needed.

```
cd BESS-trubleshooting-agent
python spikes\spike0_tool_calling\run.py --model qwen3.8:27b
python spikes\spike0_tool_calling\run.py --model qwen3.8:27b --think
```

Options: `--runs` (default 3), `--host` (default `http://localhost:11434`), `--timeout` (default 120 s).

Results are written to `results/<date>_<time>_think-<on|off>.json`. They contain only fictional prompts and model responses; commit them as evidence for D-12.

## Tests

The scorer is unit-tested with fake responses (no Ollama needed): `pytest`.
