# Installation and Setup Guide for Sophia V4
# ---
# Aider IDE (Evoluční motor Sophia)
# ---

## 🤖 Integrace LLM: GeminiLLMAdapter

Sophia V4 využívá vlastní adapter `GeminiLLMAdapter` pro přímou integraci s Google Gemini API.

- **Požadavky:**
	- Python knihovna `google-generativeai` (instaluje se automaticky přes `requirements.txt`)
	- API klíč pro Gemini: nastavte do `.env` souboru proměnnou `GEMINI_API_KEY="..."`

### Nastavení LLM v config.yaml

```yaml
llm_models:
	primary_llm:
		provider: "google"
		model_name: "gemini-2.5-flash"
		temperature: 0.7
		verbose: True
```

LLM je inicializován v `core/llm_config.py` a automaticky používán všemi agenty.

Pro přepnutí na LangChain wrapper stačí upravit provider a model v config.yaml a odkomentovat příslušný řádek v `llm_config.py`.

## 🛠️ Instalace a použití Aider IDE

Aider IDE je klíčový nástroj pro autonomní evoluci schopností Sophia. Umožňuje agentovi AiderAgent bezpečně refaktorovat, opravovat a vylepšovat kód v sandboxu.

### Instalace Aider CLI

1. **Doporučený způsob (pip):**
	```bash
	pip install aider-chat
	```
2. **Alternativně (z Gitu):**
	```bash
	pip install git+https://github.com/paul-gauthier/aider.git
	```
3. Ověřte instalaci:
	```bash
	aider --help
	```

### Spuštění Aider IDE v sandboxu

Všechny operace AiderAgent provádí pouze v adresáři `/sandbox`.

Příklad ručního spuštění:
```bash
cd sandbox
aider main.py
```

### Propojení s Sophia (AiderAgent)

AiderAgent komunikuje s Aider CLI přes příkazovou řádku. Všechny změny jsou auditované (git log) a validované testy a Ethos modulem.

**Bezpečnostní doporučení:**
- Nikdy nespouštějte Aider CLI mimo sandbox.
- Pravidelně kontrolujte git historii a validujte změny.
- Všechny změny lze revertovat pomocí git.

---
# ---
# PostgreSQL Setup (Docker)
# ---

## 🐘 Rychlý start PostgreSQL v Dockeru

Pro lokální vývoj spusťte PostgreSQL pomocí následujícího příkazu (používá stejné údaje jako v `config.yaml`):

```bash
docker run --name sophia-postgres \
	-e POSTGRES_USER=sophia_user \
	-e POSTGRES_PASSWORD=sophia_password \
	-e POSTGRES_DB=sophia_db \
	-p 5432:5432 \
	-d --restart unless-stopped postgres:13
```

Pokud změníte přihlašovací údaje v `config.yaml`, upravte je i zde.

Pro kontrolu běžícího kontejneru použijte:
```bash
docker ps
```

Pro zastavení a smazání databáze:
```bash
docker stop sophia-postgres && docker rm sophia-postgres
```

---


> **POZOR:** Pro plnou funkčnost AiderAgentu je nutné ručně nainstalovat [Aider CLI](https://github.com/paul-gauthier/aider) dle oficiální dokumentace. Není součástí requirements.txt!

This guide provides simple instructions to get the Sophia V4 project set up and running, specifically within a GitHub Codespace or a similar Linux-based environment.

## 🚀 Getting Started in a GitHub Codespace

Follow these steps to get a functional instance of Sophia running.

### 1. Open in Codespace

Open this repository in a GitHub Codespace. The environment will be prepared for you automatically.

### 2. Run the Setup Script

Once the Codespace is loaded and you have a terminal, you need to run the setup script. This will install all the necessary dependencies.

First, make the script executable:
```bash
chmod +x setup.sh
```

Now, run the script:
```bash
./setup.sh
```
The script will upgrade pip, install all Python libraries from `requirements.txt`, and create a `.env` file for your environment variables. The script now also installs `psutil` for system monitoring.

### 3. Set Up PostgreSQL Database

Sophia V4 uses a PostgreSQL database. The recommended way to run it locally is with Docker.

Run the following command to start a PostgreSQL container. This command will also set it up to restart automatically.

```bash
docker run --name sophia-postgres -e POSTGRES_USER=sophia_user -e POSTGRES_PASSWORD=sophia_password -e POSTGRES_DB=sophia_db -p 5432:5432 -d --restart unless-stopped postgres:13
```

The environment variables used in this command (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`) correspond to the values in `config.yaml`. If you change them in `config.yaml`, you must also change them in the `docker run` command.

### 4. Configure Environment (Optional)

The setup script creates a `.env` file. If the project requires API keys (e.g., for OpenAI, Anthropic), you must add them to this `.env` file.

Example `.env` content:
```
OPENAI_API_KEY="your_api_key_here"
ANTHROPIC_API_KEY="your_api_key_here"
```

### 5. Start Sophia

You are now ready to start the application. The main entry point is `guardian.py`, which monitors and runs the core process.

Run the following command:
```bash
python3 guardian.py
```

You should now see log output from both the Guardian and the main Sophia process in your terminal, indicating that the AGI is running its "Waking/Sleeping" lifecycle.

## 🧪 Running Tests



To ensure the integrity of the codebase, run all tests using **pytest** (doporučeno):

```bash
PYTHONPATH=. pytest tests/
```

This will automatically discover and run all tests (pytest i unittest) in the `tests` directory.

If you want to run only unittest tests (without pytest fixtures), you can use:
```bash
PYTHONPATH=. python3 -m unittest discover tests
```

---

## 🧠 Další možnosti spuštění (pro vývojáře)

- Orchestrace tvorby (CrewAI):
	```bash
	python3 -m core.consciousness_loop
	```
- Kreativní brainstorming (AutoGen):
	```bash
	python3 -m agents.autogen_team
	```

**Pozor:** Některé knihovny (např. pyautogen, langgraph) mohou způsobit konflikty s jinými AI frameworky. Pokud narazíte na chyby při importu, doporučujeme použít čisté prostředí nebo Docker.
