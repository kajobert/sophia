 
import os

def episodic_memory_summary_tool(num_events: int = 20) -> str:
    """Načte a sumarizuje poslední události z episodic_memory.log. Vrací stručný přehled klíčových událostí pro konsolidaci do LTM."""
    log_path = "logs/episodic_memory.log"
    if not os.path.exists(log_path):
        return "Episodic memory log neexistuje."
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        events = [line.strip() for line in lines if line.strip()][-num_events:]
        if not events:
            return "Episodic memory log je prázdný."
        summary = "Souhrn posledních událostí z episodic_memory.log:\n"
        for event in events:
            summary += f"- {event}\n"
        return summary
    except Exception as e:
        return f"Chyba při čtení episodic_memory.log: {e}"


