import os
import yaml
from dotenv import load_dotenv
from core.gemini_llm_adapter import GeminiLLMAdapter

# --- Globální cache pro LLM instanci ---
_llm_instance = None

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
    Inicializuje a vrací primární LLM instanci.
    Používá lazy initialization a cachování, aby se předešlo opakované inicializaci.
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    # --- Načtení globální konfigurace ---
    config = load_config()

    # --- Konfigurace primárního LLM ---
    llm_config = config.get('llm_models', {}).get('primary_llm')

    if not llm_config:
        raise ValueError("V konfiguračním souboru chybí sekce 'llm_models.primary_llm'.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key and os.getenv('SOPHIA_ENV') != 'test':
        print("Warning: GEMINI_API_KEY not found in .env. Some features may not work.")
        api_key = "dummy-key-for-initialization"

    provider = llm_config.get('provider')

    if provider == 'google':
        _llm_instance = GeminiLLMAdapter(
            model=llm_config['model_name'],
            api_key=api_key,
            temperature=llm_config.get('temperature', 0.7),
            max_tokens=llm_config.get('max_tokens', 2048),
            verbose=llm_config.get('verbose', False)
        )
    elif provider == 'mock':
        # V testu bude tato hodnota None, ale fixture v conftest.py
        # by měla mockovat samotnou funkci get_llm, takže se sem ani nedostaneme.
        _llm_instance = None
    else:
        raise ValueError(f"Neznámý nebo nepodporovaný provider LLM: {provider}")

    if _llm_instance:
        print(f"LLM provider '{provider}' byl úspěšně inicializován s modelem '{llm_config.get('model_name')}'.")

    return _llm_instance
