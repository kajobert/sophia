import os
import yaml
from dotenv import load_dotenv
from openai import AsyncOpenAI
from core.llm_adapters import OpenRouterAdapter

class LLMManager:
    """
    Spravuje a poskytuje instance LLM adaptérů.
    V nové architektuře je navržen pro práci výhradně s OpenRouter.
    """
    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self._client = None
        self._load_config()

        # Načtení konfigurace modelů, aliasů a fallback strategie
        llm_config = self.config.get("llm_models", {})
        self.models_config = llm_config.get("models", {})
        self.aliases = llm_config.get("aliases", {})
        self.default_model_name = llm_config.get("default", None)
        self.fallback_models = llm_config.get("fallback_models", [])

        self._initialize_client()

    def _load_config(self):
        """Načte konfiguraci z config/config.yaml."""
        config_path = os.path.join(self.project_root, "config/config.yaml")
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {}
            raise RuntimeError("Konfigurační soubor 'config.yaml' nebyl nalezen.")

    def _initialize_client(self):
        """Inicializuje jednoho sdíleného klienta pro OpenRouter."""
        dotenv_path = os.path.join(self.project_root, '.env')
        load_dotenv(dotenv_path=dotenv_path)

        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError("API klíč 'OPENROUTER_API_KEY' nebyl nalezen v .env souboru.")

        self._client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )

    def get_llm(self, name: str = None):
        """
        Vrátí instanci OpenRouterAdapter pro zadaný model.
        Nejprve zkontroluje, zda je 'name' alias, a pokud ano, přeloží ho.
        Pokud jméno není specifikováno, vrátí výchozí model.
        """
        model_alias = name or self.default_model_name
        if not model_alias:
            raise ValueError("Není definován žádný výchozí model ani alias.")

        # Přeložení aliasu na skutečný název modelu
        actual_model_name = self.aliases.get(model_alias, model_alias)

        if actual_model_name not in self.models_config:
            raise ValueError(f"Model s názvem '{actual_model_name}' (přeloženo z aliasu '{model_alias}') nebyl nalezen v 'config.yaml' v sekci 'models'.")

        # Získání konfigurace pro daný model. Pokud je None (prázdná hodnota v YAML), použije se prázdný slovník.
        model_specific_config = self.models_config.get(actual_model_name) or {}

        # Předáme sdíleného klienta, specifickou konfiguraci modelu a fallback strategii do adaptéru
        return OpenRouterAdapter(
            model_name=actual_model_name,
            client=self._client,
            fallback_models=self.fallback_models,
            **model_specific_config  # Bezpečné rozbalení, protože je to vždy slovník
        )