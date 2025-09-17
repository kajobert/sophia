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
    config = load_config()
    primary_llm_config = config['llm_models']['primary_llm']
    model_name = primary_llm_config['model_name']

    if os.getenv('SOPHIA_ENV') == 'test':
        print("--- Running in TEST environment, providing Mock LLM ---")
        # I v testu můžeme předat model, aby byl podpis konzistentní
        return MockGeminiLLMAdapter(model=model_name)
    else:
        print(f"--- Running in PRODUCTION environment, providing Real LLM: {model_name} ---")
        # Získání API klíče z proměnných prostředí
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        return GeminiLLMAdapter(api_key=api_key, model=model_name)
