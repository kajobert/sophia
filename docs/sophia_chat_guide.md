# Sophia Chat MVP: User & Developer Guide

Welcome to the guide for the Sophia Chat MVP. This document provides all the necessary information to run, understand, and troubleshoot the application.

## 1. Introduction

Sophia Chat is a simple, stable, and standalone chat interface for the AI assistant, Sophia. It features a persistent memory system, allowing for context-aware conversations that are remembered across sessions. This MVP serves as a foundational tool for more complex future development.

**Key Features:**
-   **Dual Memory System:** Utilizes an SQL database (SQLite) for chronological conversation history and a vector database (ChromaDB) for long-term semantic memory.
-   **Standalone Backend:** Runs on a lean FastAPI server, independent of the main Nomad agent architecture.
-   **Simple Web Interface:** A clean, single-file HTML/JS interface for easy interaction.
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
    Open your terminal in the project's root directory and run the following command:
    ```bash
    docker-compose -f docker-compose.mvp.yml up --build
    ```
    This command will build the Docker image from scratch (installing all dependencies) and start the backend server. The server will be accessible on `http://localhost:8080`.

3.  **Open the Frontend:**
    Navigate to the `frontend/` directory and open the `chat.html` file in your web browser. You can typically just double-click the file. The chat interface will connect to the running backend automatically.

## 3. Architecture Overview

### Backend
-   **Server (`backend/server.py`):** A FastAPI application that serves the main API and handles WebSocket connections. It uses a `lifespan` manager to ensure all components are initialized before accepting requests.
-   **WebSocket Handler (`backend/websocket.py`):** Manages the real-time, bidirectional communication between the frontend and the backend.
-   **Chat Core (`backend/sophia_chat_core.py`):** The brain of the application. It orchestrates the entire process of handling a user message, querying databases, building a prompt, and getting a response from the AI.
-   **Database Manager (`backend/database_manager.py`):** A dedicated class for managing all interactions with both the SQLite and ChromaDB databases.
-   **LLM Manager (`core/llm_manager.py`):** A factory for creating AI model adapters (e.g., for OpenRouter).
-   **LLM Adapter (`core/llm_adapters.py`):** Contains the logic for making the actual API calls to the AI model and validating the response.

### Frontend
-   **Chat Interface (`frontend/chat.html`):** A single HTML file containing all the necessary HTML for structure, CSS for styling, and JavaScript for functionality. It connects to the backend via a WebSocket and handles the display of messages.

### Memory System
-   **Short-Term Memory (SQLite):** The `data/sophia_chat.db` file stores a complete, chronological log of all messages. This is used to build the "Recent Conversation History" part of the prompt.
-   **Long-Term Memory (ChromaDB):** The `data/chroma_db/` directory contains a vector database. Every message is converted into a vector embedding and stored. When a new message arrives, ChromaDB is queried to find semantically similar messages from the past, which are then used as "Relevant Memories" in the prompt.

## 4. Troubleshooting

-   **Error: `port is already allocated`**
    -   **Cause:** Another application on your computer is using port 8080.
    -   **Solution:** Stop the other application, or change the port mapping in `docker-compose.mvp.yml`. For example, change `ports: - "8080:8080"` to `ports: - "8081:8080"`. If you do this, you must also update the WebSocket URL in `frontend/chat.html` to connect to `ws://localhost:8081/...`.

-   **Chat shows "Error connecting to the server."**
    -   **Cause:** The backend container is not running or is not accessible.
    -   **Solution:** Make sure you have run `docker-compose -f docker-compose.mvp.yml up` and that the logs show "Uvicorn running on http://0.0.0.0:8080". Also, check for any port mismatches as described above.

-   **AI responses are strange or irrelevant.**
    -   **Cause:** The prompt being sent to the AI might be malformed or lack sufficient context.
    -   **Solution:** Check the Docker logs. The backend is configured to print the exact prompt being sent to the AI. This can help diagnose issues with how the persona, history, and memories are being assembled.
