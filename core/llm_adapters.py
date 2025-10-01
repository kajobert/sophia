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
            tuple[str, dict | None]: Vygenerovaný text a informace o použití (včetně ID generace).
        """
        pass

    def count_tokens(self, text: str) -> int:
        """
        Odhadne počet tokenů v textu. Pro OpenRouter se spoléháme na data z odpovědi,
        takže tato metoda nemusí být přesná a je spíše orientační.
        """
        # Jednoduchý odhad: 1 token ~ 4 znaky
        return len(text) // 4


from core.rich_printer import RichPrinter

class OpenRouterAdapter(BaseLLMAdapter):
    """
    Univerzální adaptér pro všechny modely dostupné přes OpenRouter.
    Implementuje fallback strategii a podporuje streamování.
    """
    def __init__(self, model_name: str, client: AsyncOpenAI, fallback_models: list = None, **kwargs):
        super().__init__(model_name=model_name)
        self._client = client
        self.system_prompt = kwargs.get("system_prompt", "")
        # Seznam modelů k pokusu, primární model je vždy první
        self.models_to_try = [self.model_name] + (fallback_models or [])

    async def generate_content_async(
        self,
        prompt: str,
        response_format: dict | None = None,
        stream_callback=None
    ) -> tuple[str, dict | None]:
        """
        Odešle požadavek na OpenRouter API s fallback logikou a podporou streamování.

        Args:
            prompt (str): Vstupní prompt pro model.
            response_format (dict, optional): Schéma pro vynucení formátu odpovědi (např. JSON).
            stream_callback (callable, optional): Funkce, která se volá s každým novým kouskem dat při streamování.

        Returns:
            tuple[str, dict | None]: Kompletní text odpovědi a data o použití.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        extra_body = {}
        if response_format:
            extra_body["response_format"] = response_format

        last_error = None
        for model_name in self.models_to_try:
            try:
                if model_name != self.model_name:
                    RichPrinter.warning(f"Primární model '{self.model_name}' selhal. Zkouším záložní model: [bold cyan]{model_name}[/bold cyan]")

                if stream_callback:
                    # --- Logika pro streamování ---
                    full_response_content = ""
                    usage_data = None
                    stream = await self._client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        extra_body=extra_body if extra_body else None,
                        stream=True,
                    )
                    async for chunk in stream:
                        chunk_content = chunk.choices[0].delta.content or ""
                        full_response_content += chunk_content
                        await stream_callback(chunk_content)

                        # Uložíme si data o použití, která přijdou v posledním chunku
                        if chunk.usage:
                             usage_data = {
                                "id": chunk.id,
                                "model": chunk.model,
                                "usage": chunk.usage.model_dump()
                            }
                    return full_response_content, usage_data
                else:
                    # --- Logika bez streamování ---
                    response = await self._client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        extra_body=extra_body if extra_body else None,
                    )
                    content = response.choices[0].message.content
                    usage_data = {
                        "id": response.id,
                        "model": response.model,
                        "usage": response.usage.model_dump() if response.usage else None
                    }
                    return content, usage_data

            except Exception as e:
                last_error = e
                RichPrinter.error(f"Chyba při volání modelu '{model_name}': {e}")
                continue # Zkusíme další model v seznamu

        # Pokud všechny modely selžou
        RichPrinter.error("Všechny modely (včetně záložních) selhaly.")
        return f"Error calling OpenRouter API after all fallbacks: {str(last_error)}", None