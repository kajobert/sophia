from core.llm_config import load_config

def load_agent_config(agent_name: str) -> dict:
    """
    Načte konfiguraci pro specifického agenta z hlavního konfiguračního souboru.

    Args:
        agent_name: Název agenta (např. 'planner', 'engineer').

    Returns:
        Slovník s konfigurací pro daného agenta.

    Raises:
        ValueError: Pokud konfigurace pro daného agenta není nalezena.
    """
    config = load_config()
    agents_config = config.get('agents', {})
    agent_config = agents_config.get(agent_name)

    if not agent_config:
        raise ValueError(f"Konfigurace pro agenta '{agent_name}' nebyla nalezena v konfiguračním souboru.")

    return agent_config
