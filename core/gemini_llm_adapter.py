"""
GeminiLLMAdapter: Dočasný adapter pro Google Gemini API s rozhraním kompatibilním s LangChain LLM.

- Používá google-generativeai SDK
- Rozhraní: __call__(prompt), get_token_usage(), async podpora (volitelně)
- Připraveno na budoucí přepnutí na LangChain wrapper
"""
import os
import google.generativeai as genai

class GeminiLLMAdapter:
    def __init__(self, model: str, api_key: str, temperature: float = 0.7, max_tokens: int = 2048, **kwargs):
        self.model_name = model  # string název modelu
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra = kwargs
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self._last_token_usage = 0

    def __call__(self, prompt: str, **kwargs) -> str:
        # Syntaktická kompatibilita s LangChain LLM
        generation_config = {
            "temperature": kwargs.get("temperature", self.temperature),
            "max_output_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        response = self._generate(prompt, generation_config)
        # usage_metadata může být None nebo dict s klíčem 'total_tokens'
        usage = getattr(response, "usage_metadata", None)
        if usage and isinstance(usage, dict):
            self._last_token_usage = usage.get("total_tokens", 0)
        else:
            self._last_token_usage = 0
        return response.text if hasattr(response, "text") else str(response)

    def _generate(self, prompt, generation_config):
        return self.model.generate_content(prompt, generation_config=generation_config)

    def get_token_usage(self):
        """Vrací počet tokenů použitých při posledním volání."""
        return self._last_token_usage

    # Volitelně: async podpora, streaming, bezpečnostní parametry, atd.
