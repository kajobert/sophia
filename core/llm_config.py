import os
import yaml
from dotenv import load_dotenv
from core.gemini_llm_adapter import GeminiLLMAdapter
# from langchain_google_genai import ChatGoogleGenerativeAI  # fallback do budoucna

# Načtení proměnných prostředí ze souboru .env
load_dotenv()

# --- Načtení globální konfigurace ---
CONFIG_FILE = "config.yaml"
try:
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)
    if not config:
        raise ValueError("Konfigurační soubor je prázdný.")
except (FileNotFoundError, yaml.YAMLError) as e:
    raise ValueError(f"Chyba při načítání konfiguračního souboru '{CONFIG_FILE}': {e}")

# --- Konfigurace primárního LLM ---
llm_config = config.get('llm_models', {}).get('primary_llm')

if not llm_config:
    raise ValueError("V konfiguračním souboru chybí sekce 'llm_models.primary_llm'.")

# Získání API klíče z proměnných prostředí
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY not found in .env. Using a dummy key for test collection.")
    api_key = "dummy-key"

provider = llm_config.get('provider')
# Inicializace LLM na základě konfigurace
# V budoucnu zde může být logika pro výběr providera (google, openai, atd.)
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
