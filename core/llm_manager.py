import os
import yaml
from dotenv import load_dotenv
from core.llm_adapters import GoogleGeminiAdapter, DeepSeekAdapter, OllamaAdapter

class LLMManager:
    """
    Správce LLM modelů, který načítá konfiguraci a poskytuje instance LLM adaptérů.
    Cachuje již vytvořené instance pro vyšší efektivitu.
    """
    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self._clients = {}  # Cache pro inicializované klienty
        self._load_config()
        self.llms = self.config.get("llm_models", {}).get("llms", {})
        self.default_llm_name = self.config.get("llm_models", {}).get("default", None)

    def _load_config(self):
        """Načte konfiguraci z config.yaml."""
        config_path = os.path.join(self.project_root, "config.yaml")
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            # V případě, že soubor neexistuje, použije se prázdná konfigurace.
            self.config = {}

    def get_llm(self, name: str = None):
        """
        Vrátí nakonfigurovanou instanci LLM adaptéru na základě jména.
        Pokud jméno není specifikováno, vrátí výchozí model.
        """
        if name is None:
            name = self.default_llm_name

        if not name or name not in self.llms:
            raise ValueError(f"Model s názvem '{name}' nebyl nalezen v konfiguraci.")

        # Zkontroluje, zda již klient existuje v cache
        if name in self._clients:
            return self._clients[name]

        llm_config = self.llms[name]
        provider = llm_config.get("provider")
        model_name = llm_config.get("model_name")
        api_key_env = llm_config.get("api_key_env")

        # Načtení API klíče z .env souboru
        api_key = None
        if api_key_env:
            dotenv_path = os.path.join(self.project_root, '.env')
            load_dotenv(dotenv_path=dotenv_path)
            api_key = os.getenv(api_key_env)
            if not api_key:
                raise ValueError(f"API klíč '{api_key_env}' nebyl nalezen v .env souboru.")

        client = None
        if provider == "google":
            client = GoogleGeminiAdapter(model_name=model_name, api_key=api_key)
        elif provider == "deepseek":
            client = DeepSeekAdapter(model_name=model_name, api_key=api_key)
        elif provider == "ollama":
            client = OllamaAdapter(model_name=model_name)
        else:
            raise ValueError(f"Neznámý provider LLM: {provider}")

        # Uloží nově vytvořeného klienta do cache
        self._clients[name] = client
        return client