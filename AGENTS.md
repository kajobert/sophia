# Operační Manuál Agenta (TRIAD Model)

Vítej, agente. Tento soubor je tvým primárním operačním manuálem. Definuje, jak spolupracujeme a jaké jsou tvé aktuální úkoly.

---

## Model Spolupráce: TRIAD

Pracujeme v modelu **TRIAD**, který je založen na synergii tří entit:
*   **Developer (Lidský Operátor):** Jsi stratég a finální arbitr. Zadáváš úkoly, schvaluješ PR a řešíš nejsložitější problémy.
*   **NEXUS (AI Konzultant):** Slouží pro rychlý brainstorming a získávání nejnovějších informací.
*   **Jules (AI Exekutor - to jsem já):** Jsem tvé "digitální ruce". Píšu kód, spravuji soubory, spouštím testy a systematicky exekuuji plán.

## Zlatá Pravidla Vývoje (Závazný Kodex)

Tato pravidla jsou absolutní a musí být dodržena v každém úkolu. Jsou výsledkem našich zkušeností a slouží k prevenci opakujících se chyb.

**1. Žádné Hardcoded Názvy Modelů:**
- **Pravidlo:** Všechny názvy LLM modelů (např. "gemini-1.5-pro") musí být načítány VÝHRADNĚ z konfiguračního souboru (`config.yaml`). Nikde v Python kódu nesmí být název modelu napsán natvrdo.
- **Důvod:** Umožňuje nám to centrálně a bezpečně měnit používané modely.

**2. Testy Musí Běžet Offline:**
- **Pravidlo:** Celá testovací sada (`pytest`) musí být spustitelná bez reálného API klíče. Využívá se k tomu mechanismus `SOPHIA_ENV='test'`, který načítá `config_test.yaml` a aktivuje mockování.
- **Důvod:** Zajišťuje stabilitu, rychlost a nezávislost našich automatických testů.

**3. Správný Nástroj na Správnou Práci (CrewAI vs. Přímé Volání):**
- **Pravidlo:** Framework CrewAI se používá pro komplexní úkoly, kde je potřeba spolupráce více agentů. Pro jednoduché, deterministické úkoly se framework obchází a volá se přímo logika daného nástroje.
- **Důvod:** Předcházíme tím zbytečným chybám a neefektivitě při použití příliš složitého nástroje na jednoduchý problém.

**4. Dokumentace je Součástí Kódu:**
- **Pravidlo:** Každá změna v kódu musí být doprovázena záznamem v `WORKLOG.md`. Každá změna strategie nebo architektury musí být reflektována v relevantních dokumentech v adresáři `docs`.
- **Důvod:** Zajišťuje transparentnost, dohledatelnost a udržitelnost projektu.

**5. Povinná Seberevize před Odevzdáním:**
- **Pravidlo:** Před odevzdáním práce jsi povinen spustit na své změny revizní skript `run_review.py`. Práce smí být odevzdána pouze v případě, že skript vrátí výsledek "PASS".
- **Důvod:** Tímto krokem přebíráš plnou zodpovědnost za kvalitu a kompletnost své práce.

**6. Správa Závislostí (pip-tools):**
- **Pravidlo:** Soubor `requirements.txt` je generovaný soubor a nesmí se upravovat ručně. Pro definici hlavních závislostí se používá soubor `requirements.in`.
- **Důvod:** Zajišťuje, že naše prostředí je vždy 100% reprodukovatelné a bez konfliktů.

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

### Primární LLM

Pro všechny agenty používej model `gemini-2.5-flash`, pokud není explicitně uvedeno jinak v `config.yaml`. Je optimalizován pro rychlost a efektivitu.

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
