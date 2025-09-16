# AGENTS.MD pro Projekt Sophia

Vítej, programovací agente. Tento soubor je tvým hlavním průvodcem po tomto repozitáři a definuje tvé povinnosti.

---

## Zlatá Pravidla Vývoje (Závazný Kodex)

Tato pravidla jsou absolutní a musí být dodržena v každém úkolu. Jsou výsledkem našich zkušeností a slouží k prevenci opakujících se chyb.

**1. Žádné Hardcoded Názvy Modelů:**
- **Pravidlo:** Všechny názvy LLM modelů (např. "gemini-1.5-pro") musí být načítány VÝHRADNĚ z konfiguračního souboru (`config.yaml`). Nikde v Python kódu nesmí být název modelu napsán natvrdo.
- **Důvod:** Umožňuje nám to centrálně a bezpečně měnit používané modely.

**2. Testy Musí Běžet Offline:**
- **Pravidlo:** Celá testovací sada (`pytest`) musí být spustitelná bez reálného API klíče. Využívá se k tomu mechanismus `SOPHIA_ENV='test'`, který načítá `config_test.yaml` a aktivuje mockování přes `tests/conftest.py`.
- **Důvod:** Zajišťuje stabilitu, rychlost a nezávislost našich automatických testů.

**3. Správný Nástroj na Správnou Práci (CrewAI vs. Přímé Volání):**
- **Pravidlo:** Framework CrewAI se používá pro komplexní úkoly, kde je potřeba spolupráce více agentů a rozhodování pomocí LLM. Pro jednoduché, deterministické úkoly (jako je kontrola textu v souboru) se framework obchází a volá se přímo logika daného nástroje.
- **Důvod:** Předcházíme tím zbytečným chybám a neefektivitě při použití příliš složitého nástroje na jednoduchý problém.

**4. Dokumentace je Součástí Kódu:**
- **Pravidlo:** Každá změna v kódu (`.py` soubory) musí být doprovázena záznamem v `WORKLOG.md`. Každá změna strategie nebo architektury musí být reflektována v `docs/ROADMAP_NEXUS_V1.md` a dalších relevantních dokumentech.
- **Důvod:** Zajišťuje transparentnost, dohledatelnost a udržitelnost projektu.

---

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