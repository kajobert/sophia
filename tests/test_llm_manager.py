import unittest
from unittest.mock import patch, mock_open, ANY
import os
import sys

# Přidání cesty k projektu pro importy
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

from core.llm_manager import LLMManager

class TestLLMManagerRefactored(unittest.TestCase):

    def setUp(self):
        """Nastaví mockovanou konfiguraci a prostředí pro každý test."""
        self.mock_config_content = """
llm_models:
  default: "economical"
  aliases:
    powerful: "deepseek/deepseek-v3.2-exp"
    economical: "google/gemini-2.5-flash-lite"
  models:
    "google/gemini-2.5-flash-lite": {}
    "deepseek/deepseek-v3.2-exp": {}
    "anthropic/claude-3-haiku": {}
  fallback_models:
    - "anthropic/claude-3-haiku"
"""
        # Mockování `open` pro čtení konfiguračního souboru
        self.mock_open_func = patch('builtins.open', mock_open(read_data=self.mock_config_content))
        self.mock_open_func.start()

        # Mockování `os.getenv` pro API klíč
        self.getenv_patcher = patch('os.getenv')
        self.mock_getenv = self.getenv_patcher.start()
        # Default behavior: only OpenRouter key is found
        self.mock_getenv.side_effect = lambda key, default=None: "fake_openrouter_key" if key == 'OPENROUTER_API_KEY' else None


        # Mockování `load_dotenv`, aby se předešlo prohledávání souborového systému
        self.load_dotenv_patcher = patch('core.llm_manager.load_dotenv', return_value=True)
        self.mock_load_dotenv = self.load_dotenv_patcher.start()

        # Patchování adaptéru, abychom mohli kontrolovat, s jakými argumenty je volán
        self.adapter_patcher = patch('core.llm_manager.OpenRouterAdapter', autospec=True)
        self.mock_adapter = self.adapter_patcher.start()


    def tearDown(self):
        """Uklidí po každém testu."""
        self.mock_open_func.stop()
        self.getenv_patcher.stop()
        self.load_dotenv_patcher.stop()
        self.adapter_patcher.stop()

    def test_get_llm_with_alias_resolves_correctly(self):
        """Testuje, zda get_llm správně přeloží alias na název modelu."""
        manager = LLMManager()
        manager.get_llm("powerful")

        self.mock_adapter.assert_called_once()
        args, kwargs = self.mock_adapter.call_args
        self.assertEqual(kwargs.get('model_name'), "deepseek/deepseek-v3.2-exp")

    def test_get_default_llm_returns_correct_adapter(self):
        """Testuje, zda get_llm bez argumentu vrátí výchozí adaptér."""
        manager = LLMManager()
        manager.get_llm() # Volání bez argumentu

        self.mock_adapter.assert_called_once()
        args, kwargs = self.mock_adapter.call_args
        self.assertEqual(kwargs.get('model_name'), "google/gemini-2.5-flash-lite")

    def test_fallback_models_are_passed_to_adapter(self):
        """Testuje, zda je seznam záložních modelů správně předán do adaptéru."""
        manager = LLMManager()
        manager.get_llm("powerful")

        self.mock_adapter.assert_called_once()
        args, kwargs = self.mock_adapter.call_args
        self.assertEqual(kwargs.get('fallback_models'), ["anthropic/claude-3-haiku"])

    def test_invalid_model_name_raises_value_error(self):
        """Testuje, zda je vyhozena výjimka ValueError pro neexistující název modelu."""
        manager = LLMManager()
        with self.assertRaises(ValueError):
            manager.get_llm("non_existent_model")

    def test_get_llm_without_alias_uses_direct_name(self):
        """Testuje, zda get_llm s přímým názvem modelu funguje správně."""
        manager = LLMManager()
        manager.get_llm("anthropic/claude-3-haiku")

        self.mock_adapter.assert_called_once()
        args, kwargs = self.mock_adapter.call_args
        self.assertEqual(kwargs.get('model_name'), "anthropic/claude-3-haiku")

    def test_api_key_error_handling(self):
        """Testuje, zda je vyhozena výjimka ValueError, když není nalezen API klíč."""
        # Zastavíme a znovu patchneme os.getenv, aby vracel None
        self.mock_getenv.side_effect = None
        self.mock_getenv.return_value = None

        with self.assertRaisesRegex(ValueError, "Žádný LLM provider není dostupný"):
            LLMManager()

if __name__ == '__main__':
    unittest.main()