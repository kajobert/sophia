import os
from typing import Optional

from core.conversational_manager import ConversationalManager
from core.rich_printer import RichPrinter

class MissionManager:
    """
    Řídí dlouhodobou misi, udržuje kontext a deleguje jednotlivé kroky
    na ConversationalManager.
    """
    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.conversational_manager = ConversationalManager(project_root=self.project_root)
        self.mission_prompt: Optional[str] = None
        self.mission_history: list[tuple[str, str]] = []
        self.is_mission_active = False

    async def initialize(self):
        """Inicializuje podřízeného konverzačního manažera."""
        RichPrinter.info("MissionManager se inicializuje...")
        await self.conversational_manager.initialize()
        RichPrinter.info("MissionManager je připraven.")

    async def shutdown(self):
        """Bezpečně ukončí podřízeného konverzačního manažera."""
        await self.conversational_manager.shutdown()
        RichPrinter.info("MissionManager byl bezpečně ukončen.")

    def get_mission_status(self) -> dict:
        """Vrací aktuální stav mise."""
        return {
            "is_active": self.is_mission_active,
            "mission_prompt": self.mission_prompt,
            "history_length": len(self.mission_history),
        }

    async def start_mission(self, prompt: str):
        """
        Zahájí novou misi.
        """
        RichPrinter.info(f"Nová mise zadána: '{prompt}'")
        self.mission_prompt = prompt
        self.is_mission_active = True
        self.mission_history = []

        # Pro první krok jednoduše předáme prompt konverzačnímu manažerovi.
        # V budoucnu můžeme přidat logiku pro "shrnutí" mise.
        initial_task = (
            f"Toto je první krok v rámci větší mise. Celkový cíl mise je: '{prompt}'.\n"
            f"Začni tím, že analyzuješ tento cíl a navrhneš první konkrétní krok."
        )
        await self.conversational_manager.handle_user_input(initial_task)
        self.mission_history.append(("user", prompt))


    async def continue_mission(self, user_input: str):
        """
        Pokračuje v plnění aktuální mise s dalším vstupem od uživatele.
        """
        if not self.is_mission_active:
            RichPrinter.warning("Nelze pokračovat, žádná mise není aktivní. Spouštím jako novou misi.")
            await self.start_mission(user_input)
            return

        RichPrinter.info(f"Pokračuji v misi. Vstup od uživatele: '{user_input}'")

        # Zde je klíčová logika: musíme zkombinovat původní cíl mise,
        # historii a nový vstup, aby ConversationalManager měl plný kontext.
        contextual_prompt = (
            f"Pokračujeme v plnění mise. Původní cíl byl: '{self.mission_prompt}'.\n"
            f"Dosavadní historie interakcí: {self.mission_history}\n\n"
            f"Aktuální požadavek od uživatele je: '{user_input}'.\n\n"
            f"Zpracuj tento požadavek v kontextu celé mise."
        )

        await self.conversational_manager.handle_user_input(contextual_prompt)
        self.mission_history.append(("user", user_input))