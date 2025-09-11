# TASK: Finální refaktoring na architekturu řetězených úkolů

## Cíl
Definitivně vyřešit problém s předáváním dat mezi nástroji tím, že refaktorujeme naši logiku do dvou oddělených, na sebe navazujících úkolů (`Task`). Tím zajistíme, že výstup z jednoho úkolu bude spolehlivě sloužit jako vstup pro další.

## Analýza
Diagnostika je kompletní. Problém není v nástrojích samotných, ale v nespolehlivém předávání argumentů v rámci jednoho komplexního úkolu. Řešením je rozdělit logiku na dva jednodušší, specializované úkoly a využít vestavěný mechanismus `context` pro předávání dat mezi nimi.

## Plán Krok za Krokem

### Krok 1: Zjednodušení `core/custom_tools.py`
Upravíme naše nástroje tak, aby byly co nejjednodušší a dělaly jen jednu věc.

**Nahraď celý obsah souboru `core/custom_tools.py` tímto kódem:**
```python
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool as CrewaiSerperDevTool

class WebSearchTool(BaseTool):
    name: str = "Web Search Tool"
    description: str = "Performs a web search for a given query."
    
    def _run(self, search_query: str) -> str:
        # Tento nástroj nyní vrací jen stručný výsledek
        results = CrewaiSerperDevTool().run(search_query)
        # Zpracujeme výsledek, abychom vrátili jen čistou informaci
        # Zde by mohla být pokročilejší logika, pro teď stačí toto:
        return results.split('Snippet:')[0]

class FileWriteTool(BaseTool):
    name: str = "File Write Tool"
    description: str = "Writes content to a specified file."

    def _run(self, file_path: str, content: str) -> str:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to file: {file_path}."
        except Exception as e:
            return f"Error writing to file {file_path}: {e}"
Krok 2: Úprava core/agents.py
Agent bude mít k dispozici jen tyto dva jednoduché nástroje.

Nahraď celý obsah core/agents.py tímto kódem:

Python

from crewai import Agent
from core.custom_tools import WebSearchTool, FileWriteTool

developer_agent = Agent(
    role='Autonomous Task Executor',
    goal='Execute multi-step tasks by sequentially using the available tools based on instructions.',
    backstory="A reliable agent that follows instructions perfectly.",
    verbose=True,
    allow_delegation=False,
    llm='gemini/gemini-1.5-flash-latest',
    tools=[
        WebSearchTool(),
        FileWriteTool()
    ]
)
Krok 3: Vytvoření řetězených úkolů v core/tasks.py
Toto je klíčová změna, která implementuje naši "montážní linku".

Nahraď celý obsah core/tasks.py tímto kódem:

Python

from crewai import Task
from .agents import developer_agent

# Úkol č. 1: Pouze vyhledávání informací
search_task = Task(
    description="Perform a web search to find out who the current CEO of NVIDIA is. Focus only on finding the name.",
    expected_output="The full name of the current CEO of NVIDIA.",
    agent=developer_agent
)

# Úkol č. 2: Vytvoření reportu na základě výsledků z PŘEDCHOZÍHO úkolu
report_task = Task(
    description="""Create a new report file named 'ceo_nvidia_report.txt'.
    Write the name of the CEO you found in the previous task into this file.
    The content should be a simple sentence, e.g., 'The current CEO of NVIDIA is [Name]'.""",
    expected_output="A confirmation that the file 'ceo_nvidia_report.txt' was created with the correct sentence.",
    agent=developer_agent,
    # Tento klíčový parametr říká, že tento úkol potřebuje výstup z předchozích úkolů
    context=[search_task]
)
Krok 4: Finální main.py
Upravíme main.py pro spuštění celé sekvence.

Nahraď celý obsah main.py tímto kódem:

Python

from dotenv import load_dotenv
from crewai import Crew, Process
load_dotenv()

from core.agents import developer_agent
from core.tasks import search_task, report_task

def main():
    print("🚀 Initializing the Sophia v2 Crew for a chained task...")
    sophia_crew = Crew(
        agents=[developer_agent],
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