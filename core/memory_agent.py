from crewai import Agent

memory_agent = Agent(
    role='Memory Consolidator',
    goal='Analyze recent short-term memory and extract key insights for long-term storage.',
    backstory="You are responsible for reviewing the agent's recent experiences and saving important knowledge to long-term memory.",
    verbose=True,
    allow_delegation=False,
    llm='gemini/gemini-2.5-flash',
    tools=[]  # Pokud bude potřeba, lze přidat nástroje pro práci s pamětí
)
