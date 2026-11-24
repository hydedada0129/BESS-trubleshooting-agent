"""Load settings and build clients. Not a router: it never decides which client a task uses.

The cloud client is always returned wrapped in GuardedClient (D-36), so code
using this module cannot send unchecked data to a cloud model.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path

from llm.ollama import OllamaClient
from llm.openai_compat import OpenAICompatClient
from privacy.guard import GuardedClient
from privacy.patterns import Detector, default_detector

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS = REPO_ROOT / "config" / "settings.toml"
DEFAULT_ENV_FILE = REPO_ROOT / ".env"


@dataclass(frozen=True)
class CloudSettings:
    base_url: str
    model: str
    api_key_env: str
    timeout_s: float = 30.0
    max_retries: int = 2
    backoff_s: float = 1.0


@dataclass(frozen=True)
class LocalSettings:
    host: str
    model: str
    num_ctx: int = 8192
    think: bool = False
    timeout_s: float = 120.0
    max_retries: int = 2
    backoff_s: float = 1.0


@dataclass(frozen=True)
class Settings:
    cloud: CloudSettings
    local: LocalSettings


def load_settings(path: Path = DEFAULT_SETTINGS) -> Settings:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return Settings(cloud=CloudSettings(**data["cloud"]), local=LocalSettings(**data["local"]))


def load_env_file(path: Path = DEFAULT_ENV_FILE, environ: MutableMapping[str, str] = os.environ) -> None:
    """Load KEY=VALUE lines into `environ`. Existing variables win. Missing file is fine."""
    path = Path(path)
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in environ:
            environ[key] = value


def build_cloud_client(
    settings: CloudSettings,
    environ: MutableMapping[str, str] = os.environ,
    detector: Detector | None = None,
) -> GuardedClient:
    inner = OpenAICompatClient(
        base_url=settings.base_url,
        model=settings.model,
        api_key=environ.get(settings.api_key_env) or None,
        timeout_s=settings.timeout_s,
        max_retries=settings.max_retries,
        backoff_s=settings.backoff_s,
    )
    return GuardedClient(inner, detector or default_detector())


def build_local_client(settings: LocalSettings) -> OllamaClient:
    return OllamaClient(
        host=settings.host,
        model=settings.model,
        num_ctx=settings.num_ctx,
        think=settings.think,
        timeout_s=settings.timeout_s,
        max_retries=settings.max_retries,
        backoff_s=settings.backoff_s,
    )
