# Sophia Chat MVP: User & Developer Guide

Welcome to the guide for the Sophia Chat MVP. This document provides all the necessary information to run, understand, and troubleshoot the application.

## 1. Introduction

Sophia Chat is a simple, stable, and standalone chat interface for the AI assistant, Sophia. It features a persistent memory system, allowing for context-aware conversations that are remembered across sessions. This MVP serves as a foundational tool for more complex future development.

**Key Features:**
-   **Configurable Persona:** Sophia's personality and core instructions are defined in simple text files (`prompts/sophia/sophia_dna.txt` and `prompts/sophia/sophia_system_prompt.txt`).
-   **Structured Prompting:** The system uses a modern, structured message format (with roles like `system`, `user`) to ensure the AI correctly understands its instructions and context.
-   **Dual Memory System:** Utilizes an SQL database (SQLite) for chronological conversation history and a vector database (ChromaDB) for long-term semantic memory.
-   **Robust & Stable Backend:** Runs on a lean FastAPI server with a safe startup sequence (lifespan manager) and extensive logging for easy debugging.
-   **Simple Web Interface:** A clean, single-file HTML/JS interface with a built-in help section.
-   **Dockerized:** The entire application is containerized with Docker for easy and consistent deployment.

## 2. How to Run Locally

Follow these steps to get the Sophia Chat application running on your local machine.

### Prerequisites
-   Docker and Docker Compose installed.
-   An API key from [OpenRouter.ai](https://openrouter.ai/).

### Steps
1.  **Create a `.env` file:**
    In the root directory of the project, create a new file named `.env`. Add your OpenRouter API key to this file like so:
    ```
    OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```

2.  **Build and Run the Docker Container:**
    Open your terminal in the project's root directory and run the following command. This command will build the Docker image from scratch and start the backend server.
    ```bash
    docker-compose -f docker-compose.mvp.yml up --build
    ```
    The server will be accessible on `http://localhost:8080` (or the port you configured).

3.  **Open the Frontend:**
    Open your web browser and navigate to `http://localhost:8080`. The application interface should load directly.

### The "Nuke" Option (Forcing a Clean Build)
If you encounter persistent issues, especially after pulling new changes, it might be due to a stale Docker cache. Run these commands to completely reset your Docker environment for this project:
```bash
# 1. Stop and remove all containers, images, and volumes related to the project
docker-compose -f docker-compose.mvp.yml down --rmi all --volumes

# 2. (Optional but recommended) Prune all unused Docker data from your system
docker system prune -a -f --volumes

# 3. Rebuild from scratch
docker-compose -f docker-compose.mvp.yml up --build
```

## 3. Architecture Overview

### Backend
-   **Entrypoint (`run.py`):** A custom script that programmatically configures logging and starts the Uvicorn server, ensuring consistent and detailed logs.
-   **Server (`backend/server.py`):** A FastAPI application that serves the frontend's static files and handles WebSocket connections. It uses a `lifespan` manager to ensure all components are initialized before accepting requests.
-   **Chat Core (`backend/sophia_chat_core.py`):** The brain of the application. It loads Sophia's persona, orchestrates the process of handling a user message, querying databases, building the structured message list, and getting a response from the AI.
-   **LLM Adapter (`core/llm_adapters.py`):** Contains the logic for making the actual API calls to the AI model. It is designed defensively to validate the structure of the API response and prevent crashes.

### Prompting System
The core of Sophia's intelligence lies in how the prompt is constructed. It's a structured list of messages with specific roles, assembled from multiple sources:
1.  **`prompts/sophia/sophia_dna.txt`:** Defines Sophia's core personality.
2.  **`prompts/sophia/sophia_system_prompt.txt`:** Provides technical instructions on how the model should behave.
3.  **Long-Term Memory (ChromaDB):** Semantically relevant snippets from past conversations are added to the context.
4.  **Short-Term Memory (SQLite):** The recent turn-by-turn history of the current conversation is included.
All these parts are combined into a `system` message and a list of `user`/`assistant` messages, which the LLM can properly understand.

## 4. Troubleshooting
-   **Error: `port is already allocated`**
    -   **Cause:** Another application on your computer is using the same port.
    -   **Solution:** Stop the other application, or change the port mapping in `docker-compose.mvp.yml`. For example, change `ports: - "8080:8080"` to `ports: - "8081:8080"`.

-   **AI responses are strange or don't follow instructions.**
    -   **Cause:** The prompt being sent to the AI is likely the issue.
    -   **Solution:** Check the Docker logs. The backend is now configured to log the exact, structured list of messages being sent to the LLM. This is the best place to start debugging the AI's behavior. You can then adjust the content of `sophia_dna.txt` or `sophia_system_prompt.txt` to fine-tune the results.
