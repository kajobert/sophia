# Plán Opravy a Dokončení Migrace Projektu Sophia V4

## Autor: Jules, AI Inženýr
## Datum: 2025-09-14

---

## 1. Souhrn Zjištění (Stav Projektu)

Po důkladné analýze kódu byl projekt Sophia V4 shledán v **nekonzistentním a aktuálně nespustitelném stavu**. Jedná se o napůl dokončenou migraci z architektury V3 na V4. Klíčové problémy jsou:

-   **Kritický Konflikt Závislostí:** Soubor `requirements.txt` obsahuje nekompatibilní verze klíčových AI knihoven (`pyautogen`, `crewai`, `langchain`, atd.). To způsobuje, že instalace prostředí selhává s chybou vypršení časového limitu, což znemožňuje jakékoliv spuštění nebo testování.
-   **Nedokončená Migrace Databáze:** Kód již vyžaduje databázi PostgreSQL (dle souboru `memory/advanced_memory.py`), ale v hlavní roadmapě projektu je tento úkol (9.1) označen jako nedokončený. Chybí také jakákoliv dokumentace pro nastavení databáze.
-   **Neúplná Integrace Logiky:** Hlavní aplikační smyčka v `main.py` nespouští plný řetězec agentů (Planner -> Engineer -> Tester), jak je popsáno v architektuře V4. Existuje pouze jako neintegrovaný prototyp v `core/consciousness_loop.py`.

---

## 2. Navrhovaný Plán Opravy

Cílem tohoto plánu je systematicky opravit základní problémy, stabilizovat projekt a dokončit migraci na architekturu V4.

1.  **Stabilizace Prostředí (`requirements.txt`):**
    -   **Akce:** Provedu finální úpravu souboru `requirements.txt`. Odstraním problematické a zastaralé verze u hlavních AI knihoven a ponechám pouze ty, které jsou nezbytné, aby `pip` mohl najít nejnovější kompatibilní sadu.
    -   **Akce:** Spustím instalaci závislostí z nově upraveného souboru.
    -   **Ověření:** Instalace se úspěšně dokončí.

2.  **Dokončení Migrace na PostgreSQL (Úkol 9.1):**
    -   **Akce:** Upravím `INSTALL.md` a přidám do něj jasné instrukce pro spuštění PostgreSQL databáze pomocí Dockeru.
    -   **Akce:** Upravím soubor `config.yaml`, aby odpovídal přihlašovacím údajům použitým v Docker příkazu.
    -   **Ověření:** Dokumentace bude srozumitelná a konfigurační soubor bude správně nastaven.

3.  **Integrace Plné V4 Orchestrace:**
    -   **Akce:** Přepíšu logiku v `main.py` tak, aby po naplánování úkolu skutečně spustila celý řetězec zahrnující `EngineerAgent`a a `TesterAgent`a.
    -   **Akce:** Přizpůsobím tuto logiku, aby správně fungovala v `asyncio` prostředí hlavní smyčky a spolupracovala s `AdvancedMemory`.
    -   **Ověření:** `main.py` bude obsahovat kompletní, integrovanou V4 smyčku.

4.  **Aktualizace Roadmapy a Spuštění Testů:**
    -   **Akce:** Upravím `docs/ROADMAP_NEXUS_V1.md` a označím úkol 9.1 (`Upgrade Databáze`) jako dokončený (`[x]`).
    -   **Akce:** Spustím unit testy příkazem `python3 -m unittest discover tests`.
    -   **Ověření:** Testy proběhnou a roadmapa bude reflektovat aktuální stav.

5.  **Finální Ověření a Odevzdání:**
    -   **Akce:** Požádám o revizi kódu, abych se ujistil, že mé změny jsou kvalitní.
    -   **Akce:** Spustím proces záznamu svých zjištění do paměti.
    -   **Akce:** Odevzdám svou práci s detailním popisem provedených změn.

---

## 3. Prompt pro AI Agenta (Souhrnné Zadání)

**Cíl:** Opravit, stabilizovat a dokončit migraci projektu Sophia V4.

**Kontext:** Projekt je v nekonzistentním stavu s nefunkčním prostředím a nedokončenou migrací na PostgreSQL. Je třeba systematicky postupovat podle definovaného plánu.

**Úkoly:**
1.  **Oprav `requirements.txt`:** Odstraň konfliktní verze knihoven a nainstaluj stabilní prostředí.
2.  **Dokumentuj a konfiguruj PostgreSQL:** Aktualizuj `INSTALL.md` o instrukce pro Docker a synchronizuj `config.yaml`.
3.  **Implementuj plnou smyčku V4:** Integruj do `main.py` plnou orchestraci agentů Planner, Engineer a Tester.
4.  **Finalizuj:** Aktualizuj roadmapu v `docs/ROADMAP_NEXUS_V1.md`, spusť testy a zajisti, že je projekt funkční.
5.  **Odevzdej:** Po kontrole kvality kódu odevzdej svou práci.

**Důležité:** Postupuj přesně podle kroků v plánu. Každý krok ověř, než postoupíš k dalšímu. Komunikuj jasně o svém postupu.
