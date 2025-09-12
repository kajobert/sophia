
from langchain.tools import BaseTool
from memory.long_term_memory import LongTermMemory

def ltm_write_tool(memory_text: str) -> str:
    """Zapíše textový vstup jako vzpomínku do Dlouhodobé Paměti (LTM)"""
    # memory_text může být předán jako dict (pokud invoke), nebo přímo jako string
    if isinstance(memory_text, dict):
        memory_text = memory_text.get("memory_text") or next(iter(memory_text.values()), "")
    if not memory_text:
        return "LtmWriteTool: Chybí text ke zpracování."
    memory_keywords = [
        "zapamatuj", "ulož do paměti", "vzpomínka", "remember", "memory", "pamatuj si", "ulož si", "save to memory", "store in memory"
    ]
    lower_text = memory_text.lower()
    if not any(kw in lower_text for kw in memory_keywords):
        return (
            "Tento nástroj je určen pouze pro zápis do dlouhodobé paměti (LTM). "
            "Pokud chcete upravit soubor, použijte FileWriteTool nebo FileEditTool. "
            "Pokud chcete uložit vzpomínku, formulujte prompt např. 'Zapamatuj si ...' nebo 'Ulož do paměti ...'."
        )
    ltm = LongTermMemory()
    existing = ltm.fetch_relevant_memories(memory_text, num_results=10)
    if existing and existing[0]:
        for doc in existing[0]:
            if memory_text.strip() == doc.strip():
                return f"Duplicitní vzpomínka nebyla uložena (již existuje v LTM): '{memory_text[:50]}...'"
    ltm.add_memory(memory_text)
    return f"Vzpomínka úspěšně uložena: '{memory_text[:50]}...'"


class LtmWriteTool(BaseTool):
    name: str = "LTM Write Tool"
    description: str = "Zapíše textový vstup jako vzpomínku do Dlouhodobé Paměti (LTM)"

    def _run(self, memory_text: str) -> str:
        return ltm_write_tool(memory_text)