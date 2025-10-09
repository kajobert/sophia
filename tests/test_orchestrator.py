import pytest
import os
import sys
import json
from unittest.mock import MagicMock, AsyncMock

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Mockování modulů PŘED jejich importem v orchestrátoru
# Tyto moduly mají vedlejší efekty (logování, TUI), které v testech nechceme.
sys.modules['core.rich_printer'] = MagicMock()

from core.worker_orchestrator import WorkerOrchestrator, TaskType
from core.mcp_client import MCPClient
from tests.mocks import MockLLMManager

@pytest.fixture
def orchestrator_instance(monkeypatch):
    """
    Vytvoří instanci WorkerOrchestrator s mockovanými závislostmi pro testování.
    """
    # Mock MCPClient to avoid running real servers
    mock_mcp_client = MagicMock(spec=MCPClient)
    mock_mcp_client.start_servers = AsyncMock()
    monkeypatch.setattr('core.worker_orchestrator.MCPClient', lambda *args, **kwargs: mock_mcp_client)

    # Patch the LLMManager class *before* orchestrator is instantiated
    monkeypatch.setattr('core.worker_orchestrator.LLMManager', MockLLMManager)

    # Now, create the orchestrator instance.
    orc = WorkerOrchestrator(project_root='.')

    # Replace the real PromptBuilder, which reads files
    mock_prompt_builder = MagicMock()
    mock_prompt_builder.build_prompt.return_value = "Mocked complex prompt"
    mock_prompt_builder.build_prompt_for_simple_query.return_value = "Mocked simple prompt"
    orc.prompt_builder = mock_prompt_builder

    return orc

def test_parse_llm_response_valid_json(orchestrator_instance):
    """Testuje parsování validní JSON odpovědi."""
    response_text = json.dumps({"key": "value"})
    parsed = orchestrator_instance._parse_llm_response(response_text)
    assert parsed == {"key": "value"}

def test_parse_llm_response_invalid_json(orchestrator_instance):
    """Testuje, jak si parsování poradí s nevalidním JSON."""
    parsed = orchestrator_instance._parse_llm_response("this is not json")
    assert "error" in parsed
    assert parsed["error"] == "JSON_DECODE_ERROR"

def test_parse_llm_response_wrapped_in_markdown(orchestrator_instance):
    """Testuje parsování JSONu, který je zabalený v Markdown bloku."""
    raw_response = '```json\n{"key": "wrapped"}\n```'
    parsed = orchestrator_instance._parse_llm_response(raw_response)
    assert parsed == {"key": "wrapped"}

@pytest.mark.asyncio
async def test_triage_simple_query(orchestrator_instance, monkeypatch):
    """
    Ověřuje, že vstup klasifikovaný jako SIMPLE_QUERY zavolá _handle_simple_query.
    """
    triage_response = {"task_type": "SIMPLE_QUERY", "details": "User is asking a question."}
    orchestrator_instance.llm_manager.configure_llm_response('default', {
        "klasifikuj typ úkolu": triage_response
    })

    mock_handler = AsyncMock()
    monkeypatch.setattr(orchestrator_instance, '_handle_simple_query', mock_handler)

    await orchestrator_instance.run("Jak se máš?")

    mock_handler.assert_called_once()
    call_args, _ = mock_handler.call_args
    assert call_args[0] == "Jak se máš?"
    assert call_args[1] == "User is asking a question."

@pytest.mark.asyncio
async def test_triage_direct_command(orchestrator_instance, monkeypatch):
    """
    Ověřuje, že vstup klasifikovaný jako DIRECT_COMMAND zavolá _handle_direct_command.
    """
    triage_response = {"task_type": "DIRECT_COMMAND"}
    orchestrator_instance.llm_manager.configure_llm_response('default', {
        "klasifikuj typ úkolu": triage_response
    })

    mock_handler = AsyncMock()
    monkeypatch.setattr(orchestrator_instance, '_handle_direct_command', mock_handler)

    await orchestrator_instance.run("vypiš soubory")

    mock_handler.assert_called_once_with("vypiš soubory")

@pytest.mark.asyncio
async def test_triage_complex_task(orchestrator_instance, monkeypatch):
    """
    Ověřuje, že vstup klasifikovaný jako COMPLEX_TASK zavolá _execute_complex_task.
    """
    triage_response = {"task_type": "COMPLEX_TASK"}
    orchestrator_instance.llm_manager.configure_llm_response('default', {
        "klasifikuj typ úkolu": triage_response
    })

    mock_handler = AsyncMock()
    monkeypatch.setattr(orchestrator_instance, '_execute_complex_task', mock_handler)

    await orchestrator_instance.run("Refaktoruj celý projekt")

    mock_handler.assert_called_once_with("Refaktoruj celý projekt")