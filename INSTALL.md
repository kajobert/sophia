# Installation and Setup Guide for Sophia V3

This guide provides simple instructions to get the Sophia V3 project set up and running, specifically within a GitHub Codespace or a similar Linux-based environment.

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
The script will upgrade pip, install all Python libraries from `requirements.txt`, and create a `.env` file for your environment variables.

### 3. Configure Environment (Optional)

The setup script creates a `.env` file. If the project requires API keys (e.g., for OpenAI, Anthropic), you must add them to this `.env` file.

Example `.env` content:
```
OPENAI_API_KEY="your_api_key_here"
ANTHROPIC_API_KEY="your_api_key_here"
```

### 4. Start Sophia

You are now ready to start the application. The main entry point is `guardian.py`, which monitors and runs the core process.

Run the following command:
```bash
python3 guardian.py
```

You should now see log output from both the Guardian and the main Sophia process in your terminal, indicating that the AGI is running its "Waking/Sleeping" lifecycle.

## 🧪 Running Tests

To ensure the integrity of the codebase, you can run the unit tests.

Run the following command from the root of the repository:
```bash
python3 -m unittest discover tests
```
This will automatically discover and run all tests in the `tests` directory.
