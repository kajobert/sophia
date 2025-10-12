import os
import yaml
from dotenv import load_dotenv
from openai import AsyncOpenAI
from core.llm_adapters import OpenRouterAdapter
from core.gemini_adapter import GeminiAdapter

class LLMManager:
    """
    Spravuje a poskytuje instance LLM adaptérů.
    Podporuje OpenRouter i přímý Gemini API access.
    
    Priority:
    1. Pokud existuje GEMINI_API_KEY -> použij Gemini
    2. Pokud existuje OPENROUTER_API_KEY -> použij OpenRouter
    3. Jinak vyhoď chybu
    """
    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self._openrouter_client = None
        self._gemini_adapter = None
        self._load_config()

        # Načtení konfigurace modelů, aliasů a fallback strategie
        llm_config = self.config.get("llm_models", {})
        self.models_config = llm_config.get("models", {})
        self.aliases = llm_config.get("aliases", {})
        self.default_model_name = llm_config.get("default", None)
        self.fallback_models = llm_config.get("fallback_models", [])

        self._initialize_clients()

    def _load_config(self):
        """Načte konfiguraci z config/config.yaml."""
        config_path = os.path.join(self.project_root, "config/config.yaml")
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {}
            raise RuntimeError("Konfigurační soubor 'config.yaml' nebyl nalezen.")

    def _initialize_clients(self):
        """
        Inicializuje klienty podle dostupných API klíčů.
        
        Priority:
        1. GEMINI_API_KEY -> Gemini adapter (primární)
        2. OPENROUTER_API_KEY -> OpenRouter client (fallback)
        """
        dotenv_path = os.path.join(self.project_root, '.env')
        load_dotenv(dotenv_path=dotenv_path)

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Inicializace Gemini (priorita)
        if gemini_api_key:
            try:
                self._gemini_adapter = GeminiAdapter(api_key=gemini_api_key)
                print(f"✅ Gemini adapter initialized: {self._gemini_adapter.model_name}")
            except Exception as e:
                print(f"⚠️ Gemini initialization failed: {e}")
                self._gemini_adapter = None
        
        # Inicializace OpenRouter (fallback)
        if openrouter_api_key:
            try:
                self._openrouter_client = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=openrouter_api_key,
                )
                print("✅ OpenRouter client initialized")
            except Exception as e:
                print(f"⚠️ OpenRouter initialization failed: {e}")
                self._openrouter_client = None
        
        # Ověření, že alespoň jeden klient je dostupný
        if not self._gemini_adapter and not self._openrouter_client:
            raise ValueError(
                "Žádný LLM provider není dostupný. "
                "Nastavte GEMINI_API_KEY nebo OPENROUTER_API_KEY v .env souboru."
            )

    def get_llm(self, name: str = None):
        """
        Vrátí instanci adaptéru pro zadaný model.
        
        Logika výběru:
        1. Pokud model začíná "gemini/" nebo je to Gemini model -> použij Gemini
        2. Jinak použij OpenRouter
        
        Args:
            name: Název modelu nebo alias
        
        Returns:
            GeminiAdapter nebo OpenRouterAdapter
        """
        model_alias = name or self.default_model_name
        if not model_alias:
            raise ValueError("Není definován žádný výchozí model ani alias.")

        # Přeložení aliasu na skutečný název modelu
        actual_model_name = self.aliases.get(model_alias, model_alias)

        # Detekce Gemini modelu
        is_gemini_model = (
            actual_model_name.startswith("gemini/") or
            actual_model_name.startswith("gemini-") or
            "gemini" in actual_model_name.lower()
        )
        
        # Použití Gemini adaptéru
        if is_gemini_model and self._gemini_adapter:
            # Gemini má vlastní konfiguraci v konstruktoru
            return self._gemini_adapter
        
        # Použití OpenRouter
        if self._openrouter_client:
            if actual_model_name not in self.models_config:
                raise ValueError(
                    f"Model s názvem '{actual_model_name}' (přeloženo z aliasu '{model_alias}') "
                    f"nebyl nalezen v 'config.yaml' v sekci 'models'."
                )

            # Získání konfigurace pro daný model
            model_specific_config = self.models_config.get(actual_model_name) or {}

            return OpenRouterAdapter(
                model_name=actual_model_name,
                client=self._openrouter_client,
                fallback_models=self.fallback_models,
                **model_specific_config
            )
        
        # Žádný provider není dostupný
        raise RuntimeError(
            f"Nelze vytvořit adaptér pro model '{actual_model_name}'. "
            f"Gemini: {'✅' if self._gemini_adapter else '❌'}, "
            f"OpenRouter: {'✅' if self._openrouter_client else '❌'}"
        )