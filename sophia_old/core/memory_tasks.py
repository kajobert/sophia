from crewai import Task
from core.memory_agent import memory_agent

memory_consolidation_task = Task(
    description=(
        "Analyzuj následující text, který představuje záznam nedávné události nebo interakce: '{context}'. "
        "Extrahuj z něj jeden nejdůležitější a nejucelenější klíčový poznatek nebo informaci, která by měla být trvale uložena. "
        "Tento poznatek formuluj jako jednu nebo dvě stručné, jasné věty."
    ),
    expected_output=(
        "Jeden klíčový poznatek ve formě stručného textového řetězce, připravený k uložení do dlouhodobé paměti."
    ),
    agent=memory_agent,
)
