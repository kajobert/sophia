import pytest
import asyncio
from pathlib import Path

from plugins.tool_local_llm import LocalLLMTool


def is_ollama_up(base_url="http://localhost:11434"):
    import requests
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=2)
        return r.ok
    except Exception:
        return False


@pytest.mark.asyncio
@pytest.mark.skipif(not is_ollama_up(), reason="Ollama not available on localhost:11434")
async def test_local_llm_smoke():
    # Basic smoke test: setup plugin and run check_availability and list_models
    plugin = LocalLLMTool()
    config = {"local_llm": {"base_url": "http://localhost:11434", "model": "llama3.1:8b"}, "offline_mode": True}
    plugin.setup({"local_llm": config["local_llm"], "offline_mode": True})

    available = await plugin.check_availability()
    assert available is True

    models = await plugin.list_models()
    assert isinstance(models, list)
    assert "llama3.1:8b" in models
