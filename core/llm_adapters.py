import os
from openai import OpenAI, AsyncOpenAI
from abc import ABC, abstractmethod

class BaseLLMAdapter(ABC):
    """
    Abstraktní základní třída pro všechny LLM adaptéry.
    Definuje jednotné rozhraní pro interakci s jazykovými modely.
    """
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name

    @abstractmethod
    async def generate_content_async(self, prompt: str, response_format: dict | None = None) -> tuple[str, dict | None]:
        """
        Asynchronně generuje obsah.

        Vrací:
            tuple[str, dict | None]: Vygenerovaný text a informace o použití (tokeny, náklady).
        """
        pass

    def count_tokens(self, text: str) -> int:
        """
        Odhadne počet tokenů v textu. Pro OpenRouter se spoléháme na data z odpovědi,
        takže tato metoda nemusí být přesná a je spíše orientační.
        """
        # Jednoduchý odhad: 1 token ~ 4 znaky
        return len(text) // 4


class OpenRouterAdapter(BaseLLMAdapter):
    """
    Univerzální adaptér pro všechny modely dostupné přes OpenRouter.
    Používá oficiální `openai` knihovnu pro komunikaci.
    """
    def __init__(self, model_name: str, client: AsyncOpenAI, **kwargs):
        super().__init__(model_name=model_name)
        self._client = client
        self.system_prompt = kwargs.get("system_prompt", "")

    async def generate_content_async(self, prompt: str, response_format: dict | None = None) -> tuple[str, dict | None]:
        """
        Odešle požadavek na OpenRouter API a vrátí odpověď a data o použití.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        extra_body = {}
        if response_format:
            extra_body["response_format"] = response_format

        try:
            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                extra_body=extra_body if extra_body else None,
            )

            content = response.choices[0].message.content
            usage_data = response.usage.model_dump() if response.usage else None

            return content, usage_data

        except Exception as e:
            # V případě chyby vrátíme chybovou zprávu a žádná data o použití
            return f"Error calling OpenRouter API: {str(e)}", None