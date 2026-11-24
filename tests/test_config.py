from privacy.guard import GuardedClient
from llm.config import (
    DEFAULT_SETTINGS,
    build_cloud_client,
    build_local_client,
    load_env_file,
    load_settings,
)


def test_repo_settings_load():
    s = load_settings(DEFAULT_SETTINGS)
    assert s.cloud.base_url == "https://api.moonshot.ai/v1"
    assert s.cloud.api_key_env == "MOONSHOT_API_KEY"
    assert s.local.model == "qwen3.8:27b"
    assert s.local.num_ctx == 8192
    assert s.local.think is False


def test_build_clients_from_settings():
    s = load_settings(DEFAULT_SETTINGS)
    cloud = build_cloud_client(s.cloud, environ={"MOONSHOT_API_KEY": "k"})
    local = build_local_client(s.local)
    assert isinstance(cloud, GuardedClient)
    assert cloud._inner._api_key == "k"
    assert cloud._inner.max_retries == s.cloud.max_retries
    assert local.model == "qwen3.8:27b"
    assert local.num_ctx == 8192


def test_missing_api_key_becomes_none():
    s = load_settings(DEFAULT_SETTINGS)
    assert build_cloud_client(s.cloud, environ={})._inner._api_key is None
    assert build_cloud_client(s.cloud, environ={"MOONSHOT_API_KEY": ""})._inner._api_key is None


def test_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('# comment\nMOONSHOT_API_KEY="from-file"\nEXISTING=from-file\n\nBROKEN_LINE\n', encoding="utf-8")
    environ = {"EXISTING": "already-set"}
    load_env_file(env_file, environ)
    assert environ == {"EXISTING": "already-set", "MOONSHOT_API_KEY": "from-file"}


def test_missing_env_file_is_ignored(tmp_path):
    environ = {}
    load_env_file(tmp_path / "missing.env", environ)
    assert environ == {}
