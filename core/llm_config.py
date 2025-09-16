import os
import yaml
from dotenv import load_dotenv
from core.gemini_llm_adapter import GeminiLLMAdapter
from core.mocks import MockGeminiLLMAdapter

# Načtení proměnných prostředí ze souboru .env
load_dotenv()

def load_config():
    """
    Načte konfigurační soubor na základě proměnné prostředí SOPHIA_ENV.
    Pokud SOPHIA_ENV='test', načte 'config_test.yaml'.
    Jinak načte 'config.yaml'.
    """
    is_test_env = os.getenv('SOPHIA_ENV') == 'test'
    config_file = 'config_test.yaml' if is_test_env else 'config.yaml'

    if not os.path.exists(config_file):
        if is_test_env:
            print(f"Warning: Test config '{config_file}' not found. Using dummy config.")
            return {'llm_models': {'primary_llm': {'provider': 'mock', 'model_name': 'mock-model'}}}
        raise FileNotFoundError(f"Konfigurační soubor '{config_file}' nebyl nalezen.")

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        if not config:
            raise ValueError("Konfigurační soubor je prázdný.")
        return config
    except yaml.YAMLError as e:
        raise ValueError(f"Chyba při načítání konfiguračního souboru '{config_file}': {e}")

def get_llm():
    """
    Tovární funkce, která vrací správnou instanci LLM adaptéru
    na základě proměnné prostředí SOPHIA_ENV.
    """
    if os.getenv('SOPHIA_ENV') == 'test':
        print("--- Running in TEST environment, providing Mock LLM ---")
        return MockGeminiLLMAdapter()
    else:
        # V budoucnu zde bude inicializace reálného LLM s klíči z configu
        print("--- Running in PRODUCTION environment, providing Real LLM ---")
        return GeminiLLMAdapter()
