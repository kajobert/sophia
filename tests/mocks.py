import json
from typing import Callable, Any, Dict, List, Tuple

class MockLLM:
    """
    Mock LLM pro testování, který umožňuje konfigurovat odpovědi
    na základě obsahu promptu.
    """
    def __init__(self, default_response: dict | None = None):
        self.response_map: Dict[str, Any] = {}
        self.call_history: List[str] = []
        if default_response is None:
            self.default_response = {"explanation": "Default mock response", "tool_call": None}
        else:
            self.default_response = default_response

    def configure_responses(self, response_map: Dict[str, Any]):
        """
        Konfiguruje mapování z klíčových slov v promptu na specifické odpovědi.

        Args:
            response_map: Slovník, kde klíč je text (nebo regex), který se hledá
                          v promptu, a hodnota je odpověď, která se má vrátit.
        """
        self.response_map = response_map

    async def generate_content_async(
        self,
        prompt: str,
        stream_callback: Callable[[str], Any] | None = None,
        response_format: Dict[str, str] | None = None
    ) -> Tuple[str, Dict[str, Any] | None]:
        """
        Simuluje generování odpovědi. Prohledá `response_map` a vrátí
        nakonfigurovanou odpověď, pokud najde shodu. Jinak vrátí defaultní odpověď.
        """
        self.call_history.append(prompt)

        for key, response in self.response_map.items():
            if key in prompt:
                response_str = json.dumps(response)
                if stream_callback:
                    await stream_callback(response_str)
                return response_str, {"usage": {"total_tokens": 100}} # Mock usage data

        default_response_str = json.dumps(self.default_response)
        if stream_callback:
            await stream_callback(default_response_str)

        return default_response_str, {"usage": {"total_tokens": 10}}

    @property
    def model_name(self):
        return "mock_llm"

class MockLLMManager:
    """Mock LLMManager, který vrací instance MockLLM."""
    def __init__(self, *args, **kwargs):
        """Přijímá jakékoliv argumenty, aby odpovídal signatuře skutečné třídy."""
        self.config = {"llm": {"default_model": "mock_default"}}
        self.mock_llms: Dict[str, MockLLM] = {
            "default": MockLLM(),
            "powerful": MockLLM(),
            "fast": MockLLM(),
        }

    def get_llm(self, model_alias: str = "default") -> MockLLM:
        """Vrátí specifickou instanci MockLLM podle aliasu."""
        if model_alias in self.mock_llms:
            return self.mock_llms[model_alias]
        return self.mock_llms["default"]

    def configure_llm_response(self, alias: str, response_map: Dict[str, Any]):
        """Pohodlná metoda pro konfiguraci konkrétního mock LLM."""
        if alias in self.mock_llms:
            self.mock_llms[alias].configure_responses(response_map)
        else:
            raise KeyError(f"Mock LLM s aliasem '{alias}' neexistuje.")