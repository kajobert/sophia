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
        self.llms_config = self.config.get("llm_models", {}).get("models", {})
        self.default_model_name = self.config.get("llm_models", {}).get("default", None)
        self._initialize_client()

    def _load_config(self):
        """Načte konfiguraci z config.yaml."""
        config_path = os.path.join(self.project_root, "config.yaml")
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
        Pokud jméno není specifikováno, vrátí výchozí model.
        """
        model_name = name or self.default_model_name
        if not model_name or model_name not in self.llms_config:
            raise ValueError(f"Model s názvem '{model_name}' nebyl nalezen v 'config.yaml'.")

        model_config = self.llms_config[model_name]

        # Předáme sdíleného klienta a specifickou konfiguraci modelu do adaptéru
        return OpenRouterAdapter(
            model_name=model_name,
            client=self._client,
            **model_config  # Předá další parametry, např. system_prompt
        )