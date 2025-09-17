"""
Tým Snů (AutoGen): Kreativní brainstorming agentů Philosopher a Architect v AutoGen frameworku.
"""
from pyautogen.agentchat import Agent, GroupChat, GroupChatManager
from core.agent_config import load_agent_config

class SimplePhilosopher(Agent):
    def __init__(self):
        agent_config = load_agent_config("philosopher")
        super().__init__(name=agent_config['role'], system_message=agent_config['goal'])
    def generate_message(self, messages, context):
        return "Navrhuji analyzovat poslední cyklus a hledat vzory pro zlepšení."

class SimpleArchitect(Agent):
    def __init__(self):
        agent_config = load_agent_config("architect")
        super().__init__(name=agent_config['role'], system_message=agent_config['goal'])
    def generate_message(self, messages, context):
        return "Navrhuji vytvořit nový plán pro efektivnější workflow."

def run_autogen_brainstorm():
    philosopher = SimplePhilosopher()
    architect = SimpleArchitect()
    group = GroupChat([philosopher, architect], manager=GroupChatManager())
    result = group.chat("Jak můžeme vylepšit systém Sophia?")
    return result

if __name__ == "__main__":
    print("--- AutoGen Tým Snů: Brainstorming ---")
    output = run_autogen_brainstorm()
    print(output)
