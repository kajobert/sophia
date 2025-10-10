import pytest
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Sestavení správné cesty k 'core'
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.conversational_manager import ConversationalManager

# --- Testovací Fixtures ---

@pytest.fixture
def temp_project_root(tmp_path):
    """Vytvoří dočasný kořenový adresář projektu pro izolované testy."""
    (tmp_path / "prompts").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "db").mkdir()
    with open(tmp_path / "prompts/system_prompt.txt", "w") as f:
        f.write("You are a worker agent.")
    with open(tmp_path / "prompts/manager_prompt.txt", "w") as f:
        f.write("You are a manager agent.")
    with open(tmp_path / "prompts/reflection_prompt.txt", "w") as f:
        f.write("Analyze history: {task_history}. Produce one learning.")
    with open(tmp_path / "config/config.yaml", "w") as f:
        f.write("""
llm_models:
  default: 'mock_model'
  options:
    mock_model:
      adapter: 'MockLLM'
      config: {}
vector_database:
  path: 'db/test_chroma.db'
  collection_name: 'test_collection'
""")
    with open(tmp_path / ".env", "w") as f:
        f.write("OPENROUTER_API_KEY=dummy_key_for_testing\n")
    return str(tmp_path)


@pytest.fixture
async def manager_with_mocks(temp_project_root):
    """
    Fixture, která poskytuje instanci ConversationalManager s mockovanými
    závislostmi pro testování reflexního cyklu.
    """
    # Klíčový fix: Patchujeme tam, kde se objekty POUŽÍVAJÍ (v orchestratoru).
    # To zajistí, že i PromptBuilder dostane správný mock.
    with patch('core.llm_manager.LLMManager') as MockLLMManager, \
         patch('core.orchestrator.LongTermMemory') as MockLTM, \
         patch('core.conversational_manager.WorkerOrchestrator') as MockWorkerOrchestrator:

        # Mockování LLM
        mock_llm_instance = AsyncMock()
        mock_llm_instance.generate_content_async.side_effect = [
            # 1. Odpověď Manažera -> delegovat na Workera
            ('{"explanation": "Delegating to worker.", "tool_call": {"tool_name": "delegate_task_to_worker", "kwargs": {"task": "Create a directory"}}}', {}),
            # 2. Odpověď LLM pro Reflexi -> vygeneruje poučení
            ("Poučení: Pro vytvoření adresáře je přímý příkaz `mkdir` efektivnější.", {}),
            # 3. Finální odpověď Manažera pro uživatele
            ("Worker has finished the task.", {}),
        ]
        mock_llm_manager_instance = MockLLMManager.return_value
        mock_llm_manager_instance.get_llm.return_value = mock_llm_instance

        # Mockování LTM
        mock_ltm_instance = MockLTM.return_value
        mock_ltm_instance.add = MagicMock()

        # Mockování Workera
        # Nemusíme testovat vnitřní logiku workera, jen to, že vrátí historii.
        mock_worker_instance = MockWorkerOrchestrator.return_value
        mock_worker_instance.run = AsyncMock(return_value={
            "status": "completed",
            "summary": "Directory created.",
            "history": [
                ("Myšlenka: Zkontrolovat adresář", "Výsledek: Neexistuje"),
                ("Myšlenka: Vytvořit adresář", "Výsledek: Vytvořen"),
            ]
        })
        # Důležité: Musíme také mockovat LTM instanci na workerovi pro `_run_reflection`
        mock_worker_instance.ltm = mock_ltm_instance
        # Musíme také mockovat asynchronní metody, které manažer volá
        mock_worker_instance.initialize = AsyncMock()
        mock_worker_instance.shutdown = AsyncMock()

        manager = ConversationalManager(project_root=temp_project_root)
        # Přepsání skutečných instancí mocky
        manager.llm_manager = mock_llm_manager_instance
        manager.worker = mock_worker_instance # Nahradíme celého workera mockem

        await manager.initialize()
        yield manager, mock_llm_instance, mock_ltm_instance
        await manager.shutdown()

# --- Testovací Scénář ---

@pytest.mark.asyncio
async def test_reflection_is_called_and_saves_learning(manager_with_mocks):
    """
    Ověří, že po dokončení úkolu:
    1. Je spuštěna sebereflexe.
    2. Do LTM je uložen správně zformátovaný poznatek.
    """
    manager, mock_llm, mock_ltm = manager_with_mocks

    # Spustit hlavní handle funkci
    await manager.handle_user_input("Vytvoř adresář `test_dir`.")

    # 1. Ověření, že se volal LLM pro reflexi
    # První volání je pro rozhodnutí manažera, druhé pro reflexi.
    reflection_llm_call = mock_llm.generate_content_async.call_args_list[1]
    reflection_prompt = reflection_llm_call.args[0]
    assert "Analyze history" in reflection_prompt
    assert "Myšlenka: Zkontrolovat adresář" in reflection_prompt

    # 2. Ověření, že se zavolala metoda pro uložení do LTM se správnými daty
    mock_ltm.add.assert_called_once()
    args, kwargs = mock_ltm.add.call_args

    # Ověření dokumentu (learning)
    assert "documents" in kwargs
    assert len(kwargs["documents"]) == 1
    assert "Poučení: Pro vytvoření adresáře je přímý příkaz `mkdir` efektivnější." in kwargs['documents'][0]

    # Ověření metadat
    assert "metadatas" in kwargs
    assert len(kwargs["metadatas"]) == 1
    assert kwargs['metadatas'][0]['type'] == 'learning'

    print("Test reflection mechanism passed successfully.")