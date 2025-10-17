# Local Development Guide

This guide provides instructions for setting up and running the Nomad agent and its related services for local development.

## Prerequisites

*   Python 3.10+
*   Docker and Docker Compose
*   An API key for an LLM provider (e.g., OpenAI, Google Gemini, or OpenRouter)

## Standard Setup (Backend + TUI)

This is the standard way to run the full Nomad application, including the FastAPI backend and the Textual TUI.

1.  **Create an Environment File:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```

2.  **Add Your API Key:**
    Open the `.env` file and add your API key:
    ```
    GEMINI_API_KEY=your_api_key_here
    ```

3.  **Build and Run with Docker Compose:**
    This command will build the Docker images and start the backend service.
    ```bash
    docker-compose up -d --build
    ```

4.  **Run the TUI (Optional):**
    To interact with the backend, you can run the TUI in a separate terminal:
    ```bash
    docker-compose run --rm tui
    ```

## NEW: Running the Proactive MVP Agent

This mode runs the new, simplified proactive agent directly. It's ideal for testing the core decision-making loop without the overhead of the full API and TUI.

1.  **Ensure Your Environment is Set Up:**
    You still need a valid `.env` file with an API key, as described in the standard setup.

2.  **Run the MVP with Docker Compose:**
    Use the `docker-compose.mvp.yml` file to start the agent.
    ```bash
    docker-compose -f docker-compose.mvp.yml up
    ```

3.  **Enter the Mission Goal:**
    After the container starts, you will be prompted directly in your terminal to enter a mission goal. Type the goal and press Enter.

    ```
    Please enter the mission goal for the proactive agent:
    Read the file 'hello.txt' and then write 'goodbye' to it.
    ```

4.  **Observe the Agent:**
    The agent will now begin its work, and you can observe its thinking process, tool calls, and results directly in the terminal output.

## Running Tests

To run the test suite, you can execute `pytest` from the root of the project. It's recommended to do this within the virtual environment.

1.  **Set up the environment:**
    ```bash
    ./scripts/setup.sh
    ```

2.  **Run all tests:**
    ```bash
    PYTHONPATH=. .venv/bin/python -m pytest
    ```

## Running the End-to-End (E2E) Test

The E2E test provides the highest level of confidence that the agent is working correctly. It spins up the entire application stack using Docker, submits a real mission via the API, and verifies the outcome by checking the agent's logs and output files.

**Prerequisites:**
*   Docker must be running.
*   The test requires an OpenRouter API key.

**Execution:**

1.  **Run the E2E test script:**
    From the root of the project, execute the following command:
    ```bash
    python scripts/run_e2e_test.py
    ```

2.  **Observe the Output:**
    The script will print its progress, including:
    *   Setting up the Docker environment.
    *   Waiting for the backend API to become healthy.
    *   Submitting the test mission.
    *   Monitoring logs for success or failure markers.
    *   Verifying the final output file in the `sandbox` directory.
    *   Cleaning up the Docker environment.

    The script will exit with code `0` on success and `1` on failure.