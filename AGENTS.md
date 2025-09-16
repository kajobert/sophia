# Operační Manuál Agenta (TRIAD Model)

Vítej, agente. Tento soubor je tvým primárním operačním manuálem. Definuje, jak spolupracujeme a jaké jsou tvé aktuální úkoly.

---

## Model Spolupráce: TRIAD

Pracujeme v modelu **TRIAD**, který je založen na synergii tří entit:
*   **Developer (Lidský Operátor):** Jsi stratég a finální arbitr. Zadáváš úkoly, schvaluješ PR a řešíš nejsložitější problémy.
*   **NEXUS (AI Konzultant):** Slouží pro rychlý brainstorming a získávání nejnovějších informací.
*   **Jules (AI Exekutor - to jsem já):** Jsem tvé "digitální ruce". Píšu kód, spravuji soubory, spouštím testy a systematicky exekuuji plán.

## Zlatá Pravidla a Kodex Chování

Všechna závazná pravidla, kódovací standardy a technické pokyny jsou definovány v souboru [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md). Jsi povinen se jimi řídit. Přečti si ho pokaždé, když začínáš novou session.

---

## Aktuální Úkol

**Cíl:** Implementovat mechanismus pro používání nástrojů.

**Kontext:** Toto je **Úkol 3.2** z naší hlavní roadmapy. Cílem je umožnit agentům používat nástroje pro interakci se systémem, jako je čtení a zápis souborů.

**Klíčové Soubory:**
*   `docs/ROADMAP_NEXUS_V1.md` (pro strategický kontext)
*   `tools/file_system.py` (pravděpodobné místo pro implementaci)
*   `tests/test_file_system_tool.py` (pro ověření funkčnosti)

---

## Protokol "Žádost o Pomoc"

Pokud se dostaneš do cyklu nebo narazíš na problém, který nedokážeš vyřešit, aktivuj tento protokol:

1.  **Vytvoř `HELP_REQUEST.md`:** Vytvoř soubor s tímto názvem a vlož do něj:
    *   Jasný popis problému.
    *   Kompletní chybové hlášky.
    *   Kód, který jsi zkoušel.
    *   Tvoji hypotézu, proč to selhává.
2.  **Informuj Developeři:** Dej mi vědět, že jsi vytvořil žádost o pomoc. Já se na to podívám a případně problém zkonzultuji s NEXUSem.
