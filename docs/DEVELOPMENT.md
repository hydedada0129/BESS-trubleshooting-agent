# Development

## Setup (Windows)

Requires Python 3.11+.

With [uv](https://docs.astral.sh/uv/) (recommended):

```
uv sync --extra dev
uv run pytest
```

With pip:

```
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

Run `pytest` before every commit. Tests mock all network calls: no API key or Ollama needed.

## Configuration

- `config/settings.toml`: non-secret settings (endpoints, model IDs, timeouts, retries). Committed.
- `.env`: secrets. Copy `.env.example` to `.env` and set `MOONSHOT_API_KEY`. Never committed; existing environment variables take precedence.
- The cloud model ID is empty until confirmed. List the IDs your key can use:

  ```
  curl https://api.moonshot.ai/v1/models -H "Authorization: Bearer <your key>"
  ```

## Using the LLM clients

```python
from llm import Message
from llm.config import build_cloud_client, build_local_client, load_env_file, load_settings

load_env_file()
settings = load_settings()
cloud = build_cloud_client(settings.cloud)   # Kimi (OpenAI-compatible)
local = build_local_client(settings.local)   # Ollama

reply = local.chat([Message(role="user", content="Hello")])
print(reply.content, reply.usage, reply.latency_s)
```

For tests, use `llm.fake.FakeLLMClient` with scripted responses (`text_response`, `tool_call_response`).

## Building the case index

Requires Ollama running with `bge-m3:latest`. Rebuild after any case change:

```
uv run python -m kb.ingest
```

Only `reviewed: true` cases are indexed. The index lives in `chroma/` (not committed).

## Layout

```
llm/            LLMClient interface and clients (M1)
kb/             case loading, validation, embeddings, ingest (M2, M4)
privacy/        detection rules, anonymizer, pre-send guard (M3)
tools/          agent tools, e.g. parse_log (M3)
cases/          reviewed troubleshooting cases (M2)
samples/logs/   fictional demo logs
retrieval.py    hybrid retrieval: BM25 + vector + RRF (M4, D-38)
config/         settings.toml
spikes/         throwaway experiments; never imported by production code (D-30)
tests/          pytest suite
docs/           SPEC, DECISIONS, this file
```
