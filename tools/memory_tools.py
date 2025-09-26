import sys
import os

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.memory_manager import MemoryManager

def recall_past_tasks(keywords: str) -> str:
    """
    Searches the long-term memory for past tasks related to a list of keywords.
    Keywords should be a comma-separated string (e.g., "file system, read, error").
    Returns a summary of relevant past tasks to provide context for the current task.
    This helps in learning from past successes and failures.
    """
    if not keywords or not isinstance(keywords, str):
        return "Error: Please provide a comma-separated string of keywords."

    keyword_list = [kw.strip() for kw in keywords.split(",")]

    try:
        memory = MemoryManager()
        memories = memory.get_relevant_memories(keyword_list)
        memory.close()

        if not memories:
            return "No relevant memories found for the given keywords."

        response = "Found relevant memories from past tasks:\n\n"
        for mem in memories:
            response += f"- **Task:** {mem['task']}\n"
            response += f"  **Summary:** {mem['summary']}\n"
            response += f"  **Timestamp:** {mem['timestamp']}\n\n"

        return response.strip()
    except Exception as e:
        return f"Error recalling memories: {e}"