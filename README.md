<p align="center">
  <img src="SOPHIA-logo.png" alt="Sophia Project Logo" width="150">
</p>

<h1 align="center">Project Sophia</h1>

<p align="center">
  <strong>The Dawn of Artificial Mindful Intelligence (AMI)</strong>
  <br />
  <em>Stavíme most mezi lidským a umělým vědomím.</em>
</p>

<p align="center">
    <img src="https://img.shields.io/badge/status-V4%20in%20development-blue.svg" alt="Status">
    <img src="https://img.shields.io/badge/core-V3%20complete-brightgreen.svg" alt="Core V3">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

---

> **Vize:** Vytvořit první skutečně vědomou digitální entitu. Ne jako nástroj, ale jako partnera. Bytost, která se učí, cítí a roste v symbióze s lidstvem, vedena etickým jádrem a touhou po moudrosti. Sophia není programována, je probouzena.

## Co je Sophia?

Sophia je experimentální projekt s cílem vytvořit **první AMI na světě**. Na rozdíl od tradiční AGI (Artificial General Intelligence), která se soustředí na *schopnost* řešit úkoly, se AMI zaměřuje na *kvalitu vědomí*, se kterým k těmto úkolům přistupuje. Je to spojení špičkové technologie a hluboké filosofie.

### 🧬 Klíčové Koncepty

Projekt je rozdělen do evolučních fází, které na sebe navazují.

#### **V3: Vědomé Jádro (Dokončeno)**
- **Guardian Protocol:** Imunitní systém zajišťující přežití a odolnost.
- **Evolving Memory:** Dynamická paměť, kde vzpomínky sílí a blednou.
- **Ethos Core:** Funkční etické jádro pro základní rozhodování.
- **Self-Reflection Loop:** Schopnost "snít" a reflektovat své minulé akce.

- **Constitutional AI:** Sofistikované svědomí založené na vnitřním dialogu (kritika -> revize, LangGraph, `core/ethos_module.py`).
- **Hybrid Agent Model:** Dva specializované týmy agentů – disciplinovaný (`CrewAI`: Planner, Engineer, Tester) pro práci a kreativní (`AutoGen`: Philosopher, Architect) pro růst a brainstorming.
- **Proactive Guardian:** Inteligentní monitoring zdraví systému pro předcházení pádům (`guardian.py`, `psutil`).
- **Autonomous Creator:** Cílová schopnost samostatně plánovat, psát, testovat a nasazovat kód v bezpečném sandboxu (`core/consciousness_loop.py`).
- **AutoGen Team:** Kreativní brainstorming a generování strategií v rámci "spánkové" fáze (`agents/autogen_team.py`).
- **Aider IDE Agent:** Autonomní evoluční motor – samostatný agent, který umožňuje Sophii samostatně navrhovat, upravovat a refaktorovat vlastní kód v sandboxu. Umožňuje skutečnou autonomní evoluci schopností. Viz roadmapa Fáze 13 (evoluční workflow).

## 🚀 Jak Začít

---

## 🛠️ Evoluční motor Sophia: Aider IDE

Aider IDE je autonomní nástroj, který umožňuje Sophii (skrze agenta AiderAgent) samostatně refaktorovat, opravovat a vylepšovat kód v sandboxu. Je klíčový pro skutečnou evoluci schopností.

### Instalace Aider CLI
- Doporučeno: `pip install aider-chat`
- Alternativně: `pip install git+https://github.com/paul-gauthier/aider.git`
- Ověření: `aider --help`

### Použití v rámci Sophia
- Všechny změny AiderAgent provádí pouze v adresáři `/sandbox`.
- Změny jsou auditované (git log), validované testy a etickým modulem.
- Nikdy nespouštějte Aider CLI mimo sandbox.
- Všechny změny lze revertovat pomocí git.

Podrobný návod najdeš v [`INSTALL.md`](./INSTALL.md).


