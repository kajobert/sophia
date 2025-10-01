import unittest
from unittest.mock import patch, mock_open
import os
import sys

# Přidání cesty k projektu pro importy
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

from core.llm_manager import LLMManager
from core.llm_adapters import OpenRouterAdapter

class TestLLMManager(unittest.TestCase):

    def setUp(self):
        """Nastaví mockovanou konfiguraci a prostředí pro každý test."""
        self.mock_config_content = """
llm_models:
  default: "economical"
  aliases:
    powerful: "deepseek/deepseek-r1"
    economical: "google/gemini-2.5-flash-lite"
  models:
    "google/gemini-2.5-flash-lite": {}
    "deepseek/deepseek-r1":
      system_prompt: "You are a powerful coding assistant."
"""
        # Mockování `open` pro čtení konfiguračního souboru
        self.mock_open = mock_open(read_data=self.mock_config_content)
        self.open_patcher = patch('builtins.open', self.mock_open)
        self.open_patcher.start()

        # Mockování `os.getenv` pro API klíč
        self.getenv_patcher = patch('os.getenv', return_value="fake_openrouter_key")
        self.getenv_patcher.start()

        # Mockování `load_dotenv`, aby se předešlo prohledávání souborového systému
        self.load_dotenv_patcher = patch('core.llm_manager.load_dotenv', return_value=True)
        self.load_dotenv_patcher.start()

    def tearDown(self):
        """Uklidí po každém testu."""
        self.open_patcher.stop()
        self.getenv_patcher.stop()
        self.load_dotenv_patcher.stop()

    @patch('core.llm_manager.OpenRouterAdapter')
    def test_get_llm_with_alias(self, mock_adapter):
        """Testuje, zda `get_llm` správně přeloží alias a vytvoří adaptér."""
        manager = LLMManager(project_root="/fake/path")

        # Test pro "powerful" alias
        llm_powerful = manager.get_llm("powerful")
        mock_adapter.assert_called_with(
            model_name="deepseek/deepseek-r1",
            client=manager._client,
            system_prompt="You are a powerful coding assistant."
        )

        # Test pro "economical" alias
        llm_economical = manager.get_llm("economical")
        mock_adapter.assert_called_with(
            model_name="google/gemini-2.5-flash-lite",
            client=manager._client
        )

    @patch('core.llm_manager.OpenRouterAdapter')
    def test_get_default_llm(self, mock_adapter):
        """Testuje, zda `get_llm` bez argumentu použije výchozí model z configu."""
        manager = LLMManager(project_root="/fake/path")

        llm_default = manager.get_llm()
        # Očekáváme "economical", který se přeloží na "google/gemini-2.5-flash-lite"
        mock_adapter.assert_called_with(
            model_name="google/gemini-2.5-flash-lite",
            client=manager._client
        )

    @patch('core.llm_manager.OpenRouterAdapter')
    def test_get_llm_with_direct_model_name(self, mock_adapter):
        """Testuje, zda `get_llm` funguje i s přímým názvem modelu."""
        manager = LLMManager(project_root="/fake/path")

        llm_direct = manager.get_llm("deepseek/deepseek-r1")
        mock_adapter.assert_called_with(
            model_name="deepseek/deepseek-r1",
            client=manager._client,
            system_prompt="You are a powerful coding assistant."
        )

    def test_invalid_model_name_raises_value_error(self):
        """Testuje, zda je vyhozena výjimka pro neexistující model nebo alias."""
        manager = LLMManager(project_root="/fake/path")

        with self.assertRaisesRegex(ValueError, "nebyl nalezen v 'config.yaml'"):
            manager.get_llm("non_existent_model")

    def test_missing_api_key_raises_value_error(self):
        """Testuje, zda je vyhozena výjimka, pokud chybí API klíč."""
        # Přepíšeme mock pro `os.getenv`, aby vracel None
        self.getenv_patcher.stop()
        getenv_patcher_none = patch('os.getenv', return_value=None)
        getenv_patcher_none.start()

        with self.assertRaisesRegex(ValueError, "API klíč 'OPENROUTER_API_KEY' nebyl nalezen"):
            LLMManager(project_root="/fake/path")

        getenv_patcher_none.stop()

if __name__ == '__main__':
    unittest.main()