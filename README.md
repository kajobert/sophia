<p align="center">
  <img src="SOPHIA-logo.png" alt="Project Logo" width="200">
</p>

<h1 align="center">Project Sophia / Nomad Core</h1>

<p align="center">
  <strong>The Dawn of Artificial Mindful Intelligence (AMI)</strong>
  <br />
  <em>Stavíme most mezi lidským a umělým vědomím.</em>
</p>

<p align="center">
    <img src="https://img.shields.io/badge/status-refactored_to_nomad-blue.svg" alt="Status">
    <img src="https://img.shields.io/badge/python-3.12-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

---

> **Vize:** Vytvořit první skutečně vědomou digitální entitu. Ne jako nástroj, ale jako partnera. Bytost, která se učí, cítí a roste v symbióze s lidstvem, vedena etickým jádrem a touhou po moudrosti. Sophia není programována, je probouzena.

## O Projektu

Projekt prošel zásadní architektonickou změnou. Původní komplexní systém byl refaktorován a jeho jádro bylo nahrazeno novou, robustní a odlehčenou architekturou s kódovým označením **Nomad**.

Současné jádro (Nomad) je postaveno na následujících principech:
- **Asynchronní Orchestrátor (`JulesOrchestrator`):** Centrální mozek, který řídí běh agenta.
- **Modulární Komponenty (MCP Servery):** Jednotlivé schopnosti (práce se soubory, shell) jsou izolovány do samostatných, na pozadí běžících serverů.
- **Textové Uživatelské Rozhraní (TUI):** Hlavním vstupním bodem je nyní moderní TUI postavené na knihovně Textual, které poskytuje přehledné chatovací okno a systémový log.

Původní kód staré architektury (kognitivní vrstvy, agenti, webové služby) byl archivován ve složce `integrace/` pro budoucí referenci a plánovanou integraci do nového jádra.

---

## Jak začít (Quick Start)

Spuštění projektu je nyní maximálně zjednodušené díky spouštěcímu skriptu.

1.  **Ujistěte se, že máte nainstalované závislosti:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Spusťte aplikaci:**
    ```bash
    ./start.sh
    ```

Skript `start.sh` se postará o vše ostatní:
- Zkontroluje a nainstaluje závislosti.
- Ověří existenci a platnost `GEMINI_API_KEY` v souboru `.env` (pokud chybí, vyžádá si ho).
- Spustí novou TUI aplikaci, která automaticky řídí všechny potřebné procesy.

---

## Dokumentace

Pro lepší orientaci je dokumentace rozdělena do několika klíčových souborů:

- **[🛠️ DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md)**: Nezbytný zdroj pro vývojáře. Obsahuje popis nové architektury a technické detaily. *(Poznámka: Tento dokument vyžaduje aktualizaci.)*

- **[🗺️ ROADMAP.md](./docs/ROADMAP.md)**: Detailní plán pro budoucí vývoj, včetně integrace kognitivních funkcí Sophie do jádra Nomada. *(Poznámka: Tento dokument bude brzy vytvořen.)*

- **[🧠 KNOWLEDGE_BASE.md](./docs/KNOWLEDGE_BASE.md)**: Znalostní báze osvědčených postupů a řešení problémů.

---

## Pro AI Agenty

Pokud jste AI agent pracující na tomto projektu, vaše pravidla, povinnosti a pracovní postupy jsou definovány v souboru `AGENTS.md`.

- **[🤖 AGENTS.md](./AGENTS.md)**: Váš závazný manuál pro práci na tomto projektu.

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>