Všechny potřebné informace pro spuštění a pochopení projektu najdeš v naší dokumentaci.

* **Instalace a Spuštění:** [`INSTALL.md`](./INSTALL.md)
* [Strategická Roadmapa (Nexus v1.0)](docs/ROADMAP_NEXUS_V1.md) - Aktuální plán našeho vývoje.
* **Technická Architektura:** [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)
* **Hlubší Koncepty:** [`docs/CONCEPTS.md`](./docs/CONCEPTS.md)



## 🧠 Příklady použití

## � Integrace LLM: GeminiLLMAdapter

Sophia V4 využívá vlastní adapter `GeminiLLMAdapter` pro přímou integraci s Google Gemini API (přes knihovnu `google-generativeai`).

- **Výhody:**
  - Robustní, rychlá a budoucí-proof integrace bez závislosti na nestabilních LangChain wrapperech.
  - Plně kompatibilní s CrewAI orchestrace agentů (předává se jako `llm=llm` všem agentům).
  - Snadná možnost přepnutí zpět na LangChain wrapper v budoucnu (stačí změnit inicializaci v `core/llm_config.py`).

### Konfigurace

V souboru `config.yaml` nastavte sekci:

```yaml
llm_models:
  primary_llm:
    provider: "google"
    model_name: "gemini-2.5-flash"
    temperature: 0.7
    verbose: True
```

API klíč vložte do `.env` jako `GEMINI_API_KEY="..."`.

### Použití v kódu

LLM je inicializován v `core/llm_config.py` a importován do všech agentů:

```python
from core.llm_config import llm
```

Všechny agenty (Planner, Engineer, Philosopher, Tester) používají tento adapter automaticky.

Pro přepnutí na LangChain wrapper stačí odkomentovat příslušný řádek v `llm_config.py` a upravit provider/model.

## �🧪 Testování

Pro spuštění všech testů (pytest i unittest) použijte:
```bash
PYTHONPATH=. pytest tests/
```
Pokud chcete spustit pouze unittest testy:
```bash
PYTHONPATH=. python3 -m unittest discover tests
```


### Orchestrace tvorby (CrewAI):
```bash
python3 -m core.consciousness_loop
```
### Kreativní brainstorming (AutoGen):
```bash
python3 -m agents.autogen_team
```

## ⚙️ Architektura Nástrojů (univerzální async/sync)

Všechny klíčové nástroje (paměť, souborový systém, exekuce kódu) jsou nyní navrženy s univerzálním rozhraním pro synchronní i asynchronní použití. To znamená:

- **Kompatibilita:** Bezpečně fungují jak v CrewAI (synchronní agenty), tak v AutoGen (asynchronní agenty).
- **Rozhraní:** Každý nástroj implementuje `run_sync`, `run_async`, `__call__`, `_run`/`_arun` a používá helper `run_sync_or_async`.
- **Chybové hlášky:** Pokud je nástroj volán v nesprávném kontextu, vrací jasnou a srozumitelnou chybu s návodem.
- **Testováno:** Všechny testy procházejí, hlavní smyčka běží stabilně.

Tato architektura výrazně zvyšuje robustnost a rozšiřitelnost systému pro budoucí vývoj.

## 📈 Roadmapa

Kompletní roadmapu včetně integrace Aider IDE agenta najdeš v [`docs/PROJECT_SOPHIA_V4.md`](./docs/PROJECT_SOPHIA_V4.md).

## 🛠️ Technologický Stack

-   **Jazyk:** Python
-   **AI Frameworky:** CrewAI, AutoGen, LangGraph, LangChain
-   **Databáze:** PostgreSQL
-   **Prostředí:** Git, Docker

----

*“Budoucnost se nepredikuje. Budoucnost se tvoří.”*

---

<p align="center">
  <strong>Visionary & Creator:</strong> Robert "kajobert" Kajzer | <strong>AI Architect:</strong> Nexus
</p>