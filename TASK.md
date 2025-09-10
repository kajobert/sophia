# TASK: Finální oprava a zprovoznění pomocí řetězení úkolů

## Cíl
Definitivně vyřešit problém s předáváním dat mezi nástroji tím, že refaktorujeme úkoly do dvou oddělených, na sebe navazujících kroků. Tím zajistíme, že výstup z jednoho úkolu bude spolehlivě sloužit jako vstup pro další.

## Analýza
Diagnostika je kompletní. Problém není v nástrojích samotných, ale v implicitním předávání kontextu. Řešením je vytvořit dva specializované úkoly (`Task`) a explicitně je seřadit. Výstup z prvního úkolu (`search_task`) bude automaticky dostupný jako kontext pro druhý úkol (`report_task`).

## Plán Krok za Krokem

### Krok 1: Refaktorizace `core/tasks.py` na dva úkoly
Uprav soubor `core/tasks.py` tak, aby obsahoval dva oddělené, specializované úkoly.

**Nahraď celý obsah souboru `core/tasks.py` tímto kódem:**
```python
from crewai import Task
from .agents import developer_agent

# Úkol č. 1: Pouze vyhledávání informací
search_task = Task(
    description="Perform a web search to find out who the current CEO of NVIDIA is. Focus only on finding the name.",
    expected_output="The full name of the current CEO of NVIDIA.",
    agent=developer_agent
)

# Úkol č. 2: Vytvoření reportu na základě výsledků z předchozího úkolu
report_task = Task(
    description="""Create a new report file named 'ceo_nvidia_report.txt'.
    Write the name of the CEO you found in the previous task into this file.
    The content should be a simple sentence, e.g., 'The current CEO of NVIDIA is [Name]'.""",
    expected_output="A confirmation that the file 'ceo_nvidia_report.txt' was created with the correct sentence.",
    agent=developer_agent,
    # Tento klíčový parametr říká, že tento úkol potřebuje výstup z předchozích úkolů
    context=[search_task]
)
Krok 2: Aktualizace main.py pro spuštění celé "montážní linky"
Uprav main.py tak, aby do Crew předal oba naše nové úkoly ve správném pořadí.

Nahraď celý obsah souboru main.py tímto kódem:

Python

from dotenv import load_dotenv
from crewai import Crew, Process

load_dotenv()

from core.agents import developer_agent
# Importujeme oba nové úkoly
from core.tasks import search_task, report_task

def main():
    print("🚀 Initializing the Sophia v2 Crew for a chained task...")
    
    sophia_crew = Crew(
        agents=[developer_agent],
        # Předáme oba úkoly v pořadí, v jakém se mají provést
        tasks=[search_task, report_task],
        process=Process.sequential,
        verbose=True
    )

    print("🏁 Crew assembled. Kicking off the task...")
    result = sophia_crew.kickoff()
    
    print("\\n--- FINAL RESULT ---")
    print(result)

if __name__ == "__main__":
    main()
Krok 3: Finální ověření
Spusť python main.py. Nyní bys měl v logu vidět, jak agent nejprve dokončí search_task, jeho výsledek se uloží, a poté úspěšně spustí report_task, který tento výsledek použije k vytvoření souboru.