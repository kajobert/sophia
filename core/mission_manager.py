import os
import yaml
from typing import Optional

from core.conversational_manager import ConversationalManager
from core.rich_printer import RichPrinter
from tools.git_tools import get_git_branch_name

class MissionManager:
    """
    Řídí dlouhodobou misi, udržuje kontext a deleguje jednotlivé kroky
    na ConversationalManager.
    """
    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.conversational_manager = ConversationalManager(project_root=self.project_root, mission_manager=self)
        self.mission_prompt: Optional[str] = None
        self.mission_history: list[tuple[str, str]] = []
        self.is_mission_active = False
        self.completed_missions_count = 0
        self.default_jules_source = None
        self._load_config()

    def _load_config(self):
        """Načte konfiguraci a nastaví výchozí zdroj pro Jules."""
        try:
            config_path = os.path.join(self.project_root, "config/config.yaml")
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                self.default_jules_source = config.get("jules_api", {}).get("default_source")
        except (FileNotFoundError, yaml.YAMLError):
            self.default_jules_source = None
            RichPrinter.warning("Nepodařilo se načíst výchozí zdroj pro Jules z config.yaml.")

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
        Rozlišuje mezi přímou odpovědí na schvalovací otázku a běžným pokračováním mise.
        """
        if not self.is_mission_active:
            RichPrinter.warning("Nelze pokračovat, žádná mise není aktivní. Spouštím jako novou misi.")
            await self.start_mission(user_input)
            return

        # Zkontrolujeme, zda ConversationalManager čeká na schválení.
        if self.conversational_manager.state == "AWAITING_DELEGATION_APPROVAL":
            # Pokud ano, předáme mu pouze čistý vstup od uživatele ("ano"/"ne").
            RichPrinter.info("Zpracovávám přímou odpověď na žádost o schválení.")
            await self.conversational_manager.handle_user_input(user_input)
        else:
            # V ostatních případech sestavíme plný kontext pro pokračování mise.
            RichPrinter.info(f"Pokračuji v misi. Vstup od uživatele: '{user_input}'")

            history_str = "\n".join([f"- {role.capitalize()}: {text}" for role, text in self.mission_history])
            current_branch = get_git_branch_name() or "neznámá větev"

            delegation_context = (
                f"**KONTEXT PRO DELEGACI:**\n"
                f"- Cílový repozitář (source): `{self.default_jules_source or 'není nastaven'}`\n"
                f"- Aktuální větev (branch): `{current_branch}`\n\n"
            ) if self.default_jules_source else ""

            contextual_prompt = (
                f"{delegation_context}"
                f"**CELKOVÝ CÍL MISE:**\n{self.mission_prompt}\n\n"
                f"**HISTORIE MISE:**\n{history_str}\n\n"
                f"**OKAMŽITÝ CÍL:**\n{user_input}\n\n"
                f"---\n"
                f"**TVŮJ ÚKOL:**\nNa základě **OKAMŽITÉHO CÍLE** a s ohledem na **CELKOVÝ CÍL MISE** a poskytnutý **KONTEXT PRO DELEGACI** navrhni a proveď další krok."
            )

            await self.conversational_manager.handle_user_input(contextual_prompt)

        # Přidáme vstup do historie mise bez ohledu na cestu.
        self.mission_history.append(("user", user_input))

    def get_completed_missions_count(self) -> int:
        """Vrací počet úspěšně dokončených misí."""
        return self.completed_missions_count