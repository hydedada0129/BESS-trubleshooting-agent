"""Text embeddings. Not an LLM, so not behind LLMClient (D-37)."""

from __future__ import annotations

import hashlib
import math
import re
import tomllib
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS = REPO_ROOT / "config" / "settings.toml"


class EmbeddingError(RuntimeError):
    pass


class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in order."""


class OllamaEmbedder(Embedder):
    def __init__(
        self,
        *,
        host: str = "http://localhost:11434",
        model: str = "bge-m3:latest",
        num_gpu: int = 0,
        timeout_s: float = 120.0,
        batch_size: int = 16,
        http_client: httpx.Client | None = None,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.num_gpu = num_gpu
        self.batch_size = batch_size
        self._http = http_client or httpx.Client(timeout=timeout_s)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            payload = {"model": self.model, "input": batch, "options": {"num_gpu": self.num_gpu}}
            try:
                resp = self._http.post(f"{self.host}/api/embed", json=payload)
                resp.raise_for_status()
                embeddings = resp.json()["embeddings"]
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                raise EmbeddingError(f"embedding request failed: {exc}") from exc
            if len(embeddings) != len(batch):
                raise EmbeddingError(f"expected {len(batch)} embeddings, got {len(embeddings)}")
            vectors.extend(embeddings)
        return vectors

    def preflight(self) -> str | None:
        """Return an error message if Ollama is unreachable or the model is missing."""
        try:
            resp = self._http.get(f"{self.host}/api/tags", timeout=10)
            resp.raise_for_status()
            names = [m["name"] for m in resp.json().get("models", [])]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            return f"cannot reach Ollama at {self.host}: {exc}"
        if self.model not in names:
            return f"embedding model '{self.model}' not found; available: {', '.join(names) or 'none'}"
        return None


def build_embedder(settings_path: Path = DEFAULT_SETTINGS) -> OllamaEmbedder:
    cfg = tomllib.loads(Path(settings_path).read_text(encoding="utf-8"))["embedding"]
    return OllamaEmbedder(**cfg)


# --- test double ----------------------------------------------------------------

# Small zh->en glossary so tests can check cross-language retrieval without Ollama.
# The real cross-language ability comes from bge-m3.
_ZH_EN = {
    "輔助電源": "auxiliary power", "接觸器": "contactor", "過壓": "overvoltage", "欠壓": "undervoltage",
    "過溫": "overtemperature", "過熱": "overtemperature", "冷卻": "cooling", "風扇": "fan", "故障": "fault",
    "跳機": "trip", "充電": "charging", "放電": "discharging", "絕緣": "insulation", "通訊": "communication",
    "中斷": "loss", "預充": "precharge", "電網": "grid", "頻率": "frequency", "電壓": "voltage",
    "降載": "derate", "啟動": "startup", "待機": "standby", "電池": "battery", "末段": "end", "模組": "module",
}


class FakeEmbedder(Embedder):
    """Deterministic hashed bag-of-words vectors. For tests only."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _tokens(self, text: str) -> list[str]:
        for zh, en in _ZH_EN.items():
            text = text.replace(zh, f" {en} ")
        return re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vec = [0.0] * self.dim
            vec[0] = 0.1  # never a zero vector (cosine distance would be undefined)
            for token in self._tokens(text):
                bucket = int(hashlib.md5(token.encode()).hexdigest(), 16) % (self.dim - 1) + 1
                vec[bucket] += 1.0
            norm = math.sqrt(sum(v * v for v in vec))
            vectors.append([v / norm for v in vec])
        return vectors
