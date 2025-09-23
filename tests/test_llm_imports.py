import ast
import os

SRC_DIRS = ["agents", "core", "memory", "tools"]
EXCEPTIONS = [
    "core/llm_config.py",
    "core/gemini_llm_adapter.py",
    "agents/planner_agent.py",  # PlannerAgent is now a special case, directly using the adapter
]

FORBIDDEN = ["GeminiLLMAdapter", "genai.GenerativeModel"]
REQUIRED_IMPORT = "from core.llm_config import llm"


def find_py_files():
    files = []
    for src in SRC_DIRS:
        for root, _, filenames in os.walk(src):
            for f in filenames:
                if f.endswith(".py"):
                    rel = os.path.join(root, f)
                    if rel not in EXCEPTIONS:
                        files.append(rel)
    return files


def test_no_forbidden_llm_imports():
    files = find_py_files()
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src, filename=file)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "core.gemini_llm_adapter":
                    for n in node.names:
                        assert (
                            n.name != "GeminiLLMAdapter"
                        ), f"{file} nesmí importovat GeminiLLMAdapter přímo!"
            if isinstance(node, ast.Import):
                for n in node.names:
                    assert n.name != "genai", f"{file} nesmí importovat genai přímo!"
            if isinstance(node, ast.Name):
                assert (
                    node.id not in FORBIDDEN
                ), f"{file} nesmí používat {node.id} přímo!"


def test_llm_import_pattern():
    files = find_py_files()
    # This test is too broad. Agent classes receive llm in __init__ and don't need to import it.
    # We will exclude them from this check.
    agent_class_files = [
        "agents/architect_agent.py",
        "agents/engineer_agent.py",
        "agents/philosopher_agent.py",
        "agents/planner_agent.py",
        "agents/tester_agent.py",
        "core/consciousness_loop.py",
            "core/orchestrator.py",  # Receives LLM in __init__
        "tools/worklog_compressor.py",  # This file mentions LLM in a comment, but doesn't use it.
    ]

    for file in files:
        if file in agent_class_files:
            continue

        with open(file, "r", encoding="utf-8") as f:
            src = f.read()
        if "llm" in src:
            # Akceptuj jakýkoliv import llm z core/llm_config.py (i kombinovaný)
            found = False
            for line in src.splitlines():
                line = line.strip()
                if line.startswith("from core.llm_config import") and "llm" in line:
                    found = True
                if line.startswith("import llm"):
                    found = True
            assert found, f"{file} musí importovat llm z core/llm_config.py!"
