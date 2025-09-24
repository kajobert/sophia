import os
import google.generativeai as genai
from typing import Any, Dict, List

class GeminiLLMAdapter:
    def __init__(self, model: str = "gemini-pro", temperature: float = 0.7):
        self.model_name = model
        self.temperature = temperature
        self.client = self._configure_client()

    def _configure_client(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str, **kwargs) -> str:
        generation_config = genai.types.GenerationConfig(
            temperature=self.temperature, **kwargs
        )
        response = self.client.generate_content(prompt, generation_config=generation_config)
        return response.text

    def _generate(self, prompts: List[str], **kwargs) -> Dict[str, Any]:
        # This is a legacy method for compatibility, not actively used.
        results = []
        for prompt in prompts:
            results.append({"text": self.generate(prompt, **kwargs)})
        return {"generations": results}