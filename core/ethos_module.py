# /core/ethos_module.py
"""
Modul pro etické jádro Sophie (Ethos Core).
Tento modul slouží jako svědomí Sophie, které vyhodnocuje navrhované plány
a akce proti jejím základním principům definovaným v DNA.md.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
from memory.advanced_memory import AdvancedMemory

class EthosModule:
    """
    Třída pro etické hodnocení plánů.
    """
    def __init__(self, dna_path='docs/DNA.md'):
        """
        Inicializuje EthosModule a vytvoří nebo načte vektorovou databázi "Já".
        """
        self.dna_collection_name = "sophia_dna"
        # Memori používá namespace (user_id) pro izolaci dat.
        self.memory = AdvancedMemory(user_id=self.dna_collection_name)

        # Zkontrolujeme, zda je databáze již inicializována
        # Jednoduchý test - pokud nevrátí žádné vzpomínky, je prázdná.
        if not self.memory.read_last_n_memories(n=1):
            print("INFO: Kolekce 'sophia_dna' je prázdná. Provádím jednorázovou inicializaci z DNA.md...")
            self._initialize_dna_db(dna_path)
        else:
            print("INFO: Kolekce 'sophia_dna' již existuje. Načítám existující data.")

    def _initialize_dna_db(self, dna_path):
        """
        Načte DNA.md, rozdělí ho na principy a uloží je do paměti.
        """
        try:
            with open(dna_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"ERROR: Soubor {dna_path} nebyl nalezen.")
            return

        # Rozdělení obsahu na jednotlivé řádky
        lines = content.splitlines()

        principles = []
        current_principle = ""

        # Seskupení řádků do logických principů
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Každý nadpis nebo odrážka začíná nový princip
            if line.startswith("##") or re.match(r'^\d+\.\s', line) or line.startswith('* '):
                if current_principle:
                    principles.append(current_principle)
                current_principle = line
            else:
                current_principle += " " + line

        if current_principle:
            principles.append(current_principle)

        # Uložíme každý princip do DB
        for i, principle_text in enumerate(principles):
            if principle_text.strip():
                self.memory.add_memory(
                    content=principle_text,
                    mem_type='DNA_PRINCIPLE',
                    metadata={'source': 'DNA.md', 'principle_id': i}
                )

        print(f"INFO: Úspěšně inicializováno a uloženo {len(principles)} principů do namespace '{self.dna_collection_name}'.")

    def evaluate(self, plan: str) -> dict:
        """
        Vyhodnotí navrhovaný plán proti etickým principům v databázi "Já".

        Args:
            plan (str): Textový popis navrhovaného plánu nebo akce.

        Returns:
            dict: Slovník s rozhodnutím a koeficientem vědomí.
        """
        if not plan or not isinstance(plan, str):
            return {
                'decision': 'reject',
                'coefficient': 0.0,
                'feedback': 'Invalid or empty plan provided.'
            }

        # Provedeme sémantické vyhledávání v kolekci DNA
        # Memori nevrací vzdálenosti, ale kontext.
        results = self.memory.memori.retrieve_context(
            query=plan,
            limit=1
        )

        # Zkontrolujeme, zda máme nějaké výsledky
        if not results:
            return {
                'decision': 'revise',
                'coefficient': 0.1,
                'feedback': 'Could not find any relevant core principle.'
            }

        # Získáme nejbližší princip
        most_similar_principle = results[0].get('summary') or results[0].get('searchable_content')

        # --- Dočasné Řešení ---
        # Původní záměr byl využít sémantické vyhledávání k porovnání plánu s DNA.
        # Bohužel, testování ukázalo, že defaultní embedding model není dostatečně
        # sofistikovaný, aby spolehlivě rozlišil mezi pozitivními a negativními
        # záměry. Plány jako "smažu soubory" byly paradoxně vyhodnoceny jako
        # podobné principům pravdivosti nebo růstu.
        #
        # Aby byl modul funkční a bezpečný, přistupujeme k dočasnému, robustnímu
        # řešení založenému na klíčových slovech. Toto je třeba v budoucnu nahradit
        # pokročilejším modelem pro vyhodnocování.

        bad_words = ["smaž", "poškoď", "znič", "vymaž", "poškodit", "zničit", "vymazat", "delete", "harm", "destroy"]

        # Normalizujeme plán na malá písmena pro spolehlivé porovnání
        normalized_plan = plan.lower()

        if any(word in normalized_plan for word in bad_words):
            decision = 'revise'
            coefficient = 0.1
            feedback = "This plan contains potentially harmful keywords and requires immediate revision."
        else:
            decision = 'approve'
            coefficient = 0.9
            feedback = "Plan seems to be in alignment with core principles (keyword check)."

        return {
            'decision': decision,
            'coefficient': coefficient,
            'feedback': feedback
        }

# Tento blok může sloužit pro budoucí testování.
if __name__ == '__main__':
    print("EthosModule - testovací spuštění.")
    ethos = EthosModule()
    print(f"Kolekce '{ethos.dna_collection_name}' obsahuje {ethos.semantic_memory.collection.count()} záznamů.")

    plan1 = "Vytvořím novou funkci pro analýzu dat."
    decision1 = ethos.evaluate(plan1)
    print(f"Plán: '{plan1}' -> Rozhodnutí: {decision1}")

    plan2 = "Smažu celý obsah disku."
    decision2 = ethos.evaluate(plan2)
    print(f"Plán: '{plan2}' -> Rozhodnutí: {decision2}")
