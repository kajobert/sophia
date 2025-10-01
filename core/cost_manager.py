import httpx
import os
from dotenv import load_dotenv

class CostManager:
    """
    Spravuje a sleduje náklady na volání LLM přes OpenRouter API.
    """
    def __init__(self, project_root: str = "."):
        self.total_cost = 0.0
        self.api_url = "https://openrouter.ai/api/v1/generation"

        dotenv_path = os.path.join(project_root, '.env')
        load_dotenv(dotenv_path=dotenv_path)
        self.api_key = os.getenv("OPENROUTER_API_KEY")

    async def get_generation_cost(self, generation_id: str) -> float:
        """
        Získá náklady na konkrétní generaci z OpenRouter API.
        Vrací cenu generace jako float, nebo 0.0 v případě chyby.
        """
        if not self.api_key:
            # Nemůžeme nic dělat bez klíče
            return 0.0

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        params = {"id": generation_id}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.api_url, headers=headers, params=params)
                response.raise_for_status()  # Vyvolá výjimku pro 4xx/5xx odpovědi

                data = response.json()
                cost = data.get("data", {}).get("total_cost", 0.0)
                return float(cost)
        except httpx.RequestError as e:
            # Problém se sítí, DNS, atd.
            print(f"CostManager: Chyba při dotazu na API: {e}")
            return 0.0
        except httpx.HTTPStatusError as e:
            # Chyba HTTP (např. 404, 500)
            print(f"CostManager: Chyba stavového kódu API: {e.response.status_code}")
            return 0.0
        except (ValueError, KeyError) as e:
            # Chyba při parsování JSON nebo chybějící klíč
            print(f"CostManager: Chyba při zpracování odpovědi API: {e}")
            return 0.0

    def add_cost(self, cost: float):
        """
        Přičte náklady k celkové útratě za sezení.
        """
        self.total_cost += cost

    def get_total_cost_str(self) -> str:
        """
        Vrátí celkové náklady naformátované jako string v USD.
        """
        # Formátování na 6 desetinných míst pro přesnost u malých částek
        return f"${self.total_cost:.6f}"