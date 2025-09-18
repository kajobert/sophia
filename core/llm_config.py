import os
import yaml
from dotenv import load_dotenv
from core.gemini_llm_adapter import GeminiLLMAdapter
from core.mocks import MockGeminiLLMAdapter

# Načtení proměnných prostředí ze souboru .env
load_dotenv()

def load_config():
    """
    Načte konfigurační soubor. Hledá 'config_test.yaml' (pokud SOPHIA_ENV='test')
    nebo 'config.yaml' v několika možných lokacích.
    """
    is_test_env = os.getenv('SOPHIA_ENV') == 'test'
    config_file = 'config_test.yaml' if is_test_env else 'config.yaml'

    # --- Robustní načtení globální konfigurace (převzato z forku) ---
    config = None
    paths_to_try = [
        os.path.abspath(config_file), # 1. Aktuální pracovní adresář
        os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file), # 2. Adresář modulu
        os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', config_file)) # 3. Kořenový adresář projektu
    ]

    for path in paths_to_try:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    config = yaml.safe_load(f)
                if config:
                    print(f"Konfigurační soubor '{config_file}' úspěšně načten z: {path}")
                    return config
            except yaml.YAMLError as e:
                raise ValueError(f"Chyba při načítání konfiguračního souboru '{path}': {e}")

    # Pokud se soubor nenajde a jsme v testu, vrátíme dummy config
    if is_test_env:
        print(f"Warning: Test config '{config_file}' not found in {paths_to_try}. Using dummy config.")
        return {'llm_models': {'primary_llm': {'provider': 'mock', 'model_name': 'mock-model'}}}

    raise FileNotFoundError(f"Konfigurační soubor '{config_file}' nebyl nalezen v žádné z prohledávaných cest: {paths_to_try}")


def get_llm():
    """
    Tovární funkce, která vrací správnou instanci LLM adaptéru
    na základě proměnné prostředí SOPHIA_ENV.
    """
    config = load_config()
    primary_llm_config = config.get('llm_models', {}).get('primary_llm')
    if not primary_llm_config:
        raise ValueError("V konfiguračním souboru chybí sekce 'llm_models.primary_llm'.")

    model_name = primary_llm_config.get('model_name')

    if os.getenv('SOPHIA_ENV') == 'test':
        print("--- Running in TEST environment, providing Mock LLM ---")
        return MockGeminiLLMAdapter(model=model_name)
    else:
        print(f"--- Running in PRODUCTION environment, providing Real LLM: {model_name} ---")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")

        return GeminiLLMAdapter(
            model=model_name,
            api_key=api_key,
            temperature=primary_llm_config.get('temperature', 0.7),
            max_tokens=primary_llm_config.get('max_tokens', 2048),
            verbose=primary_llm_config.get('verbose', False)
        )
