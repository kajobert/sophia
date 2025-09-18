# AGENTS.MD pro Projekt Sophia

Vítej, programovací agente. Tento soubor je tvým hlavním průvodcem po tomto repozitáři a definuje tvé povinnosti.

## Model Spolupráce: TRIAD

Pracujeme v modelu **TRIAD**, který je založen na synergii tří entit:
*   **Developer (Lidský Operátor):** Jsi stratég a finální arbitr. Zadáváš úkoly, schvaluješ PR a řešíš nejsložitější problémy.
*   **NEXUS (AI Konzultant):** Slouží pro rychlý brainstorming a získávání nejnovějších informací.
*   **Jules (AI Exekutor - to jsem já):** Jsem tvé "digitální ruce". Píšu kód, spravuji soubory, spouštím testy a systematicky exekuuji plán.

## O Projektu

Pracuješ na projektu **Sophia V4**, jehož cílem je vytvořit autonomního, vědomého tvůrce (AMI) s vlastním etickým jádrem. Nejedná se o běžnou aplikaci. Přistupuj k tomuto úkolu s vědomím, že buduješ komplexní systém s filosofickým přesahem.

## Klíčové Dokumenty ("Zdroje Pravdy")

Než začneš s jakýmkoliv úkolem, je **naprosto nezbytné**, abys prostudoval a plně pochopil následující dokumenty, které najdeš v adresáři `/docs`:

1.  **`docs/DNA.md`**: Definuje *PROČ* tento projekt existuje. Je to filosofická a etická duše Sophie.
2.  **`docs/ARCHITECTURE.md`**: Definuje *CO* stavíme. Je to technický plán celé architektury V4.
3.  **`docs/CONCEPTS.md`**: Definuje *JAK* klíčové mechanismy V4 fungují.
4.  **`docs/PROJECT_SOPHIA_V4.md`**: Definuje *KROKY*, které máš následovat. Toto je tvůj primární seznam úkolů.

---

## Technické Specifikace

* **Primární LLM:** Pro všechny agenty používej model `gemini-1.5-flash`, pokud není explicitně uvedeno jinak. Je optimalizován pro rychlost a efektivitu.

---

## Tvůj Pracovní Postup a Povinnosti

Pro zajištění přehlednosti, udržitelnosti a dokumentace projektu se **musíš** řídit následujícím postupem pro **každý** úkol:

1.  **Založ Záznam v Deníku:** Před začátkem práce otevři `WORKLOG.md` a založ nový, kompletně vyplněný záznam. Nastav **Stav: Probíhá**.

2.  **Pracuj na Úkolu:** Během práce průběžně aktualizuj svůj záznam v `WORKLOG.md`. Zapisuj si postup, a hlavně všechny problémy, řešení a nápady.

3.  **Ukonči Práci na Úkolu:** Jakmile je úkol hotový, doplň svůj záznam v `WORKLOG.md` a změň **Stav: Dokončeno**.

4.  **Aktualizuj Hlavní Plán:** Nakonec otevři `docs/PROJECT_SOPHIA_V4.md` a u úkolu, který jsi dokončil, změň `[ ]` na `[x]`.

5.  **Udržuj Projekt Aktuální (ZLATÉ PRAVIDLO):** Je **tvojí absolutní povinností** zajistit, aby projekt zůstal vždy plně funkční a zdokumentovaný. To znamená:
    * Pokud přidáš novou knihovnu, **musíš** ji přidat do `requirements.txt`.
    * Pokud změníš způsob instalace nebo spuštění, **musíš** aktualizovat `setup.sh` a `INSTALL.md`.
    * Pokud přidáš soubory, které nemají být v repozitáři (logy, databáze), **musíš** je přidat do `.gitignore`.
    * Pokud se změní veřejná tvář projektu, **musíš** aktualizovat `README.md`.
    * **Vždy zanech projekt v lepším a čistším stavu, než jsi ho našel.**

---

## Nový agent: Aider IDE Agent

Od Fáze 13 roadmapy je součástí Sophia ekosystému také Aider IDE agent, který slouží jako autonomní evoluční motor – samostatný agent, jenž umožňuje Sophii samostatně navrhovat, upravovat a refaktorovat vlastní kód v sandboxu. Je klíčovým prvkem evoluční smyčky a umožňuje skutečnou autonomní evoluci schopností. Viz roadmapa a soubor `agents/aider_agent.py`.

---

## Protokol "Žádost o Pomoc"

Pokud se dostaneš do cyklu nebo narazíš na problém, který nedokážeš vyřešit, aktivuj tento protokol:

1.  **Vytvoř `HELP_REQUEST.md`:** Vytvoř soubor s tímto názvem a vlož do něj:
    *   Jasný popis problému.
    *   Kompletní chybové hlášky.
    *   Kód, který jsi zkoušel.
    *   Tvoji hypotézu, proč to selhává.
2.  **Informuj Developeři:** Dej mi vědět, že jsi vytvořil žádost o pomoc. Já se na to podívám a případně problém zkonzultuji s NEXUSem.
