[📚 Documentation Index](INDEX.md) | [⬅️ 05 Project Governance](05_PROJECT_GOVERNANCE.md) | **06** → [07 Developer Guide](07_DEVELOPER_GUIDE.md)

---

# Sophia V2 - User Guide

**How to Use Sophia** | Setup & Interaction | For End Users

This guide will walk you through setting up and running the Sophia V2 application on your local machine.

> 🚀 **Quick Start:** `python run.py` launches both Terminal and Web UI (http://localhost:8000) simultaneously.  
> 💬 **Interaction:** Chat in terminal or browser - Sophia processes input from whichever interface speaks first.

## 1. Prerequisites

Before you begin, ensure you have the following installed on your system:
- **Python 3.12 or higher:** [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Git:** [https://git-scm.com/downloads](https://git-scm.com/downloads)
- **`uv`:** A fast Python package installer. You can install it with `pip install uv`.

## 2. Setup Instructions

### 2.1. Clone the Repository
First, clone the project repository from GitHub to your local machine.

```bash
git clone https://github.com/kajobert/sophia.git
cd sophia
```

### 2.2. Create a Virtual Environment
It is highly recommended to use a virtual environment to manage project dependencies.

```bash
uv venv
```
This will create a `.venv` directory in your project folder.

### 2.3. Activate the Virtual Environment
Activate the virtual environment. On macOS and Linux:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 2.4. Install Dependencies
Install all the required Python packages using `uv`.

```bash
uv pip sync requirements.in
```

### 2.5. Configure the Application
The application requires an API key for the LLM service.

1.  **Create a configuration file:**
    Copy the example configuration file to create your own local settings.

    ```bash
    cp config/settings.example.yaml config/settings.yaml
    ```

2.  **Add your API Key:**
    You need an API key from a provider supported by `litellm`. We recommend [OpenRouter](https://openrouter.ai/).
    - Create an environment variable named `OPENROUTER_API_KEY` and set its value to your API key. You can do this by adding the following line to your `.bashrc`, `.zshrc`, or by setting it in your system's environment variables:
      ```bash
      export OPENROUTER_API_KEY="your-api-key-here"
      ```
    - Alternatively, you can edit the `config/settings.yaml` file and add your key directly, but using environment variables is more secure.

    The application is pre-configured to use the `openrouter/mistralai/mistral-7b-instruct` model, which is a free model available on OpenRouter.

3.  **Optional: Configure Jules API (for AI-assisted coding):**
    If you want to use the Jules API integration for AI coding assistance, you'll need a Jules API key:
    - Create a `.env` file in the project root (this file is in `.gitignore` and won't be committed):
      ```bash
      echo "JULES_API_KEY=your-jules-api-key-here" >> .env
      ```
    - The plugin will automatically load this key from the environment.
    - See `docs/JULES_API_SETUP.md` for detailed setup instructions.

4.  **Optional: Configure Tavily API (for AI-optimized web search):**
    If you want to use Tavily's AI-powered search capabilities, you'll need a Tavily API key:
    - Get your free API key at [https://tavily.com](https://tavily.com)
    - Add it to the `.env` file:
      ```bash
      echo "TAVILY_API_KEY=tvly-your-api-key-here" >> .env
      ```
    - The plugin will automatically load this key from the environment.
    - See `docs/TAVILY_API_SETUP.md` for detailed setup instructions.

## 3. Running the Application

Sophia V2 can be run in two modes: with a terminal interface or a web-based UI.

### 3.1. Terminal Interface
To interact with Sophia through your terminal, run the following command from the root of the project directory:

```bash
python run.py
```

You will see a prompt `>>> You:`. Type your message and press Enter to get a response from Sophia.

### 3.2. Web Interface
The application also provides a web-based chat interface.

1.  **Start the application:**
    Run the same command as for the terminal interface:
    ```bash
    python run.py
    ```
    When the application starts, it will also launch a web server. You will see a log message like this in your terminal: `INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`.

2.  **Access the Web UI:**
    Open your web browser and navigate to the following address:
    [http://127.0.0.1:8000](http://127.0.0.1:8000)

You can now chat with Sophia through the web interface.

## 4. Stopping the Application
To stop the application, simply press `Ctrl+C` in the terminal where it is running.

---

## Sophia 2.0 Features

**Current Capabilities (27 Plugins):**
- ✅ **Natural Language Interaction** - Terminal and Web UI
- ✅ **File System Operations** - Read, write, manage files and directories
- ✅ **Code Execution** - Run Bash commands, Python scripts
- ✅ **Git & GitHub Integration** - Repository management, PR/Issue handling
- ✅ **Web Search** - Internet access via Tavily and generic web search
- ✅ **Long-Term Memory** - ChromaDB vector database for episodic memory
- ✅ **Jules Integration** - Async task execution via Jules API/CLI
- ✅ **Model Evaluation** - Performance benchmarking and optimization
- ✅ **Observability** - Langfuse integration for monitoring

**Coming in Sophia 2.0 Autonomous Operations:**
- 🚧 **Continuous Operation** - Event-driven loop, runs 24/7
- 🚧 **Autonomous Task Execution** - Self-directed work from `roberts-notes.txt` ideas
- 🚧 **Memory Consolidation** - "Dreaming" phase for pattern recognition
- 🚧 **Self-Improvement** - Automated code improvements with HITL approval

See [Autonomous MVP Roadmap](AUTONOMOUS_MVP_ROADMAP.md) for details.

---

## Related Documentation

- 📖 **[Project Overview](08_PROJECT_OVERVIEW.md)** - High-level architecture and vision
- 🧑‍💻 **[Developer Guide](07_DEVELOPER_GUIDE.md)** - For extending Sophia with new plugins
- 🔧 **[Development Guidelines](04_DEVELOPMENT_GUIDELINES.md)** - Code quality standards
- 🎯 **[Vision & DNA](01_VISION_AND_DNA.md)** - Core philosophy

**Configuration:**
- [`config/settings.yaml`](../../config/settings.yaml) - LLM settings, memory, logging
- [`config/autonomy.yaml`](../../config/autonomy.yaml) - Autonomous operation boundaries
- [`config/model_strategy.yaml`](../../config/model_strategy.yaml) - Model routing strategy

---

**Navigation:** [📚 Index](INDEX.md) | [🏠 Home](../../README.md) | [⬅️ Previous: Governance](05_PROJECT_GOVERNANCE.md) | [➡️ Next: Developer Guide](07_DEVELOPER_GUIDE.md)

---

*Last Updated: November 3, 2025 | Status: ✅ Current | Sophia 2.0 Active*
