import pytest

import app.services.llm as llm


@pytest.fixture(autouse=True)
def clear_llm_caches() -> None:
    llm.get_chat_client.cache_clear()
    llm.get_embeddings_client.cache_clear()
    yield
    llm.get_chat_client.cache_clear()
    llm.get_embeddings_client.cache_clear()


def test_get_chat_client_uses_ollama_when_configured(monkeypatch) -> None:
    settings = type(
        "Settings",
        (),
        {
            "generation_provider": "ollama",
            "generation_model": "tenerife-gemma-4-12b-it",
            "generation_temperature": 0.1,
            "generation_max_tokens": 2048,
            "ollama_base_url": "http://ollama:11434",
            "google_api_key": None,
        },
    )()
    calls: dict[str, object] = {}

    class FakeChatOllama:
        def __init__(self, **kwargs) -> None:
            calls.update(kwargs)

    monkeypatch.setattr(llm, "get_settings", lambda: settings)
    monkeypatch.setattr(llm, "ChatOllama", FakeChatOllama)

    client = llm.get_chat_client()

    assert isinstance(client, FakeChatOllama)
    assert calls == {
        "model": "tenerife-gemma-4-12b-it",
        "base_url": "http://ollama:11434",
        "temperature": 0.1,
        "num_predict": 2048,
    }


def test_get_embeddings_client_uses_ollama_when_configured(monkeypatch) -> None:
    settings = type(
        "Settings",
        (),
        {
            "embedding_provider": "ollama",
            "embedding_model": "nomic-embed-text",
            "ollama_base_url": "http://ollama:11434",
            "google_api_key": None,
        },
    )()
    calls: dict[str, object] = {}

    class FakeOllamaEmbeddings:
        def __init__(self, **kwargs) -> None:
            calls.update(kwargs)

    monkeypatch.setattr(llm, "get_settings", lambda: settings)
    monkeypatch.setattr(llm, "OllamaEmbeddings", FakeOllamaEmbeddings)

    client = llm.get_embeddings_client()

    assert isinstance(client, FakeOllamaEmbeddings)
    assert calls == {
        "model": "nomic-embed-text",
        "base_url": "http://ollama:11434",
    }


def test_require_generation_configuration_rejects_missing_gemini_key(monkeypatch) -> None:
    settings = type(
        "Settings",
        (),
        {
            "generation_provider": "gemini",
            "google_api_key": None,
            "ollama_base_url": "http://ollama:11434",
        },
    )()
    monkeypatch.setattr(llm, "get_settings", lambda: settings)

    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        llm.require_generation_configuration()
