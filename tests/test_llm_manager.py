import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys

# Přidání cesty k projektu pro importy
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

from core.llm_manager import LLMManager
from core.llm_adapters import GoogleGeminiAdapter, DeepSeekAdapter, OllamaAdapter

# Mock pro google.generativeai
mock_google_genai = MagicMock()
# sys.modules['google'] = MagicMock() # This is too broad and might cause issues
sys.modules['google.generativeai'] = mock_google_genai


class TestLLMManager(unittest.TestCase):

    def setUp(self):
        """Nastaví mockovanou konfiguraci a prostředí pro každý test."""
        self.mock_config_content = """
llm_models:
  default: economical
  llms:
    powerful:
      provider: "google"
      model_name: "gemini-1.5-pro-latest"
      api_key_env: "GEMINI_API_KEY"
    economical:
      provider: "deepseek"
      model_name: "deepseek-coder-v2"
      api_key_env: "DEEPSEEK_API_KEY"
    local:
      provider: "ollama"
      model_name: "llama3"
"""
        # Mockování `open` pro čtení konfiguračního souboru
        self.mock_open_func = mock_open(read_data=self.mock_config_content)

        # Mockování `os.getenv` pro API klíče
        self.getenv_patcher = patch('os.getenv', self._mock_getenv)
        self.mock_getenv = self.getenv_patcher.start()

        # Zásadní oprava: Mockování `load_dotenv`, aby se předešlo prohledávání souborového systému, které způsobuje timeout.
        self.load_dotenv_patcher = patch('core.llm_manager.load_dotenv', return_value=True)
        self.mock_load_dotenv = self.load_dotenv_patcher.start()

    def tearDown(self):
        """Uklidí po každém testu."""
        self.getenv_patcher.stop()
        self.load_dotenv_patcher.stop()
        # Resetování mocku, aby testy byly izolované
        mock_google_genai.reset_mock()


    def _mock_getenv(self, key):
        """Mockovací funkce pro os.getenv."""
        if key == "GEMINI_API_KEY":
            return "fake_gemini_key"
        if key == "DEEPSEEK_API_KEY":
            return "fake_deepseek_key"
        return None

    @patch('core.llm_adapters.GoogleGeminiAdapter')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_powerful_llm_returns_correct_adapter(self, mock_file, mock_adapter):
        """Testuje, zda `get_llm` správně vrací 'powerful' (Google) adaptér."""
        mock_file.return_value.read.return_value = self.mock_config_content
        manager = LLMManager()

        llm = manager.get_llm("powerful")
        self.assertIsInstance(llm, mock_adapter.__class__)

    @patch('builtins.open', new_callable=mock_open)
    def test_get_economical_llm_returns_correct_adapter(self, mock_file):
        """Testuje, zda `get_llm` správně vrací 'economical' (DeepSeek) adaptér."""
        mock_file.return_value.read.return_value = self.mock_config_content
        manager = LLMManager()

        llm = manager.get_llm("economical")
        self.assertIsInstance(llm, DeepSeekAdapter)

    @patch('builtins.open', new_callable=mock_open)
    def test_get_local_llm_returns_correct_adapter(self, mock_file):
        """Testuje, zda `get_llm` správně vrací 'local' (Ollama) adaptér."""
        mock_file.return_value.read.return_value = self.mock_config_content
        manager = LLMManager()

        llm = manager.get_llm("local")
        self.assertIsInstance(llm, OllamaAdapter)

    @patch('builtins.open', new_callable=mock_open)
    def test_get_default_llm_returns_correct_adapter(self, mock_file):
        """Testuje, zda `get_llm` bez argumentu vrací výchozí adaptér."""
        mock_file.return_value.read.return_value = self.mock_config_content
        manager = LLMManager()

        llm = manager.get_llm() # Volání bez argumentu
        self.assertIsInstance(llm, DeepSeekAdapter)

    @patch('builtins.open', new_callable=mock_open)
    def test_caching_mechanism_returns_same_instance(self, mock_file):
        """Testuje, zda LLM klienti jsou cachováni a vrací se stejná instance."""
        mock_file.return_value.read.return_value = self.mock_config_content
        manager = LLMManager()

        llm1 = manager.get_llm("powerful")
        llm2 = manager.get_llm("powerful")

        self.assertIs(llm1, llm2, "LLMManager by měl pro stejný název modelu vracet stejnou instanci.")

    @patch('builtins.open', new_callable=mock_open)
    def test_invalid_model_name(self, mock_file):
        """Testuje, zda je vyhozena výjimka pro neexistující model."""
        mock_file.return_value.read.return_value = self.mock_config_content
        manager = LLMManager()

        with self.assertRaises(ValueError):
            manager.get_llm("non_existent_model")

if __name__ == '__main__':
    unittest.main()