from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path


def main() -> None:
    base_url = os.environ["OLLAMA_BASE_URL"].rstrip("/")
    chat_model = os.environ["OLLAMA_CHAT_MODEL"]
    model_url = os.environ["OLLAMA_MODEL_SOURCE_URL"]
    model_filename = os.environ["OLLAMA_MODEL_FILENAME"]
    embedding_model = os.environ["OLLAMA_EMBEDDING_MODEL"]
    models_dir = Path(os.environ.get("OLLAMA_MODELS_DIR", "/models"))
    hf_token = os.environ.get("HF_TOKEN", "")
    gguf_path = models_dir / model_filename

    models_dir.mkdir(parents=True, exist_ok=True)

    wait_for_ollama(base_url)
    ensure_downloaded(model_url, gguf_path, hf_token)
    ensure_custom_model(base_url, chat_model, gguf_path)
    ensure_pulled_model(base_url, embedding_model)


def wait_for_ollama(base_url: str, retries: int = 60, delay_seconds: int = 2) -> None:
    for _ in range(retries):
        try:
            with urllib.request.urlopen(f"{base_url}/api/tags", timeout=5) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(delay_seconds)
    raise RuntimeError("Ollama no respondió a tiempo durante el bootstrap del modelo.")


def ensure_downloaded(source_url: str, destination: Path, hf_token: str) -> None:
    if destination.exists():
        return

    request = urllib.request.Request(source_url)
    if hf_token:
        request.add_header("Authorization", f"Bearer {hf_token}")

    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as target:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            target.write(chunk)


def ensure_custom_model(base_url: str, model_name: str, gguf_path: Path) -> None:
    if model_exists(base_url, model_name):
        return

    payload = {
        "name": model_name,
        "modelfile": f"FROM {gguf_path.as_posix()}\nPARAMETER num_ctx 8192\n",
        "stream": False,
    }
    post_json(f"{base_url}/api/create", payload, timeout=600)


def ensure_pulled_model(base_url: str, model_name: str) -> None:
    if model_exists(base_url, model_name):
        return

    post_json(
        f"{base_url}/api/pull",
        {
            "name": model_name,
            "stream": False,
        },
        timeout=600,
    )


def model_exists(base_url: str, model_name: str) -> bool:
    with urllib.request.urlopen(f"{base_url}/api/tags", timeout=10) as response:
        payload = json.load(response)
    models = payload.get("models") or []
    return any(model.get("name") == model_name for model in models)


def post_json(url: str, payload: dict, timeout: int) -> None:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status >= 400:
            raise RuntimeError(f"Fallo llamando a {url}: HTTP {response.status}")


if __name__ == "__main__":
    main()
