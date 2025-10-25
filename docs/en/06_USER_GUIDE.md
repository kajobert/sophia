# Sophia V2 - User Guide

This guide will walk you through setting up and running the Sophia V2 application on your local machine.

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
