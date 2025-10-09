import pytest
import os
import sys
import json
from unittest.mock import MagicMock, AsyncMock

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Mockování modulů PŘED jejich importem v orchestrátoru
sys.modules['core.long_term_memory'] = MagicMock()
sys.modules['core.rich_printer'] = MagicMock()

# Musíme nechat PromptBuilder jako skutečnou třídu, abychom mohli mockovat jeho metody
from core.prompt_builder import PromptBuilder

from core.orchestrator import WorkerOrchestrator # Změněno z JulesOrchestrator
from core.llm_manager import LLMManager
from core.mcp_client import MCPClient

@pytest.fixture
def orchestrator_instance(monkeypatch):
    """
    Vytvoří bezpečnou a izolovanou instanci orchestrátoru pro testování.
    """
    monkeypatch.setenv('OPENROUTER_API_KEY', 'mock_key')

    def mock_load_config(self):
        self.config = {
            "llm_models": {"default": "mock", "aliases": {}, "models": {"mock": {}}},
            "orchestrator": {"max_iterations": 10},
            "memory": {"short_term_limit": 3, "long_term_retrieval_limit": 3},
        }
    monkeypatch.setattr(LLMManager, "_load_config", mock_load_config)

    # MCPClient nyní vyžaduje 'profile' v __init__
    async def mock_start_servers(self):
        pass
    monkeypatch.setattr(MCPClient, "__init__", lambda self, project_root, profile: None)
    monkeypatch.setattr(MCPClient, "start_servers", mock_start_servers)


    # Mockujeme PromptBuilder, abychom se vyhnuli čtení souboru a LTM
    mock_prompt_builder_instance = MagicMock(spec=PromptBuilder)
    mock_prompt_builder_instance.build_prompt.return_value = "Mocked prompt"
    monkeypatch.setattr('core.orchestrator.PromptBuilder', lambda *args, **kwargs: mock_prompt_builder_instance)

    # Instancujeme novou třídu
    orc = WorkerOrchestrator(project_root='.')
    # Připojíme si mock pro pozdější kontrolu
    orc.prompt_builder = mock_prompt_builder_instance
    # Mockujeme klienta i po inicializaci, abychom měli plnou kontrolu
    orc.mcp_client = MagicMock(spec=MCPClient)
    return orc

def test_parse_llm_response_valid(orchestrator_instance):
    """Testuje parsování validní JSON odpovědi."""
    response_text = json.dumps({"explanation": "Test.", "tool_call": {"tool_name": "test_tool"}})
    explanation, tool_call = orchestrator_instance._parse_llm_response(response_text)
    assert explanation == "Test."
    assert tool_call['tool_name'] == "test_tool"

def test_parse_llm_response_invalid_json(orchestrator_instance):
    """Testuje, jak si parsování poradí s nevalidním JSON."""
    explanation, tool_call = orchestrator_instance._parse_llm_response("not json")
    assert "CHYBA PARSOVÁNÍ JSON" in explanation
    assert tool_call is None

def test_parse_llm_response_wrapped_in_markdown(orchestrator_instance):
    """Testuje parsování JSON odpovědi, která je zabalená v Markdown bloku."""
    raw_response = '```json\n{"explanation": "Wrapped", "tool_call": {"tool_name": "wrapped_tool"}}\n```'
    explanation, tool_call = orchestrator_instance._parse_llm_response(raw_response)
    assert explanation == "Wrapped"
    assert tool_call['tool_name'] == "wrapped_tool"

@pytest.mark.asyncio
async def test_orchestrator_gets_and_passes_main_goal(orchestrator_instance, monkeypatch):
    """
    Ověřuje, že WorkerOrchestrator zavolá `get_main_goal` a předá výsledek do PromptBuilderu.
    """
    mock_mcp_client = orchestrator_instance.mcp_client
    mock_mcp_client.get_tool_descriptions.return_value = "Mocked tool descriptions"

    expected_main_goal = "Toto je hlavní cíl mise."
    async def mock_execute_tool(tool_name, *args, **kwargs):
        if tool_name == "get_main_goal":
            return expected_main_goal
        # Simulujeme dokončení úkolu, aby se smyčka ukončila
        if tool_name == "task_complete":
            return '{"status": "completed"}'
        return "{}"
    mock_mcp_client.execute_tool = AsyncMock(side_effect=mock_execute_tool)

    mock_llm = MagicMock()
    mock_llm.generate_content_async = AsyncMock(return_value=(json.dumps({
        "explanation": "Ukončuji test.",
        "tool_call": {"tool_name": "task_complete"}
    }), {}))
    monkeypatch.setattr(orchestrator_instance.llm_manager, "get_llm", lambda *args: mock_llm)

    # Spustíme `run` s budgetem 1, aby proběhla jen jedna iterace
    await orchestrator_instance.run("Testovací úkol", budget=1)

    # Ověříme, že `get_main_goal` byl zavolán
    mock_mcp_client.execute_tool.assert_any_call("get_main_goal", [], {}, False)

    # Ověříme, že PromptBuilder byl volán se správným `main_goal`
    orchestrator_instance.prompt_builder.build_prompt.assert_called_once()
    call_args, call_kwargs = orchestrator_instance.prompt_builder.build_prompt.call_args
    assert "main_goal" in call_kwargs
    assert call_kwargs["main_goal"] == expected_main_goal