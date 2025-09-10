# TASK: Vybavení agenta schopností číst soubory

## Cíl
Rozšířit schopnosti agenta `researcher` o nástroje pro práci s lokálním souborovým systémem. Toto je první krok k tomu, aby agent mohl v budoucnu analyzovat a upravovat svůj vlastní kód.

## Analýza
Agent momentálně umí prohledávat pouze web. Pro sebereflexi potřebuje přístup k souborům v projektu. K tomu využijeme předpřipravené nástroje `FileReadTool` a `DirectoryReadTool`.

## Plán Krok za Krokem

### Krok 1: Aktualizace kódu v `core/agents.py` (úkol pro Agenta)
Uprav soubor `core/agents.py` tak, aby obsahoval nové nástroje pro čtení souborů a adresářů.

1.  **Importuj** nové nástroje z `crewai_tools`.
2.  **Inicializuj** je.
3.  **Přidej** je do seznamu nástrojů pro agenta `researcher`.

**Výsledný soubor `core/agents.py` by měl vypadat takto:**
```python
import os
from crewai import Agent
from crewai_tools import SerperDevTool, FileReadTool, DirectoryReadTool # <-- ZMĚNA ZDE
from langchain_google_genai import ChatGoogleGenerativeAI

# Inicializace LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",
                             google_api_key=os.getenv("GEMINI_API_KEY"))

# Inicializace nástrojů
search_tool = SerperDevTool()
file_read_tool = FileReadTool()
directory_read_tool = DirectoryReadTool()

# Definice agenta, nyní s rozšířenými schopnostmi
researcher = Agent(
    role='Senior Source Code Analyst', # <-- Mírná úprava role
    goal='Analyze source code and project structures to understand their functionality', # <-- Mírná úprava cíle
    backstory="""You are an expert software developer.
    Your expertise lies in analyzing complex codebases and project layouts.
    You have a knack for reading code and explaining its purpose clearly.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[search_tool, file_read_tool, directory_read_tool] # <-- ZMĚNA ZDE
)
Krok 2: Aktualizace úkolu v core/tasks.py (úkol pro Agenta)
Uprav soubor core/tasks.py tak, aby agent dostal za úkol analyzovat jeden ze svých vlastních souborů. Nahraď obsah celého souboru tímto novým zadáním:

Python

from crewai import Task
from .agents import researcher

# Nový úkol, který vyžaduje čtení lokálního souboru
code_analysis_task = Task(
    description="""Read the content of the 'core/agents.py' file.
    Based on the code, identify the 'role', 'goal', and the list of 'tools'
    assigned to the agent defined in that file.
    Your final answer MUST be a clear, bulleted list of these three pieces of information.""",
    expected_output="A bullet point list containing the role, goal, and tools of the agent.",
    agent=researcher
)
Krok 3: Aktualizace main.py (úkol pro Agenta)
Uprav soubor main.py, aby importoval a spouštěl náš nový úkol. Nahraď obsah celého souboru:

Python

from dotenv import load_dotenv
from crewai import Crew, Process

# Načteme API klíč hned na začátku
load_dotenv()

# Importujeme naše agenty a NOVÝ úkol z modulu 'core'
from core.agents import researcher
from core.tasks import code_analysis_task # <-- ZMĚNA ZDE

def main():
    """Hlavní funkce pro sestavení a spuštění Crew."""
    print("🚀 Initializing the Sophia v2 Crew for a code analysis task...")

    # Sestavení posádky s naším agentem a NOVÝM úkolem
    sophia_crew = Crew(
        agents=[researcher],
        tasks=[code_analysis_task], # <-- ZMĚNA ZDE
        process=Process.sequential,
        verbose=2
    )

    print("🏁 Crew assembled. Kicking off the task...")
    result = sophia_crew.kickoff()

    print("\n\n########################")
    print("## ✅ Task Completed!")
    print("## Here is the result:")
    print("########################\n")
    print(result)

if __name__ == "__main__":
    main()