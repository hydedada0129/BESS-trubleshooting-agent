import json
import math

import httpx
import pytest
import respx

from kb.embedder import EmbeddingError, FakeEmbedder, OllamaEmbedder, build_embedder

URL = "http://ollama.test:11434/api/embed"


def emb(**kw):
    return OllamaEmbedder(host="http://ollama.test:11434", model="bge-m3:latest", **kw)


@respx.mock
def test_ollama_embed_request_and_batching():
    route = respx.post(URL).mock(side_effect=lambda req: httpx.Response(
        200, json={"embeddings": [[float(i)] for i, _ in enumerate(json.loads(req.content)["input"])]}))
    vectors = emb(batch_size=2).embed(["a", "b", "c"])
    assert vectors == [[0.0], [1.0], [0.0]]
    assert route.call_count == 2
    sent = json.loads(route.calls[0].request.content)
    assert sent["model"] == "bge-m3:latest"
    assert sent["options"] == {"num_gpu": 0}


@respx.mock
@pytest.mark.parametrize("response", [httpx.Response(500), httpx.Response(200, json={"wrong": 1}),
                                      httpx.Response(200, json={"embeddings": []})])
def test_ollama_embed_errors(response):
    respx.post(URL).mock(return_value=response)
    with pytest.raises(EmbeddingError):
        emb().embed(["a"])


@respx.mock
def test_preflight():
    respx.get("http://ollama.test:11434/api/tags").mock(
        return_value=httpx.Response(200, json={"models": [{"name": "bge-m3:latest"}]}))
    assert emb().preflight() is None
    assert "not found" in OllamaEmbedder(host="http://ollama.test:11434", model="other").preflight()


@respx.mock
def test_preflight_unreachable():
    respx.get("http://ollama.test:11434/api/tags").mock(side_effect=httpx.ConnectError("refused"))
    assert "cannot reach" in emb().preflight()


def test_build_embedder_from_settings():
    e = build_embedder()
    assert (e.model, e.num_gpu) == ("bge-m3:latest", 0)


def test_fake_embedder_is_deterministic_normalized_and_bilingual():
    fake = FakeEmbedder()
    a, b, zh = fake.embed(["cooling fan fault", "cooling fan fault", "冷卻風扇故障"])
    assert a == b
    assert math.isclose(sum(v * v for v in a), 1.0)
    assert a == zh  # glossary maps the Chinese terms onto the same tokens
    assert fake.embed([""])[0][0] > 0  # never a zero vector
