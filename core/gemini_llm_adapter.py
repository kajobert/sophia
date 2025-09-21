"""
GeminiLLMAdapter: Adapter pro Google Gemini API, který je kompatibilní s LangChain a crewAI.
"""

import os
import google.generativeai as genai
from typing import Any, List, Optional, Dict
from langchain_core.language_models.llms import LLM


class GeminiLLMAdapter(LLM):
    """
    LangChain-kompatibilní wrapper pro Google Gemini API s podporou sledování tokenů.
    """

    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048

    _model: Any = None
    _last_token_usage: int = 0

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ):
        # Force litellm to use the 'gemini' provider instead of defaulting to 'vertex_ai'
        # by prepending 'gemini/' to the model name.
        prefixed_model = f"gemini/{model}" if not model.startswith("gemini/") else model

        super().__init__(
            model_name=prefixed_model, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

        final_api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not final_api_key:
            raise ValueError(
                "GEMINI_API_KEY musí být poskytnut buď jako argument, nebo nastaven jako proměnná prostředí."
            )

        genai.configure(api_key=final_api_key)
        # Use the original model name for the genai client, as it doesn't understand the prefix.
        # The prefixed `self.model_name` is for crewai/litellm.
        self._model = genai.GenerativeModel(model)
        self._last_token_usage = 0

    def _call(
        self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any
    ) -> str:
        """
        Zavolá Gemini model, vrátí textovou odpověď a zaznamená počet použitých tokenů.
        """
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }

        response = self._model.generate_content(
            prompt, generation_config=generation_config
        )

        # Zaznamenání počtu tokenů
        usage = getattr(response, "usage_metadata", None)
        if usage and isinstance(usage, dict):
            self._last_token_usage = usage.get("total_tokens", 0)
        else:
            self._last_token_usage = 0

        # Zpracování odpovědi
        try:
            return response.text
        except ValueError:
            # Pokud odpověď neobsahuje text (např. byla blokována), vrátíme prázdný string nebo informaci o chybě.
            return f"Error: Response from Gemini API was blocked. Reason: {response.prompt_feedback}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    def get_token_usage(self) -> int:
        """Vrací počet tokenů použitých při posledním volání."""
        return self._last_token_usage

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "gemini_llm_adapter"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
