def get_llm():
    """
    Vrací instanci inicializovaného LLM (globální proměnná llm).
    Pokud není validní, zaloguje a vyhodí chybu.
    """
    global llm
    if llm is None:
        print("[get_llm] Chyba: llm je None!")
        raise ValueError("LLM instance není inicializována (llm is None)")
    print(f"[get_llm] Vrací instanci typu: {type(llm)}")
    return llm

import os
import yaml
from dotenv import load_dotenv
from core.gemini_llm_adapter import GeminiLLMAdapter
# from langchain_google_genai import ChatGoogleGenerativeAI  # fallback do budoucna

# Načtení proměnných prostředí ze souboru .env
load_dotenv()

# --- Robustní načtení globální konfigurace ---
CONFIG_FILE = "config.yaml"
config = None
config_paths_tried = []


try:
    # 1. Zkus aktuální pracovní adresář
    cwd_path = os.path.abspath(CONFIG_FILE)
    module_dir = os.path.dirname(os.path.abspath(__file__))
    module_path = os.path.join(module_dir, CONFIG_FILE)
    root_path = os.path.abspath(os.path.join(module_dir, '..', CONFIG_FILE))
    config_paths_tried = [cwd_path, module_path, root_path]

    if os.path.exists(cwd_path):
        with open(cwd_path, 'r') as f:
            config = yaml.safe_load(f)
    elif os.path.exists(module_path):
        with open(module_path, 'r') as f:
            config = yaml.safe_load(f)
    elif os.path.exists(root_path):
        with open(root_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        raise FileNotFoundError()
    if not config:
        raise ValueError("Konfigurační soubor je prázdný.")
except Exception as e:
    raise ValueError(f"Chyba při načítání konfiguračního souboru '{CONFIG_FILE}'. Hledané cesty: {config_paths_tried}. Chyba: {e}")

# --- Konfigurace primárního LLM ---
llm_config = config.get('llm_models', {}).get('primary_llm')
if not llm_config:
    raise ValueError("V konfiguračním souboru chybí sekce 'llm_models.primary_llm'.")

# Získání API klíče z proměnných prostředí
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("API klíč pro LLM (GEMINI_API_KEY) nebyl nalezen v .env souboru.")

provider = llm_config.get('provider')
# Inicializace LLM na základě konfigurace
if provider == 'google':
    llm = GeminiLLMAdapter(
        model=llm_config.get('model_name', 'gemini-2.5-flash'),
        api_key=api_key,
        temperature=llm_config.get('temperature', 0.7),
        max_tokens=llm_config.get('max_tokens', 2048),
        verbose=llm_config.get('verbose', False)
    )
    # Pokud bude LangChain wrapper funkční, lze zde přepnout na ChatGoogleGenerativeAI
else:
    # V budoucnu zde může být podpora pro další providery
    raise ValueError(f"Neznámý nebo nepodporovaný provider LLM: {provider}")

print(f"LLM provider '{provider}' byl úspěšně inicializován s modelem '{llm_config.get('model_name')}'.")
