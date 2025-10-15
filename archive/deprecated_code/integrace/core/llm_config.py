import os
import yaml
from dotenv import load_dotenv
from core.gemini_llm_adapter import GeminiLLMAdapter

# from langchain_google_genai import ChatGoogleGenerativeAI  # fallback do budoucna

# Only load .env into the environment when not running in test mode.
if os.getenv("SOPHIA_TEST_MODE") != "1":
    # Načtení proměnných prostředí ze souboru .env
    load_dotenv()

# --- Globals ---
config = None
llm = None
llm_config = None
LLMConfig = dict  # Default to dict, can be a placeholder class in test mode

# V testovacím režimu LLM a konfiguraci neinicializujeme, testy si vše mockují samy.
if os.getenv("SOPHIA_TEST_MODE") == "1":
    print("Testovací režim aktivní, LLM a globální konfigurace se neincializují.")

    class DummyLLMConfig:
        """A dummy class for type hinting in test mode."""

        pass

    LLMConfig = DummyLLMConfig
else:
    # --- Robustní načtení globální konfigurace ---
    CONFIG_FILE = "config.yaml"
    config_paths_tried = []

    try:
        # Hledání konfiguračního souboru
        cwd_path = os.path.abspath(CONFIG_FILE)
        module_dir = os.path.dirname(os.path.abspath(__file__))
        root_path = os.path.abspath(os.path.join(module_dir, ".."))

        search_paths = [cwd_path, os.path.join(root_path, CONFIG_FILE)]
        config_paths_tried = search_paths

        found_path = None
        for path in search_paths:
            if os.path.exists(path):
                found_path = path
                break

        if found_path:
            with open(found_path, "r") as f:
                config = yaml.safe_load(f)
        else:
            raise FileNotFoundError(
                f"Config file '{CONFIG_FILE}' not found in search paths."
            )

        if not config:
            raise ValueError("Konfigurační soubor je prázdný.")

    except Exception as e:
        raise ValueError(
            f"Chyba při načítání konfiguračního souboru '{CONFIG_FILE}'. Hledané cesty: {config_paths_tried}. Chyba: {e}"
        )

    # --- Konfigurace primárního LLM ---
    llm_config = config.get("llm_models", {}).get("primary_llm")
    if not llm_config:
        raise ValueError(
            "V konfiguračním souboru chybí sekce 'llm_models.primary_llm'."
        )

    # --- Inicializace LLM ---
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "API klíč pro LLM (GEMINI_API_KEY) nebyl nalezen v .env souboru."
        )

    provider = llm_config.get("provider")
    if provider == "google":
        llm = GeminiLLMAdapter(
            model=llm_config.get("model_name", "gemini-1.5-flash"),
            api_key=api_key,
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 2048),
            verbose=llm_config.get("verbose", False),
        )
        print(
            f"LLM provider '{provider}' byl úspěšně inicializován s modelem '{llm_config.get('model_name')}'."
        )
    else:
        raise ValueError(f"Neznámý nebo nepodporovaný provider LLM: {provider}")
