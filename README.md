# Sophia

Lightweight project to demo autonomous agents built with CrewAI.

Setup

1. Create a `.env` file in the repository root with required API keys:

```
SERPER_API_KEY="your_serper_api_key"
GEMINI_API_KEY="your_gemini_api_key"
```

2. Install Python deps:

```bash
pip install -r requirements.txt
```

Run

```bash
python main.py
```

Notes

- Do not commit `.env` to the repo.
- The project includes tools for web search (`SerperDevTool`) and local file reading (`FileReadTool`, `DirectoryReadTool`).
