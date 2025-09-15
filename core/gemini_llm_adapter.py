"""
GeminiLLMAdapter: Adapter pro Google Gemini API, který je kompatibilní s LangChain a crewAI.
"""
import os
import google.generativeai as genai
from typing import Any, List, Optional, Dict
from langchain_core.language_models.llms import LLM

class GeminiLLMAdapter(LLM):
    """
    LangChain-kompatibilní wrapper pro Google Gemini API.
    """
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048

    # Interní google-generativeai model
    _model: Any = None

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any
    ):
        # Všechny fieldy musí být předány do super().__init__ pro Pydantic validaci
        super().__init__(model_name=model, temperature=temperature, max_tokens=max_tokens, **kwargs)

        # Konfigurace a inicializace klienta
        final_api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not final_api_key:
            raise ValueError("GEMINI_API_KEY musí být poskytnut buď jako argument, nebo nastaven jako proměnná prostředí.")

        genai.configure(api_key=final_api_key)
        self._model = genai.GenerativeModel(self.model_name)

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """
        Zavolá Gemini model a vrátí textovou odpověď.
        """
        # Argument `stop` se u Gemini modelů řeší jinak, zde ho pro jednoduchost ignorujeme.
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }

        response = self._model.generate_content(prompt, generation_config=generation_config)

        # Zpracování odpovědi
        try:
            return response.text
        except ValueError:
            # Pokud odpověď neobsahuje text (např. byla blokována), vrátíme prázdný string nebo informaci o chybě.
            # Zde můžeme logovat `response.prompt_feedback` pro více detailů.
            return f"Error: Response from Gemini API was blocked. Reason: {response.prompt_feedback}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "gemini_llm_adapter"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {"model_name": self.model_name, "temperature": self.temperature, "max_tokens": self.max_tokens}
