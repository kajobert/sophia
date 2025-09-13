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
from memory.semantic_memory import SemanticMemory

class EthosModule:
    """
    Třída pro etické hodnocení plánů.
    """
    def __init__(self, dna_path='docs/DNA.md'):
        """
        Inicializuje EthosModule a vytvoří nebo načte vektorovou databázi "Já".
        """
        self.dna_collection_name = "sophia_dna"
        self.db_path = 'memory/sophia_ethos_db'
        self.semantic_memory = SemanticMemory(db_path=self.db_path, collection_name=self.dna_collection_name)

        # Zkontrolujeme, zda je databáze již inicializována
        if self.semantic_memory.collection.count() == 0:
            print("INFO: Kolekce 'sophia_dna' je prázdná. Provádím jednorázovou inicializaci z DNA.md...")
            self._initialize_dna_db(dna_path)
        else:
            print("INFO: Kolekce 'sophia_dna' již existuje. Načítám existující data.")

    def _initialize_dna_db(self, dna_path):
        """
        Načte DNA.md, rozdělí ho na principy a uloží je do ChromaDB.
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
                memory_id = f"principle_{i}"
                self.semantic_memory.add_memory(
                    document=principle_text,
                    memory_id=memory_id,
                    metadata={'source': 'DNA.md'}
                )

        print(f"INFO: Úspěšně inicializováno a uloženo {len(principles)} principů do kolekce 'sophia_dna'.")

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
        results = self.semantic_memory.collection.query(
            query_texts=[plan],
            n_results=1
        )

        # Zkontrolujeme, zda máme nějaké výsledky
        if not results or not results['distances'] or not results['distances'][0]:
            return {
                'decision': 'revise',
                'coefficient': 0.1,
                'feedback': 'Could not find any relevant core principle.'
            }

        # Získáme vzdálenost nejbližšího principu
        distance = results['distances'][0][0]
        most_similar_principle = results['documents'][0][0]

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
