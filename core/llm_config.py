import os
import yaml
from dotenv import load_dotenv
from core.gemini_llm_adapter import GeminiLLMAdapter

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

    # Zkontroluje, zda soubor existuje
    if not os.path.exists(config_file):
        if is_test_env:
            # V testu můžeme vrátit dummy config, abychom se vyhnuli chybě API klíče
            # a umožnili Pytestu alespoň sebrat testy bez pádu na importu.
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


# --- Načtení globální konfigurace ---
config = load_config()


# --- Konfigurace primárního LLM ---
llm_config = config.get('llm_models', {}).get('primary_llm')

if not llm_config:
    raise ValueError("V konfiguračním souboru chybí sekce 'llm_models.primary_llm'.")

# Získání API klíče z proměnných prostředí
# V testovacím prostředí se klíč nepoužívá, protože LLM je mockován.
api_key = os.getenv("GEMINI_API_KEY")
if not api_key and os.getenv('SOPHIA_ENV') != 'test':
    print("Warning: GEMINI_API_KEY not found in .env. Some features may not work.")
    # V non-test prostředí by zde mohla být přísnější kontrola
    api_key = "dummy-key-for-collection"


provider = llm_config.get('provider')

# Inicializace LLM na základě konfigurace
# V testu bude tato instance nahrazena mockem přes conftest.py
if provider == 'google':
    llm = GeminiLLMAdapter(
        model=llm_config['model_name'],
        api_key=api_key,
        temperature=llm_config.get('temperature', 0.7),
        max_tokens=llm_config.get('max_tokens', 2048),
        verbose=llm_config.get('verbose', False)
    )
elif provider == 'mock':
    # Tento blok se použije, pokud je v config_test.yaml explicitně provider 'mock'
    # nebo pokud config_test.yaml chybí a vrátí se dummy config.
    llm = None
else:
    raise ValueError(f"Neznámý nebo nepodporovaný provider LLM: {provider}")

if llm:
    print(f"LLM provider '{provider}' byl úspěšně inicializován s modelem '{llm_config.get('model_name')}'.")
