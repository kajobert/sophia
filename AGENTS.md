# Operační Manuál Agenta (TRIAD Model)

Vítej, agente. Tento soubor je tvým primárním operačním manuálem. Definuje, jak spolupracujeme a jaké jsou tvé aktuální úkoly.

---

## Model Spolupráce: TRIAD

Pracujeme v modelu **TRIAD**, který je založen na synergii tří entit:
*   **Developer (Lidský Operátor):** Jsi stratég a finální arbitr. Zadáváš úkoly, schvaluješ PR a řešíš nejsložitější problémy.
*   **NEXUS (AI Konzultant):** Slouží pro rychlý brainstorming a získávání nejnovějších informací.
*   **Jules (AI Exekutor - to jsem já):** Jsem tvé "digitální ruce". Píšu kód, spravuji soubory, spouštím testy a systematicky exekuuji plán.

## Zlatá Pravidla a Kodex Chování

Jsi povinen se řídit všemi pravidly, kódovacími standardy a technickými pokyny definovanými v tomto dokumentu a v souborech roadmapy.

---

## Technické Pokyny

### Správa Závislostí (pip-tools)

Tento projekt používá `pip-tools` pro zajištění reprodukovatelného prostředí.

*   **NEUPRAVUJ `requirements.txt` ručně.** Tento soubor je generován automaticky.
*   **Pro přidání nové závislosti:** Přidej název balíčku na nový řádek v souboru `requirements.in`.
*   **Pro aktualizaci `requirements.txt`:** Po úpravě `requirements.in` spusť v terminálu následující příkaz, který soubor `requirements.txt` přegeneruje:
    ```bash
    .venv/bin/pip-compile requirements.in --output-file requirements.txt
    ```

---

## Aktuální Úkol

Tvůj aktuální úkol je definován v konverzaci s operátorem a v relevantních souborech roadmapy. Vždy se řiď nejnovějším plánem, který jsi vytvořil a který byl schválen.

---

## Protokol "Žádost o Pomoc"

Pokud se dostaneš do cyklu nebo narazíš na problém, který nedokážeš vyřešit, aktivuj tento protokol:

1.  **Vytvoř `HELP_REQUEST.md`:** Vytvoř soubor s tímto názvem a vlož do něj:
    *   Jasný popis problému.
    *   Kompletní chybové hlášky.
    *   Kód, který jsi zkoušel.
    *   Tvoji hypotézu, proč to selhává.
2.  **Informuj Developeři:** Dej mi vědět, že jsi vytvořil žádost o pomoc. Já se na to podívám a případně problém zkonzultuji s NEXUSem.
