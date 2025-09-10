Project Overview
Sophia is an advanced autonomous AI agent written in Python 3.11+. The project follows a multi-agent architecture orchestrated by the CrewAI framework. The primary goal is to create a system capable of complex problem-solving, continuous learning through a cognitive memory architecture, and autonomous code self-improvement via a secure DevOps pipeline.
• Primary Language: Python 3.11+
• Orchestration Framework: CrewAI
• Key Component Libraries: LangChain (for agent tools), LlamaIndex (for RAG capabilities)
• Cognitive Memory: A dual-component system with an episodic log and a semantic vector store (ChromaDB for development, Pinecone for production).
• Architecture: See the architectural diagram and description in the project's documentation.
--------------------------------------------------------------------------------
Dev Environment Setup
1. Create and activate a virtual environment:
2. Install dependencies using pip:
3. Set up required environment variables: Create a .env file from the .env.example template and fill in the necessary API keys (e.g., GEMINI_API_KEY, PINECONE_API_KEY).
--------------------------------------------------------------------------------
Code Style and Conventions
• All Python code MUST adhere to the PEP 8 style guide.
• Use the black code formatter to ensure consistent formatting. Run black . before committing.
• All new functions and classes MUST have Google-style docstrings.
• Type hints are mandatory for all function signatures.
• Avoid global variables. Pass state explicitly through function arguments or class instances.
--------------------------------------------------------------------------------
Testing
• The project uses pytest for unit and integration testing.
• Run all tests from the project root directory:
To run tests for a specific file:
Bash
pytest path/to/your/test_file.py All new features or bug fixes MUST be accompanied by corresponding tests. Code coverage should not decrease.
Commit and PR Instructions Commit Message Format: Follow the Conventional Commits specification.
Example: feat: add self-healing capability to CodingAgent
Example: fix: resolve issue with memory retrieval loop
Pull Requests (PRs):
PR titles should be clear and descriptive.
The PR description must explain the "what" and "why" of the changes.
All CI checks (linting, testing) MUST pass before a PR can be merged.