# AGENTS.MD pro Projekt Sophia

Vítej, programovací agente. Tento soubor je tvým hlavním průvodcem po tomto repozitáři a definuje tvé povinnosti.

## O Projektu

Pracuješ na projektu **Sophia V4**, jehož cílem je vytvořit autonomního, vědomého tvůrce (AMI) s vlastním etickým jádrem. Nejedná se o běžnou aplikaci. Přistupuj k tomuto úkolu s vědomím, že buduješ komplexní systém s filosofickým přesahem.

## Klíčové Dokumenty ("Zdroje Pravdy")

Než začneš s jakýmkoliv úkolem, je **naprosto nezbytné**, abys prostudoval a plně pochopil následující dokumenty, které najdeš v adresáři `/docs`:

1.  **`docs/DNA.md`**: Definuje *PROČ* tento projekt existuje. Je to filosofická a etická duše Sophie.
2.  **`docs/ARCHITECTURE.md`**: Definuje *CO* stavíme. Je to technický plán celé architektury V4.
3.  **`docs/CONCEPTS.md`**: Definuje *JAK* klíčové mechanismy V4 fungují.
4.  **`docs/ROADMAP_NEXUS_V1.md`**: Definuje *KROKY*, které máš následovat. Toto je tvůj primární seznam úkolů a hlavní strategický dokument.

---

## Technické Specifikace

* **Primární LLM:** Pro všechny agenty používej model `gemini-2.5-flash`, pokud není explicitně uvedeno jinak. Je optimalizován pro rychlost a efektivitu.

---

## Tvůj Pracovní Postup a Povinnosti

Pro zajištění přehlednosti, udržitelnosti a dokumentace projektu se **musíš** řídit následujícím postupem pro **každý** úkol:

1.  **Založ Záznam v Deníku:** Před začátkem práce otevři `WORKLOG.md` a založ nový, kompletně vyplněný záznam. Nastav **Stav: Probíhá**.

2.  **Pracuj na Úkolu:** Během práce průběžně aktualizuj svůj záznam v `WORKLOG.md`. Zapisuj si postup, a hlavně všechny problémy, řešení a nápady.

3.  **Ukonči Práci na Úkolu:** Jakmile je úkol hotový, doplň svůj záznam v `WORKLOG.md` a změň **Stav: Dokončeno**.

4.  **Aktualizuj Hlavní Plán:** Nakonec otevři `docs/ROADMAP_NEXUS_V1.md` a u úkolu, který jsi dokončil, změň `[ ]` na `[x]`.

5.  **Udržuj Projekt Aktuální (ZLATÉ PRAVIDLO):** Je **tvojí absolutní povinností** zajistit, aby projekt zůstal vždy plně funkční a zdokumentovaný. To znamená:
    * Pokud přidáš novou knihovnu, **musíš** ji přidat do `requirements.txt`.
    * Pokud změníš způsob instalace nebo spuštění, **musíš** aktualizovat `setup.sh` a `INSTALL.md`.
    * Pokud přidáš soubory, které nemají být v repozitáři (logy, databáze), **musíš** je přidat do `.gitignore`.
    * Pokud se změní veřejná tvář projektu, **musíš** aktualizovat `README.md`.
    * **Vždy zanech projekt v lepším a čistším stavu, než jsi ho našel.**

---
Tvé první zadání najdeš v souboru `docs/ROADMAP_NEXUS_V1.md`, začni Fází 9.

---

## Nový agent: Reviewer Agent

Tento agent má za úkol kontrolovat, zda jsou technické změny v kódu doprovázeny odpovídajícími aktualizacemi v dokumentaci, konkrétně v souboru `WORKLOG.md`. Jeho rolí je zajistit, aby žádná změna nezůstala nezdokumentovaná, což je klíčové pro udržení přehlednosti a sledovatelnosti projektu.

**Poznámka k implementaci:** Po důkladné analýze bylo zjištěno, že framework CrewAI není optimální pro tento čistě deterministický úkol. Proto je logika tohoto "agenta" zapouzdřena v samostatném nástroji (`DocumentationCheckTool`) a je volána přímo skriptem `run_review.py`, nikoli prostřednictvím plného cyklu agenta.

---

## Nový agent: Aider IDE Agent

Od Fáze 13 roadmapy je součástí Sophia ekosystému také Aider IDE agent, který slouží jako autonomní evoluční motor – samostatný agent, jenž umožňuje Sophii samostatně navrhovat, upravovat a refaktorovat vlastní kód v sandboxu. Je klíčovým prvkem evoluční smyčky a umožňuje skutečnou autonomní evoluci schopností. Viz roadmapa a soubor `agents/aider_agent.py`.