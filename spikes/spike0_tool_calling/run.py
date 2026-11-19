"""Spike 0: measure local model tool-calling validity via Ollama.

Exception to the LLMClient rule (D-30): this throwaway spike calls Ollama's
/api/chat directly. Production code must never import from spikes/.

Usage (Windows):
    python spikes\\spike0_tool_calling\\run.py --model qwen3.8:27b --runs 3
    python spikes\\spike0_tool_calling\\run.py --think
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from prompts import CASES
from scorer import score_attempt, summarize
from tools import SCHEMAS, TOOLS

PASS_THRESHOLD = 0.95  # D-08
SYSTEM_PROMPT = (
    "You are an assistant inside a BESS PCS troubleshooting tool. "
    "Call a tool only when the user's request needs one; otherwise answer directly."
)
RESULTS_DIR = Path(__file__).parent / "results"


def chat(host: str, model: str, prompt: str, think: bool, timeout: float) -> tuple[dict | None, float, str | None]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "tools": TOOLS,
        "stream": False,
        "think": think,
        "options": {"temperature": 0, "num_ctx": 8192},
    }
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("message"), time.perf_counter() - start, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, time.perf_counter() - start, str(exc)


def preflight(host: str, model: str) -> str | None:
    """Return an error message if Ollama is unreachable or the model is missing."""
    try:
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=10) as resp:
            names = [m["name"] for m in json.loads(resp.read().decode("utf-8")).get("models", [])]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return f"cannot reach Ollama at {host}: {exc}"
    if model not in names:
        return f"model '{model}' not found; available: {', '.join(names) or 'none'}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="qwen3.8:27b")
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--think", action="store_true", help="enable Qwen3 thinking mode")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    problem = preflight(args.host, args.model)
    if problem:
        print(f"Error: {problem}")
        return 1

    total = len(CASES) * args.runs
    print(f"Spike 0: {args.model}, think={args.think}, {len(CASES)} cases x {args.runs} runs = {total} requests")

    attempts = []
    for run in range(1, args.runs + 1):
        for case in CASES:
            message, latency, error = chat(args.host, args.model, case["prompt"], args.think, args.timeout)
            score = score_attempt(case, message, SCHEMAS)
            attempts.append({
                "case_id": case["id"],
                "group": case["group"],
                "run": run,
                "latency_s": round(latency, 2),
                "error": error,
                "tool_calls": (message or {}).get("tool_calls"),
                "content": (message or {}).get("content"),
                **score,
            })
            mark = "ok " if score["valid"] else "FAIL"
            print(f"[{len(attempts):>3}/{total}] {mark} {case['id']} run {run} ({latency:.1f}s) {'; '.join(score['errors'])}")

    summary = summarize(attempts)
    summary["request_errors"] = sum(1 for a in attempts if a["error"] is not None)
    latencies = [a["latency_s"] for a in attempts if a["error"] is None]
    if latencies:
        summary["latency_p50_s"] = round(statistics.median(latencies), 2)
        summary["latency_max_s"] = round(max(latencies), 2)
    summary["passed"] = (summary["valid_rate"] or 0) >= PASS_THRESHOLD

    now = datetime.now()
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"{now:%Y-%m-%d_%H%M}_think-{'on' if args.think else 'off'}.json"
    out.write_text(json.dumps({
        "meta": {
            "timestamp": now.isoformat(timespec="seconds"),
            "model": args.model,
            "think": args.think,
            "runs": args.runs,
            "temperature": 0,
            "num_ctx": 8192,
            "threshold": PASS_THRESHOLD,
        },
        "summary": summary,
        "attempts": attempts,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== Summary ===")
    for key, value in summary.items():
        print(f"{key:>24}: {value}")
    print(f"\nResult: {'PASS' if summary['passed'] else 'FAIL'} (threshold {PASS_THRESHOLD:.0%})")
    print(f"Saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
